document.addEventListener("DOMContentLoaded", () => {
    const handleAuth = (e) => {
        e.preventDefault();
        const email = document.getElementById("email") ? document.getElementById("email").value : "virat@example.com";
        localStorage.setItem("emergency_token", "fake_jwt_token_123");
        localStorage.setItem("profileEmail", email);
        window.location.href = "dashboard.html";
    };

    const handleSocialAuth = (provider) => {
        // Simulating the "Choose an account" popup
        const userEmail = prompt(`[${provider} Auth]\nPlease choose your account by entering your email:`, "virat@gmail.com");
        
        if(userEmail) {
            localStorage.setItem("emergency_token", `${provider}_oauth_token`);
            localStorage.setItem("profileName", userEmail.split('@')[0]);
            localStorage.setItem("profileEmail", userEmail);
            alert(`Successfully authenticated with ${provider}!`);
            window.location.href = "dashboard.html";
        }
    };

    const loginForm = document.getElementById("login-form");
    if (loginForm) loginForm.addEventListener("submit", handleAuth);

    const googleBtn = document.getElementById("google-login");
    if (googleBtn) googleBtn.addEventListener("click", () => handleSocialAuth("Google"));

    const githubBtn = document.getElementById("github-login");
    if (githubBtn) githubBtn.addEventListener("click", () => handleSocialAuth("GitHub"));
});