// js/profile.js
document.addEventListener("DOMContentLoaded", async () => {
    const editBtn = document.getElementById("edit-profile-btn");
    const logoutBtn = document.getElementById("logout-btn");
    const fileInput = document.getElementById("profile-upload");
    const imgPreview = document.getElementById("profile-img-preview");

    // Element references
    const fields = ['name', 'email', 'username', 'role', 'phone', 'address', 'bio'];
    const supportReference = document.getElementById("disp-support-reference");
    const creditsValue = document.getElementById("credits-value");
    const creditsBar = document.getElementById("credits-bar");
    const creditsMessage = document.getElementById("credits-message");
    const currentLevel = document.getElementById("current-level");
    const levelProgressMessage = document.getElementById("level-progress-message");
    const dispEls = {};
    const editEls = {};

    fields.forEach(f => {
        dispEls[f] = document.getElementById(`disp-${f}`);
        editEls[f] = document.getElementById(`edit-${f}`);
    });

    const displaySection = document.getElementById("display-section");
    const editSection = document.getElementById("edit-section");
    let isEditing = false;

    async function loadProfile() {
        const token = localStorage.getItem("emergency_token");
        let user = null;

        if (token && typeof API !== "undefined") {
            try {
                const response = await API.request("/users/profile");
                user = response.data || response.user || response;
            } catch (error) {
                console.warn("Could not load the authenticated profile.", error);
            }
        }

        const values = {
            name: user?.name || localStorage.getItem("profileName") || dispEls.name.textContent,
            email: user?.email || localStorage.getItem("profileEmail") || dispEls.email.textContent,
            username: localStorage.getItem("profile_username") || `@${(user?.email || localStorage.getItem("profileEmail") || dispEls.email.textContent || "user").split("@")[0]}`,
            role: user?.role || localStorage.getItem("profile_role") || dispEls.role.textContent,
            phone: localStorage.getItem("profile_phone") || dispEls.phone.textContent,
            address: localStorage.getItem("profile_address") || dispEls.address.textContent,
            bio: localStorage.getItem("profile_bio") || dispEls.bio.textContent
        };

        fields.forEach((field) => {
            const value = values[field] || "Not set";
            dispEls[field].textContent = value;
            editEls[field].value = value;
        });

        const credits = Math.max(0, Number(user?.credits ?? localStorage.getItem("profile_credits") ?? 0));
        localStorage.setItem("profile_credits", String(credits));
        if (creditsValue) creditsValue.textContent = credits;
        if (creditsBar) creditsBar.style.width = `${Math.min(100, credits)}%`;
        if (creditsMessage) creditsMessage.innerHTML = `<i class="fas fa-trophy"></i> ${credits ? `You have earned ${credits} safety credits through verified reports.` : "Submit a verified emergency report to earn 100 credits."}`;
        const level = credits >= 1500 ? "Gold" : credits >= 500 ? "Silver" : "Bronze";
        if (currentLevel) {
            currentLevel.textContent = level;
            currentLevel.className = `level-badge ${level.toLowerCase()}-badge`;
        }
        if (levelProgressMessage) levelProgressMessage.textContent = level === "Gold"
            ? "Gold level unlocked. Keep helping your campus community."
            : `${level === "Bronze" ? 500 - credits : 1500 - credits} credits to the next level.`;

        localStorage.setItem("profileName", values.name);
        localStorage.setItem("profileEmail", values.email);
    }

    await loadProfile();
    if (supportReference) {
        let reference = localStorage.getItem("support_reference");
        if (!reference) {
            reference = `SS-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
            localStorage.setItem("support_reference", reference);
        }
        supportReference.textContent = reference;
    }

    if(localStorage.getItem("profilePic")) {
        imgPreview.src = localStorage.getItem("profilePic");
    }

    // Toggle Edit Mode
    if (editBtn) {
        editBtn.addEventListener("click", async () => {
            isEditing = !isEditing;
            
            if(isEditing) {
                dispEls.name.classList.add("hidden");
                dispEls.email.classList.add("hidden");
                editEls.name.classList.remove("hidden");
                editEls.email.classList.remove("hidden");
                
                displaySection.classList.add("hidden");
                editSection.classList.remove("hidden");
                
                editBtn.innerHTML = '<i class="fas fa-save"></i> Save Changes';
                editBtn.classList.replace("btn-outline", "btn-primary");
            } else {
                // Save Data
                const updatedValues = {};
                fields.forEach(f => {
                    const val = editEls[f].value.trim();
                    dispEls[f].textContent = val;
                    localStorage.setItem(`profile_${f}`, val);
                    updatedValues[f] = val;
                });

                if (localStorage.getItem("emergency_token") && typeof API !== "undefined") {
                    try {
                        await API.patch("/users/profile", {
                            name: updatedValues.name,
                            email: updatedValues.email,
                            phone_number: updatedValues.phone
                        });
                        localStorage.setItem("profileName", updatedValues.name);
                        localStorage.setItem("profileEmail", updatedValues.email);
                    } catch (error) {
                        console.warn("Profile saved locally, but server sync failed.", error);
                    }
                }

                dispEls.name.classList.remove("hidden");
                dispEls.email.classList.remove("hidden");
                editEls.name.classList.add("hidden");
                editEls.email.classList.add("hidden");
                
                displaySection.classList.remove("hidden");
                editSection.classList.add("hidden");
                
                editBtn.innerHTML = '<i class="fas fa-edit"></i> Edit Profile';
                editBtn.classList.replace("btn-primary", "btn-outline");
            }
        });
    }

    // Upload Image
    if (fileInput) {
        fileInput.addEventListener("change", function() {
            const file = this.files[0];
            if(file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const base64Image = e.target.result;
                    imgPreview.src = base64Image;
                    localStorage.setItem("profilePic", base64Image);
                }
                reader.readAsDataURL(file);
            }
        });
    }
    // Remove Profile Picture Logic
    const removePicBtn = document.getElementById("remove-pic-btn");
    if(removePicBtn) {
        removePicBtn.addEventListener("click", () => {
            localStorage.removeItem("profilePic"); // Local storage se delete karega
            imgPreview.src = "images/logo.svg"; // Default logo wapas set karega
        });
    }


    // Logout
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            localStorage.removeItem("emergency_token");
            window.location.href = "login.html";
        });
    }
});