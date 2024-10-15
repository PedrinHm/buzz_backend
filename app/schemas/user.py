from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional
import phonenumbers
import re

# Função para validar o CPF
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

# Modelo base para o usuário
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    faculty_id: Optional[int] = None
    device_token: Optional[str] = None

    # Validador de telefone
    @field_validator('phone')
    def validate_phone(cls, v):
        if v:
            try:
                phone_number = phonenumbers.parse(v, "BR")
                if not phonenumbers.is_valid_number(phone_number):
                    raise ValueError("Invalid phone number")
            except phonenumbers.phonenumberutil.NumberParseException:
                raise ValueError("Invalid phone number format")
        return v

    # Validador de CPF
    @field_validator('cpf')
    def validate_cpf(cls, v):
        if v and not validate_cpf(v):
            raise ValueError("Invalid CPF")
        return v

# Modelo para criação de um usuário
class UserCreate(UserBase):
    email: EmailStr
    password: str
    name: str
    cpf: str
    phone: str
    user_type_id: int

# Modelo para atualização de um usuário
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    faculty_id: Optional[int] = None
    device_token: Optional[str] = None
    name: Optional[str] = None  # Adicionado para permitir a edição do nome

    # Validador de telefone para atualização
    @field_validator('phone', check_fields=False)
    def validate_phone(cls, v):
        if v:
            try:
                phone_number = phonenumbers.parse(v, "BR")
                if not phonenumbers.is_valid_number(phone_number):
                    raise ValueError("Invalid phone number")
            except phonenumbers.phonenumberutil.NumberParseException:
                raise ValueError("Invalid phone number format")
        return v

    # Validador de CPF para atualização
    @field_validator('cpf', check_fields=False)
    def validate_cpf(cls, v):
        if v and not validate_cpf(v):
            raise ValueError("Invalid CPF")
        return v

# Modelo para foto de perfil do usuário
class UserProfilePicture(BaseModel):
    picture: str

# Modelo base de usuário no banco de dados
class UserInDBBase(UserBase):
    id: int
    email: EmailStr
    name: str
    cpf: str
    phone: str
    user_type_id: int
    profile_picture: Optional[str] = None
    faculty_name: Optional[str] = None  

    model_config = ConfigDict(from_attributes=True) 

class User(UserInDBBase):
    pass
