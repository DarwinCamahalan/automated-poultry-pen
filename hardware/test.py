import Adafruit_DHT
import time
import RPi.GPIO as GPIO
import threading
dht_pin = 4
dht_type = Adafruit_DHT.DHT11

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

def test_all():
    
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(dht_type, dht_pin)
        print(humidity)
        if(humidity > 70):
            motor_thread = threading.Thread(target=motor)
            motor_thread.start()
                        
            
        time.sleep(1)  # Adjust the delay between readings as needed
    
def motor():
    GPIO.output(relay_pin_1, GPIO.HIGH)
    GPIO.output(relay_pin_2, GPIO.HIGH)
    
    for i in range(5):
        for i in range(512):
            for halfstep in range(8):
                for pin in range(4):
                    GPIO.output(MotorPin_A[pin], seq[halfstep][pin])
                    GPIO.output(MotorPin_B[pin], seq[halfstep][pin])
                time.sleep(0.001)
                
    GPIO.output(relay_pin_1, GPIO.LOW)
    GPIO.output(relay_pin_2, GPIO.LOW)

test_all_thread = threading.Thread(target=test_all)  
test_all_thread.start()        
