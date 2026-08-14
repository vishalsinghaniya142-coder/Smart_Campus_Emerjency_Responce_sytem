// frontend/js/login.js

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");

    // 1. Regular Email/Password Login with FastAPI Backend
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;

            try {
                // FastAPI backend ke /auth/login endpoint par request bhej raha hai
                const result = await API.post("/auth/login", { email, password });
                
                if (result.access_token) {
                    localStorage.setItem("emergency_token", result.access_token);
                    localStorage.setItem("profileEmail", email);
                    localStorage.setItem("profileName", email.split('@')[0]);
                    
                    alert("Login successful!");
                    window.location.href = "dashboard.html";
                } else {
                    alert(result.detail || "Invalid credentials!");
                }
            } catch (err) {
                console.error(err);
                alert("Server connection failed! Make sure FastAPI backend is running on port 8000.");
            }
        });
    }

    // 2. Social Login Modal Triggers (Google / GitHub)
    const authModal = document.getElementById("auth-modal");
    const modalIcon = document.getElementById("modal-provider-icon");
    const modalTitle = document.getElementById("modal-title");

    document.getElementById("google-login")?.addEventListener("click", () => {
        if(modalIcon) {
            modalIcon.className = 'fab fa-google';
            modalIcon.style.color = '#db4437';
        }
        if(modalTitle) modalTitle.textContent = "Sign in with Google";
        authModal?.classList.remove("hidden");
    });

    document.getElementById("github-login")?.addEventListener("click", () => {
        if(modalIcon) {
            modalIcon.className = 'fab fa-github';
            modalIcon.style.color = '#333';
        }
        if(modalTitle) modalTitle.textContent = "Sign in with GitHub";
        authModal?.classList.remove("hidden");
    });

    // 3. Phone Login Modal Trigger
    document.getElementById("phone-login")?.addEventListener("click", () => {
        document.getElementById("phone-modal")?.classList.remove("hidden");
    });
});

// --- Modal Helper Functions ---

function closeAuthModal() {
    document.getElementById("auth-modal")?.classList.add("hidden");
}

function selectAccount(email, name) {
    localStorage.setItem("emergency_token", "oauth_mock_token_123");
    localStorage.setItem("profileEmail", email);
    localStorage.setItem("profileName", name);
    window.location.href = "dashboard.html";
}

function customAccountLogin() {
    const customEmail = prompt("Enter the email address you want to use:");
    if(customEmail && customEmail.includes('@')) {
        const name = customEmail.split('@')[0];
        selectAccount(customEmail, name);
    } else if (customEmail) {
        alert("Please enter a valid email!");
    }
}

// --- Phone OTP Simulation Logic ---
function sendOTP() {
    const phone = document.getElementById("phone-input")?.value;
    if(!phone || phone.length < 10) {
        alert("Please enter a valid phone number!");
        return;
    }
    
    const otp = prompt(`An OTP has been sent to ${phone}.\nPlease enter the 4-digit OTP (hint: type 1234):`);
    
    if(otp === "1234") {
        localStorage.setItem("emergency_token", "phone_auth_token");
        localStorage.setItem("profileEmail", phone + "@phone.auth");
        localStorage.setItem("profileName", "Phone User");
        
        alert("Phone verification successful!");
        window.location.href = "dashboard.html";
    } else {
        alert("Invalid OTP! Try again.");
    }
}