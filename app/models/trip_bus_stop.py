from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..config.database import Base
from enum import Enum
from datetime import datetime

class TripBusStopStatusEnum(int, Enum):
    A_CAMINHO = 1
    NO_PONTO = 2
    PROXIMO_PONTO = 3
    JA_PASSOU = 4
    ONIBUS_COM_PROBLEMA = 5

class TripBusStop(Base):
    __tablename__ = 'trip_bus_stops'

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey('trips.id'), nullable=False)
    bus_stop_id = Column(Integer, ForeignKey('bus_stops.id'), nullable=False)
    status = Column(Integer, nullable=False, default=TripBusStopStatusEnum.A_CAMINHO)
   
    system_deleted = Column(Integer, default=0)
    update_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    create_date = Column(DateTime, default=datetime.utcnow)

    trip = relationship("Trip", back_populates="trip_bus_stops")
    bus_stop = relationship("BusStop", back_populates="trip_bus_stops")