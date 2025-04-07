from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import uuid
import asyncio
import gc
from starlette.concurrency import run_in_threadpool

app = FastAPI()

# Load model and tokenizer
model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map=None
)
device = torch.device("cpu")
model.to(device)

# Chat history config
MAX_HISTORY = 3
chat_histories = {}

# Shared lock to serialize model access
model_lock = asyncio.Lock()

@app.websocket("/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    chat_histories[session_id] = []
    print(f"[{session_id}] Connected")

    try:
        while True:
            user_input = await websocket.receive_text()
            print(f"[{session_id}] User: {user_input}")

            chat_histories[session_id].append(f"User: {user_input}")
            if len(chat_histories[session_id]) > MAX_HISTORY * 2:
                chat_histories[session_id] = chat_histories[session_id][-MAX_HISTORY * 2:]

            context = "\n".join(chat_histories[session_id]) + "\nAssistant:"

            # Serialize model access via lock
            async with model_lock:
                response = await run_in_threadpool(generate_response, context)

            chat_histories[session_id].append(f"Assistant: {response}")
            print(f"[{session_id}] Assistant: {response}")

            for line in response.split("\n"):
                if line.strip():
                    await websocket.send_text(line.strip())
            await websocket.send_text("[END]")

            gc.collect()

    except WebSocketDisconnect:
        print(f"[{session_id}] Disconnected")
        chat_histories.pop(session_id, None)
        gc.collect()


def generate_response(context: str) -> str:
    inputs = tokenizer(context, return_tensors="pt").to(device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
    del inputs, outputs
    gc.collect()

    if "Assistant:" in decoded:
        return decoded.split("Assistant:")[-1].strip()
    return decoded.strip()
