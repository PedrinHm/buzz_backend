from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from ..models.student_trip import StudentStatusEnum

class StudentTripBase(BaseModel):
    trip_id: int
    student_id: int
    status: Optional[StudentStatusEnum] = None
    point_id: int

    model_config = ConfigDict(use_enum_values=True)

class StudentTripCreate(StudentTripBase):
    pass

class StudentTripUpdate(BaseModel):
    trip_id: Optional[int] = None
    student_id: Optional[int] = None
    status: Optional[StudentStatusEnum] = None
    point_id: Optional[int] = None

    model_config = ConfigDict(use_enum_values=True)

class StudentTripInDBBase(StudentTripBase):
    id: int
    system_deleted: int
    update_date: datetime
    create_date: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class StudentTrip(StudentTripInDBBase):
    pass
