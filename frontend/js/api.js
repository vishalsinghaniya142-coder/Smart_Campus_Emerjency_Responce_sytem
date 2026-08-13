// js/api.js
const API_BASE_URL = "http://localhost:3000/api"; // Future backend URL

const API = {
    async request(endpoint, method = "GET", body = null) {
        // Real implementation ke liye:
        /*
        const token = localStorage.getItem("emergency_token");
        const headers = { "Content-Type": "application/json", ...(token && { "Authorization": `Bearer ${token}` }) };
        const response = await fetch(`${API_BASE_URL}${endpoint}`, { method, headers, body: body ? JSON.stringify(body) : null });
        return response.json();
        */
        
        // Mock response for frontend testing
        console.log(`[API MOCK] ${method} request to ${endpoint}`, body || '');
        return { success: true, message: "Request processed successfully." };
    }
};