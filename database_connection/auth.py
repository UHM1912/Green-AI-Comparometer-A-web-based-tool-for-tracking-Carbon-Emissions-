import sqlite3
import bcrypt
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

# Sign up function
def sign_up(name, email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    
    try:
        c.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                  (name, email, password_hash))
        conn.commit()
        return True, "Sign up successful!"
    except sqlite3.IntegrityError:
        return False, "Email already registered."
    finally:
        conn.close()

# Login function
def login(email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT id, name, password_hash FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    
    if user and bcrypt.checkpw(password.encode(), user[2]):
        return True, {"id": user[0], "name": user[1], "email": email}
    else:
        return False, "Invalid email or password."
