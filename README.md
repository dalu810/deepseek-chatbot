
# DeepSeek Chatbot
A lightweight AI chatbot built with DeepSeek-R1-Distill-Qwen-1.5B model, designed for easy deployment and testing—even on systems without GPU support.

✨ Features
- Local & GPU-Free Inference – Runs efficiently on CPU-only environments for testing.
- WebSocket Support – Real-time interactive chat via WebSocket connections.
- Conversation Persistence – Stores chat history in PostgreSQL for continuity.
- Dockerized Deployment – Easy setup and scaling using Docker.
- REST API Endpoint – Simple HTTP-based interaction for remote queries.

🚀 Installation

My Environment:
- Windows 11 pro, CPU: Intel(R) Core(TM) i5-8365U CPU, RAM 16G
- VM in VMWare Workstation: 4C/8G/50G Ubuntu

Clone the repository:
git clone https://github.com/dalu810/deepseek-chatbot.git

Install dependencies:
(Include a requirements.txt or instructions for pip/poetry if applicable.)


🛠 Usage
In test folder:
#Local model testing with hardcoded queries
- deepseek_testing.py	

#Local model testing, interactive CLI chat
- deepseek_chatting.py	

#Start chatbot: 
uvicorn test.deepseek_remote:app --host 0.0.0.0 --port 8000

#Test remotely, query example:
curl -X POST "http://<SERVER_IP>:8000/chat/" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "What is AI?"}'
- deepseek_remote.py


📝 Notes
The model DeepSeek-R1-Distill-Qwen-1.5B is optimized for low-resource environments, but it is slow without GPU support, just for the user who is interested in LLM usage locally.