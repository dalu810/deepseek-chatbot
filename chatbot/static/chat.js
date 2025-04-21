const ws = new WebSocket("ws://localhost:8000/chat");

ws.onopen = () => console.log("Connected to WebSocket");
ws.onerror = (error) => console.log("WebSocket Error:", error);
ws.onclose = () => console.log("WebSocket Closed");

function sendMessage() {
    const input = document.getElementById("message");
    const text = input.value.trim();
    
    if (text) {
        displayMessage(text, "user");
        ws.send(text);
        input.value = "";
    }
}

ws.onmessage = (event) => {
    const message = event.data.trim();

    if (message === "[END]") {
        // Optionally hide loading spinner or do nothing
        return;
    }

    displayMessage(message, "ai");
};

function displayMessage(text, sender) {
    const chatBox = document.getElementById("chat-box");
    const messageDiv = document.createElement("div");

    messageDiv.classList.add("message", sender);
    messageDiv.innerText = sender === "ai" ? "AI: " + text : "You: " + text;
    
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function handleKey(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
}