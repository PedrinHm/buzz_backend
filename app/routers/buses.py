from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, aliased  
from sqlalchemy import func
from .. import models, schemas
from ..config.database import get_db
from typing import List
from ..models.trip import Trip as TripModel, TripStatusEnum, TripTypeEnum
from ..models.bus import Bus as BusModel
from ..models.student_trip import StudentTrip as StudentTripModel, StudentStatusEnum
from ..schemas.bus import Bus, BusCreate, BusUpdate


router = APIRouter(
    prefix="/buses",
    tags=["Buses"]
)

@router.get("/available_for_student", response_model=List[dict])
def get_available_buses_for_student(student_id: int = Query(...), db: Session = Depends(get_db)):

    # Buscar o trip_id atual do aluno e garantir que ele está relacionado corretamente com a trip
    current_trip = db.query(StudentTripModel).join(TripModel, StudentTripModel.trip_id == TripModel.id).filter(
        StudentTripModel.student_id == student_id,
        StudentTripModel.system_deleted == 0,
        TripModel.status == 1  # Aqui estou assumindo que 1 é o status ativo, ajuste conforme necessário
    ).first()

    if not current_trip:
        print("Nenhuma viagem encontrada para o aluno.")
        raise HTTPException(status_code=404, detail="Student trip not found")
    
    # Verificar se a trip associada ao aluno é válida
    if not current_trip.trip:
        print("Nenhuma viagem associada ao StudentTrip.")
        raise HTTPException(status_code=404, detail="Student's associated trip not found")

    # Alias para evitar ambiguidades
    trip_alias = aliased(TripModel)
    student_trip_alias = aliased(StudentTripModel)

    # Obter ônibus em viagens ativas, excluindo o ônibus que o aluno está vinculado
    active_buses = (
        db.query(
            BusModel.id.label("bus_id"),
            BusModel.registration_number,
            BusModel.name,
            BusModel.capacity,
            trip_alias.id.label("trip_id"),
            trip_alias.trip_type,
            func.count(student_trip_alias.id).label("occupied_seats")  # Conta os student_trips válidos
        )
        .join(trip_alias, BusModel.id == trip_alias.bus_id)
        .outerjoin(
            student_trip_alias,
            (student_trip_alias.trip_id == trip_alias.id) &
            (student_trip_alias.status.in_([1, 2, 3])) &
            (student_trip_alias.system_deleted == 0)
        )
        .filter(
            trip_alias.status == TripStatusEnum.ATIVA,
            trip_alias.system_deleted == 0,
            BusModel.system_deleted == 0,
            trip_alias.bus_id != current_trip.trip.bus_id  # Exclui o ônibus vinculado ao aluno
        )
        .group_by(
            BusModel.id,
            BusModel.registration_number,
            BusModel.name,
            BusModel.capacity,
            trip_alias.id,
            trip_alias.trip_type
        )
        .all()
    )
    
    if not active_buses:
        print("Nenhum ônibus ativo encontrado.")
        raise HTTPException(status_code=404, detail="No active buses found")

    return [
        {
            "bus_id": bus_id,
            "trip_id": trip_id,
            "registration_number": registration_number,
            "name": name,
            "capacity": capacity,
            "trip_type": "Ida" if trip_type == TripTypeEnum.IDA else "Volta",
            "available_seats": capacity - occupied_seats  # Calcula as vagas disponíveis
        }
        for bus_id, registration_number, name, capacity, trip_id, trip_type, occupied_seats in active_buses
    ]




@router.post("/", response_model=schemas.Bus)
def create_bus(bus: schemas.BusCreate, db: Session = Depends(get_db)):
    db_bus = db.query(BusModel).filter(
        ((BusModel.registration_number == bus.registration_number.upper()) |
         (BusModel.name == bus.name)) &
        (BusModel.system_deleted == 0)
    ).first()
    if db_bus:
        if db_bus.registration_number == bus.registration_number.upper():
            raise HTTPException(status_code=400, detail="Registration number already registered")
        if db_bus.name == bus.name:
            raise HTTPException(status_code=400, detail="Bus name already registered")
    
    db_bus_deleted = db.query(BusModel).filter(
        ((BusModel.registration_number == bus.registration_number.upper()) |
         (BusModel.name == bus.name)) &
        (BusModel.system_deleted != 0)
    ).first()
    if db_bus_deleted:
        db_bus_deleted.system_deleted = 0
        db_bus_deleted.registration_number = bus.registration_number.upper()
        db_bus_deleted.name = bus.name
        db_bus_deleted.capacity = bus.capacity
        db.commit()
        db.refresh(db_bus_deleted)
        return db_bus_deleted

    new_bus = BusModel(
        registration_number=bus.registration_number.upper(),
        name=bus.name,
        capacity=bus.capacity
    )
    db.add(new_bus)
    db.commit()
    db.refresh(new_bus)
    return new_bus

