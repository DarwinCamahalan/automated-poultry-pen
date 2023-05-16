import pyrebase
import Adafruit_DHT

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

# Define the GPIO pin connected to the DATA pin of the DHT11 sensor and the sensor type
dht_pin = 4
dht_type = Adafruit_DHT.DHT11

# Create a function to read the temperature and humidity from the sensor
def read_dht11_sensor():
    humidity, temperature = Adafruit_DHT.read_retry(dht_type, dht_pin)
    return humidity, temperature

# Write a loop to continuously read the sensor data, update the values in Firebase, and print them
while True:
    humidity, temperature = read_dht11_sensor()

    # Update the values in Firebase
    db.child("dht_sensor").update({"humidity": humidity, "temperature": temperature})

    # Print the values
    print("Humidity: {}%".format(humidity))
    print("Temperature: {}°C".format(temperature))
