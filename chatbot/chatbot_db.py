import os
import gc
import uuid
import torch
import asyncio
import databases
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from transformers import AutoTokenizer, AutoModelForCausalLM
from starlette.concurrency import run_in_threadpool
import logging

logging.getLogger("transformers").setLevel(logging.ERROR)
# Load environment variables
env_path = Path(__file__).resolve().parent.parent / "configuration" / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize DB connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env file")

database = databases.Database(DATABASE_URL)

CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS chat_logs (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Modern FastAPI lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App starting up...")
    await database.connect()
    await database.execute(CREATE_TABLE_QUERY)
    yield
    print("App shutting down...")
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

# Serve static files
app.mount("/chatbot/static", StaticFiles(directory="static"), name="static")

# Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load tokenizer and model (CPU only)
MODEL_NAME = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,  # still safe on CPU
    device_map=None
)
device = torch.device("cpu")
model.to(device)

# Shared memory structures
chat_histories = {}
MAX_HISTORY = 3
model_lock = torch.Lock() if hasattr(torch, "Lock") else asyncio.Lock()

# Store chat log
async def log_chat(session_id: str, user_message: str, ai_response: str):
    await database.execute(
        """
        INSERT INTO chat_logs (session_id, user_message, ai_response)
        VALUES (:session_id, :user_message, :ai_response)
        """,
        {
            "session_id": session_id,
            "user_message": user_message,
            "ai_response": ai_response,
        }
    )

# Inference logic
def generate_response(context: str) -> str:
    inputs = tokenizer(context, return_tensors="pt").to(device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.2,
        pad_token_id=tokenizer.eos_token_id
    )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract clean assistant response
    response = decoded.split("Assistant:")[-1].strip() if "Assistant:" in decoded else decoded.strip()
    response = response.split("</think>")[-1].strip()

    if response and not response[-1] in {".", "!", "?"}:
        response = response.rsplit(".", 1)[0] + "." if "." in response else response + "."

    del inputs, outputs, decoded
    gc.collect()
    return response

# WebSocket endpoint
@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    print(f"[{session_id}] Connected at {datetime.now().isoformat()}")

    system_prompt = (
        "You are a helpful AI assistant. Answer the user's question concisely and accurately. "
        "Do not explain your reasoning or thought process. Just provide the answer."
    )
    chat_histories[session_id] = [f"System: {system_prompt}"]

    try:
        while True:
            user_input = await websocket.receive_text()
            print(f"[{session_id}] User: {user_input}")

            # Track context per session (FIFO)
            chat_histories[session_id].append(f"User: {user_input}")
            if len(chat_histories[session_id]) > (MAX_HISTORY * 2 + 1):
                chat_histories[session_id] = [chat_histories[session_id][0]] + chat_histories[session_id][-MAX_HISTORY * 2:]

            context = "\n".join(chat_histories[session_id]) + "\nAssistant:"

            async with model_lock:
                response = await run_in_threadpool(generate_response, context)

            chat_histories[session_id].append(f"Assistant: {response}")
            await log_chat(session_id, user_input, response)
            print(f"[{session_id}] Assistant: {response}")

            for line in response.split("\n"):
                if line.strip():
                    await websocket.send_text(line.strip())
            await websocket.send_text("[END]")

            gc.collect()

    except WebSocketDisconnect:
        print(f"[{session_id}] Disconnected at {datetime.now().isoformat()}")
        chat_histories.pop(session_id, None)
        gc.collect()
    except Exception as e:
        print(f"[{session_id}] WebSocket error: {e}")
        await websocket.close()
        chat_histories.pop(session_id, None)
        gc.collect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
