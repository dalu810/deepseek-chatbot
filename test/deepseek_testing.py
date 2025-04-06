from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"

# Load the model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")

# Run inference
prompt = "What is quantum computing?"
inputs = tokenizer(prompt, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")

output = model.generate(**inputs, max_new_tokens=200)
print(tokenizer.decode(output[0], skip_special_tokens=True))
