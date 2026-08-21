// js/main.js
async function loadComponent(elementId, filePath) {
    const el = document.getElementById(elementId);
    if (!el) return;
    try {
        const response = await fetch(`${filePath}?v=3`);
        el.innerHTML = await response.text();
    } catch (error) {
        console.error(`Error loading ${filePath}:`, error);
    }
}

function addSupportLinks() {
    if (document.querySelector(".floating-support")) return;

    const support = document.createElement("div");
    support.className = "floating-support";
    support.innerHTML = `
        <a class="support-chat" href="chatbot.html" aria-label="Open AI safety assistant" title="AI safety assistant">
            <i class="fas fa-comment-dots" aria-hidden="true"></i>
        </a>
        <a class="support-whatsapp" href="#" aria-label="WhatsApp support placeholder" title="WhatsApp support (coming soon)">
            <i class="fab fa-whatsapp" aria-hidden="true"></i>
        </a>`;
    document.body.appendChild(support);
}

function addAmbientElements() {
    if (document.querySelector(".ambient-elements")) return;

    const ambient = document.createElement("div");
    ambient.className = "ambient-elements";
    ambient.setAttribute("aria-hidden", "true");
    ambient.innerHTML = '<span class="ambient-fire"></span><span class="ambient-water"></span>';
    document.body.prepend(ambient);
}

document.addEventListener("DOMContentLoaded", async () => {
    addAmbientElements();
    addSupportLinks();
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