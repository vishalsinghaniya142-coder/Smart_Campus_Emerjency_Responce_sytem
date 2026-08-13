// js/dashboard.js
document.addEventListener("DOMContentLoaded", () => {
    // 1. Fetch user name from LocalStorage
    const username = localStorage.getItem("profileName") || "Admin";
    document.getElementById("dash-username").textContent = username;

    // 2. Risk Level Logic (Change colors dynamically)
    const riskSelector = document.getElementById("risk-selector");
    const cardRisk = document.getElementById("card-risk");

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

    // 3. EMERGENCY SOS BUTTON LOGIC
    const sosBtn = document.getElementById("btn-sos");
    if (sosBtn) {
        sosBtn.addEventListener("click", () => {
            const confirmed = confirm("⚠️ ARE YOU SURE YOU WANT TO TRIGGER AN EMERGENCY SOS?\n\nThis will send your location to local authorities and nearby shelters.");
            
            if(confirmed) {
                // Change button state to "Transmitting"
                sosBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> TRANSMITTING...';
                
                // Simulate an API call / Geolocation fetch (Takes 1.5 seconds)
                setTimeout(() => {
                    // Success Alert
                    alert("🚨 SOS SIGNAL SENT SUCCESSFULLY!\n\n📍 Location: Lat 26.8467, Lng 80.9462 (Lucknow)\n🚓 Authorities have been notified and help is on the way.");
                    
                    // Update button UI permanently
                    sosBtn.innerHTML = '<i class="fas fa-check-circle"></i> SOS SENT';
                    sosBtn.style.background = "#16a34a"; // Turn green
                    sosBtn.style.animation = "none"; // Stop pulsing
                    
                    addActivity("🚨 EMERGENCY SOS TRIGGERED! Location broadcasted to authorities.");
                }, 1500);
            }
        });
    }

    // 4. Function to add items to the Live Activity Feed
    function addActivity(text) {
        const list = document.getElementById("activity-list");
        const li = document.createElement("li");
        const time = new Date().toLocaleTimeString();
        li.innerHTML = `<i class="fas fa-clock" style="color:#94a3b8;"></i> [${time}] ${text}`;
        
        // Add at the top of the list
        list.prepend(li);
    }
});