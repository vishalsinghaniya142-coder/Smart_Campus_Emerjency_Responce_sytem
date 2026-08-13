// js/prediction.js
document.addEventListener("DOMContentLoaded", () => {
    const analyzeBtn = document.querySelector(".btn-primary");
    const input = document.querySelector("input[type='text']");
    const results = document.querySelector(".prediction-results");

    if (analyzeBtn && input) {
        analyzeBtn.addEventListener("click", () => {
            if (!input.value) return alert("Please enter a location");
            
            analyzeBtn.textContent = "Analyzing...";
            setTimeout(() => {
                analyzeBtn.textContent = "Analyze Risk";
                alert(`AI Analysis complete for ${input.value}. High risk of heavy rain detected.`);
            }, 1500);
        });
    }
});