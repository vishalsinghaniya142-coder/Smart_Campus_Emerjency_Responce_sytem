// js/dashboard.js
document.addEventListener("DOMContentLoaded", () => {
    const userName = localStorage.getItem("user_name") || "User";
    const nameEl = document.getElementById("user-name");
    if (nameEl) nameEl.textContent = userName;
});