from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..config.database import SessionLocal
from ..models.user import User
import bcrypt
from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

class LoginData(BaseModel):
    email: str
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
async def login(login_data: LoginData, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if user and user.verify_password(login_data.password):
        return {"status": "success"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")