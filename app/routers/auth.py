from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..config.database import SessionLocal
from ..models.user import User
import bcrypt
from datetime import datetime, timedelta

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

class LoginData(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    status: str
    user_type_id: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dicionário para armazenar tentativas de login
login_attempts = {}

@router.post("/", response_model=LoginResponse)
async def login(login_data: LoginData, db: Session = Depends(get_db)):
    email = login_data.email
    now = datetime.utcnow()
    attempt_window = timedelta(minutes=10)
    max_attempts = 5

    # Limpar tentativas antigas
    login_attempts[email] = [ts for ts in login_attempts.get(email, []) if now - ts < attempt_window]

    if len(login_attempts.get(email, [])) >= max_attempts:
        raise HTTPException(status_code=403, detail="Too many login attempts. Please try again in 15 minutes.")

    user = db.query(User).filter(User.email == login_data.email).first()
    if user:
        if user.verify_password(login_data.password):
            login_attempts[email] = []  # Resetar tentativas após login bem-sucedido
            return {"status": "success", "user_type_id": user.user_type_id}
        else:
            login_attempts.setdefault(email, []).append(now)
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        login_attempts.setdefault(email, []).append(now)
        raise HTTPException(status_code=401, detail="Unauthorized")
