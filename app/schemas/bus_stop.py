from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import Optional

class BusStopBase(BaseModel):
    name: str
    faculty_id: int

    @field_validator("name", mode="before")
    def name_must_not_be_empty(cls, value):
        if not value:
            raise ValueError("Name must not be empty")
        return value

class BusStopCreate(BusStopBase):
    pass

class BusStopUpdate(BaseModel):
    name: Optional[str] = None
    faculty_id: int

    @field_validator("name", mode="before")
    def name_must_not_be_empty(cls, value):
        if value == "":
            raise ValueError("Name must not be empty")
        return value

class BusStop(BusStopBase):
    id: int
    system_deleted: int
    update_date: datetime
    create_date: datetime

    model_config = {
        "from_attributes": True
    }
