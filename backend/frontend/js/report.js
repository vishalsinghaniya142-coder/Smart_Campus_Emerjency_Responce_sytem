// js/report.js
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            alert("Emergency report submitted successfully. Authorities have been notified.");
            form.reset();
        });
    }
});