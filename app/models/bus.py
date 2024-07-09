from sqlalchemy import Column, Integer, String, DateTime
from ..config.database import Base
from datetime import datetime

class Bus(Base):
    __tablename__ = 'buses'
    id = Column(Integer, primary_key=True, index=True)
    registration_number = Column(String, unique=True, index=True)
    name = Column(String, unique=True, index=True)
    capacity = Column(Integer)
    system_deleted = Column(String, default="0")
    update_date = Column(DateTime, default=datetime.utcnow)
    create_date = Column(DateTime, default=datetime.utcnow)
