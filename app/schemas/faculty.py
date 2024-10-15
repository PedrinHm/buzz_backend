from pydantic import BaseModel, ConfigDict
from datetime import datetime

class FacultyBase(BaseModel):
    name: str

class FacultyCreate(FacultyBase):
    pass

class Faculty(FacultyBase):
    id: int
    system_deleted: int
    update_date: datetime
    create_date: datetime

    model_config = ConfigDict(from_attributes=True)
