from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BusStopBase(BaseModel):
    name: str
    faculdade: str

class BusStopCreate(BusStopBase):
    pass

class BusStopUpdate(BaseModel):
    name: Optional[str] = None
    faculdade: Optional[str] = None

class BusStop(BusStopBase):
    id: int
    system_deleted: str
    update_date: datetime
    create_date: datetime

    class Config:
        from_attributes = True
