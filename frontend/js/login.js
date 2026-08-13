// js/login.js

// --- 1. Normal Login Form Handling ---
document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");
    
    if (loginForm) {
        loginForm.addEventListener("submit", (e) => {
            e.preventDefault(); // Ye page refresh hone se rokega!
            
            const email = document.getElementById("email").value;
            
            // Saving data
            localStorage.setItem("emergency_token", "normal_login_token");
            localStorage.setItem("profileEmail", email);
            localStorage.setItem("profileName", email.split('@')[0]);
            
            // Success Effect
            const btn = loginForm.querySelector("button[type='submit']");
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
            
            setTimeout(() => {
                window.location.href = "dashboard.html";
            }, 800);
        });
    }

    // --- 2. Open Social Login Modal ---
    let currentProvider = '';
    const authModal = document.getElementById("auth-modal");
    const modalIcon = document.getElementById("modal-provider-icon");

    document.getElementById("google-login")?.addEventListener("click", () => {
        currentProvider = 'Google';
        modalIcon.className = 'fab fa-google';
        modalIcon.style.color = '#db4437';
        authModal.classList.remove("hidden");
    });

    document.getElementById("github-login")?.addEventListener("click", () => {
        currentProvider = 'GitHub';
        modalIcon.className = 'fab fa-github';
        modalIcon.style.color = '#333';
        authModal.classList.remove("hidden");
    });

    // --- 3. Forgot Password Modal Logic ---
    const forgotModal = document.getElementById("forgot-modal");
    
    document.getElementById("forgot-pwd-link")?.addEventListener("click", (e) => {
        e.preventDefault();
        forgotModal.classList.remove("hidden");
    });
});

// --- Modal Global Functions ---

function closeAuthModal() {
    document.getElementById("auth-modal").classList.add("hidden");
}

function closeForgotModal() {
    document.getElementById("forgot-modal").classList.add("hidden");
}

// Jab user official-looking account select karega:
function selectAccount(email, name) {
    localStorage.setItem("emergency_token", "oauth_token_123");
    localStorage.setItem("profileEmail", email);
    localStorage.setItem("profileName", name);
    
    // UI feedback
    document.getElementById("modal-title").innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    setTimeout(() => {
        window.location.href = "dashboard.html";
    }, 1000);
}

// Reset password bhejne ki script
function sendResetLink() {
    const email = document.getElementById("reset-email").value;
    if(!email) {
        alert("Please enter a valid email address!");
        return;
    }
    
    alert(`Password reset link has been successfully sent to ${email}`);
    closeForgotModal();
}