// js/chatbot.js
document.addEventListener("DOMContentLoaded", () => {
    const input = document.querySelector("input[type='text']");
    const sendBtn = document.querySelector(".btn-primary");
    const chatWindow = document.querySelector(".chat-window");

    function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        // User message
        chatWindow.innerHTML += `<p style="background: var(--primary-color); color: white; padding: 10px; border-radius: 8px; width: fit-content; margin-bottom: 10px; margin-left: auto;">${text}</p>`;
        input.value = '';
        chatWindow.scrollTop = chatWindow.scrollHeight;

        // Bot reply simulation
        setTimeout(() => {
            chatWindow.innerHTML += `<p style="background: #e2e8f0; padding: 10px; border-radius: 8px; width: fit-content; margin-bottom: 10px;">I have noted that. Please stay safe. If it's a severe emergency, press the SOS button.</p>`;
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }, 1000);
    }

    if (sendBtn && input) {
        sendBtn.addEventListener("click", sendMessage);
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") sendMessage();
        });
    }
});