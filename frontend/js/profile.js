// js/profile.js
document.addEventListener("DOMContentLoaded", () => {
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

    // Load Data
    fields.forEach(f => {
        const saved = localStorage.getItem(`profile_${f}`);
        if(saved) {
            dispEls[f].textContent = saved;
            editEls[f].value = saved;
        } else {
            // Set initial edit input values from default HTML
            editEls[f].value = dispEls[f].textContent;
        }
    });

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

    // Logout
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            localStorage.removeItem("emergency_token");
            window.location.href = "login.html";
        });
    }
});