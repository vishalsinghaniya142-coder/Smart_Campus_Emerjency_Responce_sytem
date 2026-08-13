// js/login.js
document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");
    
    // Normal Email/Password Login
    if (loginForm) {
        loginForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const email = document.getElementById("email").value;
            
            // Set session data
            localStorage.setItem("emergency_token", "fake_jwt_token_123");
            localStorage.setItem("profileEmail", email);
            
            alert("Login successful!");
            window.location.href = "dashboard.html";
        });
    }

    // Google Login Logic
    const googleBtn = document.getElementById("google-login");
    if (googleBtn) {
        googleBtn.addEventListener("click", () => {
            // Simulate Google Auth
            localStorage.setItem("emergency_token", "google_oauth_token");
            localStorage.setItem("profileName", "Google User");
            localStorage.setItem("profileEmail", "user@gmail.com");
            
            alert("Signed in with Google successfully!");
            window.location.href = "dashboard.html";
        });
    }

    // GitHub Login Logic
    const githubBtn = document.getElementById("github-login");
    if (githubBtn) {
        githubBtn.addEventListener("click", () => {
            // Simulate GitHub Auth
            localStorage.setItem("emergency_token", "github_oauth_token");
            localStorage.setItem("profileName", "GitHub Developer");
            localStorage.setItem("profileEmail", "dev@github.com");
            
            alert("Signed in with GitHub successfully!");
            window.location.href = "dashboard.html";
        });
    }
});