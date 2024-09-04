from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .. import models, schemas
from ..config.database import get_db
from ..models.bus_stop import BusStop as BusStopModel
from ..models.faculty import Faculty as FacultyModel
from ..models.trip_bus_stop import TripBusStop as TripBusStopModel  
from ..models.trip import Trip as TripModel, TripTypeEnum  
from ..models.student_trip import StudentTrip as StudentTripModel  
from ..models.trip_bus_stop import TripBusStopStatusEnum 
from ..schemas.bus_stop import BusStop, BusStopCreate, BusStopUpdate
from typing import List, Optional


router = APIRouter(
    prefix="/bus_stops",
    tags=["Bus Stops"]
)

@router.get("/action/trip", response_model=List[dict])
def get_bus_stops_for_trip(
    student_id: int = Query(..., description="ID do aluno"),
    trip_id: int = Query(..., description="ID da viagem selecionada"),
    db: Session = Depends(get_db)
):
    # Obtém a viagem associada ao trip_id fornecido
    trip = db.query(TripModel).filter(
        TripModel.id == trip_id,
        TripModel.system_deleted == 0
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Viagem não encontrada para o ID fornecido")

    # Consulta para verificar se o aluno está vinculado a algum ponto de ônibus em student_trip
    student_trip = db.query(StudentTripModel).filter(
        StudentTripModel.student_id == student_id,
        StudentTripModel.trip_id == trip.id,
        StudentTripModel.system_deleted == 0
    ).first()

    selected_bus_stop_id = student_trip.point_id if student_trip else None

    # Base da consulta para todos os pontos de ônibus vinculados à faculdade
    base_query = db.query(BusStopModel, FacultyModel).join(FacultyModel, BusStopModel.faculty_id == FacultyModel.id).filter(
        BusStopModel.system_deleted == 0,
        FacultyModel.system_deleted == 0,
        BusStopModel.id != selected_bus_stop_id  # Exclui o ponto de ônibus vinculado ao aluno
    )

    # Verifica o tipo de viagem
    if trip.trip_type == TripTypeEnum.VOLTA:
        # Busca apenas os pontos de ônibus vinculados à viagem em trip_bus_stops
        trip_bus_stops = db.query(TripBusStopModel).filter(
            TripBusStopModel.trip_id == trip.id,
            TripBusStopModel.system_deleted == 0
        ).all()

        # Converte para um dicionário de IDs de pontos de ônibus e seus status
        trip_bus_stop_status = {tbs.bus_stop_id: tbs.status for tbs in trip_bus_stops}

        # Busca todos os pontos de ônibus vinculados a essa viagem, excluindo o ponto selecionado pelo aluno
        bus_stops = base_query.all()

        # Retorna o resultado com o status apropriado
        result = [
            {
                "id": bus_stop.id,
                "name": f"{bus_stop.name} - {faculty.name}",
                "status": TripBusStopStatusEnum(trip_bus_stop_status[bus_stop.id]).label()
                if bus_stop.id in trip_bus_stop_status else "A caminho"
            }
            for bus_stop, faculty in bus_stops
        ]

    elif trip.trip_type == TripTypeEnum.IDA:
        # Para a viagem de ida, o status padrão é "Desembarque"
        trip_bus_stops = db.query(TripBusStopModel).filter(
            TripBusStopModel.trip_id == trip.id,
            TripBusStopModel.system_deleted == 0
        ).all()

        trip_bus_stop_ids = {tbs.bus_stop_id for tbs in trip_bus_stops}

        # Busca todos os pontos de ônibus vinculados a essa viagem
        bus_stops = base_query.all()

        result = [
            {
                "id": bus_stop.id,
                "name": f"{bus_stop.name} - {faculty.name}",
                "status": "Desembarque" if bus_stop.id not in trip_bus_stop_ids else 
                TripBusStopStatusEnum(next(
                    (tbs.status for tbs in trip_bus_stops if tbs.bus_stop_id == bus_stop.id), 
                    TripBusStopStatusEnum.DESENBARQUE.value)).label()
            }
            for bus_stop, faculty in bus_stops
        ]
    else:
        raise HTTPException(status_code=400, detail="Tipo de viagem inválido. Use 'ida' ou 'volta'.")

    # Adiciona lógica para status "A caminho" para pontos não vinculados à viagem na viagem de volta
    if trip.trip_type == TripTypeEnum.VOLTA:
        bus_stops = base_query.all()  # Recupera todos os pontos de ônibus
        result = [
            {
                "id": bus_stop.id,
                "name": f"{bus_stop.name} - {faculty.name}",
                "status": TripBusStopStatusEnum(trip_bus_stop_status.get(bus_stop.id, TripBusStopStatusEnum.A_CAMINHO.value)).label()
            }
            for bus_stop, faculty in bus_stops
        ]

    if not result:
        raise HTTPException(status_code=404, detail="Nenhum ponto de ônibus encontrado")

    return result

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

