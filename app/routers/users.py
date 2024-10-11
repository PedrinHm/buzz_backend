from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..config.database import get_db
from typing import List
from ..models.user import User as UserModel
from ..schemas.user import User, UserCreate, UserUpdate, UserProfilePicture
from ..schemas import User as UserSchema

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(
        ((UserModel.email == user.email) | 
         (UserModel.phone == user.phone) | 
         (UserModel.cpf == user.cpf))
    ).first()
    
    if db_user:
        if db_user.system_deleted == 0:
            if db_user.email == user.email:
                raise HTTPException(status_code=400, detail="Email already registered")
            if db_user.phone == user.phone:
                raise HTTPException(status_code=400, detail="Phone number already registered")
            if db_user.cpf == user.cpf:
                raise HTTPException(status_code=400, detail="CPF already registered")
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
        first_login="false"
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

@router.get("/{user_id}", response_model=UserSchema)
def read_user(user_id: int, db: Session = Depends(get_db)):
    # Realiza a consulta para trazer o usuário junto com o nome da faculdade
    user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.system_deleted == 0).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

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
        raise HTTPException(status_code=404, detail="User not found")
    for var, value in vars(user).items():
        if value:
            if var == "password":
                db_user.set_password(value)
            else:
                setattr(db_user, var, value)
    db.commit()
    return db_user

@router.put("/{user_id}/profile-picture", response_model=schemas.User)
def update_profile_picture(user_id: int, profile_picture: schemas.UserProfilePicture, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.system_deleted == 0).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.profile_picture = profile_picture.picture
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

@router.delete("/{user_id}/profile-picture", response_model=schemas.User)
def delete_profile_picture(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.system_deleted == 0).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Remove a foto de perfil definindo o campo como None
    db_user.profile_picture = None
    db.commit()
    db.refresh(db_user)
    return db_user