@router.get("/", response_model=List[schemas.Bus])
def read_buses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    buses = db.query(BusModel).filter(BusModel.system_deleted == 0).offset(skip).limit(limit).all()
    return buses

@router.get("/available", response_model=List[schemas.Bus])
def read_available_buses(db: Session = Depends(get_db)):
    buses = db.query(BusModel).filter(
        BusModel.system_deleted == 0,
        ~db.query(models.Trip).filter(models.Trip.bus_id == BusModel.id, models.Trip.status == 1, models.Trip.system_deleted == 0).exists()
    ).all()
    return buses

@router.get("/{bus_id}", response_model=schemas.Bus)
def read_bus(bus_id: int, db: Session = Depends(get_db)):
    bus = db.query(BusModel).filter(BusModel.id == bus_id, BusModel.system_deleted == 0).first()
    if bus is None:
        raise HTTPException(status_code=404, detail="Bus not found")
    return bus

@router.put("/{bus_id}", response_model=schemas.Bus)
def update_bus(bus_id: int, bus: schemas.BusUpdate, db: Session = Depends(get_db)):
    db_bus = db.query(BusModel).filter(BusModel.id == bus_id, BusModel.system_deleted == 0).first()
    if not db_bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    # Verifica se o novo nome já está registrado
    if bus.name and bus.name != db_bus.name:
        existing_bus = db.query(BusModel).filter(BusModel.name == bus.name, BusModel.system_deleted == 0).first()
        if existing_bus:
            raise HTTPException(status_code=400, detail="Bus name already registered")

    for var, value in vars(bus).items():
        if value:
            setattr(db_bus, var, value)
    db.commit()
    return db_bus

@router.delete("/{bus_id}", response_model=dict)
def delete_bus(bus_id: int, db: Session = Depends(get_db)):
    db_bus = db.query(BusModel).filter(BusModel.id == bus_id).first()
    if not db_bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    db_bus.system_deleted = 1
    db.commit()
    return {"ok": True}

from sqlalchemy import func  # Certifique-se de que func está importado corretamente
from sqlalchemy.orm import aliased  # Para criar alias se necessário

@router.get("/trips/active_trips", response_model=List[dict])
def get_active_buses(db: Session = Depends(get_db)):
    # Alias para evitar ambiguidades
    trip_alias = aliased(TripModel)
    student_trip_alias = aliased(StudentTripModel)

    # Consulta para obter os ônibus com viagens ativas
    active_buses = (
        db.query(
            BusModel.id.label("bus_id"),
            BusModel.registration_number,
            BusModel.name,
            BusModel.capacity,
            trip_alias.id.label("trip_id"),
            trip_alias.trip_type,
            func.count(student_trip_alias.id).label("occupied_seats")  # Conta os student_trips válidos
        )
        .select_from(BusModel)  # Definimos explicitamente que estamos começando de BusModel
        .join(trip_alias, BusModel.id == trip_alias.bus_id)  # Fazendo JOIN com TripModel
        .outerjoin(
            student_trip_alias,  # Faz um LEFT JOIN com StudentTripModel
            (student_trip_alias.trip_id == trip_alias.id) &
            (student_trip_alias.status.in_([1, 2, 3])) &
            (student_trip_alias.system_deleted == 0)
        )
        .filter(
            trip_alias.status == TripStatusEnum.ATIVA,
            trip_alias.system_deleted == 0,
            BusModel.system_deleted == 0
        )
        .group_by(
            BusModel.id,
            BusModel.registration_number,
            BusModel.name,
            BusModel.capacity,
            trip_alias.id,
            trip_alias.trip_type
        )
        .all()
    )

    if not active_buses:
        raise HTTPException(status_code=404, detail="No active buses found")

    return [
        {
            "bus_id": bus_id,
            "trip_id": trip_id,
            "registration_number": registration_number,
            "name": name,
            "capacity": capacity,
            "trip_type": "Ida" if trip_type == TripTypeEnum.IDA else "Volta",
            "available_seats": capacity - occupied_seats  # Calcula as vagas disponíveis
        }
        for bus_id, registration_number, name, capacity, trip_id, trip_type, occupied_seats in active_buses
    ]
