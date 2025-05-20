from flask import Flask, render_template, request, jsonify
from embedding_utils import embed_text
import psycopg2
import numpy as np
from psycopg2.extensions import register_adapter, AsIs

app = Flask(__name__)

def adapt_numpy_array(arr):
    # Ensures format like '[0.1, 0.2, 0.3]' → valid for pgvector
    return AsIs("'" + "[" + ",".join([str(x) for x in arr.tolist()]) + "]" + "'")

register_adapter(np.ndarray, adapt_numpy_array)

# PostgreSQL DB connection
DB_NAME = 'chatdb'
DB_USER = 'deepseek'
DB_PASSWORD = 'Deepseek202502!'
DB_HOST = 'localhost'
DB_PORT = '5432'

# Better threshold
DISTANCE_THRESHOLD = 0.4

def get_top_chunks_by_query(query, top_n=3):
    embedding = embed_text(query)
    normalized = np.array(embedding) / np.linalg.norm(embedding)

    print("Embedding norm:", np.linalg.norm(normalized))

    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    # Pass np.ndarray directly
    cur.execute("""
        SELECT chunk, embedding <=> %s AS distance
        FROM rag_chunks
        ORDER BY distance ASC
        LIMIT %s
    """, (normalized, top_n))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@app.route('/')
def index():
    return render_template('test_chat.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({'response': "Please enter a question."}), 400

    try:
        chunks = get_top_chunks_by_query(user_input, top_n=3)

        print(f"\nQuery: {user_input}")
        for chunk, distance in chunks:
            print(f"Distance: {distance:.4f} | Chunk: {chunk}")

        if chunks and chunks[0][1] <= DISTANCE_THRESHOLD:
            parts = chunks[0][0].split(",", 1)
            response_text = parts[1].strip() if len(parts) == 2 else parts[0].strip()
        else:
            response_text = "Sorry, I couldn't find a good match for your question."

        return jsonify({'response': response_text})

    except Exception as e:
        print(f"RAG error: {e}")
        return jsonify({'response': "An internal error occurred."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
