// frontend/js/prediction.js

document.addEventListener("DOMContentLoaded", () => {
    const analyzeBtn = document.getElementById("analyze-btn");
    const locationInput = document.getElementById("location-input");
    const aiLoader = document.getElementById("ai-loader");
    const resultsContainer = document.getElementById("results-container");
    const locDisplay = document.getElementById("location-display");
    
    const floodBar = document.getElementById("flood-bar");
    const floodVal = document.getElementById("flood-val");
    const quakeBar = document.getElementById("quake-bar");
    const quakeVal = document.getElementById("quake-val");
    const weatherBar = document.getElementById("weather-bar");
    const weatherVal = document.getElementById("weather-val");

    if (analyzeBtn) {
        analyzeBtn.addEventListener("click", async () => {
            const location = locationInput?.value.trim();
            if (!location) {
                alert("Please enter a six-digit Indian pincode.");
                return;
            }

            if (!/^\d{6}$/.test(location)) {
                alert("Please enter a valid six-digit Indian pincode.");
                return;
            }

            // Loader dikhayein aur purane results chupayein
            if (aiLoader) aiLoader.classList.remove("hidden");
            if (resultsContainer) resultsContainer.classList.add("hidden");

            try {
                // FastAPI backend ke prediction endpoint ko call karna
                const data = await API.post("/prediction/analyze", { location });

                if (aiLoader) aiLoader.classList.add("hidden");
                if (resultsContainer) resultsContainer.classList.remove("hidden");

                const prediction = data.prediction || {};
                const weather = data.weather || {};
                const risks = data.risks || {};
                const floodRisk = Number(risks.flood_risk);
                const earthquakeProbability = Number(
                    risks.earthquake_probability
                );
                const severeWeatherRisk = Number(risks.severe_weather_risk);

                if (locDisplay) {
                    locDisplay.textContent = (
                        data.location?.display_name || location
                    ).toUpperCase();
                }

                // Backend se aaye risk percentages ko UI bars mein set karna
                if (floodBar && floodVal) {
                    floodBar.style.width = `${floodRisk}%`;
                    floodVal.textContent = `${floodRisk}%`;
                }

                if (quakeBar && quakeVal) {
                    quakeBar.style.width = `${earthquakeProbability}%`;
                    quakeVal.textContent = `${earthquakeProbability}%`;
                }

                if (weatherBar && weatherVal) {
                    weatherBar.style.width = `${severeWeatherRisk}%`;
                    weatherVal.textContent = `${severeWeatherRisk}%`;
                }

                const conclusion = document.getElementById("ai-conclusion");
                if (conclusion) {
                    conclusion.textContent = [
                        `AI severity: ${prediction.severity || "unknown"}.`,
                        `AI score: ${prediction.risk_score ?? "unavailable"}.`,
                        `Earthquakes in 500 km feed: ${data.earthquake?.recent_event_count ?? "unavailable"}.`,
                        `Live temperature: ${weather.temperature_c ?? "unavailable"} C.`,
                        `Precipitation: ${weather.precipitation_mm ?? "unavailable"} mm.`,
                        `Wind: ${weather.wind_speed_kmh ?? "unavailable"} km/h.`,
                        `Factors: ${(prediction.factors || []).join(", ") || "none"}.`
                    ].join(" ");
                }

            } catch (err) {
                if (aiLoader) aiLoader.classList.add("hidden");
                console.error(err);
                if (resultsContainer) resultsContainer.classList.remove("hidden");
                const conclusion = document.getElementById("ai-conclusion");
                if (conclusion) {
                    conclusion.className = "ai-alert error";
                    conclusion.textContent = `Prediction is temporarily unavailable. ${err.message || "Please try again shortly."}`;
                }
            }
        });
    }
});