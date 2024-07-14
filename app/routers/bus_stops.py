from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..config.database import get_db
from ..models.bus_stop import BusStop as BusStopModel
from ..schemas.bus_stop import BusStop, BusStopCreate, BusStopUpdate
from typing import List

router = APIRouter(
    prefix="/bus_stops",
    tags=["Bus Stops"]
)

@router.post("/", response_model=schemas.BusStop)
def create_bus_stop(bus_stop: schemas.BusStopCreate, db: Session = Depends(get_db)):
    db_bus_stop = db.query(BusStopModel).filter(BusStopModel.name == bus_stop.name).first()
    if db_bus_stop:
        raise HTTPException(status_code=400, detail="Bus stop name already registered")
    
    new_bus_stop = BusStopModel(
        name=bus_stop.name,
        university =bus_stop.university ,
        system_deleted="0"
    )
    db.add(new_bus_stop)
    db.commit()
    db.refresh(new_bus_stop)
    return new_bus_stop

@router.get("/", response_model=List[schemas.BusStop])
def read_bus_stops(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    bus_stops = db.query(BusStopModel).filter(BusStopModel.system_deleted == 0).offset(skip).limit(limit).all()
    return bus_stops

@router.get("/{bus_stop_id}", response_model=schemas.BusStop)
def read_bus_stop(bus_stop_id: int, db: Session = Depends(get_db)):
    bus_stop = db.query(BusStopModel).filter(BusStopModel.id == bus_stop_id, BusStopModel.system_deleted == 0).first()
    if bus_stop is None:
        raise HTTPException(status_code=404, detail="Bus stop not found")
    return bus_stop

@router.put("/{bus_stop_id}", response_model=schemas.BusStop)
def update_bus_stop(bus_stop_id: int, bus_stop: schemas.BusStopUpdate, db: Session = Depends(get_db)):
    db_bus_stop = db.query(BusStopModel).filter(BusStopModel.id == bus_stop_id).first()
    if not db_bus_stop:
        raise HTTPException(status_code=404, detail="Bus stop not found")
    for var, value in vars(bus_stop).items():
        if value is not None:
            setattr(db_bus_stop, var, value)
    db.commit()
    db.refresh(db_bus_stop)
    return db_bus_stop

@router.delete("/{bus_stop_id}", response_model=dict)
def delete_bus_stop(bus_stop_id: int, db: Session = Depends(get_db)):
    db_bus_stop = db.query(BusStopModel).filter(BusStopModel.id == bus_stop_id).first()
    if not db_bus_stop:
        raise HTTPException(status_code=404, detail="Bus stop not found")
    db_bus_stop.system_deleted = "1"
    db.commit()
    return {"ok": True}
