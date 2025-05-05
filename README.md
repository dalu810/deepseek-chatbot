
# LLM Chatbot
- A lightweight AI chatbot built with LLM, designed for easy deployment and testing—even on systems without GPU support.
- Recently model used: DeepSeek-R1-Distill-Qwen-1.5B 

Features
- Local & GPU-Free Inference – Runs efficiently on CPU-only environments for testing.
- WebSocket Support – Real-time interactive chat via WebSocket connections.
- Conversation Persistence – Stores chat history in PostgreSQL for continuity.
- Dockerized Deployment – Easy setup and scaling using Docker.
- REST API Endpoint – Simple HTTP-based interaction for remote queries.

Installation

My Environment:
- Windows 11 pro, CPU: Intel(R) Core(TM) i5-8365U CPU, RAM 16G
- VM in VMWare Workstation: 4C/8G/50G Ubuntu

Clone the repository:
git clone https://github.com/dalu810/LLM-Chatbot.git

Install dependencies:
(Include a requirements.txt or instructions for pip/poetry if applicable.)


Usage

LLM-Chatbot/

- admin/
  - static/
  - admin_dashboard.py
- upload/
  - static/
  - upload_dashboard.py
- configuration/
  - .env
- chatbot/
  - static/
  - chatbot.py
  - chatbot_db.py
- test/
  - deepseek_testing.py
  - deepseek_chatting.py
  - test.deepseek_remote.py
- websocket/
  - fastapi_websocket.py

In test folder:
Local model testing with hardcoded queries
- deepseek_testing.py	

Local model testing, interactive CLI chat
- deepseek_chatting.py	

Remote: 
- uvicorn deepseek_remote:app --host 0.0.0.0 --port 8000

Test remotely, query example:
curl -X POST "http://<SERVER_IP>:8000/chat/" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "What is AI?"}'
- deepseek_remote.py

In websocket folder
- server: uvicorn fastapi_websocket:app --host 0.0.0.0 --port 8000
- client: websocat ws://localhost:8000/chat

In chatbot folder

Chatbot without database
- server: python3 chatbot.py
- browser: http://server_IP:8000/chatbot/static/chat.html

Chatbot with PostgreSQL
- server: python3 chatbot_db.py
- browser: http://server_IP:8000/chatbot/static/chat.html

In admin folder
- server: python3 admin_dashboard.py
- browser: http://server_IP:8010/admin/static/dashboard.html

In upload folder
- server: python3 upload_dashboard.py
- browser: http://server_IP:8020/upload/static/upload.html



Notes
The model DeepSeek-R1-Distill-Qwen-1.5B is optimized for low-resource environments, but it is slow without GPU support, just for the user who is interested in LLM usage locally.