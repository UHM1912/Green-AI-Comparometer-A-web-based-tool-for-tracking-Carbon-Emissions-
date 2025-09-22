import sqlite3
import os

# Make sure the DB is in the same folder as this file
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

# Connect to database
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Create the users table if it doesn't exist
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("Database and users table are ready!")
