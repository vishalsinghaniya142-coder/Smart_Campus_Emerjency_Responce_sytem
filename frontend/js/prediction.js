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
                alert("Please enter a location!");
                return;
            }

            // Loader dikhayein aur purane results chupayein
            if (aiLoader) aiLoader.classList.remove("hidden");
            if (resultsContainer) resultsContainer.classList.add("hidden");

            try {
                // FastAPI backend ke prediction endpoint ko call karna
                const data = await API.post("/predictions/analyze", { location });

                if (aiLoader) aiLoader.classList.add("hidden");
                if (resultsContainer) resultsContainer.classList.remove("hidden");

                if (locDisplay) locDisplay.textContent = location.toUpperCase();

                // Backend se aaye risk percentages ko UI bars mein set karna
                if (floodBar && floodVal) {
                    floodBar.style.width = `${data.flood_risk || 0}%`;
                    floodVal.textContent = `${data.flood_risk || 0}%`;
                }

                if (quakeBar && quakeVal) {
                    quakeBar.style.width = `${data.earthquake_prob || 0}%`;
                    quakeVal.textContent = `${data.earthquake_prob || 0}%`;
                }

                if (weatherBar && weatherVal) {
                    weatherBar.style.width = `${data.severe_weather || 0}%`;
                    weatherVal.textContent = `${data.severe_weather || 0}%`;
                }

            } catch (err) {
                if (aiLoader) aiLoader.classList.add("hidden");
                console.error(err);
                alert("Failed to fetch AI prediction from backend. Make sure the server is running.");
            }
        });
    }
});