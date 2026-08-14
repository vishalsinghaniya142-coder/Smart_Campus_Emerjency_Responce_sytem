// // frontend/js/prediction.js
document.addEventListener("DOMContentLoaded", () => {
    const analyzeBtn = document.getElementById("analyze-btn");
    const locationInput = document.getElementById("location-input");
    const aiLoader = document.getElementById("ai-loader");
    const resultsContainer = document.getElementById("prediction-results");
    
    // Result Elements
    const locDisplay = document.getElementById("result-location");
    const aiConclusion = document.getElementById("ai-conclusion");
    
    const bars = {
        flood: { val: document.getElementById("flood-val"), bar: document.getElementById("flood-bar") },
        quake: { val: document.getElementById("quake-val"), bar: document.getElementById("quake-bar") },
        weather: { val: document.getElementById("weather-val"), bar: document.getElementById("weather-bar") }
    };

    if (analyzeBtn && locationInput) {
        // Backend ka wait karne ke liye function ko 'async' banana zaroori hai
        analyzeBtn.addEventListener("click", async () => {
            const loc = locationInput.value.trim();
            
            if (!loc) {
                alert("Please enter a valid City Name or Pincode!");
                locationInput.focus();
                return;
            }

            // 1. Start "AI Processing" UI
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
            resultsContainer.classList.add("hidden");
            aiLoader.classList.remove("hidden");

            // 2. Reset progress bars to 0
            Object.values(bars).forEach(b => {
                b.bar.style.width = '0%';
                b.val.textContent = '0%';
            });

            try {
                // 3. REAL BACKEND CALL (Fake random data hata diya gaya hai)
                // Ye api.js se API_BASE_URL (http://127.0.0.1:8000/prediction) ko request bhejega
                const data = await API.post("/prediction", { location: loc });

                // Backend se aaye hue result ko variables mein set karna
                const floodRisk = data.flood_risk || 0; 
                const quakeRisk = data.earthquake_prob || 0; 
                const weatherRisk = data.severe_weather || 0;

                // Stop Loader & Show Results
                aiLoader.classList.add("hidden");
                resultsContainer.classList.remove("hidden");
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = 'Analyze Risk';
                
                // Update text
                if (locDisplay) locDisplay.textContent = loc.toUpperCase();

                // Animate bars and set text
                setTimeout(() => {
                    bars.flood.bar.style.width = `${floodRisk}%`;
                    bars.flood.val.textContent = `${floodRisk}%`;
                    
                    bars.quake.bar.style.width = `${quakeRisk}%`;
                    bars.quake.val.textContent = `${quakeRisk}%`;
                    
                    bars.weather.bar.style.width = `${weatherRisk}%`;
                    bars.weather.val.textContent = `${weatherRisk}%`;

                    // Generate AI Conclusion based on highest risk
                    let highest = Math.max(floodRisk, quakeRisk, weatherRisk);
                    if (highest === weatherRisk && weatherRisk > 70) {
                        setConclusion("🔴 High risk of severe weather detected. Please secure loose objects and prepare for potential power outages.", "#fef2f2", "#ef4444", "#991b1b");
                    } else if (highest === floodRisk && floodRisk > 60) {
                        setConclusion("🟠 Moderate to High flood risk. Avoid low-lying areas and keep emergency kits ready.", "#fffbeb", "#f59e0b", "#92400e");
                    } else {
                        setConclusion("🟢 Overall environmental risks are currently manageable. Stay tuned for routine updates.", "#f0fdf4", "#22c55e", "#166534");
                    }
                }, 100); // Small delay to trigger CSS animation

            } catch (error) {
                // Agar backend band hai ya koi error aata hai
                console.error("Backend fetch error:", error);
                aiLoader.classList.add("hidden");
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = 'Analyze Risk';
                alert("Failed to fetch AI prediction from backend. Make sure the FastAPI server is running.");
            }
        });
    }

    function setConclusion(text, bg, border, textColor) {
        if(!aiConclusion) return;
        aiConclusion.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${text}`;
        aiConclusion.style.background = bg;
        aiConclusion.style.borderLeftColor = border;
        aiConclusion.style.color = textColor;
    }
});