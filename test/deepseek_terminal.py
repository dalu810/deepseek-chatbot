from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Initialize FastAPI app
app = FastAPI()

# Load the model
model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")

# Define request model
class ChatRequest(BaseModel):
    prompt: str

# Define the chat endpoint
@app.post("/chat/")
def chat(request: ChatRequest):
    prompt = request.prompt
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
    
    output = model.generate(**inputs, max_new_tokens=200)
    response = tokenizer.decode(output[0], skip_special_tokens=True)
    
    return {"response": response}

