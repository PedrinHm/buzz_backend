from sqlalchemy import Column, Integer, String, DateTime, Enum
from ..config.database import Base
from datetime import datetime
import enum

class UserTypeNames(enum.Enum):
    STUDENT = "Aluno"
    DRIVER = "Motorista"
    ADMIN = "Administrador"

class UserType(Base):
    __tablename__ = 'user_types'
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(Enum(UserTypeNames))
    
    system_deleted = Column(Integer, default=0) 
    update_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  
    create_date = Column(DateTime, default=datetime.utcnow)