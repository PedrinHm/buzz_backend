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

class LoginResponse(BaseModel):
    status: str
    user_type_id: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=LoginResponse)
async def login(login_data: LoginData, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if user:
        print(f"Usuário encontrado: {user.email}")
        if user.verify_password(login_data.password):
            print(f"Senha verificada com sucesso para o usuário: {user.email}")
            return {"status": "success", "user_type_id": user.user_type_id}
        else:
            print(f"Falha na verificação da senha para o usuário: {user.email}")
    else:
        print("Usuário não encontrado")
    raise HTTPException(status_code=401, detail="Unauthorized")

