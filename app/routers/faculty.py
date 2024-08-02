from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..config.database import get_db
from ..models import faculty as faculty_model
from ..schemas import faculty as faculty_schema

router = APIRouter(
    prefix="/faculties",
    tags=["Faculties"]
)

@router.post("/", response_model=faculty_schema.Faculty)
def create_faculty(faculty: faculty_schema.FacultyCreate, db: Session = Depends(get_db)):
    db_faculty = faculty_model.Faculty(name=faculty.name)
    db.add(db_faculty)
    db.commit()
    db.refresh(db_faculty)
    return db_faculty

@router.get("/", response_model=List[faculty_schema.Faculty])
def read_faculties(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    faculties = db.query(faculty_model.Faculty).offset(skip).limit(limit).all()
    return faculties

@router.get("/{faculty_id}", response_model=faculty_schema.Faculty)
def read_faculty(faculty_id: int, db: Session = Depends(get_db)):
    faculty = db.query(faculty_model.Faculty).filter(faculty_model.Faculty.id == faculty_id).first()
    if faculty is None:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return faculty

@router.delete("/{faculty_id}", response_model=faculty_schema.Faculty)
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    faculty = db.query(faculty_model.Faculty).filter(faculty_model.Faculty.id == faculty_id).first()
    if faculty is None:
        raise HTTPException(status_code=404, detail="Faculty not found")
    db.delete(faculty)
    db.commit()
    return faculty
