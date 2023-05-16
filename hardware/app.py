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
i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)
mlx = adafruit_mlx90640.MLX90640(i2c)
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
frame = np.zeros((24 * 32,))
mlx_shape = (24, 32)


# Setup the figure for plotting
plt.ion() # enables interactive plotting
fig, ax = plt.subplots(figsize=(12, 7))
therm1 = ax.imshow(np.zeros(mlx_shape), vmin=0, vmax=60, cmap='jet') # start plot with zeros and jet colormap
cbar = fig.colorbar(therm1) # setup colorbar for temps
cbar.set_label('Temperature [$^{\circ}$C]', fontsize=14) # colorbar label

frame = np.zeros((24*32,)) # setup array for storing all 768 temperatures
t_array = []
snapshot_filename = "image_capture.png"
print("Starting loop")


while True:
    # Read data from DHT11 sensor
    humidity, temperature = read_dht11_sensor()

    # Update DHT11 sensor values in Firebase
    db.child("dht_sensor").update({"humidity": humidity, "temperature": temperature})

    # Print DHT11 sensor values
    print("\nDHT11 Sensor:")
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
    print("\nMLX90640 Sensor:")
    print("Average Temperature: {0:2.1f}°C".format(average_temperature))
    
    t1 = time.monotonic()
    try:
        mlx.getFrame(frame) # read MLX temperatures into frame var
        data_array = np.reshape(frame, mlx_shape) # reshape to 24x32

        # Interpolate the data to a higher resolution
        interp_data = cv2.resize(data_array, (256, 192), interpolation=cv2.INTER_CUBIC)

        # Update the plot with interpolated data
        therm1.set_data(np.fliplr(interp_data)) # flip left to right
        therm1.set_clim(vmin=np.min(interp_data), vmax=np.max(interp_data)) # set bounds

        plt.title(f"Max Temp: {np.max(data_array):.1f}C")

        # Calculate average temperature
        avg_temp = np.mean(data_array)

        # Highlight hottest and coldest pixels
        max_temp = np.max(data_array)
        min_temp = np.min(data_array)

        # Apply temperature color mapping to the plot
        therm1.set_cmap('jet')

        # Draw text annotations for hottest, coldest, and average temperatures
        ax.text(0, -2, f"Max: {max_temp:.1f}°C", color='red', fontsize=12)
        ax.text(16, -2, f"Avg: {avg_temp:.1f}°C", color='yellow', fontsize=12)
        ax.text(28, -2, f"Min: {min_temp:.1f}°C", color='darkblue', fontsize=12)

        cbar.update_normal(therm1) # update colorbar range

        plt.pause(0.001) # required
        t_array.append(time.monotonic() - t1)
        print('Sample Rate: {0:2.1f}fps'.format(len(t_array) / np.sum(t_array)))

        # # Save snapshot image
        # snapshot_count += 1
        # image_filename = f"snapshot_{snapshot_count}.png"
        # fig.savefig(image_filename, dpi=300)
        # print(f"Snapshot saved: {image_filename}")
        
        # storage.child(image_filename).put(image_filename)
        # print(f"Snapshot sent to Firebase Storage: {image_filename}")
        
        # Save snapshot image
        fig.savefig(snapshot_filename, dpi=300)
        print(f"Snapshot saved: {snapshot_filename}")

        # Upload snapshot image to Firebase Storage
        storage.child(snapshot_filename).put(snapshot_filename)
        print(f"Snapshot sent to Firebase Storage: {snapshot_filename}")

        # Delete the local snapshot image after uploading to Firebase Storage
        os.remove(snapshot_filename)
        
    except ValueError:
        continue # if error, just read again

    # Wait for a specified time before reading again
    time.sleep(1)
