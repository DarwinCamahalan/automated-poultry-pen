// Function to fetch updated temperature and humidity values
function fetchSensorData() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/sensor-data", true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var data = JSON.parse(xhr.responseText);
            // Update temperature and humidity values on the webpage
            document.getElementById("temperature").textContent = data.temperature;
            document.getElementById("humidity").textContent = data.humidity;
        }
    };
    xhr.send();
}

// Fetch sensor data every 1 second
setInterval(fetchSensorData, 1000);
