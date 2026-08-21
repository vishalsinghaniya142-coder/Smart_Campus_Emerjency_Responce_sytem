document.addEventListener("DOMContentLoaded", () => {
    const mapEl = document.getElementById("emergency-map");
    if (!mapEl) return;

    const defaultCoords = [28.6139, 77.2090];
    const map = L.map("emergency-map").setView(defaultCoords, 12);
    const statusEl = document.getElementById("map-status");
    const userLayer = L.layerGroup().addTo(map);
    const shelterLayer = L.layerGroup().addTo(map);

    const fallbackShelters = [
        {
            id: "central-school-camp",
            name: "Central School Camp",
            latitude: 28.6239,
            longitude: 77.219,
            capacity: "150 / 500",
            availability: "Available"
        },
        {
            id: "city-community-center",
            name: "City Community Center",
            latitude: 28.6049,
            longitude: 77.198,
            capacity: "480 / 500",
            availability: "Almost full"
        }
    ];

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    function setStatus(message) {
        if (statusEl) statusEl.textContent = message;
    }

    function directionsUrl(latitude, longitude) {
        return `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}`;
    }

    function renderShelters(shelters, center) {
        shelterLayer.clearLayers();

        shelters.forEach((shelter) => {
            const latitude = Number(shelter.latitude ?? shelter.lat);
            const longitude = Number(shelter.longitude ?? shelter.lng);
            if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return;

            const popup = `
                <div class="map-popup">
                    <strong>${shelter.name || "Emergency shelter"}</strong>
                    <span>${shelter.capacity || "Capacity information unavailable"}</span>
                    <span class="popup-availability">${shelter.availability || "Open"}</span>
                    <a href="${directionsUrl(latitude, longitude)}" target="_blank" rel="noopener">Get directions</a>
                </div>`;

            L.marker([latitude, longitude])
                .addTo(shelterLayer)
                .bindPopup(popup);
        });

        if (center && shelters.length) {
            const points = shelters
                .map((shelter) => [Number(shelter.latitude ?? shelter.lat), Number(shelter.longitude ?? shelter.lng)])
                .filter(([latitude, longitude]) => Number.isFinite(latitude) && Number.isFinite(longitude));
            if (points.length) map.fitBounds(L.latLngBounds([center, ...points]), { padding: [40, 40] });
        }
    }

    async function loadShelters(center) {
        try {
            const query = center ? `?latitude=${center[0]}&longitude=${center[1]}&limit=10` : "";
            const response = await API.request(`/shelters/nearest${query}`);
            const shelters = response.data || [];
            renderShelters(shelters.length ? shelters : fallbackShelters, center);
            setStatus(`${shelters.length || fallbackShelters.length} safe zones available`);
        } catch (error) {
            renderShelters(fallbackShelters, center);
            setStatus("Showing nearby safe zones from the local emergency directory");
            console.warn("Shelter service unavailable; using local directory.", error);
        }
    }

    function showUserLocation(loc) {
        const userCoords = [loc.lat, loc.lng];
        userLayer.clearLayers();
        L.circleMarker(userCoords, {
            radius: 9,
            color: "#ffffff",
            weight: 3,
            fillColor: "#2563eb",
            fillOpacity: 1
        }).addTo(userLayer).bindPopup("<strong>Your current location</strong>").openPopup();
        map.setView(userCoords, 14);
        loadShelters(userCoords);
    }

    function locateUser() {
        setStatus("Requesting your location...");
        LocationService.getUserLocation()
            .then(showUserLocation)
            .catch(() => {
                setStatus("Location unavailable; showing the default campus area");
                loadShelters(defaultCoords);
            });
    }

    document.getElementById("locate-me")?.addEventListener("click", locateUser);
    document.getElementById("reset-map")?.addEventListener("click", () => {
        userLayer.clearLayers();
        map.setView(defaultCoords, 12);
        loadShelters(defaultCoords);
    });

    loadShelters(defaultCoords);
    locateUser();
});