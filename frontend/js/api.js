// js/api.js

const API_BASE_URL = "http://127.0.0.1:8000";

const API = {
    async request(endpoint, method = "GET", body = null) {
        const token = localStorage.getItem("emergency_token");

        const headers = {
            "Content-Type": "application/json"
        };

        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const options = {
            method,
            headers
        };

        if (body !== null) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(
            `${API_BASE_URL}${endpoint}`,
            options
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                data.message ||
                "Backend request failed."
            );
        }

        return data;
    }
};