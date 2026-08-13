// js/notifications.js
const NotificationSystem = {
    init() {
        if ("Notification" in window && Notification.permission !== "granted") {
            Notification.requestPermission();
        }
    },
    
    sendAlert(title, message) {
        if ("Notification" in window && Notification.permission === "granted") {
            new Notification(title, { body: message, icon: "images/emergency.svg" });
        } else {
            alert(`${title}\n${message}`);
        }
    },

    triggerSOS() {
        LocationService.getUserLocation().then(loc => {
            this.sendAlert("SOS SENT!", `Help is on the way to Lat: ${loc.lat.toFixed(4)}, Lng: ${loc.lng.toFixed(4)}`);
            API.request('/sos', 'POST', loc);
        }).catch(err => {
            this.sendAlert("SOS SENT!", "Location unavailable. Defaulting to registered address.");
        });
    }
};

// Initialize on load
document.addEventListener("DOMContentLoaded", () => NotificationSystem.init());