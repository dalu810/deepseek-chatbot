import os
import psycopg2
from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")

# Get correct static directory path
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files properly
app.mount("/admin/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Connect to PostgreSQL
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

@app.get("/logs")
async def get_logs(request: Request):
    session_id = request.query_params.get("session_id")
    start_time = request.query_params.get("start_time")
    end_time = request.query_params.get("end_time")

    query = "SELECT id, session_id, user_message, ai_response, timestamp FROM chat_logs"
    conditions = []
    params = []

    if session_id:
        conditions.append("session_id = %s")
        params.append(session_id)

    if start_time:
        conditions.append("timestamp >= %s")
        params.append(start_time)

    if end_time:
        conditions.append("timestamp <= %s")
        params.append(end_time)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY timestamp DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    logs = []
    for row in rows:
        logs.append({
            "id": row[0],
            "session_id": row[1],
            "user_message": row[2],
            "ai_response": row[3],
            "timestamp": row[4].strftime("%Y-%m-%d %H:%M")  # 24-hour format, no seconds
        })

    return JSONResponse(content=logs)

@app.post("/delete")
async def delete_logs(request: Request):
    data = await request.json()
    ids = data.get("ids", [])

    if ids:
        cursor.execute(
            f"DELETE FROM chat_logs WHERE id = ANY(%s)", (ids,)
        )
        conn.commit()

    return JSONResponse(content={"deleted": ids})
