from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..config.database import Base
from datetime import datetime
from enum import IntEnum

class TripTypeEnum(IntEnum):
    IDA = 1
    VOLTA = 2

class TripStatusEnum(IntEnum):
    ATIVA = 1
    CONCLUIDA = 2

class Trip(Base):
    __tablename__ = 'trips'
    id = Column(Integer, primary_key=True, index=True)
    trip_type = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False, default=TripStatusEnum.ATIVA)
    bus_id = Column(Integer, ForeignKey('buses.id'), nullable=False)
    driver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    bus = relationship("Bus", back_populates="trips")
    driver = relationship("User", back_populates="trips")
    student_trips = relationship("StudentTrip", back_populates="trip")
    
    system_deleted = Column(Integer, default=0)
    update_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    create_date = Column(DateTime, default=datetime.utcnow)
