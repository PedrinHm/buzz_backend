from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
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
    # Buscar o trip_id atual do aluno
    current_trip = db.query(StudentTripModel).filter(
        StudentTripModel.student_id == student_id,
        StudentTripModel.system_deleted == 0
    ).first()

    if not current_trip:
        raise HTTPException(status_code=404, detail="Student trip not found")

    # Obter ônibus em viagens ativas, excluindo o ônibus que o aluno está vinculado
    active_buses = db.query(
        BusModel.id.label("bus_id"),
        BusModel.registration_number,
        BusModel.name,
        BusModel.capacity,
        TripModel.id.label("trip_id"),
        TripModel.trip_type
    ).join(TripModel).filter(
        TripModel.status == TripStatusEnum.ATIVA,
        TripModel.system_deleted == 0,
        BusModel.system_deleted == 0,
        TripModel.bus_id != current_trip.trip.bus_id  # Exclui o ônibus vinculado ao aluno
    ).all()

    if not active_buses:
        raise HTTPException(status_code=404, detail="No active buses found")

    return [
        {
            "bus_id": bus_id,
            "trip_id": trip_id,
            "registration_number": registration_number,
            "name": name,
            "capacity": capacity,
            "trip_type": "Ida" if trip_type == TripTypeEnum.IDA else "Volta"
        }
        for bus_id, registration_number, name, capacity, trip_id, trip_type in active_buses
    ]

@router.post("/", response_model=schemas.Bus)
def create_bus(bus: schemas.BusCreate, db: Session = Depends(get_db)):
    # Verifica se o número de registro ou nome já estão registrados
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
    
    # Verifica se o ônibus está deletado e reativa-o, se necessário
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

    # Cria um novo ônibus
    new_bus = BusModel(
        registration_number=bus.registration_number.upper(),  # Aplica o upper case
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
        ~db.query(models.Trip).filter(models.Trip.bus_id == BusModel.id, models.Trip.status == 1).exists()
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

@router.get("/trips/active_trips", response_model=List[dict])
def get_active_buses(db: Session = Depends(get_db)):
    active_buses = db.query(
        BusModel.id.label("bus_id"),  # Adiciona o campo 'id' do ônibus
        BusModel.registration_number,
        BusModel.name,
        BusModel.capacity,
        TripModel.id.label("trip_id"),  # Adiciona o campo 'id' da viagem
        TripModel.trip_type
    ).join(TripModel).filter(
        TripModel.status == TripStatusEnum.ATIVA,
        TripModel.system_deleted == 0,
        BusModel.system_deleted == 0
    ).all()

    if not active_buses:
        raise HTTPException(status_code=404, detail="No active buses found")

    return [
        {
            "bus_id": bus_id,  # Inclui o 'id' do ônibus na resposta
            "trip_id": trip_id,  # Inclui o 'id' da viagem na resposta
            "registration_number": registration_number,
            "name": name,
            "capacity": capacity,
            "trip_type": "Ida" if trip_type == TripTypeEnum.IDA else "Volta"
        }
        for bus_id, registration_number, name, capacity, trip_id, trip_type in active_buses
    ]

