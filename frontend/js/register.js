// js/register.js
document.addEventListener("DOMContentLoaded", () => {
    const registerForm = document.getElementById("register-form");
    
    // Normal Registration
    if (registerForm) {
        registerForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const name = document.getElementById("name").value;
            const email = document.getElementById("email").value;
            
            // Set session data
            localStorage.setItem("profileName", name);
            localStorage.setItem("profileEmail", email);
            
            alert("Registration successful! Please login.");
            window.location.href = "login.html";
        });
    }

    // Social Registration common function
    const handleSocialAuth = (provider) => {
        localStorage.setItem("emergency_token", `${provider}_oauth_token`);
        localStorage.setItem("profileName", `New ${provider} User`);
        
        alert(`Account created and linked with ${provider}!`);
        window.location.href = "dashboard.html";
    };

    // Google Auth
    const googleRegBtn = document.getElementById("google-register");
    if (googleRegBtn) {
        googleRegBtn.addEventListener("click", () => handleSocialAuth("Google"));
    }

    // GitHub Auth
    const githubRegBtn = document.getElementById("github-register");
    if (githubRegBtn) {
        githubRegBtn.addEventListener("click", () => handleSocialAuth("GitHub"));
    }
});