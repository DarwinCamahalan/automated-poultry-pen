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
online = "Offline"
bulb_status="OFF"
fan_status="OFF"
motor_status = "OFF"
rolling_direction=""
days_left=0
humidity=0
temperature=0
body_temperature=0
room_temperature=0
max_temp_depending_on_day = 0
minx_temp_depending_on_day = 0

# Constants for time ranges
MORNING_START_TIME = datetime.time(7, 0)
MORNING_END_TIME = datetime.time(18, 59)
EVENING_START_TIME = datetime.time(19, 0)
EVENING_END_TIME = datetime.time(6, 59)

def check_internet():
    global online
    try:
        urllib.request.urlopen('http://www.google.com', timeout=1)
        online = "Online"
        return True
    except urllib.request.URLError:
        online = "Offline"
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
        try:
            humidity, temperature = Adafruit_DHT.read_retry(dht_type, dht_pin)
            if check_internet():
                # Update DHT11 sensor values in Firebase
                db.child("dht_sensor").update({"humidity": humidity, "temperature": temperature})
        except Exception as e:
            print(f"DHT11: {str(e)}")               
            continue
        time.sleep(1)  # Adjust the delay between readings as needed

def mlx90640_camera():
    # Set up the MLX90640 infrared camera
    global room_temperature, body_temperature
    
    while True:
        i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
        mlx = adafruit_mlx90640.MLX90640(i2c)
        mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
        mlx_shape = (24, 32)

        mlx_interp_val = 10
        mlx_interp_shape = (mlx_shape[0] * mlx_interp_val, mlx_shape[1] * mlx_interp_val)

        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111)
        fig.subplots_adjust(0.05, 0.05, 0.95, 0.95)
        
        color_map = plt.cm.seismic
        
        if check_internet():
            color_map = db.child('image_color/color').get().val()
            if(color_map == 1):
                color_map = plt.cm.gist_gray
            elif(color_map == 2):
                color_map = plt.cm.hot
            elif(color_map == 3):
                color_map = plt.cm.Greens.reversed()
            elif(color_map == 4):
                color_map = plt.cm.seismic
            
            

        therm1 = ax.imshow(np.zeros(mlx_interp_shape), interpolation='none', cmap=color_map, vmin=25, vmax=45)

        cbar = fig.colorbar(therm1)
        cbar.set_label('Temperature °C', fontsize=14)

        fig.canvas.draw()
        ax_background = fig.canvas.copy_from_bbox(ax.bbox)
        fig.show()

        frame = np.zeros(mlx_shape[0] * mlx_shape[1])
        t_array = []
        snapshot_filename = "image_capture.jpg"

        # Create a function to read the temperature from the MLX90640 infrared camera
        try:
            mlx.getFrame(frame)
            room_temperature = np.mean(frame)
            body_temperature = frame[16 + 16 * 32] 
            
            if check_internet():
                # Update MLX90640 temperature in Firebase
                db.child("camera_sensor").update({"bodyTemp": body_temperature})
                db.child("camera_sensor").update({"roomTemp": room_temperature})
                
                # Create a function to capture and upload the image from the MLX90640 infrared camera
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
            
        except (ValueError, RuntimeError) as e:
            print("MLX90640 Camera Error:", str(e))
            continue  # if error, just read again
        
        time.sleep(1)  # Adjust the delay between readings as needed

    

def calculate_remaining_days():
    global max_temp_depending_on_day, min_temp_depending_on_day
    
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
        
    # DAY 1-3 - temperature > 34 
    # DAY 4-7 - temperature > 34 
    # DAY 8-14 - temperature > 31   
    
    # DAY 1-3 - temperature < 33 
    # DAY 4-7 - temperature < 32 
    # DAY 8-14 - temperature < 29 
    
    if(days_left == 1 or days_left == 2 or days_left == 3):
        max_temp_depending_on_day = 34
        min_temp_depending_on_day = 33
    elif(days_left == 4 or days_left == 5 or days_left == 6 or days_left == 7):
        max_temp_depending_on_day = 34
        min_temp_depending_on_day = 32
    elif(days_left > 7 ):
        max_temp_depending_on_day = 31
        min_temp_depending_on_day = 29 
          
        
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
    global motor_status, rolling_direction
    
    while True:
        # ENABLED
        # 7AM - 7PM CLOSE, THIS FUNCTION
        
        # DAY 1-3 - temperature > 34 
        # DAY 4-7 - temperature > 34 
        # DAY 8-14 - temperature > 31 
        if MORNING_START_TIME <= datetime.datetime.now().time() <= MORNING_END_TIME:
            if (humidity > 60):
            # while (temperature < min_temp_depending_on_day):    
                motor_status="ON"
                rolling_direction="Rolling Forward."
                
                if check_internet():
                    db.child("motor_status").update({"status": "rolling down"})
                    db.child("fan_status").update({"status": "OFF"})
                
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
                
                time.sleep(60)
                # DAY 1-3 - temperature > 34 
                # DAY 4-7 - temperature > 34 
                # DAY 8-14 - temperature > 31
                while (humidity > 60):
                    if(humidity < 60):
                        continue

    
