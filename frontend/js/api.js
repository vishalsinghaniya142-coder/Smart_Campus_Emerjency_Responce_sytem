const API_BASE_URL = "http://127.0.0.1:8001";

const API = {

    async request(endpoint, options = {}) {

        const token = localStorage.getItem("emergency_token");

        const headers = {
            ...(options.headers || {})
        };

        if (!(options.body instanceof FormData)) {
            headers["Content-Type"] = "application/json";
        }

        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        try {

            const response = await fetch(
                `${API_BASE_URL}${endpoint}`,
                {
                    ...options,
                    headers
                }
            );

            const text = await response.text();

            let data = {};

            try {
                data = text ? JSON.parse(text) : {};
            } catch {
                data = {
                    detail: text || "Invalid server response."
                };
            }

            if (!response.ok) {

                const message =
                    data?.detail ||
                    data?.message ||
                    "Something went wrong.";

                throw new Error(message);
            }

            return data;

        } catch (error) {

            console.error("API Error:", error);

            throw error;
        }
    },


    async get(endpoint) {

        return this.request(endpoint, {
            method: "GET"
        });
    },


    async post(endpoint, data) {

        return this.request(endpoint, {
            method: "POST",
            body:
                data instanceof FormData
                    ? data
                    : JSON.stringify(data)
        });
    },


    async put(endpoint, data) {

        return this.request(endpoint, {
            method: "PUT",
            body: JSON.stringify(data)
        });
    },


    async patch(endpoint, data) {

        return this.request(endpoint, {
            method: "PATCH",
            body: JSON.stringify(data)
        });
    },


    async delete(endpoint) {

        return this.request(endpoint, {
            method: "DELETE"
        });
    },


    clearSession() {

        localStorage.removeItem("emergency_token");
        localStorage.removeItem("profile_branch");
        localStorage.removeItem("profile_hostel");
        localStorage.removeItem("profileName");
        localStorage.removeItem("profileEmail");
        localStorage.removeItem("profilePhoto");
        localStorage.removeItem("profileProvider");
        localStorage.removeItem("support_reference");
    }
};


window.API = API;