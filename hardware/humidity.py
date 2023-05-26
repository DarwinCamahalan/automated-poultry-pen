import Adafruit_DHT
import time
dht_pin = 4
dht_type = Adafruit_DHT.DHT11


while True:
    humidity, temperature = Adafruit_DHT.read_retry(dht_type, dht_pin)
    print("Humidity: ", humidity)
    print("Temp.: ", temperature)
    time.sleep(1)  # Adjust the delay between readings as needed