import time
import datetime
import board
import busio
import numpy as np
import adafruit_mlx90640
import pyrebase
import Adafruit_DHT
import matplotlib.pyplot as plt
import cv2
import os
import json
from scipy import ndimage
import threading
import RPi.GPIO as GPIO
import urllib.request
from board import SCL, SDA
from oled_text import OledText

i2c = busio.I2C(SCL, SDA)
oled = OledText(i2c, 128, 64)

# declaring variables
bulb_status="OFF"
fan_status="OFF"
motor_status = "OFF"
rolling_direction=""
forward_ON = False
backward_ON = False
fan_bulb_ON = False
days_left=0
humidity=0
temperature=0
body_temperature=0
room_temperature=0

def check_internet():
    try:
        urllib.request.urlopen('http://www.google.com', timeout=1)
        return True
    except urllib.request.URLError:
        return False

if check_internet():
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
    global humidity, temperature
    
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(dht_type, dht_pin)

        if check_internet():
            # Update DHT11 sensor values in Firebase
            db.child("dht_sensor").update({"humidity": humidity, "temperature": temperature})
        
        time.sleep(1)  # Adjust the delay between readings as needed

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

# Create a function to read the temperature from the MLX90640 infrared camera
def read_mlx90640_temperature():
    global room_temperature, body_temperature
    while True:
        try:
            mlx.getFrame(frame)
            room_temperature = np.mean(frame)
            body_temperature = frame[16 + 16 * 32] 
            
            if check_internet():
                # Update MLX90640 temperature in Firebase
                db.child("camera_sensor").update({"bodyTemp": body_temperature})
                db.child("camera_sensor").update({"roomTemp": room_temperature})
                
        except ValueError:
            continue  # if error, just read again
        time.sleep(1)  # Adjust the delay between readings as needed

# Create a function to capture and upload the image from the MLX90640 infrared camera
def capture_and_upload_image():
    while True:
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
        time.sleep(1)  # Adjust the delay between readings as needed

def calculate_remaining_days():
    start_date = datetime.date(2023, 5, 16)
    current_date = datetime.date.today()
    remaining_days = (start_date - current_date).days

    # Store the remaining days and starting date in variables
    global days_left, starting_date
    days_left = remaining_days
    if days_left < 0:
        days_left = abs(days_left)
        
    starting_date = start_date.strftime("%Y-%m-%d")

    # Update the JSON file
    data = {
        "days_left": days_left,
        "starting_date": starting_date
    }
    with open("date.json", "w") as file:
        json.dump(data, file)
        
    # Schedule the next update after 24 hours
    threading.Timer(24 * 60 * 60, calculate_remaining_days).start()

def update_firebase():
    with open("date.json", "r") as file:
        data = json.load(file)

    days_left = data.get("days_left", 0)
    starting_date = data.get("starting_date", "")

    # Make sure days_left is positive
    if days_left < 0:
        days_left = abs(days_left)

    if check_internet():
        db.child("day_tracker").update({"daysLeft": days_left})
        db.child("day_tracker").update({"startDate": starting_date})

    # Schedule the next update after 24 hours
    threading.Timer(24 * 60 * 60, update_firebase).start()

# Set up GPIO pins for the stepper motor control
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

relay_pin_1 = 23 # BULB
relay_pin_2 = 24 # FAN

GPIO.setup(relay_pin_1, GPIO.OUT)
GPIO.setup(relay_pin_2, GPIO.OUT)

MotorPin_A = [17, 18, 27, 22]
MotorPin_B = [12, 13, 6, 5]

seq = [[1, 0, 0, 0],
       [1, 1, 0, 0],
       [0, 1, 0, 0],
       [0, 1, 1, 0],
       [0, 0, 1, 0],
       [0, 0, 1, 1],
       [0, 0, 0, 1],
       [1, 0, 0, 1]]

# Set up motor pins
for pin in MotorPin_A:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

for pin in MotorPin_B:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)


