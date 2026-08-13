// js/login.js

// --- 1. Normal Login Form Handling ---
document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const email =
                document.getElementById("email").value.trim();

            const password =
                document.getElementById("password").value;

            const btn =
                loginForm.querySelector(
                    "button[type='submit']"
                );

            try {
                btn.disabled = true;
                btn.innerHTML =
                    '<i class="fas fa-spinner fa-spin"></i> Logging in...';

                // Real FastAPI backend call
                const response = await API.request(
                    "/auth/login",
                    "POST",
                    {
                        email: email,
                        password: password
                    }
                );

                // Backend response se token nikalo
                const data = response.data || response;

                const token =
                    data.access_token ||
                    data.token;

                if (!token) {
                    throw new Error(
                        "Login successful but access token was not received."
                    );
                }

                // Save authentication data
                localStorage.setItem(
                    "emergency_token",
                    token
                );

                if (data.user) {
                    localStorage.setItem(
                        "profileEmail",
                        data.user.email || email
                    );

                    localStorage.setItem(
                        "profileName",
                        data.user.name ||
                        email.split("@")[0]
                    );

                    if (data.user.role) {
                        localStorage.setItem(
                            "userRole",
                            data.user.role
                        );
                    }
                } else {
                    localStorage.setItem(
                        "profileEmail",
                        email
                    );

                    localStorage.setItem(
                        "profileName",
                        email.split("@")[0]
                    );
                }

                window.location.href =
                    "dashboard.html";

            } catch (error) {
                console.error(
                    "Login failed:",
                    error
                );

                alert(
                    error.message ||
                    "Login failed. Please check your email and password."
                );

                btn.disabled = false;
                btn.innerHTML = "Login";
            }
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
// --- Use Another Account Logic ---
function customAccountLogin() {
    const customEmail = prompt("Enter the email address you want to use:");
    if(customEmail && customEmail.includes('@')) {
        const name = customEmail.split('@')[0];
        selectAccount(customEmail, name); // Call existing select function
    } else if (customEmail) {
        alert("Please enter a valid email!");
    }
}

// --- Phone Login Logic ---
document.getElementById("phone-login")?.addEventListener("click", () => {
    document.getElementById("phone-modal").classList.remove("hidden");
});

function sendOTP() {
    const phone = document.getElementById("phone-input").value;
    if(phone.length < 10) {
        alert("Please enter a valid phone number!");
        return;
    }
    
    // OTP Simulation
    const otp = prompt(`An OTP has been sent to ${phone}.\nPlease enter the 4-digit OTP (hint: type 1234):`);
    
    if(otp === "1234") {
        localStorage.setItem("emergency_token", "phone_auth_token");
        localStorage.setItem("profileEmail", phone);
        localStorage.setItem("profileName", "Phone User");
        
        alert("Phone verification successful!");
        window.location.href = "dashboard.html";
    } else {
        alert("Invalid OTP! Try again.");
    }
}

