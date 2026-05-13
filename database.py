import sqlite3
from datetime import datetime

def get_db():
    conn = sqlite3.connect("healthmate.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS exercise_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            duration INTEGER,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    db.commit()

def log_exercise(type: str, duration: int):
    db = get_db()
    db.execute("INSERT INTO exercise_logs (type, duration) VALUES (?, ?)",
               (type, duration))
    db.commit()

def get_days_since_exercise() -> int:
    db = get_db()
    row = db.execute(
        "SELECT logged_at FROM exercise_logs ORDER BY logged_at DESC LIMIT 1"
    ).fetchone()
    if not row:
        return 3  # 默认3天没运动
    last = datetime.fromisoformat(row["logged_at"])
    return (datetime.now() - last).days
