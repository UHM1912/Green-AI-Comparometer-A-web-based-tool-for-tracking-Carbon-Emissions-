import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")  # make sure path is correct

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("SELECT * FROM users")  # fetch all users
rows = c.fetchall()

for row in rows:
    print(row)

conn.close()
