from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..config.database import get_db
from ..models.bus_stop import BusStop as BusStopModel
from ..models.faculty import Faculty as FacultyModel
from ..models.trip_bus_stop import TripBusStop as TripBusStopModel  # Importa o modelo TripBusStop
from ..models.trip import Trip as TripModel  # Importa o modelo Trip, caso necessário
from ..schemas.bus_stop import BusStop, BusStopCreate, BusStopUpdate
from typing import List

router = APIRouter(
    prefix="/bus_stops",
    tags=["Bus Stops"]
)

@router.get("/ida", response_model=List[dict])  # Define explicitamente o caminho "/ida"
def get_bus_stops_for_departure(db: Session = Depends(get_db)):
    bus_stops = db.query(BusStopModel, FacultyModel).join(FacultyModel, BusStopModel.faculty_id == FacultyModel.id).filter(
        BusStopModel.system_deleted == 0,
        FacultyModel.system_deleted == 0
    ).all()

    if not bus_stops:
        raise HTTPException(status_code=404, detail="No bus stops found")

    return [
        {
            "id": bus_stop.id,
            "name": f"{bus_stop.name} - {faculty.name}",  # Concatena o nome do ponto com o nome da faculdade
            "status": "A caminho"  # Status fixo para ida
        }
        for bus_stop, faculty in bus_stops
    ]

@router.get("/volta/{trip_id}", response_model=List[dict])
def get_bus_stops_for_return(trip_id: int, db: Session = Depends(get_db)):
    trip_bus_stops = db.query(TripBusStopModel, BusStopModel, FacultyModel).join(
        BusStopModel, TripBusStopModel.bus_stop_id == BusStopModel.id
    ).join(
        FacultyModel, BusStopModel.faculty_id == FacultyModel.id
    ).filter(
        TripBusStopModel.trip_id == trip_id,
        TripBusStopModel.system_deleted == 0,
        BusStopModel.system_deleted == 0,
        FacultyModel.system_deleted == 0
    ).all()

    if not trip_bus_stops:
        raise HTTPException(status_code=404, detail="No bus stops found for this trip")

    return [
        {
            "id": trip_bus_stop.bus_stop.id,
            "name": f"{trip_bus_stop.bus_stop.name} - {trip_bus_stop.faculty.name}",  # Concatena o nome do ponto com o nome da faculdade
            "status": TripBusStopModel.status.label()  # Usa o método label() para exibir o status em formato legível
        }
        for trip_bus_stop, bus_stop, faculty in trip_bus_stops
    ]

@router.post("/", response_model=schemas.BusStop)
def create_bus_stop(bus_stop: schemas.BusStopCreate, db: Session = Depends(get_db)):
    # Verifica se o nome já está registrado e não está deletado
    db_bus_stop = db.query(BusStopModel).filter(
        (BusStopModel.name == bus_stop.name) &
        (BusStopModel.system_deleted == 0)
    ).first()
    if db_bus_stop:
        raise HTTPException(status_code=400, detail="Bus stop name already registered")

    # Verifica se o nome já está registrado mas está deletado e reativa-o
    db_bus_stop_deleted = db.query(BusStopModel).filter(
        (BusStopModel.name == bus_stop.name) &
        (BusStopModel.system_deleted != 0)
    ).first()
    if db_bus_stop_deleted:
        db_bus_stop_deleted.system_deleted = 0
        db_bus_stop_deleted.faculty_id = bus_stop.faculty_id
        db.commit()
        db.refresh(db_bus_stop_deleted)
        return db_bus_stop_deleted
    
    new_bus_stop = BusStopModel(
        name=bus_stop.name,
        faculty_id=bus_stop.faculty_id,
        system_deleted=0
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
    db_bus_stop = db.query(BusStopModel).filter(BusStopModel.id == bus_stop_id, BusStopModel.system_deleted == 0).first()
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
    db_bus_stop.system_deleted = 1
    db.commit()
    return {"ok": True}

@router.get("/list/faculty_names", response_model=List[dict])
def get_bus_stops_with_faculty_names(db: Session = Depends(get_db)):
    bus_stops = db.query(
        BusStopModel.id,
        BusStopModel.name,
        FacultyModel.name
    ).join(FacultyModel, BusStopModel.faculty_id == FacultyModel.id).filter(
        BusStopModel.system_deleted == 0,
        FacultyModel.system_deleted == 0
    ).all()

    if not bus_stops:
        raise HTTPException(status_code=404, detail="No bus stops found")

    return [
        {
            "id": bus_stop_id,
            "name": f"{bus_stop_name} - {faculty_name}"
        }
        for bus_stop_id, bus_stop_name, faculty_name in bus_stops
    ]

