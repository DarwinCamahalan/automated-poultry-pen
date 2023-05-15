// script.js

// Function to update the DHT11 temperature and humidity values
function updateDHT11Values() {
    // Send an AJAX request to the server to fetch the updated values
    fetch('/data')
        .then(response => response.json())
        .then(data => {
            // Update the temperature and humidity elements with the new values
            document.getElementById('dht-temperature').innerText = data.temperature + ' °C';
            document.getElementById('dht-humidity').innerText = data.humidity + ' %';
        });
}

// Update DHT11 values initially
updateDHT11Values();

// Update DHT11 values every 1 second
setInterval(updateDHT11Values, 1000);
