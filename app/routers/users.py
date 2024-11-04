from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..config.database import get_db
from typing import List
from ..models.user import User as UserModel
from ..schemas.user import User, UserCreate, UserUpdate, UserProfilePicture
from ..schemas import User as UserSchema
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv 
import os

load_dotenv()

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

def send_welcome_email(recipient_email: str, user_type: str):
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')

    subject = "Bem-vindo ao Sistema"
    body = f"""Olá,

Seu cadastro como {user_type} foi realizado com sucesso!
Para seu primeiro acesso, utilize seu e-mail para login e seu CPF para senha.

Após o primeiro login, você será solicitado a alterar sua senha.

Atenciosamente,
Equipe Buzz"""
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipient_email, msg.as_string())
        print("E-mail de boas-vindas enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
    finally:
        server.quit()

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(
        ((UserModel.email == user.email) | 
         (UserModel.cpf == user.cpf))
    ).first()
    
    if db_user:
        if db_user.system_deleted == 0:
            if db_user.email == user.email:
                raise HTTPException(status_code=400, detail="E-mail já cadastrado")
            if db_user.cpf == user.cpf:
                raise HTTPException(status_code=400, detail="CPF já cadastrado")
        else:
            # Reativar usuário
            db_user.system_deleted = 0
            db_user.name = user.name
            db_user.email = user.email
            db_user.cpf = user.cpf
            db_user.phone = user.phone
            db_user.faculty_id = user.faculty_id
            db_user.user_type_id = user.user_type_id
            db_user.set_password(user.password)
            db.commit()
            db.refresh(db_user)
            return db_user

    # Cria um novo usuário
    new_user = UserModel(
        name=user.name,
        email=user.email,
        cpf=user.cpf,
        phone=user.phone,
        faculty_id=user.faculty_id,
        user_type_id=user.user_type_id,
        first_login="true"
    )
    new_user.set_password(user.cpf)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Determinar o tipo de usuário
    user_type = "Motorista" if user.user_type_id == 2 else "Aluno"
    
    # Enviar email de boas-vindas
    send_welcome_email(user.email, user_type)

    return new_user

@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(UserModel).filter(UserModel.system_deleted == 0).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserSchema)
def read_user(user_id: int, db: Session = Depends(get_db)):
    # Realiza a consulta para trazer o usuário junto com o nome da faculdade
    user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.system_deleted == 0).first()

    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Verifica se o usuário possui uma faculdade associada e retorna o nome
    if user.faculty:
        user.faculty_name = user.faculty.name
    else:
        user.faculty_name = None

    return user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.system_deleted == 0).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    for var, value in vars(user).items():
        if value:
            if var == "password":
                db_user.set_password(value)
            else:
                setattr(db_user, var, value)  # Atualiza o campo `name` se ele estiver no payload
    db.commit()
    return db_user


@router.put("/{user_id}/profile-picture", response_model=schemas.User)
def update_profile_picture(user_id: int, profile_picture: schemas.UserProfilePicture, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.system_deleted == 0).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    db_user.profile_picture = profile_picture.picture
    db.commit()
    return db_user

@router.delete("/{user_id}", response_model=dict)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    db_user.system_deleted = 1
    db.commit()
    return {"ok": True}

@router.delete("/{user_id}/profile-picture", response_model=schemas.User)
def delete_profile_picture(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.system_deleted == 0).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")


    db_user.profile_picture = None
    db.commit()
    db.refresh(db_user)
    return db_user
