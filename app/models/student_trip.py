from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..config.database import Base
from datetime import datetime

class StudentTrip(Base):
    __tablename__ = 'student_trips'
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey('trips.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(Integer, nullable=False)
    point_id = Column(Integer, ForeignKey('bus_stops.id'), nullable=False)
    
    trip = relationship("Trip", back_populates="student_trips")
    student = relationship("User", back_populates="student_trips")
    point = relationship("BusStop", back_populates="student_trips")
    
    system_deleted = Column(Integer, default=0)
    update_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    create_date = Column(DateTime, default=datetime.utcnow)
