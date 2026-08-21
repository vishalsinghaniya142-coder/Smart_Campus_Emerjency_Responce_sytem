// js/dashboard.js
document.addEventListener("DOMContentLoaded", async () => {
    const defaultLocation = { latitude: 26.8467, longitude: 80.9462 };
    const addActivity = (text) => {
        const list = document.getElementById("activity-list");
        if (!list) return;
        const loading = document.getElementById("activity-loading");
        if (loading) loading.remove();
        const li = document.createElement("li");
        li.innerHTML = `<i class="fas fa-clock" style="color:#94a3b8;"></i> ${escapeHtml(text)}`;
        list.prepend(li);
    };

    async function loadDashboardData() {
        let location = defaultLocation;
        try {
            const current = await LocationService.getUserLocation();
            location = { latitude: current.lat, longitude: current.lng };
        } catch (_) {
            addActivity("Using the default campus location for shelter search.");
        }

        const results = await Promise.allSettled([
            API.request("/users/profile"),
            API.request(`/shelters/nearest?latitude=${location.latitude}&longitude=${location.longitude}&limit=1`),
            API.request("/alerts?active_only=true&limit=100"),
            API.request("/notifications?limit=20")
        ]);

        const [profileResult, shelterResult, alertsResult, notificationsResult] = results;
        if (profileResult.status === "fulfilled") {
            const profile = profileResult.value.data || profileResult.value;
            document.getElementById("dash-username").textContent = profile.name || "User";
        } else {
            document.getElementById("dash-username").textContent = localStorage.getItem("profileName") || "User";
        }

        if (shelterResult.status === "fulfilled") {
            const shelters = shelterResult.value.data || [];
            const nearest = shelters[0];
            document.getElementById("shelter-text").textContent = nearest
                ? `${nearest.name} (${nearest.distance_km} km)`
                : "No shelter found";
        } else {
            document.getElementById("shelter-text").textContent = "Unavailable";
        }

        if (alertsResult.status === "fulfilled") {
            const payload = alertsResult.value.data;
            const alerts = Array.isArray(payload) ? payload : (payload?.alerts || []);
            document.getElementById("alerts-text").textContent = `${alerts.length} Active`;
        } else {
            document.getElementById("alerts-text").textContent = "Unavailable";
        }

        if (notificationsResult.status === "fulfilled") {
            const notifications = notificationsResult.value.data || [];
            const latestSos = notifications.find(notification => notification.type === "sos");
            if (latestSos) {
                addActivity(`🚨 ${latestSos.title}: ${latestSos.message}`);
            }
        }

        addActivity("Dashboard data synchronized from the backend.");
    }

    await loadDashboardData();

    const smsSettingsForm = document.getElementById("sms-settings-form");
    const smsSettingsStatus = document.getElementById("sms-settings-status");
    const smsFields = {
        server: document.getElementById("sms-server"),
        username: document.getElementById("sms-username"),
        password: document.getElementById("sms-password"),
        deviceId: document.getElementById("sms-device-id")
    };

    if (smsFields.server) smsFields.server.value = "backend/.env";
    if (smsFields.username) smsFields.username.value = "configured on server";
    if (smsFields.password) smsFields.password.value = "";
    if (smsFields.deviceId) smsFields.deviceId.value = "configured on server";

    smsSettingsForm?.addEventListener("submit", (event) => {
        event.preventDefault();
        smsSettingsStatus.textContent = "Actual SMS delivery is configured in backend/.env on the server. Browser storage is not used for SMS credentials.";
        addActivity("SMS gateway settings remain server-controlled.");
    });

    // 2. Risk Level Logic (Change colors dynamically)
    const riskSelector = document.getElementById("risk-selector");
    const cardRisk = document.getElementById("card-risk");
    const imageInput = document.getElementById("risk-image");
    const analyzeImageButton = document.getElementById("analyze-image-btn");
    const imageResult = document.getElementById("image-risk-result");

    const updateRiskColor = (level) => {
        riskSelector.style.color = "white";
        if(level === "low") {
            riskSelector.style.background = "#16a34a"; // Green
            cardRisk.style.borderLeftColor = "#16a34a";
        } else if(level === "moderate") {
            riskSelector.style.background = "#f59e0b"; // Yellow
            cardRisk.style.borderLeftColor = "#f59e0b";
        } else if(level === "high") {
            riskSelector.style.background = "#ea580c"; // Orange
            cardRisk.style.borderLeftColor = "#ea580c";
        } else if(level === "severe") {
            riskSelector.style.background = "#dc2626"; // Red
            cardRisk.style.borderLeftColor = "#dc2626";
        }
    };

    // Initialize default color on load
    updateRiskColor(riskSelector.value);

    // Update color and activity log when user changes dropdown
    riskSelector.addEventListener("change", (e) => {
        updateRiskColor(e.target.value);
        addActivity(`Risk level manually updated to ${e.target.value.toUpperCase()}`);
    });

    analyzeImageButton?.addEventListener("click", async () => {
        const file = imageInput?.files?.[0];
        if (!file) {
            imageResult.textContent = "Choose a JPG, PNG, or WEBP image first.";
            return;
        }

        const formData = new FormData();
        formData.append("file", file);
        analyzeImageButton.disabled = true;
        imageResult.textContent = "Analyzing uploaded image...";

        try {
            const response = await API.request("/image-analysis", {
                method: "POST",
                body: formData
            });
            const data = response.data || response;
            const level = data.risk_level || "moderate";
            riskSelector.value = level;
            updateRiskColor(level);
            imageResult.textContent = `${level.toUpperCase()} risk (${Math.round((data.confidence || 0) * 100)}% baseline confidence): ${data.reason}`;
            addActivity(`Image baseline analysis set risk to ${level.toUpperCase()}.`);
        } catch (error) {
            imageResult.textContent = error.message || "Image analysis failed.";
        } finally {
            analyzeImageButton.disabled = false;
        }
    });

    // 3. EMERGENCY SOS BUTTON LOGIC
    const sosBtn = document.getElementById("btn-sos");
    if (sosBtn) {
        function showWhatsAppAction(latitude, longitude) {
            let recipient = localStorage.getItem("emergency_whatsapp_recipient") || "";
            if (!recipient) {
                recipient = prompt("Enter the emergency member's WhatsApp number with country code:", "+91");
                if (recipient) {
                    recipient = recipient.replace(/\D/g, "");
                    if (recipient.length < 10) recipient = "";
                    if (recipient) localStorage.setItem("emergency_whatsapp_recipient", recipient);
                }
            }

            if (!recipient) return;

            const message = [
                "EMERGENCY SOS from Suraksha_Setu",
                "Please respond immediately.",
                `Location: https://www.google.com/maps?q=${latitude},${longitude}`
            ].join("\n");
            const action = document.createElement("a");
            action.href = `https://wa.me/${recipient}?text=${encodeURIComponent(message)}`;
            action.target = "_blank";
            action.rel = "noopener noreferrer";
            action.className = "whatsapp-sos-action";
            action.innerHTML = '<i class="fab fa-whatsapp"></i><span>Send SOS on WhatsApp</span>';
            document.querySelector(".whatsapp-sos-action")?.remove();
            document.body.appendChild(action);
        }

        sosBtn.addEventListener("click", () => {
            const confirmed = confirm("⚠️ ARE YOU SURE YOU WANT TO TRIGGER AN EMERGENCY SOS?\n\nThis will send your location to local authorities and nearby shelters.");
            
            if(confirmed) {
                // Change button state to "Transmitting"
                sosBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> TRANSMITTING...';
                
                // Simulate an API call / Geolocation fetch (Takes 1.5 seconds)
                // Get user's current location and send SOS to backend
if (!navigator.geolocation) {
    alert("Geolocation is not supported by your browser.");
    sosBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> EMERGENCY SOS';
    return;
}

navigator.geolocation.getCurrentPosition(
    async (position) => {

        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        try {
            const response = await API.post(
                "/sos",
                {
                    location: {
                        latitude: latitude,
                        longitude: longitude
                    },
                    message: "Emergency SOS"
                }
            );

            console.log("SOS response:", response);

            alert(
                "🚨 SOS SIGNAL SENT SUCCESSFULLY!\n\n" +
                "📍 Your current location has been sent to the emergency system."
            );

            showWhatsAppAction(latitude, longitude);

            sosBtn.innerHTML =
                '<i class="fas fa-check-circle"></i> SOS SENT';

            sosBtn.style.background = "#16a34a";
            sosBtn.style.animation = "none";

            addActivity(
                "🚨 EMERGENCY SOS TRIGGERED! Current location sent to emergency system."
            );

        } catch (error) {

            console.error("SOS error:", error);

            alert(
                error.message ||
                "Unable to send SOS. Please try again."
            );

            sosBtn.innerHTML =
                '<i class="fas fa-exclamation-triangle"></i> EMERGENCY SOS';

        }
    },

    (error) => {

        console.error(
            "Location error:",
            error
        );

        alert(
            "Unable to get your location. Please allow location access and try again."
        );

        sosBtn.innerHTML =
            '<i class="fas fa-exclamation-triangle"></i> EMERGENCY SOS';
    }
);
            }
        });
    }

    function escapeHtml(value) {
        const element = document.createElement("div");
        element.textContent = String(value ?? "");
        return element.innerHTML;
    }
});