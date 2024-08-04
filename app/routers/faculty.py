from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..config.database import get_db
from ..models import faculty as faculty_model, bus_stop as bus_stop_model, user as user_model
from ..schemas import faculty as faculty_schema

router = APIRouter(
    prefix="/faculties",
    tags=["Faculties"]
)

@router.post("/", response_model=faculty_schema.Faculty)
def create_faculty(faculty: faculty_schema.FacultyCreate, db: Session = Depends(get_db)):
    # Verifica se já existe uma faculdade com o mesmo nome que não esteja deletada
    existing_faculty = db.query(faculty_model.Faculty).filter(faculty_model.Faculty.name == faculty.name, faculty_model.Faculty.system_deleted == 0).first()
    if existing_faculty:
        raise HTTPException(status_code=400, detail="Faculty with this name already exists")

    db_faculty = faculty_model.Faculty(name=faculty.name)
    db.add(db_faculty)
    db.commit()
    db.refresh(db_faculty)
    return db_faculty

@router.get("/", response_model=List[faculty_schema.Faculty])
def read_faculties(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    faculties = db.query(faculty_model.Faculty).filter(faculty_model.Faculty.system_deleted == 0).offset(skip).limit(limit).all()
    return faculties

@router.get("/{faculty_id}", response_model=faculty_schema.Faculty)
def read_faculty(faculty_id: int, db: Session = Depends(get_db)):
    faculty = db.query(faculty_model.Faculty).filter(faculty_model.Faculty.id == faculty_id, faculty_model.Faculty.system_deleted == 0).first()
    if faculty is None:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return faculty

@router.put("/{faculty_id}", response_model=faculty_schema.Faculty)
def update_faculty(faculty_id: int, faculty: faculty_schema.FacultyCreate, db: Session = Depends(get_db)):
    db_faculty = db.query(faculty_model.Faculty).filter(faculty_model.Faculty.id == faculty_id).first()
    if db_faculty is None:
        raise HTTPException(status_code=404, detail="Faculty not found")
    
    # Verifica se já existe uma faculdade com o mesmo nome (exceto a que está sendo atualizada) que não esteja deletada
    existing_faculty = db.query(faculty_model.Faculty).filter(faculty_model.Faculty.name == faculty.name, faculty_model.Faculty.id != faculty_id, faculty_model.Faculty.system_deleted == 0).first()
    if existing_faculty:
        raise HTTPException(status_code=400, detail="Faculty with this name already exists")
    
    db_faculty.name = faculty.name
    db.commit()
    db.refresh(db_faculty)
    return db_faculty

@router.delete("/{faculty_id}", response_model=faculty_schema.Faculty)
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    faculty = db.query(faculty_model.Faculty).filter(faculty_model.Faculty.id == faculty_id).first()
    if faculty is None:
        raise HTTPException(status_code=404, detail="Faculty not found")
    
    # Verifica se há pontos de ônibus vinculados a esta faculdade
    bus_stops = db.query(bus_stop_model.BusStop).filter(bus_stop_model.BusStop.faculty_id == faculty_id, bus_stop_model.BusStop.system_deleted == 0).all()
    if bus_stops:
        raise HTTPException(status_code=400, detail="Cannot delete faculty with linked bus stops")
    
    # Verifica se há alunos vinculados a esta faculdade
    students = db.query(user_model.User).filter(user_model.User.faculty_id == faculty_id, user_model.User.system_deleted == 0).all()
    if students:
        raise HTTPException(status_code=400, detail="Cannot delete faculty with linked students")
    
    faculty.system_deleted = 1
    db.commit()
    return faculty
