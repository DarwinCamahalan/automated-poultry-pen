from flask import Flask, render_template, jsonify
import Adafruit_DHT

app = Flask(__name__, static_url_path='/static')

def read_sensor():
    # Set sensor type: Options are DHT11, DHT22, or AM2302
    sensor = Adafruit_DHT.DHT11
    # Set GPIO sensor is connected to
    gpio = 4
    # Use read_retry method. This will retry up to 15 times to get a sensor reading (waiting 2 seconds between each retry).
    humidity, temperature = Adafruit_DHT.read_retry(sensor, gpio)
    # Return the temperature and humidity values
    return temperature, humidity

@app.route('/')
def index():
    # Read temperature and humidity from the DHT11 sensor
    temperature, humidity = read_sensor()
    # Render the template with temperature and humidity values
    return render_template('index.html', temperature=temperature, humidity=humidity)

@app.route('/data')
def get_data():
    # Read temperature and humidity from the DHT11 sensor
    temperature, humidity = read_sensor()
    # Return the temperature and humidity values as JSON data
    return jsonify({'temperature': temperature, 'humidity': humidity})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
