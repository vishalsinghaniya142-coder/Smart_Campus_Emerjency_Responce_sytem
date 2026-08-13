// js/auth.js
const Auth = {
    isAuthenticated() {
        return localStorage.getItem("emergency_token") !== null;
    },
    logout() {
        localStorage.removeItem("emergency_token");
        localStorage.removeItem("user_name");
        window.location.href = "login.html";
    },
    checkProtected() {
        if (!this.isAuthenticated() && !window.location.pathname.includes("login.html") && !window.location.pathname.includes("register.html") && !window.location.pathname.includes("index.html")) {
            window.location.href = "login.html";
        }
    }
};

// Uncomment below line to strictly enforce login
// Auth.checkProtected();