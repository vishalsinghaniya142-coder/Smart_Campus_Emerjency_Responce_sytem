// js/chatbot.js
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("chat-input");
    const sendBtn = document.getElementById("chat-send");
    const chatWindow = document.querySelector(".chat-messages");

    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        const userMessage = document.createElement("p");
        userMessage.className = "user-message";
        userMessage.textContent = text;
        chatWindow.appendChild(userMessage);
        input.value = '';
        chatWindow.scrollTop = chatWindow.scrollHeight;
        sendBtn.disabled = true;

        try {
            const response = await API.post("/chatbot", { message: text });
            const data = response.data || response;
            const botMessage = document.createElement("div");
            botMessage.className = "bot-response";
            botMessage.innerHTML = `<strong>${data.emergency_type || "Safety guidance"} · ${data.severity || "medium"}</strong><p>${escapeHtml(data.message || "Please stay calm and follow these steps.")}</p><ul>${(data.instructions || []).map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
            chatWindow.appendChild(botMessage);
        } catch (error) {
            const errorMessage = document.createElement("p");
            errorMessage.className = "bot-message error-message";
            errorMessage.textContent = error.message || "Safety assistant is temporarily unavailable. Use SOS for immediate danger.";
            chatWindow.appendChild(errorMessage);
        } finally {
            sendBtn.disabled = false;
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
    }

    function escapeHtml(value) {
        const element = document.createElement("div");
        element.textContent = String(value ?? "");
        return element.innerHTML;
    }

    if (sendBtn && input) {
        sendBtn.addEventListener("click", sendMessage);
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") sendMessage();
        });
    }
});