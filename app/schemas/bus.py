from pydantic import BaseModel, validator
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

    @validator("registration_number", pre=True, always=True)
    def uppercase_registration_number(cls, v):
        if v:
            return v.upper()
        return v

    @validator("registration_number")
    def validate_registration_number(cls, v):
        pattern = r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$|^[A-Z]{3}[0-9]{4}$'
        if not re.match(pattern, v):
            raise ValueError("Invalid registration number format")
        return v

class BusUpdate(BusBase):
    @validator("registration_number", pre=True, always=True)
    def uppercase_registration_number(cls, v):
        if v:
            return v.upper()
        return v

class BusInDBBase(BusBase):
    id: int
    registration_number: str
    name: str
    capacity: int
    system_deleted: int

    class Config:
        orm_mode = True

class Bus(BusInDBBase):
    pass
