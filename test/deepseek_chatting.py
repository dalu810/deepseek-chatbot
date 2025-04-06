from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Load the model and tokenizer
model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")

# Chat history
chat_history = []

print("🤖 DeepSeek Chatbot - Type 'exit' to stop.\n")

while True:
    # User input
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Goodbye! 👋")
        break

    # Append user message to history
    chat_history.append(f"User: {user_input}")

    # Format conversation history
    context = "\n".join(chat_history) + "\nAI:"

    # Tokenize input
    inputs = tokenizer(context, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")

    # Generate response
    output = model.generate(**inputs, max_new_tokens=200)
    response = tokenizer.decode(output[0], skip_special_tokens=True).split("AI:")[-1].strip()

    # Show AI response
    print(f"AI: {response}")

    # Append AI response to history
    chat_history.append(f"AI: {response}")

