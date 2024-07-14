from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BusStopBase(BaseModel):
    name: str
    university : str

class BusStopCreate(BusStopBase):
    pass

class BusStopUpdate(BaseModel):
    name: Optional[str] = None
    university : Optional[str] = None

class BusStop(BusStopBase):
    id: int
    system_deleted: int
    update_date: datetime
    create_date: datetime

    class Config:
        from_attributes = True
