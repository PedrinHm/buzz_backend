from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..config.database import get_db
from typing import List
from ..models.user import User as UserModel
from ..schemas.user import User, UserCreate, UserUpdate

router = APIRouter()

@router.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(
        (UserModel.email == user.email) |
        (UserModel.phone == user.phone) |
        (UserModel.cpf == user.cpf)
    ).first()
    if db_user:
        if db_user.email == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        if db_user.phone == user.phone:
            raise HTTPException(status_code=400, detail="Phone number already registered")
        if db_user.cpf == user.cpf:
            raise HTTPException(status_code=400, detail="CPF already registered")

    new_user = UserModel(
        login=user.email,  
        name=user.name,
        email=user.email,
        cpf=user.cpf,
        phone=user.phone,
        user_type_id=user.user_type_id,
        system_deleted="",
        update_date=None,
        create_date=None,
        first_login="true"
    )
    new_user.set_password(user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users

@router.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email and user.email != db_user.email:
        if db.query(UserModel).filter(UserModel.email == user.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        db_user.login = user.email
        db_user.email = user.email
    if user.phone and user.phone != db_user.phone:
        if db.query(UserModel).filter(UserModel.phone == user.phone).first():
            raise HTTPException(status_code=400, detail="Phone number already registered")
        db_user.phone = user.phone
    if user.password:
        db_user.set_password(user.password)
    db.commit()
    return db_user

@router.delete("/users/{user_id}", response_model=dict)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"ok": True}
