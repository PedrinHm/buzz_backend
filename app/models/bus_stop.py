# app/models/bus_stop.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..config.database import Base
from datetime import datetime

class BusStop(Base):
    __tablename__ = 'bus_stops'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    faculty_id = Column(Integer, ForeignKey('faculties.id'), nullable=False)
    
    system_deleted = Column(Integer, default=0) 
    update_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    create_date = Column(DateTime, default=datetime.utcnow)

    student_trips = relationship("StudentTrip", back_populates="bus_stop")
    trip_bus_stops = relationship("TripBusStop", back_populates="bus_stop")
