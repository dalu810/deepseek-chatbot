import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / "configuration" / ".env"
load_dotenv(dotenv_path=env_path)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/admin/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Ensure admin_settings table exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS admin_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
""")
conn.commit()

@app.get("/logs")
async def get_logs(request: Request):
    session_id = request.query_params.get("session_id")
    start_time = request.query_params.get("start_time")
    end_time = request.query_params.get("end_time")

    # Get retention policy from DB
    cursor.execute("SELECT value FROM admin_settings WHERE key = 'retention_days'")
    result = cursor.fetchone()
    if result:
        days = int(result[0])
        threshold = datetime.now() - timedelta(days=days)
        cursor.execute("DELETE FROM chat_logs WHERE timestamp < %s", (threshold,))
        conn.commit()

    query = "SELECT id, session_id, user_message, ai_response, timestamp FROM chat_logs"
    values = []
    conditions = []

    if session_id:
        conditions.append("session_id = %s")
        values.append(session_id)
    if start_time:
        conditions.append("timestamp >= %s")
        values.append(start_time)
    if end_time:
        conditions.append("timestamp <= %s")
        values.append(end_time)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY timestamp DESC"

    cursor.execute(query, values)
    rows = cursor.fetchall()

    logs = [{
        "id": row[0],
        "session_id": row[1],
        "user_message": row[2],
        "ai_response": row[3],
        "timestamp": row[4].strftime("%-m/%-d/%Y, %-I:%M:%S %p")
    } for row in rows]

    return JSONResponse(content=logs)

@app.post("/delete")
async def delete_logs(request: Request):
    data = await request.json()
    ids = data.get("ids", [])

    try:
        ids = list(map(int, ids))  # convert to integer for SQL match
        cursor.execute("DELETE FROM chat_logs WHERE id = ANY(%s)", (ids,))
        conn.commit()
        return JSONResponse(content={"message": "Deleted successfully."})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/retention")
async def get_retention():
    cursor.execute("SELECT value FROM admin_settings WHERE key = 'retention_days'")
    result = cursor.fetchone()
    return {"days": int(result[0]) if result else 30}

@app.post("/retention")
async def update_retention(request: Request):
    data = await request.json()
    days = data.get("days", 30)
    cursor.execute("""
        INSERT INTO admin_settings (key, value)
        VALUES ('retention_days', %s)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """, (str(days),))
    conn.commit()
    return {"message": f"Retention updated to {days} days."}
