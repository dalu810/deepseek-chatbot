
# LLM Chatbot
- A lightweight AI chatbot built with LLM, designed for easy deployment and testing—even on systems without GPU support.
- model used: 
      DeepSeek-R1-Distill-Qwen-1.5B
      all-MiniLM-L6-v2


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
- upload/
- training/
- training_test/
- configuration/
- chatbot/
- test/
- websocket/


admin # Search/Delete/Select/Retentin support for the records of user question/AI response
    server: python3 admin_dashboard.py
    browser: http://server_IP:8010/admin/static/dashboard.html

chatbot # Chatbot with PostgreSQL 
    server: python3 chatbot.py
    browser: http://server_IP:8000/chatbot/static/chat.html

    server: python3 chatbot_db.py
    browser: http://server_IP:8000/chatbot/static/chat.html

configuration # Configuration file, .env and so on.

upload # Upload/update training materials to Chatbot 
    server: python3 upload_dashboard.py
    browser: http://server_IP:8020/upload/static/upload.html

training # Add RAG support for training material reprocessing by sentence-transformers/all-MiniLM-L6-v2 
    server: python3 training_dashboard.py
    browser: http://server_IP:5000

training_test # Test RAG feature according to training materials
    server: python3 test_chatbot.py
    browser: http://server_IP:5000

test # Test the local LLM installed
    python3 deepseek_testing.py	

    python3 deepseek_chatting.py
    uvicorn deepseek_remote:app --host 0.0.0.0 --port 8000

    python3 deepseek_remote.py
    curl -X POST "http://<SERVER_IP>:8000/chat/" -H "Content-Type: application/json" -d '{"prompt": "What is AI?"}'
    
websocket # Add WebSocat for chatting with LLM 
    server: uvicorn fastapi_websocket:app --host 0.0.0.0 --port 8000
    client: websocat ws://localhost:8000/chat


Notes on models:

- all-MiniLM-L6-v2: which is used for sentence transformers
- DeepSeek-R1-Distill-Qwen-1.5B, which is optimized for low-resource environments, but it is slow without GPU support, just for the user who is interested in LLM usage locally.