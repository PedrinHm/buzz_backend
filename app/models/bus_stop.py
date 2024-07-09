from sqlalchemy import Column, Integer, String, DateTime
from ..config.database import Base
from datetime import datetime

class BusStop(Base):
    __tablename__ = 'bus_stops'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    university  = Column(String)
    system_deleted = Column(String, default="0")
    update_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    create_date = Column(DateTime, default=datetime.utcnow)
