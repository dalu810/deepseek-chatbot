document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const processingIndicator = document.getElementById('processing-indicator');
    
    // State management
    let socket;
    const pendingQuestions = new Map(); // Tracks sent questions
    let isProcessing = false;

    // Initialize WebSocket connection
    function connectWebSocket() {
        socket = new WebSocket(`ws://${window.location.host}/ws`);

        socket.onopen = () => {
            console.log('WebSocket connected');
            appendMessage('system', 'Connected to server');
            processQueue();
        };

        socket.onmessage = (event) => {
            try {
                const { answer, source, question } = JSON.parse(event.data);
                
                // Match response to original question
                if (pendingQuestions.has(question)) {
                    const questionId = pendingQuestions.get(question);
                    appendMessage(source.toLowerCase(), answer, questionId);
                    pendingQuestions.delete(question);
                    processingComplete();
                }
            } catch (e) {
                console.error('Message parsing failed:', e);
                appendMessage('system', 'Failed to process response');
                processingComplete();
            }
        };

        socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            appendMessage('system', 'Connection error');
            processingComplete();
        };

        socket.onclose = () => {
            console.log('WebSocket disconnected');
            processingComplete();
        };
    }

    // Cleanup after processing
    function processingComplete() {
        isProcessing = false;
        processingIndicator.style.display = 'none';
        processQueue();
    }

    // Process next question in queue
    function processQueue() {
        if (!isProcessing && pendingQuestions.size > 0 && socket?.readyState === WebSocket.OPEN) {
            const [question, questionId] = [...pendingQuestions.entries()][0];
            try {
                socket.send(question);
                isProcessing = true;
                processingIndicator.style.display = 'block';
            } catch (e) {
                console.error('Send failed:', e);
                processingComplete();
            }
        }
    }

    // Display messages in chat
    function appendMessage(type, text, id = '') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `${type}-message message`;
        if (id) messageDiv.id = id;
        
        const sender = 
            type === 'user' ? 'You' :
            type === 'rag' ? 'Knowledge Base' :
            type === 'llm' ? 'LLM' : 'System';
        
        messageDiv.innerHTML = `
            <div class="sender">${sender}</div>
            <div class="content">${text}</div>
        `;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Handle message submission
    function sendMessage() {
        const question = userInput.value.trim();
        if (question && !isProcessing) {
            const questionId = `msg-${Date.now()}`;
            appendMessage('user', question, questionId);
            pendingQuestions.set(question, questionId);
            userInput.value = '';
            
            if (!socket || socket.readyState !== WebSocket.OPEN) {
                connectWebSocket();
            } else {
                processQueue();
            }
        }
    }

    // Initialize
    connectWebSocket();

    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // UI state management
    userInput.addEventListener('input', () => {
        sendBtn.disabled = userInput.value.trim() === '' || isProcessing;
    });
});