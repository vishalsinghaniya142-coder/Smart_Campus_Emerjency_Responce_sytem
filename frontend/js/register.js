document.addEventListener("DOMContentLoaded", () => {
    const registerForm = document.getElementById("register-form");

    if (!registerForm) {
        return;
    }

    registerForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const name = document.getElementById("name").value.trim();
        const email = document.getElementById("email").value.trim();
        const phone = document.getElementById("phone").value.trim();
        const password = document.getElementById("password").value;
        const submitButton = registerForm.querySelector("button[type='submit']");

        if (!phone) {
            alert("Phone number is required so emergency alerts can contact you.");
            return;
        }

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = "Creating account...";
        }

        try {
            const response = await API.post(
                "/auth/register",
                { name, email, password, phone_number: phone, role: "student" }
            );

            const data = response.data || response;
            const registeredEmail = data.user?.email || email;

            alert("Account created successfully. Please log in.");
            window.location.href = `login.html?email=${encodeURIComponent(registeredEmail)}`;
        } catch (error) {
            console.error("Registration failed:", error);
            alert(error.message || "Unable to create account. Please try again.");
        } finally {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = "Create Account";
            }
        }
    });
});