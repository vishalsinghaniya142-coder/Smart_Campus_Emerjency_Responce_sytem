// frontend/js/api.js
const API_BASE_URL = "http://127.0.0.1:8000"; // FastAPI Backend URL

const API = {
    async post(endpoint, data) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("emergency_token") || ""}`
                },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error("API POST Error:", error);
            throw error;
        }
    },

    async get(endpoint) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${localStorage.getItem("emergency_token") || ""}`
                }
            });
            return await response.json();
        } catch (error) {
            console.error("API GET Error:", error);
            throw error;
        }
    }
};