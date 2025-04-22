const statusEl = document.getElementById('status');
const retryBtn = document.getElementById('retry');
let lastSentTime = 0;

function sendLocation(lat, lon) {
  fetch('/location', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ latitude: lat, longitude: lon })
  })
  .then(response => response.text())
  .then(data => {
    statusEl.textContent = `Sent: Latitude ${lat}, Longitude ${lon}`;
    console.log(data);
  })
  .catch(err => {
    statusEl.textContent = "Error sending location.";
    console.error(err);
  });
}

function startLocationUpdates() {
  navigator.geolocation.watchPosition(
    position => {
      const lat = position.coords.latitude;
      const lon = position.coords.longitude;
      const now = Date.now();

      if (now - lastSentTime >= 1000) {
        lastSentTime = now;
        sendLocation(lat, lon);
      }
    },
    error => {
      if (error.code === error.PERMISSION_DENIED) {
        statusEl.textContent = "Location permission denied.";
        retryBtn.style.display = "inline-block";
      } else {
        statusEl.textContent = "Location error.";
      }
    },
    {
      enableHighAccuracy: true,
      maximumAge: 0,
      timeout: 10000
    }
  );
}

retryBtn.addEventListener('click', () => {
  statusEl.textContent = "Retrying location access...";
  retryBtn.style.display = "none";
  startLocationUpdates();
});

window.onload = startLocationUpdates;
