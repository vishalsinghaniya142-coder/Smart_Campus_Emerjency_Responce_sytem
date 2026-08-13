// js/profile.js
document.addEventListener("DOMContentLoaded", () => {
    const editBtn = document.getElementById("edit-profile-btn");
    const logoutBtn = document.getElementById("logout-btn");
    const fileInput = document.getElementById("profile-upload");
    const imgPreview = document.getElementById("profile-img-preview");
    
    const displayName = document.getElementById("display-name");
    const displayEmail = document.getElementById("display-email");
    const editName = document.getElementById("edit-name");
    const editEmail = document.getElementById("edit-email");

    let isEditing = false;

    // 1. Page load hone par saved data dikhana
    if(localStorage.getItem("profileName")) {
        displayName.textContent = localStorage.getItem("profileName");
        editName.value = localStorage.getItem("profileName");
    }
    if(localStorage.getItem("profileEmail")) {
        displayEmail.textContent = localStorage.getItem("profileEmail");
        editEmail.value = localStorage.getItem("profileEmail");
    }
    if(localStorage.getItem("profilePic")) {
        imgPreview.src = localStorage.getItem("profilePic");
    }

    // 2. Profile Edit karne ka Logic
    if (editBtn) {
        editBtn.addEventListener("click", () => {
            isEditing = !isEditing;
            
            if(isEditing) {
                // Edit Mode on karna
                displayName.classList.add("hidden");
                displayEmail.classList.add("hidden");
                editName.classList.remove("hidden");
                editEmail.classList.remove("hidden");
                
                editBtn.textContent = "Save Changes";
                editBtn.classList.replace("btn-outline", "btn-primary");
            } else {
                // Save Mode - naya data save karna
                const newName = editName.value.trim();
                const newEmail = editEmail.value.trim();
                
                // UI update karna
                displayName.textContent = newName;
                displayEmail.textContent = newEmail;
                
                // Naya data localStorage me save karna
                localStorage.setItem("profileName", newName);
                localStorage.setItem("profileEmail", newEmail);

                // Wapas Display Mode me aana
                displayName.classList.remove("hidden");
                displayEmail.classList.remove("hidden");
                editName.classList.add("hidden");
                editEmail.classList.add("hidden");
                
                editBtn.textContent = "Edit Profile";
                editBtn.classList.replace("btn-primary", "btn-outline");
            }
        });
    }

    // 3. Profile Picture Upload karne ka Logic
    if (fileInput) {
        fileInput.addEventListener("change", function() {
            const file = this.files[0];
            if(file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const base64Image = e.target.result;
                    imgPreview.src = base64Image;
                    localStorage.setItem("profilePic", base64Image); // Browser me image save karna
                }
                reader.readAsDataURL(file);
            }
        });
    }

    // 4. Logout karne ka Logic
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            // Authentication token remove karna
            localStorage.removeItem("emergency_token");
            
            // Login page par redirect karna
            window.location.href = "login.html";
        });
    }
});