import os
import gc
import uuid
import torch
import asyncio
import re
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from transformers import AutoTokenizer, AutoModelForCausalLM
from starlette.concurrency import run_in_threadpool
from contextlib import asynccontextmanager
from pathlib import Path

# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App starting up...")
    yield
    print("App shutting down...")

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static UI if needed
app.mount("/chatbot/static", StaticFiles(directory="static"), name="static")

# Load model and tokenizer
MODEL_NAME = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map=None
)

device = torch.device("cpu")
model.to(device)

# Locks and chat state
chat_histories = {}
MAX_HISTORY = 3
model_lock = asyncio.Lock()

# Clean up AI output
def clean_response(raw: str) -> str:
    response = raw.split("Assistant:")[-1].strip()

    # Remove XML-style tags like </think>
    response = re.sub(r"<.*?>", "", response)

    # Remove hallucinated dialog continuation
    response = re.split(r"\b(User:|Assistant:)\b", response)[0].strip()

    # Remove filler/thinking phrases
    response = re.sub(
        r'(?i)\b(Hmm|Wait|Let me think|I think|Maybe|Possibly|Alternatively|Should I|Now I need to|So|Alright|Anyway)\b.*',
        '',
        response
    ).strip()

    # Keep only the first 1-2 sentences
    sentences = re.split(r'(?<=[.!?]) +', response)
    response = " ".join(sentences[:2]).strip()

    if not response.endswith(('.', '!', '?')):
        response += '.'

    return response

# Generate model response
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
    del inputs, outputs
    gc.collect()
    return clean_response(decoded)

# WebSocket chat endpoint
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

            chat_histories[session_id].append(f"User: {user_input}")
            if len(chat_histories[session_id]) > (MAX_HISTORY * 2 + 1):
                chat_histories[session_id] = [chat_histories[session_id][0]] + chat_histories[session_id][-MAX_HISTORY * 2:]

            context = "\n".join(chat_histories[session_id]) + "\nAssistant:"

            async with model_lock:
                response = await run_in_threadpool(generate_response, context)

            chat_histories[session_id].append(f"Assistant: {response}")
            print(f"[{session_id}] Assistant: {response}")

            await websocket.send_text(response)
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
