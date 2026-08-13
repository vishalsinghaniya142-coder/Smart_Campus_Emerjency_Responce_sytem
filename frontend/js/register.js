// js/register.js
document.addEventListener("DOMContentLoaded", () => {
    const registerForm = document.getElementById("register-form");
    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const name = document.getElementById("name").value;
            const email = document.getElementById("email").value;
            
            await API.request('/register', 'POST', { name, email });
            
            alert("Registration successful! Please login.");
            window.location.href = "login.html";
        });
    }
});