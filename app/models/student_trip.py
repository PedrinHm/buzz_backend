from enum import Enum
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..config.database import Base

class StudentStatusEnum(int, Enum):
    PRESENTE = 1
    EM_AULA = 2
    AGUARDANDO_NO_PONTO = 3
    NAO_VOLTARA = 4
    FILA_DE_ESPERA = 5

class StudentTrip(Base):
    __tablename__ = "student_trips"
    
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Integer, nullable=False)
    point_id = Column(Integer, ForeignKey("bus_stops.id"))
    
    system_deleted = Column(Integer, default=0)
    update_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    create_date = Column(DateTime, default=datetime.utcnow)

    trip = relationship("Trip", back_populates="student_trips")
    student = relationship("User", back_populates="student_trips")
    bus_stop = relationship("BusStop", back_populates="student_trips")
