import os
import uuid
import numpy as np
import psycopg2
import torch
import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM
from psycopg2.extensions import register_adapter, AsIs
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Configuration
DB_CONFIG = {
    'dbname': 'chatdb',
    'user': 'deepseek',
    'password': 'Deepseek202502!',
    'host': 'localhost',
    'port': 5432
}

# Initialize ML models
logger.info("Loading sentence transformer...")
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Initialize DeepSeek LLM
logger.info("Loading LLM...")
tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B")
model = AutoModelForCausalLM.from_pretrained(
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
    torch_dtype=torch.float16,
    device_map="auto"
)
logger.info("Models loaded successfully")

# Database adapter
def adapt_numpy_array(arr):
    return AsIs("'" + "[" + ",".join([str(x) for x in arr.tolist()]) + "]" + "'")
register_adapter(np.ndarray, adapt_numpy_array)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Constants
SIMILARITY_THRESHOLD = 0.7  # Increased from 0.35 for stricter matching
model_lock = asyncio.Lock()

def get_rag_response(question: str) -> tuple[str, bool]:
    """Search for similar questions in rag_chunks"""
    try:
        logger.info(f"Searching RAG for: {question}")
        embedding = embedding_model.encode(question)
        normalized = embedding / np.linalg.norm(embedding)
        
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT chunk, 1 - (embedding <=> %s) AS similarity
                    FROM rag_chunks
                    WHERE 1 - (embedding <=> %s) > %s
                    ORDER BY similarity DESC
                    LIMIT 1
                """, (normalized, normalized, SIMILARITY_THRESHOLD))
                
                if result := cur.fetchone():
                    chunk, similarity = result
                    logger.info(f"Found match with similarity: {similarity:.2f}")
                    logger.info(f"Matching chunk: {chunk[:100]}...")  # Log first 100 chars
                    
                    # Additional validation
                    if similarity < SIMILARITY_THRESHOLD:
                        return ("", False)
                        
                    parts = chunk.split(",", 1)
                    return (parts[1].strip() if len(parts) > 1 else chunk.strip(), True)
    except Exception as e:
        logger.error(f"RAG search error: {e}")
    return ("", False)

def generate_llm_response(prompt: str) -> str:
    """Generate response using local DeepSeek LLM"""
    try:
        logger.info("Generating LLM response...")
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id
        )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Clean response
        if "Assistant:" in response:
            response = response.split("Assistant:")[-1].strip()
        response = response.split("User:")[0].strip()
        
        if not response.endswith(('.', '!', '?')):
            response += '.'
            
        logger.info(f"LLM response: {response[:100]}...")
        return response.replace('\n', ' ').strip()
    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        return "I encountered an error processing your request."

async def log_conversation(session_id: str, question: str, answer: str, source: str):
    """Log conversation to database"""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_logs (session_id, user_message, ai_response, source)
                    VALUES (%s, %s, %s, %s)
                """, (session_id, question, answer, source))
                conn.commit()
        logger.info(f"Logged conversation to DB")
    except Exception as e:
        logger.error(f"Failed to log conversation: {e}")

@app.get("/")
async def home():
    return FileResponse("static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info(f"New connection: {session_id}")
    
    try:
        while True:
            question = await websocket.receive_text()
            logger.info(f"Processing: {question}")
            
            # Try RAG first
            answer, is_rag = get_rag_response(question)
            source = "RAG" if is_rag else "LLM"
            
            # Fall back to LLM if needed
            if not is_rag:
                logger.info("Using LLM...")
                async with model_lock:
                    answer = generate_llm_response(f"User: {question}\nAssistant:")
            
            # Critical: Send as single JSON message
            await websocket.send_json({
                "answer": answer,
                "source": source,
                "question": question  # For client-side validation
            })
            logger.info(f"Response sent for: {question[:50]}...")
            
            await log_conversation(session_id, question, answer, source)
            
    except WebSocketDisconnect:
        logger.info(f"Disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await websocket.close(code=1011)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")