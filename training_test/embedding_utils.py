import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_text(text):
    vec = model.encode(text)
    return (vec / np.linalg.norm(vec)).tolist()  # Normalize to unit vector