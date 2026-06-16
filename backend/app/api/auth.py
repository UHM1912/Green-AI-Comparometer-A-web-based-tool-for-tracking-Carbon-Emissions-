from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from app.db.connection import get_db_conn
from app.core.security import get_password_hash, verify_password, create_access_token
import sqlite3

router = APIRouter(prefix="/api/auth", tags=["auth"])

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister):
    conn = get_db_conn()
    c = conn.cursor()
    
    hashed_pwd = get_password_hash(user_data.password)
    
    try:
        c.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (user_data.name, user_data.email, hashed_pwd)
        )
        conn.commit()
        return {"message": "Registration successful"}
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )
    finally:
        conn.close()

@router.post("/login", response_model=Token)
def login(credentials: UserLogin):
    conn = get_db_conn()
    c = conn.cursor()
    
    c.execute(
        "SELECT id, name, email, password_hash FROM users WHERE email = ?",
        (credentials.email,)
    )
    user_row = c.fetchone()
    conn.close()
    
    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    user_dict = dict(user_row)
    if not verify_password(credentials.password, user_dict["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    # Remove password hash from response
    user_info = {
        "id": user_dict["id"],
        "name": user_dict["name"],
        "email": user_dict["email"]
    }
    
    # Generate token
    token = create_access_token(data={"sub": str(user_dict["id"])})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_info
    }
