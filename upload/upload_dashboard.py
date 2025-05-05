import os
import csv
import io
from datetime import datetime
from fastapi import FastAPI, UploadFile, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import psycopg2
from pathlib import Path

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / "configuration" / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")

# Connect to PostgreSQL
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS training_materials (
        id SERIAL PRIMARY KEY,
        question TEXT UNIQUE,
        answer TEXT,
        updated_at TIMESTAMP
    )
""")
conn.commit()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/upload/static", StaticFiles(directory=static_dir), name="static")


@app.get("/materials")
async def list_materials():
    cursor.execute("SELECT id, question, answer, updated_at FROM training_materials ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    return JSONResponse(content=[
        {"id": row[0], "question": row[1], "answer": row[2], "updated_at": row[3].strftime("%Y-%m-%d %H:%M")}
        for row in rows
    ])


@app.post("/upload")
async def upload_csv(file: UploadFile):
    contents = await file.read()
    decoded = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    inserted, updated = 0, 0
    for row in reader:
        question = row["question"].strip()
        answer = row["answer"].strip()

        cursor.execute("SELECT answer FROM training_materials WHERE question = %s", (question,))
        result = cursor.fetchone()

        if result:
            if result[0] != answer:
                cursor.execute(
                    "UPDATE training_materials SET answer = %s, updated_at = %s WHERE question = %s",
                    (answer, datetime.now(), question)
                )
                updated += 1
        else:
            cursor.execute(
                "INSERT INTO training_materials (question, answer, updated_at) VALUES (%s, %s, %s)",
                (question, answer, datetime.now())
            )
            inserted += 1

    conn.commit()
    return JSONResponse(content={"inserted": inserted, "updated": updated})


@app.post("/delete-materials")
async def delete_materials(request: Request):
    data = await request.json()
    ids = data.get("ids", [])

    if ids:
        cursor.execute("DELETE FROM training_materials WHERE id = ANY(%s)", (ids,))
        conn.commit()

    return JSONResponse(content={"deleted": ids})

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8020))
    uvicorn.run("upload_dashboard:app", host="0.0.0.0", port=port, reload=True)
