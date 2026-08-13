// js/profile.js
document.addEventListener("DOMContentLoaded", () => {
    const logoutBtn = document.querySelector(".btn-danger");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            Auth.logout();
        });
    }
});