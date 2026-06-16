import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger("EcoRefactor.db")

# DB file inside backend root
DB_PATH = Path(__file__).resolve().parent.parent.parent / "users.db"

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # access columns by name
    return conn


def ensure_column(cursor: sqlite3.Cursor, table_name: str, column_name: str, column_definition: str):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    
    # Create the users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL
    )
    """)
    
    # Create the refactor_jobs table to record comparative results
    c.execute("""
    CREATE TABLE IF NOT EXISTS refactor_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        filename TEXT NOT NULL,
        original_code TEXT NOT NULL,
        optimized_code TEXT NOT NULL,
        explanations TEXT,
        original_co2 REAL,
        optimized_co2 REAL,
        original_power REAL,
        optimized_power REAL,
        original_duration REAL,
        optimized_duration REAL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    ensure_column(c, "refactor_jobs", "original_cpu_time", "REAL")
    ensure_column(c, "refactor_jobs", "optimized_cpu_time", "REAL")
    ensure_column(c, "refactor_jobs", "original_peak_memory_mb", "REAL")
    ensure_column(c, "refactor_jobs", "optimized_peak_memory_mb", "REAL")
    ensure_column(c, "refactor_jobs", "benchmark_runs", "INTEGER DEFAULT 1")
    ensure_column(c, "refactor_jobs", "risk_level", "TEXT")
    ensure_column(c, "refactor_jobs", "confidence", "TEXT")
    
    conn.commit()
    conn.close()
    logger.info(f"SQLite database and tables are ready at: {DB_PATH}")
