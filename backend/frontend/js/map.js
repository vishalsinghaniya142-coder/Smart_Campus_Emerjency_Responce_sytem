// js/map.js
document.addEventListener("DOMContentLoaded", () => {
    const mapEl = document.getElementById("emergency-map");
    if (!mapEl) return;

    // Default to New Delhi if location fails
    const defaultCoords = [28.6139, 77.2090]; 
    const map = L.map('emergency-map').setView(defaultCoords, 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Try to get user's real location
    LocationService.getUserLocation().then(loc => {
        const userCoords = [loc.lat, loc.lng];
        map.setView(userCoords, 14);
        
        // User Marker
        L.marker(userCoords).addTo(map)
            .bindPopup('<b>You are here</b>').openPopup();
            
        // Mock a nearby shelter
        L.circle([loc.lat + 0.01, loc.lng + 0.01], {
            color: 'green',
            fillColor: '#0f0',
            fillOpacity: 0.5,
            radius: 300
        }).addTo(map).bindPopup('Safe Zone / Shelter');
        
    }).catch(err => {
        console.warn("Using default map location.");
    });
});