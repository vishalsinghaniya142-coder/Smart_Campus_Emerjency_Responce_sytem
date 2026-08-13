// js/login.js
document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("email").value;
            
            // Simulating API Call
            await API.request('/login', 'POST', { email });
            
            localStorage.setItem("emergency_token", "fake_jwt_token_123");
            localStorage.setItem("user_name", email.split('@')[0]);
            
            NotificationSystem.sendAlert("Welcome", "Login successful!");
            window.location.href = "dashboard.html";
        });
    }
});