def rotate_backward():
    global motor_status, rolling_direction

    while True:
        # ENABLED
        # 7AM - 7PM CLOSE, THIS FUNCTION

        # DAY 1-3 - temperature < 33 
        # DAY 4-7 - temperature < 32 
        # DAY 8-14 - temperature < 29 
        if MORNING_START_TIME <= datetime.datetime.now().time() <= MORNING_END_TIME:
            if (humidity < 60):
            # while (temperature < min_temp_depending_on_day): 
                motor_status = "ON"
                rolling_direction = "Rolling Backward."

                if check_internet():
                    db.child("motor_status").update({"status": "rolling up"})
                    db.child("fan_status").update({"status": "OFF"})
                
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

                time.sleep(60)
                # DAY 1-3 - temperature < 33 
                # DAY 4-7 - temperature < 32 
                # DAY 8-14 - temperature < 29 
                while(humidity < 60):
                    if(humidity > 60):
                        continue
            
def fan_on():
    global  fan_status

    # ENABLED
    # 7:01PM - 6:59AM CLOSE
    
    # DAY 1-3 - temperature > 34 
    # DAY 4-7 - temperature > 34 
    # DAY 8-14 - temperature > 31 
    if EVENING_START_TIME <= datetime.datetime.now().time() or datetime.datetime.now().time() <= EVENING_END_TIME:
        while(humidity > 60):
        # while (temperature > max_temp_depending_on_day):
            GPIO.output(relay_pin_1, GPIO.HIGH)
            fan_status = "ON"

            if check_internet():
                db.child("fan_status").update({"status": "ON"})
                db.child("motor_status").update({"status": "OFF"})
            
            # time.sleep(300)
            time.sleep(60)
            
            GPIO.output(relay_pin_1, GPIO.LOW)

            fan_status = "OFF"

            if check_internet():
                db.child("fan_status").update({"status": "OFF"})

            time.sleep(60)
    
def bulb_on():
    global bulb_status
    
    # DAY 1-3 - temperature < 33 
    # DAY 4-7 - temperature < 32 
    # DAY 8-14 - temperature < 29 
    while (humidity < 60):
    # if (temperature < min_temp_depending_on_day):
        GPIO.output(relay_pin_2, GPIO.HIGH)
        bulb_status = "ON"    
    
        if check_internet():
            db.child("bulb_status").update({"status": "ON"})
    
        # time.sleep(300)
        time.sleep(60)
    
        GPIO.output(relay_pin_2, GPIO.LOW)
        bulb_status = "OFF"
    
        if check_internet():
            db.child("bulb_status").update({"status": "OFF"})

        time.sleep(60)
 
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
        
        time.sleep(3)  # Adjust the delay between sensor updates as per your requirement
        
        current_time = datetime.datetime.now().strftime("%I:%M %p")  # Get the current time in the format HH:MM AM/PM
        oled.text("   Current Time", 1)  # Display the current time
        oled.text("     {}".format(current_time), 3)  # Display the current time
        oled.text("", 4)        
        oled.show()
        
        time.sleep(3)  # Adjust the delay between sensor updates as per your requirement
        
        oled.clear()
        oled.text("  Internet Status", 1)
        oled.text("      {}".format(online), 3)
        oled.text("", 4)        
        oled.show()
        
        time.sleep(3)  # Adjust the delay between sensor updates as per your requirement



# Create and start the threads for DHT11 sensor, MLX90640 temperature, image capture, and stepper motor control
check_internet_thread = threading.Thread(target=check_internet)
oled_screen_thread = threading.Thread(target=oled_screen_display)
dht_thread = threading.Thread(target=read_dht11_sensor)
mlx_camera_thread = threading.Thread(target=mlx90640_camera)
calculate_days_thread = threading.Thread(target=calculate_remaining_days)
update_firebase_thread = threading.Thread(target=update_firebase)
bulb_thread = threading.Thread(target=bulb_on)


check_internet_thread.start()
dht_thread.start()
mlx_camera_thread.start()
calculate_days_thread.start()
oled_screen_thread.start()
bulb_thread.start()


if check_internet():
    update_firebase_thread.start()
    
# Create and start the threads
forward_thread = threading.Thread(target=rotate_forward)
backward_thread = threading.Thread(target=rotate_backward)
fan_thread = threading.Thread(target=fan_on)

forward_thread.start()
backward_thread.start()
fan_thread.start()