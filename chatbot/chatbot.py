from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from transformers import AutoTokenizer, AutoModelForCausalLM
from starlette.concurrency import run_in_threadpool
import torch
import uuid
import gc
import asyncio

app = FastAPI()

# Static file mount
app.mount("/chatbot/static", StaticFiles(directory="static"), name="static")

# Enable CORS if needed (browser access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model config
MODEL_NAME = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map=None  # CPU-only
)
device = torch.device("cpu")
model.to(device)

# Session state
MAX_HISTORY = 3
chat_histories = {}
model_lock = torch.Lock() if hasattr(torch, "Lock") else asyncio.Lock()

@app.websocket("/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    print(f"[{session_id}] Connected")
    system_prompt = (
        "You are a helpful AI assistant. Answer the user's question concisely and accurately. "
        "Do not explain your reasoning or thought process. Just provide the answer."
    )
    chat_histories[session_id] = [f"System: {system_prompt}"]

    try:
        while True:
            user_input = await websocket.receive_text()
            print(f"[{session_id}] User: {user_input}")

            # Update per-session history (FIFO)
            chat_histories[session_id].append(f"User: {user_input}")
            if len(chat_histories[session_id]) > (MAX_HISTORY * 2 + 1):
                chat_histories[session_id] = [chat_histories[session_id][0]] + chat_histories[session_id][-MAX_HISTORY * 2:]

            # Format input
            context = "\n".join(chat_histories[session_id]) + "\nAssistant:"

            # Generate in thread-safe, non-blocking fashion
            async with model_lock:
                response = await run_in_threadpool(generate_response, context)

            chat_histories[session_id].append(f"Assistant: {response}")
            print(f"[{session_id}] Assistant: {response}")

            # Send response in parts
            for line in response.split("\n"):
                if line.strip():
                    await websocket.send_text(line.strip())
            await websocket.send_text("[END]")

            gc.collect()

    except WebSocketDisconnect:
        print(f"[{session_id}] Disconnected")
        chat_histories.pop(session_id, None)
        gc.collect()
    except Exception as e:
        print(f"[{session_id}] WebSocket error: {e}")
        await websocket.close()
        chat_histories.pop(session_id, None)
        gc.collect()

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
    if "Assistant:" in decoded:
        response = decoded.split("Assistant:")[-1].strip()
    else:
        response = decoded.strip()

    # Remove any trailing tags or hallucinations
    response = response.split("</think>")[-1].strip()

    del inputs, outputs, decoded
    gc.collect()
    return response
