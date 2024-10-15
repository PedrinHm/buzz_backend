from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
import re

class BusBase(BaseModel):
    registration_number: Optional[str] = None
    name: Optional[str] = None
    capacity: Optional[int] = None

class BusCreate(BusBase):
    registration_number: str
    name: str
    capacity: int

    # Validador para transformar em letras maiúsculas
    @field_validator("registration_number", mode='before')
    def uppercase_registration_number(cls, v):
        if v is not None:  # Verifica se não é None
            return v.upper()
        return v

    # Validador para verificar o formato da placa
    @field_validator("registration_number")
    def validate_registration_number(cls, v):
        pattern = r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$|^[A-Z]{3}[0-9]{4}$'
        if not re.match(pattern, v):
            raise ValueError("Invalid registration number format")
        return v

class BusUpdate(BusBase):
    # Mesmo validador de uppercase para BusUpdate
    @field_validator("registration_number", mode='before')
    def uppercase_registration_number(cls, v):
        if v is not None:  # Verifica se não é None
            return v.upper()
        return v

class BusInDBBase(BusBase):
    id: int
    registration_number: str
    name: str
    capacity: int
    system_deleted: int

    model_config = ConfigDict(from_attributes=True)

class Bus(BusInDBBase):
    pass
