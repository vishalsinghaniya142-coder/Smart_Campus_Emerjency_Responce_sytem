// js/alerts.js


document.addEventListener("DOMContentLoaded", async () => {

    const alertsContainer =
        document.getElementById("alerts-container");


    if (!alertsContainer) {
        return;
    }


    // ============================================================
    // CHECK LOGIN
    // ============================================================

    const token =
        localStorage.getItem("emergency_token");


    if (!token) {

        alertsContainer.innerHTML = `
            <div style="
                background: #fee2e2;
                border-left: 5px solid #dc2626;
                padding: 1rem;
                border-radius: 4px;
            ">
                <h3 style="color: #991b1b;">
                    <i class="fas fa-lock"></i>
                    Login Required
                </h3>

                <p style="color: #7f1d1d;">
                    Please login to view live emergency alerts.
                </p>

                <button
                    class="btn btn-primary"
                    onclick="window.location.href='login.html'"
                >
                    Login
                </button>
            </div>
        `;

        return;
    }


    // ============================================================
    // LOAD ALERTS FROM MEMBER 2 BACKEND
    // GET /alerts
    // ============================================================

    try {

        const response =
            await API.request(
                "/alerts",
                "GET"
            );


        console.log(
            "Alerts API response:",
            response
        );


        // --------------------------------------------------------
        // Handle possible backend response structures
        // --------------------------------------------------------

        let alerts = [];


        if (Array.isArray(response)) {

            alerts = response;

        } else if (Array.isArray(response.data)) {

            alerts = response.data;

        } else if (
            response.data &&
            Array.isArray(response.data.alerts)
        ) {

            alerts = response.data.alerts;

        } else if (Array.isArray(response.alerts)) {

            alerts = response.alerts;

        }


        // --------------------------------------------------------
        // No alerts
        // --------------------------------------------------------

        if (alerts.length === 0) {

            alertsContainer.innerHTML = `
                <div style="
                    background: #dcfce7;
                    border-left: 5px solid #16a34a;
                    padding: 1rem;
                    border-radius: 4px;
                ">
                    <h3 style="color: #166534;">
                        <i class="fas fa-check-circle"></i>
                        No Active Alerts
                    </h3>

                    <p style="color: #166534;">
                        There are currently no active emergency alerts.
                    </p>
                </div>
            `;

            return;
        }


        // --------------------------------------------------------
        // Display alerts
        // --------------------------------------------------------

        alertsContainer.innerHTML = "";


        alerts.forEach((alert) => {

            const alertElement =
                createAlertElement(alert);


            alertsContainer.appendChild(
                alertElement
            );

        });


    } catch (error) {

        console.error(
            "Alerts loading error:",
            error
        );


        alertsContainer.innerHTML = `
            <div style="
                background: #fee2e2;
                border-left: 5px solid #dc2626;
                padding: 1rem;
                border-radius: 4px;
            ">

                <h3 style="color: #991b1b;">
                    <i class="fas fa-exclamation-circle"></i>
                    Unable to Load Alerts
                </h3>

                <p style="color: #7f1d1d;">
                    ${escapeHtml(
                        error.message ||
                        "Could not connect to the emergency alert service."
                    )}
                </p>

                <button
                    class="btn btn-primary"
                    onclick="loadAlertsAgain()"
                >
                    Try Again
                </button>

            </div>
        `;

    }

});


// ============================================================
// CREATE ALERT CARD
// ============================================================

function createAlertElement(alert) {

    const wrapper =
        document.createElement("div");


    // ------------------------------------------------------------
    // Get alert values
    // ------------------------------------------------------------

    const severity =
        String(
            alert.severity ||
            alert.level ||
            alert.alert_level ||
            "moderate"
        ).toLowerCase();


    const title =
        alert.title ||
        alert.name ||
        "Emergency Alert";


    const message =
        alert.message ||
        alert.description ||
        alert.details ||
        "Please stay alert and follow emergency instructions.";


    const location =
        alert.location ||
        "";


    // ------------------------------------------------------------
    // Severity styling
    // ------------------------------------------------------------

    let background = "#fef3c7";
    let borderColor = "#f59e0b";
    let titleColor = "#b45309";
    let textColor = "#92400e";
    let icon = "fa-exclamation-triangle";


    if (
        severity === "critical" ||
        severity === "severe" ||
        severity === "high" ||
        severity === "red"
    ) {

        background = "#fee2e2";
        borderColor = "#dc2626";
        titleColor = "#991b1b";
        textColor = "#7f1d1d";
        icon = "fa-exclamation-circle";

    } else if (
        severity === "low" ||
        severity === "safe" ||
        severity === "green"
    ) {

        background = "#dcfce7";
        borderColor = "#16a34a";
        titleColor = "#166534";
        textColor = "#166534";
        icon = "fa-check-circle";

    }


    // ------------------------------------------------------------
    // Create HTML
    // ------------------------------------------------------------

    wrapper.innerHTML = `
        <div
            style="
                background: ${background};
                border-left: 5px solid ${borderColor};
                padding: 1rem;
                margin-bottom: 1rem;
                border-radius: 4px;
            "
        >

            <h3 style="color: ${titleColor};">
                <i class="fas ${icon}"></i>
                ${escapeHtml(title)}
            </h3>

            <p style="color: ${textColor};">
                ${escapeHtml(message)}
            </p>

            ${
                location
                    ? `
                    <p style="
                        color: ${textColor};
                        margin-top: 8px;
                        font-size: 0.9rem;
                    ">
                        <i class="fas fa-location-dot"></i>
                        ${escapeHtml(location)}
                    </p>
                    `
                    : ""
            }

        </div>
    `;


    return wrapper;
}


// ============================================================
// TRY AGAIN
// ============================================================

function loadAlertsAgain() {

    window.location.reload();

}


// ============================================================
// SAFE HTML
// ============================================================

function escapeHtml(value) {

    const div =
        document.createElement("div");

    div.textContent =
        String(value ?? "");

    return div.innerHTML;

}