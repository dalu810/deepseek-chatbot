
# LLM Chatbot
A lightweight AI chatbot built with LLM, designed for easy deployment and testing—even on systems without GPU support.

## Model used
|Model  |Purpose  |Hardware Requirements  |
|-------|---------|-----------------------|
| `DeepSeek-R1-Distill-Qwen-1.5B` | Core LLM inference | CPU (GPU optional) |
| `all-MiniLM-L6-v2` | Sentence embeddings for RAG | CPU-efficient |

## Features

- **CPU-Friendly Inference** - Runs efficiently without GPU support using `DeepSeek-R1-Distill-Qwen-1.5B`
- **Real-Time Interaction** - WebSocket support for live chat experiences
- **Conversation History** - PostgreSQL-backed chat persistence
- **Easy Deployment** - Docker container support for simplified setup
- **API Integration** - REST endpoint for programmatic access
- **RAG Support** - Retrieval-Augmented Generation with `all-MiniLM-L6-v2` embeddings

## Installation

### My Environment:
- Windows 11 pro, CPU: Intel(R) Core(TM) i5-8365U CPU, RAM 16G
- VM in VMWare Workstation: 4C/8G/50G Ubuntu

### Clone the repository:
git clone https://github.com/dalu810/LLM-Chatbot.git

### Install dependencies:
(Include a requirements.txt or instructions for pip/poetry if applicable.)

## Project Structure
```
📁LLM-Chatbot/
├── 📁admin/              # User conversation management dashboard
├── 📁chatbot/            # chatbot interface with PostgreSQL
├── 📁chatbot_2_models/   # Core chatbot interface supported by training materials and LLM
├── 📁configuration/      # Environment and config files
├── 📁upload/             # Training material upload portal
├── 📁training/           # RAG processing with sentence-transformers
├── 📁training_test/      # RAG feature testing
├── 📁test/               # Local LLM validation tests
└── 📁websocket/          # WebSocket communication layer
```

## Usage

### admin
```
    server: python3 admin_dashboard.py
    browser: http://server_IP:8010/admin/static/dashboard.html
```
### chatbot
```
    server: python3 chatbot.py
    browser: http://server_IP:8000/chatbot/static/chat.html

    server: python3 chatbot_db.py
    browser: http://server_IP:8000/chatbot/static/chat.html
```
### chatbot_2_models
```
    server: python3 main.py
    browser: http://server_IP:8000/

```

### configuration

### upload
```
    server: python3 upload_dashboard.py
    browser: http://server_IP:8020/upload/static/upload.html
```
### training
```
    server: python3 training_dashboard.py
    browser: http://server_IP:5000
```

### training_test
```
    server: python3 test_chatbot.py
    browser: http://server_IP:5000
```

### test
```
    python3 deepseek_testing.py	

    python3 deepseek_chatting.py
    uvicorn deepseek_remote:app --host 0.0.0.0 --port 8000

    python3 deepseek_remote.py
    curl -X POST "http://<SERVER_IP>:8000/chat/"\ 
         -H "Content-Type: application/json"\ 
         -d '{"prompt":"What is AI?"}'
```

### websocket
```
    server: uvicorn fastapi_websocket:app --host 0.0.0.0 --port 8000
    client: websocat ws://localhost:8000/chat
```


##  Notes on models:

- **all-MiniLM-L6-v2**, which is used for sentence transformers
- **DeepSeek-R1-Distill-Qwen-1.5B**, which is optimized for low-resource environments, but it is slow without GPU support, just for the user who is interested in LLM usage locally.