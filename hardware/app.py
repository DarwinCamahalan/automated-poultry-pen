import time
import board
import busio
import numpy as np
import adafruit_mlx90640
import pyrebase
import Adafruit_DHT
import matplotlib.pyplot as plt
import cv2
import os
from scipy import ndimage

# Configure Firebase with your credentials
config = {
    "apiKey": "AIzaSyBq68owsBjnpM6KRiFdJm41nd5mSpKBaW0",
    "authDomain": "poultry-monitoring-system-1.firebaseapp.com",
    "databaseURL": "https://poultry-monitoring-system-1-default-rtdb.asia-southeast1.firebasedatabase.app",
    "storageBucket": "poultry-monitoring-system-1.appspot.com",
    "serviceAccount": "./sdk.json"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()
storage = firebase.storage()

# Define the GPIO pin connected to the DATA pin of the DHT11 sensor and the sensor type
dht_pin = 4
dht_type = Adafruit_DHT.DHT11

# Create a function to read the temperature and humidity from the DHT11 sensor
def read_dht11_sensor():
    humidity, temperature = Adafruit_DHT.read_retry(dht_type, dht_pin)
    return humidity, temperature

# Set up the MLX90640 infrared camera
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
mlx = adafruit_mlx90640.MLX90640(i2c)
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
mlx_shape = (24, 32)

mlx_interp_val = 10
mlx_interp_shape = (mlx_shape[0] * mlx_interp_val, mlx_shape[1] * mlx_interp_val)

fig = plt.figure(figsize=(12, 9))
ax = fig.add_subplot(111)
fig.subplots_adjust(0.05, 0.05, 0.95, 0.95)
therm1 = ax.imshow(np.zeros(mlx_interp_shape), interpolation='none', cmap=plt.cm.bwr, vmin=25, vmax=45)
cbar = fig.colorbar(therm1)
cbar.set_label('Temperature °C', fontsize=14)

fig.canvas.draw()
ax_background = fig.canvas.copy_from_bbox(ax.bbox)
fig.show()

frame = np.zeros(mlx_shape[0] * mlx_shape[1])
t_array = []
snapshot_filename = "image_capture.jpg"

while True:
    # Read data from DHT11 sensor
    humidity, temperature = read_dht11_sensor()

    # Update DHT11 sensor values in Firebase
    db.child("dht_sensor").update({"humidity": humidity, "temperature": temperature})

    # Print DHT11 sensor values
    print("\nDHT11:")
    print("Humidity: {}%".format(humidity))
    print("Temperature: {}°C".format(temperature))

    # Read data from MLX90640 infrared camera
    try:
        mlx.getFrame(frame)
    except ValueError:
        continue

    # Calculate average temperature from the MLX90640
    average_temperature = np.mean(frame)

    # Update MLX90640 temperature in Firebase
    db.child("camera_sensor").update({"temperature": average_temperature})

    # Print MLX90640 temperature
    print("\nMLX90640 Temperature: {0:2.1f}°C".format(average_temperature))

    t1 = time.monotonic()
    try:
        mlx.getFrame(frame)
        data_array = np.reshape(frame, mlx_shape)
        data_array = ndimage.zoom(data_array, mlx_interp_val)
        therm1.set_array(data_array)
        therm1.set_clim(vmin=np.min(data_array), vmax=np.max(data_array))
        cbar.update_normal(therm1)
        ax.draw_artist(therm1)
        fig.canvas.blit(ax.bbox)
        fig.canvas.flush_events()

        # Save snapshot image
        fig.savefig(snapshot_filename, bbox_inches='tight')

        # Upload snapshot image to Firebase Storage
        storage.child(snapshot_filename).put(snapshot_filename)

        # Delete the local snapshot image after uploading to Firebase Storage
        os.remove(snapshot_filename)
        print("\nImage sent to Database")
    except ValueError:
        continue  # if error, just read again
