from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from ..models.trip import TripTypeEnum, TripStatusEnum

class TripBase(BaseModel):
    trip_type: TripTypeEnum
    status: TripStatusEnum
    bus_id: int
    driver_id: int
    bus_issue: bool = False  # Adicionado o campo de problema no ônibus

    model_config = ConfigDict(use_enum_values=True)

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    trip_type: Optional[TripTypeEnum] = None
    status: Optional[TripStatusEnum] = None
    bus_id: Optional[int] = None
    driver_id: Optional[int] = None
    bus_issue: Optional[bool] = None  # Adicionado o campo de problema no ônibus

    model_config = ConfigDict(use_enum_values=True)

class TripInDBBase(TripBase):
    id: int
    system_deleted: int
    update_date: datetime
    create_date: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class Trip(TripInDBBase):
    pass
