function appendMessage(role, text) {
    const chatBox = document.getElementById("chat-box");
    const messageDiv = document.createElement("div");
    messageDiv.className = role === "user" ? "user-message" : "bot-message";
    messageDiv.innerText = text;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function sendMessage() {
    const inputField = document.getElementById("user-input");
    const message = inputField.value.trim();
    if (message === "") return;

    appendMessage("user", message);
    inputField.value = "";

    fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
    })
    .then(response => response.json())
    .then(data => {
        appendMessage("bot", data.response);
    })
    .catch(() => {
        appendMessage("bot", "Error occurred. Try again later.");
    });
}

// Enable Enter key to submit
document.addEventListener("DOMContentLoaded", function () {
    const inputField = document.getElementById("user-input");
    inputField.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            event.preventDefault(); // prevent page reload if in form
            sendMessage();          // call the same send function
        }
    });
});