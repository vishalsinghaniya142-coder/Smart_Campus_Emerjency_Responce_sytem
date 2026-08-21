// js/report.js

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("incident-report-form");

    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const submitBtn = document.getElementById("submit-report-btn");

        const incidentType =
            document.getElementById("incident-type").value;

        const title =
            document.getElementById("incident-title").value.trim();

        const locationText =
            document.getElementById("incident-location").value.trim();

        const description =
            document.getElementById("incident-description").value.trim();

        const severity =
            document.getElementById("incident-severity").value;

        const token =
            localStorage.getItem("emergency_token");

        // Login check
        if (!token) {
            alert("Please login first.");
            window.location.href = "login.html";
            return;
        }

        if (!title || !locationText || !description) {
            alert("Please fill all required fields.");
            return;
        }

        try {
            submitBtn.disabled = true;
            submitBtn.textContent = "Submitting...";

            /*
             * Backend currently expects latitude/longitude.
             * For now we use campus coordinates.
             * Later we can connect browser GPS/maps here.
             */
            const payload = {
                incident_type: incidentType,

                title: title,

                description: description,

                location: {
                    latitude: 26.8467,
                    longitude: 80.9462,
                    address: locationText,
                    building: "",
                    floor: "",
                    room: ""
                },

                severity: severity,

                images: []
            };

            const response = await API.request(
                "/incidents",
                "POST",
                payload
            );

            console.log(
                "Incident created:",
                response
            );

            alert(
                "Emergency report submitted successfully. Authorities have been notified."
            );

            form.reset();

        } catch (error) {

            console.error(
                "Incident submission failed:",
                error
            );

            alert(
                error.message ||
                "Failed to submit emergency report."
            );

        } finally {

            submitBtn.disabled = false;
            submitBtn.textContent = "Submit Report";

        }
    });
});