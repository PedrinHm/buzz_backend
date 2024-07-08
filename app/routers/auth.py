from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class LoginData(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(login_data: LoginData):
    if login_data.email == "user@example.com" and login_data.password == "senha123":
        return {"status": "success"}
    raise HTTPException(status_code=401, detail="Unauthorized")
