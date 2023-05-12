from flask import Flask, render_template, jsonify, Response
import Adafruit_DHT
import cv2
import threading
import time

# Initialize the DHT11 sensor
sensor = Adafruit_DHT.DHT11
pin = 4

# Initialize the output frame and a lock used to ensure thread-safe exchanges of the output frames
outputFrame = None
lock = threading.Lock()

# Initialize a flask object
app = Flask(__name__)

# Define a route for the home page
@app.route("/")
def home():
    return render_template("index.html")

# Define a route to fetch the DHT11 sensor data
@app.route("/sensor-data")
def sensor_data():
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    data = {
        "temperature": temperature,
        "humidity": humidity
    }
    return jsonify(data)

def pull_images():
    global outputFrame
    while True:
        # Capture image from the MLX90640 camera
        # Replace this code with the relevant code from the PiThermalCam library
        current_frame = capture_image()

        # Apply any necessary image processing or analysis
        processed_image = process_image(current_frame)

        # Set the outputFrame with the processed image
        # Make sure the outputFrame is a valid image frame (e.g., a numpy array)
        outputFrame = processed_image.copy()

        # Acquire the lock, set the output frame, and release the lock
        with lock:
            outputFrame = processed_image.copy()

def generate():
    global outputFrame, lock
    while True:
        with lock:
            if outputFrame is None:
                continue
            flag, encodedImage = cv2.imencode(".jpg", outputFrame)
            if not flag:
                continue
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

# Define a route for the video feed from the MLX90640 camera
@app.route("/video-feed")
def video_feed():
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

# Start the threads for capturing images from the MLX90640 camera and fetching DHT11 sensor data
t = threading.Thread(target=pull_images)
t.daemon = True
t.start()

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
