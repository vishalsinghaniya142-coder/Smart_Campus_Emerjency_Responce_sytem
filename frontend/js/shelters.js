document.addEventListener("DOMContentLoaded", async () => {
    const grid = document.getElementById("shelter-grid");
    const status = document.getElementById("shelters-list-status");
    const latitude = 26.8467;
    const longitude = 80.9462;

    const addForm = document.getElementById("add-shelter-form");
    const addStatus = document.getElementById("add-shelter-status");
    const setLocation = (location) => {
        document.getElementById("shelter-latitude").value = location.lat;
        document.getElementById("shelter-longitude").value = location.lng;
        addStatus.textContent = "Current location added to the form.";
    };

    document.getElementById("use-current-location")?.addEventListener("click", () => {
        addStatus.textContent = "Requesting your current location...";
        LocationService.getUserLocation()
            .then(setLocation)
            .catch(() => {
                addStatus.textContent = "Location permission was unavailable. Enter coordinates manually.";
            });
    });

    addForm?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const submitButton = addForm.querySelector("button[type='submit']");
        submitButton.disabled = true;
        addStatus.textContent = "Saving shelter to Firebase...";

        try {
            await API.request("/shelters", "POST", {
                name: document.getElementById("shelter-name").value.trim(),
                description: "Added from the SafeGuard shelter directory.",
                shelter_type: "shelter",
                status: document.getElementById("shelter-status").value,
                location: {
                    latitude: Number(document.getElementById("shelter-latitude").value),
                    longitude: Number(document.getElementById("shelter-longitude").value),
                    address: document.getElementById("shelter-address").value.trim() || null
                },
                capacity: {
                    total: Number(document.getElementById("shelter-capacity").value),
                    occupied: 0,
                    available: Number(document.getElementById("shelter-capacity").value)
                },
                amenities: {}
            });
            addStatus.textContent = "Shelter saved. Refreshing the Firebase directory...";
            window.location.reload();
        } catch (error) {
            addStatus.textContent = error.message || "Unable to save shelter.";
            submitButton.disabled = false;
        }
    });

    try {
        const response = await API.request(
            `/shelters/nearest?latitude=${latitude}&longitude=${longitude}&limit=20`
        );
        const shelters = response.data || [];

        if (!shelters.length) {
            grid.innerHTML = "<p>No shelters are currently available.</p>";
            status.textContent = "No shelters found";
            return;
        }

        grid.innerHTML = shelters.map((shelter) => {
            const destination = `${shelter.latitude},${shelter.longitude}`;
            return `
                <article class="shelter-card">
                    <h3>${escapeHtml(shelter.name)}</h3>
                    <p><strong>Distance:</strong> ${shelter.distance_km ?? "-"} km</p>
                    <p><strong>Capacity:</strong> ${escapeHtml(shelter.capacity || "Unavailable")}</p>
                    <p class="shelter-status"><strong>Status:</strong> ${escapeHtml(shelter.availability || "Unknown")}</p>
                    ${shelter.address ? `<p><strong>Address:</strong> ${escapeHtml(shelter.address)}</p>` : ""}
                    ${shelter.description ? `<p class="shelter-description">${escapeHtml(shelter.description)}</p>` : ""}
                    <button class="btn btn-primary directions-btn" type="button" data-destination="${destination}">Get Directions</button>
                </article>`;
        }).join("");

        status.textContent = `${shelters.length} shelter${shelters.length === 1 ? "" : "s"} found`;
        grid.querySelectorAll(".directions-btn").forEach((button) => {
            button.addEventListener("click", () => {
                window.open(`https://www.google.com/maps/dir/?api=1&destination=${button.dataset.destination}`, "_blank", "noopener");
            });
        });
    } catch (error) {
        status.textContent = "Unable to load shelters";
        grid.innerHTML = `<p class="shelter-error">${escapeHtml(error.message || "Shelter service unavailable.")}</p>`;
    }
});

function escapeHtml(value) {
    const element = document.createElement("div");
    element.textContent = value;
    return element.innerHTML;
}