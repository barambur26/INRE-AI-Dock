from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import uuid

# Setup
app = FastAPI(title="AI Dock Demo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "demo-secret-2025"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Mock Users
USERS = {
    "admin": {
        "id": str(uuid.uuid4()),
        "username": "admin",
        "email": "admin@demo.com",
        "hashed_password": pwd_context.hash("admin123"),
        "role": "admin",
        "department": "IT",
        "is_active": True
    },
    "user1": {
        "id": str(uuid.uuid4()),
        "username": "user1", 
        "email": "user1@demo.com",
        "hashed_password": pwd_context.hash("user123"),
        "role": "user",
        "department": "Marketing",
        "is_active": True
    }
}

USAGE_LOGS = []
BLACKLISTED_TOKENS = set()

# Models
class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class ChatMessage(BaseModel):
    message: str

# Utils
def create_token(data: dict):
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

def verify_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    username = payload.get("sub")
    user = USERS.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Routes
@app.get("/")
def root():
    return {"message": "AI Dock Demo", "status": "running"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "users_count": len(USERS),
        "departments_count": 2,
        "llm_configs_count": 2,
        "active_models": 2
    }

@app.get("/api/v1/auth/test-credentials")
def test_credentials():
    return {
        "test_users": [
            {"username": "admin", "password": "admin123", "role": "admin", "department": "IT"},
            {"username": "user1", "password": "user123", "role": "user", "department": "Marketing"}
        ]
    }

@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login(data: LoginRequest):
    user = USERS.get(data.username)
    if not user or not pwd_context.verify(data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token({"sub": user["username"]})
    return TokenResponse(access_token=token, refresh_token=token, expires_in=3600)

@app.post("/api/v1/auth/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    BLACKLISTED_TOKENS.add(credentials.credentials)
    return {"message": "Logged out"}

@app.get("/api/v1/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "department": user["department"],
        "is_active": user["is_active"]
    }

@app.post("/api/v1/chat/send")
def send_message(msg: ChatMessage, user: dict = Depends(get_current_user)):
    response_text = f"Hello {user['username']}! I received your message: '{msg.message}'. This is a demo AI response from AI Dock App."
    return {
        "response": response_text,
        "model": "Demo Model",
        "tokens_used": len(msg.message.split()) + len(response_text.split()),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/chat/models")
def get_models(user: dict = Depends(get_current_user)):
    return {"models": [{"model_name": "Demo Model", "provider": "demo", "enabled": True}]}

@app.get("/api/v1/admin/stats")
def admin_stats(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin required")
    return {
        "total_users": len(USERS),
        "active_users": len(USERS),
        "total_departments": 2,
        "total_llm_configs": 2,
        "enabled_llm_configs": 2,
        "total_usage_logs": len(USAGE_LOGS),
        "total_quotas": 0
    }

@app.get("/api/v1/admin/users")
def admin_users(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin required")
    return [
        {
            "id": u["id"],
            "username": u["username"],
            "email": u["email"],
            "role": u["role"],
            "department": u["department"],
            "is_active": u["is_active"],
            "created_at": datetime.now().isoformat()
        } for u in USERS.values()
    ]

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Dock Demo Backend...")
    print("📍 http://127.0.0.1:8000")
    print("📚 http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
