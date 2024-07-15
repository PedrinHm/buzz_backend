from pydantic import BaseModel
from enum import Enum
from typing import Optional

class TripBusStopStatusEnum(int, Enum):
    A_CAMINHO = 1
    NO_PONTO = 2
    PROXIMO_PONTO = 3
    JA_PASSOU = 4
    ONIBUS_COM_PROBLEMA = 5

class TripBusStopBase(BaseModel):
    trip_id: int
    bus_stop_id: int
    status: TripBusStopStatusEnum

class TripBusStopCreate(TripBusStopBase):
    pass

class TripBusStopUpdate(BaseModel):
    status: TripBusStopStatusEnum

class TripBusStop(TripBusStopBase):
    id: int

    class Config:
        from_attributes = True
