from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..config.database import SessionLocal
from ..models.user import User
import bcrypt
from datetime import datetime, timedelta, timezone
import secrets
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv 
import os

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

def send_reset_password_email(recipient_email: str, token: str):
    # Configurações do servidor SMTP a partir do .env
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))  # Porta para TLS
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')

    # Cria a mensagem de e-mail
    subject = "Redefinição de Senha"
    body = f"Olá,\n\nClique no link para redefinir sua senha: https://buzz-reset-password.vercel.app/reset-password?token={token}\n\nSe você não solicitou essa mudança, ignore este e-mail."
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Conecta ao servidor SMTP
        server = SMTP(smtp_server, smtp_port)
        server.starttls()  # Inicia a comunicação criptografada
        server.login(smtp_user, smtp_password)  # Faz login no servidor SMTP
        
        # Envia o e-mail
        server.sendmail(smtp_user, recipient_email, msg.as_string())
        print("E-mail de redefinição de senha enviado com sucesso!")

    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
    finally:
        server.quit()

class LoginData(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    status: str
    user_type_id: int
    id: int

class ForgotPasswordRequest(BaseModel):
    cpf: str  # Atualizado para aceitar CPF

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class UpdateDeviceTokenRequest(BaseModel):
    user_id: int
    device_token: str

class SetNewPasswordRequest(BaseModel):
    user_id: int
    new_password: str


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
    now = datetime.now(timezone.utc)  # Atualizado para evitar o warning
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
            
            # Verificar se é o primeiro login
            if user.first_login == "true":
                # Retornar um valor de user_type_id válido para atender ao LoginResponse
                return {"status": "first_login", "user_type_id": user.user_type_id, "id": user.id}
            
            return {"status": "success", "user_type_id": user.user_type_id, "id": user.id}
        else:
            login_attempts.setdefault(email, []).append(now)
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        login_attempts.setdefault(email, []).append(now)
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Busca o usuário pelo CPF
    user = db.query(User).filter(User.cpf == request.cpf, User.system_deleted == 0).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Gera um token de redefinição de senha
    reset_token = secrets.token_urlsafe(32)

    # Salva o token no banco de dados (ou em uma tabela de tokens)
    user.reset_token = reset_token
    db.commit()

    # Envia o e-mail de redefinição de senha
    send_reset_password_email(user.email, reset_token)

    return {"message": "An email has been sent with instructions to reset your password."}

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    # Busca o usuário pelo token de redefinição
    user = db.query(User).filter(User.reset_token == request.token).first()

    if not user:
        raise HTTPException(status_code=404, detail="Invalid or expired token")

    # Atualiza a senha do usuário
    user.set_password(request.new_password)
    user.reset_token = None  # Limpa o token após o uso
    db.commit()

    return {"message": "Your password has been reset successfully."}

@router.put("/update-device-token")
async def update_device_token(request: UpdateDeviceTokenRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == request.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.device_token = request.device_token
    db.commit()

    return {"status": "success", "message": "Device token updated successfully"}

@router.post("/set-new-password")
async def set_new_password(request: SetNewPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == request.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Atualiza a senha do usuário
    user.set_password(request.new_password)
    user.first_login = "false"  # Após a redefinição, marque o primeiro login como falso
    db.commit()

    return {"status": "success", "message": "Password updated successfully"}
