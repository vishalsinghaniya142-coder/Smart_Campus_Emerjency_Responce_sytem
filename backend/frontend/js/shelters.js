// js/shelters.js
document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll(".btn-primary");
    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            alert("Opening directions in Google Maps...");
            window.open("https://maps.google.com/?q=shelter", "_blank");
        });
    });
});