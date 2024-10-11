from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import phonenumbers
import re

def validate_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * len(cpf):
        return False
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != int(cpf[i]):
            return False
    return True

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    faculty_id: Optional[int] = None
    device_token: Optional[str] = None

    @validator('phone')
    def validate_phone(cls, v):
        if v:
            try:
                phone_number = phonenumbers.parse(v, "BR")
                if not phonenumbers.is_valid_number(phone_number):
                    raise ValueError("Invalid phone number")
            except phonenumbers.phonenumberutil.NumberParseException:
                raise ValueError("Invalid phone number format")
        return v

    @validator('cpf')
    def validate_cpf(cls, v):
        if v and not validate_cpf(v):
            raise ValueError("Invalid CPF")
        return v

class UserCreate(UserBase):
    email: EmailStr
    password: str
    name: str
    cpf: str
    phone: str
    user_type_id: int

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    faculty_id: Optional[int] = None
    device_token: Optional[str] = None
    name: Optional[str] = None  # Adicionado para permitir a edição do nome

    @validator('phone', check_fields=False)
    def validate_phone(cls, v):
        if v:
            try:
                phone_number = phonenumbers.parse(v, "BR")
                if not phonenumbers.is_valid_number(phone_number):
                    raise ValueError("Invalid phone number")
            except phonenumbers.phonenumberutil.NumberParseException:
                raise ValueError("Invalid phone number format")
        return v

    @validator('cpf', check_fields=False)
    def validate_cpf(cls, v):
        if v and not validate_cpf(v):
            raise ValueError("Invalid CPF")
        return v


class UserProfilePicture(BaseModel):
    picture: str

class UserInDBBase(UserBase):
    id: int
    email: EmailStr
    name: str
    cpf: str
    phone: str
    user_type_id: int
    profile_picture: Optional[str] = None
    faculty_name: Optional[str] = None  

    class Config:
        orm_mode = True

class User(UserInDBBase):
    pass
