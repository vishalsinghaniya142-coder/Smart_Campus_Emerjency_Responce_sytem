// js/main.js
async function loadComponent(elementId, filePath) {
    const el = document.getElementById(elementId);
    if (!el) return;
    try {
        const response = await fetch(filePath);
        el.innerHTML = await response.text();
    } catch (error) {
        console.error(`Error loading ${filePath}:`, error);
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    await loadComponent("navbar-placeholder", "components/navbar.html");
    await loadComponent("sidebar-placeholder", "components/sidebar.html");
    await loadComponent("footer-placeholder", "components/footer.html");

    // Global SOS Button Logic
    const sosBtn = document.getElementById("sos-trigger");
    if (sosBtn) {
        sosBtn.addEventListener("click", () => NotificationSystem.triggerSOS());
    }

    // Mobile Sidebar Toggle (if toggle button exists in navbar)
    const toggleBtn = document.getElementById("sidebar-toggle");
    if (toggleBtn) {
        toggleBtn.addEventListener("click", () => {
            document.querySelector(".sidebar").classList.toggle("active");
        });
    }
});