import Adafruit_DHT
from time import sleep
import RPi.GPIO as GPIO
import time


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
sensor=Adafruit_DHT.DHT11
 
gpio=4
MotorPin_A = [17,18,27,22,]
MotorPin_B = [12,13,6,5,]

for pin in MotorPin_A:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)
    
for pin in MotorPin_B:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)
    
seq = [
    [1,0,0,0],
    [1,1,0,0],
    [0,1,0,0],
    [0,1,1,0],
    [0,0,1,0],
    [0,0,1,1],
    [0,0,0,1],
    [1,0,0,1],]


def forward():
    # while True:
        for i in range (512):
            for halfstep in range(8):
                for pin in range(4):
                    GPIO.output(MotorPin_A[pin], seq[halfstep][pin])
                    GPIO.output(MotorPin_B[pin], seq[halfstep][pin])
                time.sleep(0.001)

 
def getTemp():
  while True:
    humidity, temperature = Adafruit_DHT.read_retry(sensor, gpio)
    print(int(humidity), int(temperature))
    if int(humidity) >= 45 or int(temperature) >= 34:
      forward()
  
  













getTemp()
GPIO.cleanup()
