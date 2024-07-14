from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..config.database import get_db
from typing import List
from ..models.bus import Bus as BusModel
from ..schemas.bus import Bus, BusCreate, BusUpdate

router = APIRouter(
    prefix="/buses",
    tags=["Buses"]
)

@router.post("/", response_model=schemas.Bus)
def create_bus(bus: schemas.BusCreate, db: Session = Depends(get_db)):
    # Verifica se o número de registro ou nome já estão registrados
    db_bus = db.query(BusModel).filter(
        (BusModel.registration_number == bus.registration_number) |
        (BusModel.name == bus.name) &
        (BusModel.system_deleted == 0)
    ).first()
    if db_bus:
        if db_bus.registration_number == bus.registration_number:
            raise HTTPException(status_code=400, detail="Registration number already registered")
        if db_bus.name == bus.name:
            raise HTTPException(status_code=400, detail="Bus name already registered")

    # Cria um novo ônibus
    new_bus = BusModel(
        registration_number=bus.registration_number,
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
    db_bus.system_deleted = "1"
    db.commit()
    return {"ok": True}
