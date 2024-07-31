from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from ..config.database import Base

class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    system_deleted = Column(Integer, default=0)
    update_date = Column(DateTime, default=datetime.utcnow)
    create_date = Column(DateTime, default=datetime.utcnow)

