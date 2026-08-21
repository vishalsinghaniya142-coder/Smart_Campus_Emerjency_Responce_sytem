// js/profile.js
document.addEventListener("DOMContentLoaded", async () => {
    const editBtn = document.getElementById("edit-profile-btn");
    const logoutBtn = document.getElementById("logout-btn");
    const fileInput = document.getElementById("profile-upload");
    const imgPreview = document.getElementById("profile-img-preview");

    // Element references
    const fields = ['name', 'email', 'username', 'role', 'branch', 'hostel', 'phone', 'address', 'bio'];
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
            username: localStorage.getItem("profile_username") || `@${(user?.email || "").split("@")[0]}`,
            role: user?.role || localStorage.getItem("profile_role") || dispEls.role.textContent,
            branch: localStorage.getItem("profile_branch") || dispEls.branch.textContent,
            hostel: localStorage.getItem("profile_hostel") || dispEls.hostel.textContent,
            phone: localStorage.getItem("profile_phone") || dispEls.phone.textContent,
            address: localStorage.getItem("profile_address") || dispEls.address.textContent,
            bio: localStorage.getItem("profile_bio") || dispEls.bio.textContent
        };

        fields.forEach((field) => {
            const value = values[field] || "Not set";
            dispEls[field].textContent = value;
            editEls[field].value = value;
        });

        localStorage.setItem("profileName", values.name);
        localStorage.setItem("profileEmail", values.email);
    }

    await loadProfile();

    if(localStorage.getItem("profilePic")) {
        imgPreview.src = localStorage.getItem("profilePic");
    }

    // Toggle Edit Mode
    if (editBtn) {
        editBtn.addEventListener("click", () => {
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
                fields.forEach(f => {
                    const val = editEls[f].value.trim();
                    dispEls[f].textContent = val;
                    localStorage.setItem(`profile_${f}`, val);
                });

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