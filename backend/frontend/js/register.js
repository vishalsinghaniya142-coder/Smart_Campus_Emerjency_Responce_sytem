// js/register.js
document.addEventListener("DOMContentLoaded", () => {
    const registerForm = document.getElementById("register-form");
    
    if (registerForm) {
        registerForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const name = document.getElementById("name").value;
            const email = document.getElementById("email").value;
            
            localStorage.setItem("profileName", name);
            localStorage.setItem("profileEmail", email);
            localStorage.setItem("emergency_token", "registered_token");
            
            alert("Account created successfully!");
            window.location.href = "dashboard.html";
        });
    }

    // Social buttons modal trigger
    const authModal = document.getElementById("auth-modal");
    const modalIcon = document.getElementById("modal-provider-icon");

    document.getElementById("google-register")?.addEventListener("click", () => {
        modalIcon.className = 'fab fa-google';
        modalIcon.style.color = '#db4437';
        authModal.classList.remove("hidden");
    });

    document.getElementById("github-register")?.addEventListener("click", () => {
        modalIcon.className = 'fab fa-github';
        modalIcon.style.color = '#333';
        authModal.classList.remove("hidden");
    });
});

// Shared modal functions
function closeAuthModal() {
    document.getElementById("auth-modal").classList.add("hidden");
}

function selectAccount(email, name) {
    localStorage.setItem("emergency_token", "oauth_token_123");
    localStorage.setItem("profileEmail", email);
    localStorage.setItem("profileName", name);
    window.location.href = "dashboard.html";
}

function customAccountLogin() {
    const customEmail = prompt("Enter your email address:");
    if(customEmail && customEmail.includes('@')) {
        const name = customEmail.split('@')[0];
        selectAccount(customEmail, name);
    } else if (customEmail) {
        alert("Please enter a valid email!");
    }
}