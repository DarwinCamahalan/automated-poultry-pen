import Adafruit_DHT
from time import sleep
import RPi.GPIO as GPIO

import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

oled_reset = digitalio.DigitalInOut(board.D4)
WIDTH = 128
HEIGHT = 64 
i2c = board.I2C()  
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C, reset=oled_reset)
oled.fill(0)
oled.show()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

sensor = Adafruit_DHT.DHT11
gpio = 4

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

def forward():
    for i in range(5):
        for i in range(512):
            for halfstep in range(8):
                for pin in range(4):
                    GPIO.output(MotorPin_A[pin], seq[halfstep][pin])
                    GPIO.output(MotorPin_B[pin], seq[halfstep][pin])
                sleep(0.001)
    sleep(1)

def backward():
    for i in range(5):
        for i in range(512):
            for halfstep in reversed(range(8)):
                for pin in range(4):
                    GPIO.output(MotorPin_A[pin], seq[halfstep][pin])
                    GPIO.output(MotorPin_B[pin], seq[halfstep][pin])
                sleep(0.001)
    sleep(1)

# Get temperature and humidity
def getTemp():    
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(sensor, gpio)
        oled.fill(0)
        oled.show()
        oled.text('Current Status', 25, 0, 1)
        oled.text('Temperature: ' + str(temperature) + ' C', 0, 20, 1)
        oled.text('Humidity: ' + str(humidity), 0, 35, 1)
        oled.show()
        if humidity >= 50.0 or temperature >= 35.0:
            oled.fill(0)
            oled.show()
            oled.text('OPENING COVER...', 20, 30, 1)
            oled.show()
            backward()
        elif humidity <= 35.0 or temperature <= 20.0:
            oled.fill(0)
            oled.show()
            oled.text('CLOSING COVER...', 20, 30, 1)
            oled.show()
            forward()
        else:
            continue

try:
    getTemp()
except KeyboardInterrupt:
    print("Program stopped by user")
finally:
    GPIO.cleanup()