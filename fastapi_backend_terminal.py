from fastapi import FastAPI, WebSocket
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


app = FastAPI()

# Load the DeepSeek model
model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")

# Store chat history
chat_histories = {}

@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_id = websocket.client.host  # Identify user by IP
    chat_histories.setdefault(user_id, [])  # Initialize history

    while True:
        data = await websocket.receive_text()
        
        # Add user message to history
        chat_histories[user_id].append({"role": "user", "content": data})

        # Create prompt including chat history
        chat_context = " ".join([msg["content"] for msg in chat_histories[user_id][-5:]])  # Last 5 exchanges
        inputs = tokenizer(chat_context, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")

        # Generate response
        output = model.generate(**inputs, max_new_tokens=200)
        response = tokenizer.decode(output[0], skip_special_tokens=True)

        # Add model response to history
        chat_histories[user_id].append({"role": "assistant", "content": response})

        # Stream response token by token
        for token in response.split():
            await websocket.send_text(token)
        
        await websocket.send_text("[END]")  # Indicate end of response
