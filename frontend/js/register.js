// js/report.js

document.addEventListener("DOMContentLoaded", () => {

    const form = document.querySelector("form");

    if (!form) {
        return;
    }


    form.addEventListener("submit", async (e) => {

        e.preventDefault();


        // ========================================================
        // GET FORM DATA
        // ========================================================

        const incidentType =
            document.getElementById("incident-type").value.trim();

        const location =
            document.getElementById("incident-location").value.trim();

        const description =
            document.getElementById("incident-description").value.trim();


        // ========================================================
        // BASIC VALIDATION
        // ========================================================

        if (!incidentType) {
            alert("Please select the type of emergency.");
            return;
        }

        if (!location) {
            alert("Please enter the emergency location.");
            return;
        }

        if (!description) {
            alert("Please enter a description of the emergency.");
            return;
        }


        // ========================================================
        // AUTHENTICATION CHECK
        // ========================================================

        const token =
            localStorage.getItem("emergency_token");

        if (!token) {

            alert("Please login first to submit an emergency report.");

            window.location.href = "login.html";

            return;
        }


        // ========================================================
        // SUBMIT BUTTON
        // ========================================================

        const submitBtn =
            form.querySelector("button[type='submit']");


        try {

            if (submitBtn) {

                submitBtn.disabled = true;

                submitBtn.innerHTML =
                    '<i class="fas fa-spinner fa-spin"></i> Submitting...';

            }


            // ====================================================
            // MEMBER 2 FASTAPI BACKEND
            // POST /incidents
            // ====================================================

            const response =
                await API.request(
                    "/incidents",
                    "POST",
                    {
                        incident_type: incidentType,
                        title: incidentType,
                        description: description,
                        location: location
                    }
                );


            console.log(
                "Incident report response:",
                response
            );


            // ====================================================
            // SUCCESS
            // ====================================================

            alert(
                "Emergency report submitted successfully. Authorities have been notified."
            );


            form.reset();


        } catch (error) {

            console.error(
                "Incident report error:",
                error
            );


            alert(
                error.message ||
                "Unable to submit emergency report. Please try again."
            );


        } finally {

            if (submitBtn) {

                submitBtn.disabled = false;

                submitBtn.innerHTML =
                    "Submit Report";

            }

        }

    });

});