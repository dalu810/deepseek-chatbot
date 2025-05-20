import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
from numpy.linalg import norm

DB_PARAMS = {
    'dbname': 'chatdb',
    'user': 'deepseek',
    'password': 'Deepseek202502!',
    'host': 'localhost',
    'port': 5432,
}

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def get_db_connection():
    return psycopg2.connect(**DB_PARAMS)

def create_rag_chunks_table():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS rag_chunks (
                    id SERIAL PRIMARY KEY,
                    material_id INTEGER,
                    user_name TEXT,
                    chunk TEXT NOT NULL,
                    embedding VECTOR(384),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()

def insert_material(question, answer):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT answer FROM training_materials WHERE question = %s", (question,))
        result = cur.fetchone()
        if result:
            if result[0] != answer:
                cur.execute("""
                    UPDATE training_materials SET answer = %s, updated_at = NOW() WHERE question = %s
                """, (answer, question))
                conn.commit()
                return 'updated'
            else:
                return 'duplicate'
        else:
            cur.execute("""
                INSERT INTO training_materials (question, answer, updated_at)
                VALUES (%s, %s, NOW())
            """, (question, answer))
            conn.commit()
            return 'added'
    finally:
        cur.close()
        conn.close()

def update_material(material_id, new_answer):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE training_materials
                SET answer = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (new_answer.strip(), material_id))
        conn.commit()

def delete_materials_by_ids(ids):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM training_materials WHERE id = ANY(%s::int[])", (ids,))
        conn.commit()
    finally:
        cur.close()
        conn.close()

def get_all_materials():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, question, answer,
            CASE
                WHEN updated_at IS NOT NULL THEN updated_at
                ELSE NOW()
            END as display_time
        FROM training_materials
        ORDER BY display_time DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def reprocess_embeddings_from_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch all training materials
    cur.execute("SELECT id, question, answer FROM training_materials")
    rows = cur.fetchall()

    # Clear rag_chunks
    cur.execute("DELETE FROM rag_chunks")

    for record in rows:
        material_id, question, answer = record
        question = question.strip()
        answer = answer.strip()
        chunk = f"{question},{answer}"

        vec = model.encode(question)
        vec_norm = np.linalg.norm(vec)

        if vec_norm == 0:
            print(f"[Warning] Skipped zero-vector for material ID {material_id}")
            continue

        normalized_embedding = (vec / vec_norm).tolist()

        cur.execute("""
            INSERT INTO rag_chunks (material_id, chunk, embedding, user_name)
            VALUES (%s, %s, %s, %s)
        """, (material_id, chunk, normalized_embedding, 'admin'))

    conn.commit()
    cur.close()
    conn.close()