# Create functions for stepper motor control
def rotate_forward():
    global motor_status, rolling_direction, forward_ON
    
    while True:
        # ENABLED
        # 7AM - 7PM CLOSE, THIS FUNCTION
        
        # DAY 1-3 - temperature > 34 
        # DAY 4-7 - temperature > 34 
        # DAY 8-14 - temperature > 31 
        if (humidity > 65):
            
            forward_ON = True

            motor_status="ON"
            rolling_direction="Rolling Forward."
            
            if check_internet():
                db.child("motor_status").update({"status": "rolling down"})
            
            for i in range(5):
                for i in range(512):
                    for halfstep in range(8):
                        for pin in range(4):
                            GPIO.output(MotorPin_A[pin], seq[halfstep][pin])
                            GPIO.output(MotorPin_B[pin], seq[halfstep][pin])
                        time.sleep(0.001)
            
            motor_status="OFF"
            rolling_direction=""

            if check_internet():
                db.child("motor_status").update({"status": "OFF"})
            
            while (humidity > 65):
                
                # DAY 1-3 - temperature > 34 
                # DAY 4-7 - temperature > 34 
                # DAY 8-14 - temperature > 31 
                if(humidity < 65):
                    rotate_backward()


    
def rotate_backward():
    global motor_status, rolling_direction, backward_ON
    
    while True:
        # DAY 1-3 - temperature > 34 
        # DAY 4-7 - temperature > 34 
        # DAY 8-14 - temperature > 31 
        if (humidity < 65):
            
            backward_ON = True
            motor_status = "ON"
            rolling_direction = "Rolling Backward."

            if check_internet():
                db.child("motor_status").update({"status": "rolling up"})
            
            for i in range(5):
                for i in range(512):
                    for halfstep in reversed(range(8)):
                        for pin in range(4):
                            GPIO.output(MotorPin_A[pin], seq[halfstep][pin])
                            GPIO.output(MotorPin_B[pin], seq[halfstep][pin])
                        time.sleep(0.001)
            
            motor_status = "OFF"
            rolling_direction = ""
            
            if check_internet():
                db.child("motor_status").update({"status": "OFF"})
                
            while (humidity < 65):
                # DAY 1-3 - temperature > 34 
                # DAY 4-7 - temperature > 34 
                # DAY 8-14 - temperature > 31 
                if(humidity > 65):
                    rotate_forward()
        
def fan_on():
    global  fan_status
    
    while True:
        # ENABLED
        # 7:01PM - 6:59AM CLOSE
        
        # DAY 1-3 - temperature > 34 
        # DAY 4-7 - temperature > 34 
        # DAY 8-14 - temperature > 31 
        
        if(humidity > 65):
            GPIO.output(relay_pin_2, GPIO.HIGH)
            fan_status = "ON"

            if check_internet():
                db.child("fan_status").update({"status": "ON"})
            
            time.sleep(60)
            
            GPIO.output(relay_pin_2, GPIO.LOW)

            fan_status = "OFF"

            if check_internet():
                db.child("fan_status").update({"status": "OFF"})
                
            while(humidity > 65):
                print("still hot, fan on")
                if(humidity < 65):
                    print("now cold, fan off")
                    continue
            # Delay before running the thread again
            time.sleep(5)
    
def bulb_on():
    global bulb_status
    
    # DAY 1-3 - temperature < 33 
    # DAY 4-7 - temperature < 32 
    # DAY 8-14 - temperature < 29 
    
    while True:
        if humidity < 65:
            GPIO.output(relay_pin_1, GPIO.HIGH)
            bulb_status = "ON"    
        
            if check_internet():
                db.child("bulb_status").update({"status": "ON"})
        
            time.sleep(60)
        
            GPIO.output(relay_pin_1, GPIO.LOW)
            bulb_status = "OFF"
        
            if check_internet():
                db.child("bulb_status").update({"status": "OFF"})
        
        while humidity < 65:
            if humidity > 65:
                continue  # Continue to the next iteration of the inner while loop
        # Delay before running the thread again
        time.sleep(5)

