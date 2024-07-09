from sqlalchemy import Column, Integer, String, DateTime
from ..config.database import Base

class BusStop(Base):
    __tablename__ = 'bus_stops'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    faculty = Column(String)
    system_deleted = Column(String)
    update_date = Column(DateTime)
    create_date = Column(DateTime, default=datetime.utcnow)
