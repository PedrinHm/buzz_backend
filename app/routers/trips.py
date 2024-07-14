from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..config.database import get_db
from ..models.trip import Trip as TripModel, TripStatusEnum, TripTypeEnum
from ..models.student_trip import StudentTrip as StudentTripModel
from ..models.student_status_enum import StudentStatusEnum
from ..schemas.trip import Trip, TripCreate, TripUpdate

router = APIRouter(
    prefix="/trips",
    tags=["Trips"]
)

@router.post("/", response_model=Trip)
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    # Verificar se existe uma viagem ativa para o ônibus ou motorista
    active_trip = db.query(TripModel).filter(
        (TripModel.bus_id == trip.bus_id) | 
        (TripModel.driver_id == trip.driver_id),
        TripModel.status == TripStatusEnum.ATIVA,
        TripModel.system_deleted == 0
    ).first()
    
    if active_trip:
        raise HTTPException(status_code=400, detail="Há uma viagem ativa para o ônibus ou motorista")
    
    db_trip = TripModel(
        trip_type=trip.trip_type,
        status=trip.status,
        bus_id=trip.bus_id,
        driver_id=trip.driver_id
    )
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip

@router.get("/", response_model=List[Trip])
def read_trips(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    trips = db.query(TripModel).filter(TripModel.system_deleted == 0).offset(skip).limit(limit).all()
    return trips

@router.get("/{trip_id}", response_model=Trip)
def read_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(TripModel.id == trip_id, TripModel.system_deleted == 0).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@router.put("/{trip_id}", response_model=Trip)
def update_trip(trip_id: int, trip: TripUpdate, db: Session = Depends(get_db)):
    db_trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    if not db_trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    for key, value in trip.dict().items():
        if value is not None:
            setattr(db_trip, key, value.value if isinstance(value, IntEnum) else value)
    db.commit()
    db.refresh(db_trip)
    return db_trip

@router.put("/{trip_id}/finalizar_ida", response_model=Trip)
def finalizar_viagem_ida(trip_id: int, db: Session = Depends(get_db)):
    db_trip = db.query(TripModel).filter(TripModel.id == trip_id, TripModel.trip_type == TripTypeEnum.IDA, TripModel.system_deleted == 0).first()
    if not db_trip:
        raise HTTPException(status_code=404, detail="Viagem de ida não encontrada")

    # Alterar status da viagem de ida para concluída
    db_trip.status = TripStatusEnum.CONCLUIDA.value
    db.commit()
    db.refresh(db_trip)

    # Criar uma nova viagem de volta
    new_trip = TripModel(
        trip_type=TripTypeEnum.VOLTA.value,
        status=TripStatusEnum.ATIVA.value,
        bus_id=db_trip.bus_id,
        driver_id=db_trip.driver_id
    )
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

    # Atualizar status dos alunos e criar novos registros para a viagem de volta
    student_trips = db.query(StudentTripModel).filter(StudentTripModel.trip_id == trip_id).all()
    for student_trip in student_trips:
        student_trip.status = StudentStatusEnum.EM_AULA.value
        new_student_trip = StudentTripModel(
            trip_id=new_trip.id,
            student_id=student_trip.student_id,
            status=StudentStatusEnum.EM_AULA.value,
            point_id=student_trip.point_id
        )
        db.add(new_student_trip)
    db.commit()

    return db_trip

@router.delete("/{trip_id}", response_model=dict)
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    db_trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    if not db_trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    db_trip.system_deleted = 1
    db.commit()
    return {"status": "deleted"}