def check_time():
    rotate_forward = None
    rotate_backward = None
    fan_on = None
    while True:
        now = datetime.datetime.now().time()
        if now >= datetime.time(7, 0) and now < datetime.time(19, 0):
            # Between 7:00am and 7:00pm
            
            if check_internet():
                db.child("fan_status").update({"status": "OFF"})
            
            if 'rotate_forward' not in globals():
                rotate_forward_thread = threading.Thread(target=rotate_forward)
                rotate_forward_thread.start()

            if 'rotate_backward' not in globals():
                rotate_backward_thread = threading.Thread(target=rotate_backward)
                rotate_backward_thread.start()

            if 'fan_on' in globals():
                del fan_on
        else:
            # After 7:00pm
            if check_internet():
                db.child("motor_status").update({"status": "OFF"})
            
            if 'rotate_forward' in globals():
                del rotate_forward

            if 'rotate_backward' in globals():
                del rotate_backward

            if 'fan_on' not in globals():
                fan_on_thread = threading.Thread(target=fan_on)
                fan_on_thread.start()

        time.sleep(60)  # Check time every minute
    
      
    
def oled_screen_display():
    while True:
        oled.clear()
        oled.text("   DHT11 Sensor", 1)
        oled.text("Humidity: {}%".format(humidity), 3)
        oled.text("Temp.: {}°C".format(temperature), 4)
        oled.show()

        time.sleep(3)

        oled.clear()
        oled.text("  MLX90640 Sensor", 1)
        oled.text("Room Temp: {}°C".format(int(room_temperature)), 3)
        oled.text("Body Temp: {}°C".format(int(body_temperature)), 4)
        oled.show()

        time.sleep(3)

        oled.clear()
        oled.text("   Stepper Motor", 1)
        oled.text("Status: {}".format(motor_status), 3)
        oled.text("{}".format(rolling_direction), 4)
        oled.show()

        time.sleep(3)  # Adjust the delay between sensor updates as per your requirement

        oled.clear()
        oled.text("    Exhaust Fan", 1)
        oled.text("Status: {}".format(fan_status), 3)
        oled.text("", 4)
        oled.show()

        time.sleep(3)  # Adjust the delay between sensor updates as per your requirement

        oled.clear()
        oled.text("    Light Bulb", 1)
        oled.text("Status: {}".format(bulb_status), 3)
        oled.text("", 4)
        oled.show()

        time.sleep(3)  # Adjust the delay between sensor updates as per your requirement

        oled.clear()
        oled.text("        Day", 1)
        oled.text("         {}".format(days_left), 3)
        oled.text("", 4)
        oled.show()
        
        current_time = datetime.datetime.now().strftime("%I:%M %p")  # Get the current time in the format HH:MM AM/PM
        oled.text("   Current Time", 1)  # Display the current time
        oled.text("     {}".format(current_time), 3)  # Display the current time
        oled.text("", 4)  # Display the current time
        oled.show()
        
        time.sleep(3)  # Adjust the delay between sensor updates as per your requirement



# Create and start the threads for DHT11 sensor, MLX90640 temperature, image capture, and stepper motor control
oled_screen_thread = threading.Thread(target=oled_screen_display)
dht_thread = threading.Thread(target=read_dht11_sensor)
mlx_temp_thread = threading.Thread(target=read_mlx90640_temperature)
capture_thread = threading.Thread(target=capture_and_upload_image)
calculate_days_thread = threading.Thread(target=calculate_remaining_days)
update_firebase_thread = threading.Thread(target=update_firebase)

bulb_thread = threading.Thread(target=bulb_on)
check_time_thread = threading.Thread(target=check_time)

dht_thread.start()
mlx_temp_thread.start()
calculate_days_thread.start()
oled_screen_thread.start()
bulb_thread.start()
check_time_thread.start()

if check_internet():
    capture_thread.start()
    update_firebase_thread.start()