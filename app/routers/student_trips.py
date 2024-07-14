from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..config.database import get_db
from ..models.student_trip import StudentTrip as StudentTripModel
from ..models.trip import Trip as TripModel, TripStatusEnum, TripTypeEnum
from ..models.student_status_enum import StudentStatusEnum
from ..schemas.student_trip import StudentTrip, StudentTripCreate, StudentTripUpdate

router = APIRouter(
    prefix="/student_trips",
    tags=["Student Trips"]
)

@router.post("/", response_model=StudentTrip)
def create_student_trip(student_trip: StudentTripCreate, db: Session = Depends(get_db)):
    # Verificar se o aluno já está em uma viagem ativa
    active_student_trip = db.query(StudentTripModel).join(TripModel).filter(
        StudentTripModel.student_id == student_trip.student_id,
        TripModel.status == TripStatusEnum.ATIVA,
        StudentTripModel.system_deleted == 0
    ).first()
    
    if active_student_trip:
        raise HTTPException(status_code=400, detail="O aluno já está em uma viagem ativa")
    
    # Verificar o tipo de viagem e definir status do aluno
    trip = db.query(TripModel).filter(TripModel.id == student_trip.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    if trip.trip_type == TripTypeEnum.IDA:
        student_trip.status = StudentStatusEnum.PRESENTE
    
    db_student_trip = StudentTripModel(**student_trip.dict())
    db.add(db_student_trip)
    db.commit()
    db.refresh(db_student_trip)
    return db_student_trip

@router.get("/", response_model=List[StudentTrip])
def read_student_trips(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    student_trips = db.query(StudentTripModel).filter(StudentTripModel.system_deleted == 0).offset(skip).limit(limit).all()
    return student_trips

@router.get("/{student_trip_id}", response_model=StudentTrip)
def read_student_trip(student_trip_id: int, db: Session = Depends(get_db)):
    student_trip = db.query(StudentTripModel).filter(StudentTripModel.id == student_trip_id, StudentTripModel.system_deleted == 0).first()
    if not student_trip:
        raise HTTPException(status_code=404, detail="Student trip not found")
    return student_trip

@router.put("/{student_trip_id}", response_model=StudentTrip)
def update_student_trip(student_trip_id: int, student_trip: StudentTripUpdate, db: Session = Depends(get_db)):
    db_student_trip = db.query(StudentTripModel).filter(StudentTripModel.id == student_trip_id).first()
    if not db_student_trip:
        raise HTTPException(status_code=404, detail="Student trip not found")
    for key, value in student_trip.dict().items():
        if value is not None:
            setattr(db_student_trip, key, value)
    db.commit()
    db.refresh(db_student_trip)
    return db_student_trip

@router.delete("/{student_trip_id}", response_model=dict)
def delete_student_trip(student_trip_id: int, db: Session = Depends(get_db)):
    db_student_trip = db.query(StudentTripModel).filter(StudentTripModel.id == student_trip_id).first()
    if not db_student_trip:
        raise HTTPException(status_code=404, detail="Student trip not found")
    db_student_trip.system_deleted = 1
    db.commit()
    return {"status": "deleted"}
