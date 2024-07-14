from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..config.database import get_db
from typing import List
from ..models.user import User as UserModel
from ..schemas.user import User, UserCreate, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Verifica se o email, telefone ou CPF já estão registrados e não estão deletados
    db_user = db.query(UserModel).filter(
        ((UserModel.email == user.email) | 
         (UserModel.phone == user.phone) | 
         (UserModel.cpf == user.cpf)) & 
         (UserModel.system_deleted == 0)
    ).first()
    if db_user:
        if db_user.email == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        if db_user.phone == user.phone:
            raise HTTPException(status_code=400, detail="Phone number already registered")
        if db_user.cpf == user.cpf:
            raise HTTPException(status_code=400, detail="CPF already registered")

    # Cria um novo usuário e define a senha hashada
    new_user = UserModel(
        login=user.email,  # Assuming login is same as email
        name=user.name,
        email=user.email,
        cpf=user.cpf,
        phone=user.phone,
        user_type_id=user.user_type_id,
        first_login="true"
    )
    new_user.set_password(user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(UserModel).filter(UserModel.system_deleted == 0).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.system_deleted == 0).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.system_deleted == 0).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    for var, value in vars(user).items():
        if value:
            if var == "password":
                db_user.set_password(value)
            else:
                setattr(db_user, var, value)
    db.commit()
    return db_user

@router.delete("/{user_id}", response_model=dict)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.system_deleted = 1
    db.commit()
    return {"ok": True}
