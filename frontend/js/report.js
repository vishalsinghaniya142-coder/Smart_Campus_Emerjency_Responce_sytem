// js/report.js

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("incident-report-form");

    if (!form) return;

    const getCurrentLocation = () => new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error("Geolocation is not supported by this browser."));
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                });
            },
            () => {
                reject(new Error("Location permission is required to send an emergency report."));
            },
            {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 0,
            }
        );
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const submitBtn = document.getElementById("submit-report-btn");

        const incidentType =
            document.getElementById("incident-type").value;

        const title =
            document.getElementById("incident-title").value.trim();

        const description =
            document.getElementById("incident-description").value.trim();

        const severity =
            document.getElementById("incident-severity").value;

        const token =
            localStorage.getItem("emergency_token");

        if (!token) {
            alert("Please login first.");
            window.location.href = "login.html";
            return;
        }

        if (!title || !description) {
            alert("Please fill the title and description.");
            return;
        }

        try {
            submitBtn.disabled = true;
            submitBtn.textContent = "Getting location...";

            const coordinates = await getCurrentLocation();

            submitBtn.textContent = "Submitting...";

            const payload = {
                incident_type: incidentType,
                title: title,
                description: description,
                location: {
                    latitude: coordinates.latitude,
                    longitude: coordinates.longitude,
                    address: "Auto-detected from browser GPS",
                    building: "",
                    floor: "",
                    room: ""
                },
                severity: severity,
                images: []
            };

            const response = await API.post("/incidents", payload);

            console.log(
                "Incident created:",
                response
            );

            alert(
                `Emergency report submitted successfully. You earned ${response.data?.credits_awarded ?? 0} safety credits.`
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