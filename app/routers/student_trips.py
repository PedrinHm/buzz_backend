from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from ..config.database import get_db
from ..models.student_trip import StudentTrip as StudentTripModel, StudentStatusEnum
from ..models.trip import Trip as TripModel, TripStatusEnum, TripTypeEnum
from ..models.trip_bus_stop import TripBusStop as TripBusStopModel, TripBusStopStatusEnum
from ..models.bus import Bus as BusModel
from ..schemas.student_trip import StudentTripCreate, StudentTrip, StudentTripUpdate
from typing import List

router = APIRouter(
    prefix="/student_trips",
    tags=["Student Trips"]
)

@router.put("/{student_trip_id}/update_status", response_model=StudentTrip)
def update_student_trip_status(student_trip_id: int, new_status: StudentStatusEnum, db: Session = Depends(get_db)):
    student_trip = db.query(StudentTripModel).filter(StudentTripModel.id == student_trip_id).first()
    if not student_trip:
        raise HTTPException(status_code=404, detail="Student trip not found")

    current_status = StudentStatusEnum(student_trip.status)

    # Define as transições permitidas
    allowed_transitions = {
        StudentStatusEnum.EM_AULA: [StudentStatusEnum.AGUARDANDO_NO_PONTO, StudentStatusEnum.NAO_VOLTARA, StudentStatusEnum.PRESENTE],
        StudentStatusEnum.AGUARDANDO_NO_PONTO: [StudentStatusEnum.PRESENTE, StudentStatusEnum.EM_AULA, StudentStatusEnum.NAO_VOLTARA],
        StudentStatusEnum.NAO_VOLTARA: [StudentStatusEnum.PRESENTE, StudentStatusEnum.EM_AULA, StudentStatusEnum.AGUARDANDO_NO_PONTO],
        StudentStatusEnum.FILA_DE_ESPERA: [StudentStatusEnum.PRESENTE, StudentStatusEnum.EM_AULA, StudentStatusEnum.AGUARDANDO_NO_PONTO, StudentStatusEnum.NAO_VOLTARA]
    }

    # Verifica se a transição é permitida
    if new_status not in allowed_transitions.get(current_status, []):
        raise HTTPException(status_code=400, detail="Status transition not allowed")

    # Verifica a capacidade do ônibus se a transição for de NAO_VOLTARA ou FILA_DE_ESPERA para outro status
    if current_status in [StudentStatusEnum.NAO_VOLTARA, StudentStatusEnum.FILA_DE_ESPERA] and new_status != current_status:
        if not check_capacity(student_trip.trip_id, db):
            raise HTTPException(status_code=400, detail="Bus capacity exceeded")

    # Atualiza o status do aluno
    student_trip.status = new_status
    db.commit()
    db.refresh(student_trip)
    return student_trip
    
def check_capacity(trip_id: int, db: Session) -> bool:
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    bus = db.query(BusModel).filter(BusModel.id == trip.bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    capacity = db.query(StudentTripModel).filter(
        StudentTripModel.trip_id == trip_id,
        StudentTripModel.status.notin_([StudentStatusEnum.NAO_VOLTARA, StudentStatusEnum.FILA_DE_ESPERA])
    ).count()
    bus_capacity = bus.capacity 
    return capacity < bus_capacity

@router.post("/", response_model=StudentTrip)
def create_student_trip(student_trip: StudentTripCreate, db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(TripModel.id == student_trip.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Verificar se o aluno já está cadastrado na viagem
    existing_trip = db.query(StudentTripModel).filter(
        StudentTripModel.trip_id == student_trip.trip_id,
        StudentTripModel.student_id == student_trip.student_id
    ).first()
    if existing_trip:
        raise HTTPException(status_code=400, detail="Aluno já cadastrado nesta viagem")
    
    # Verificar capacidade do ônibus
    if not check_capacity(trip.id, db):
        raise HTTPException(status_code=400, detail="Capacidade do ônibus atingida")
    
    # Criar a viagem do estudante
    db_student_trip = StudentTripModel(
        trip_id=student_trip.trip_id,
        student_id=student_trip.student_id,
        status=StudentStatusEnum.PRESENTE if trip.trip_type == TripTypeEnum.IDA else StudentStatusEnum.EM_AULA,
        point_id=student_trip.point_id
    )
    db.add(db_student_trip)
    db.commit()
    db.refresh(db_student_trip)
    
    # Criar ou atualizar TripBusStop
    trip_bus_stop = db.query(TripBusStopModel).filter(
        TripBusStopModel.trip_id == trip.id,
        TripBusStopModel.bus_stop_id == student_trip.point_id
    ).first()
    
    if not trip_bus_stop:
        new_trip_bus_stop = TripBusStopModel(
            trip_id=trip.id,
            bus_stop_id=student_trip.point_id,
            status=TripBusStopStatusEnum.DESENBARQUE if trip.trip_type == TripTypeEnum.IDA else TripBusStopStatusEnum.A_CAMINHO
        )
        db.add(new_trip_bus_stop)
        db.commit()

    return db_student_trip


@router.get("/", response_model=List[StudentTrip])
def read_student_trips(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    student_trips = db.query(StudentTripModel).offset(skip).limit(limit).all()
    return student_trips

@router.get("/{student_trip_id}", response_model=StudentTrip)
def read_student_trip(student_trip_id: int, db: Session = Depends(get_db)):
    student_trip = db.query(StudentTripModel).filter(StudentTripModel.id == student_trip_id).first()
    if not student_trip:
        raise HTTPException(status_code=404, detail="Student trip not found")
    return student_trip

@router.delete("/{student_trip_id}", response_model=dict)
def delete_student_trip(student_trip_id: int, db: Session = Depends(get_db)):
    student_trip = db.query(StudentTripModel).filter(StudentTripModel.id == student_trip_id).first()
    if not student_trip:
        raise HTTPException(status_code=404, detail="Student trip not found")
    db.delete(student_trip)
    db.commit()
    return {"status": "deleted"}

@router.put("/{student_trip_id}/update_point", response_model=StudentTrip)
def update_student_trip_point(student_trip_id: int, point_id: int, db: Session = Depends(get_db)):
    student_trip = db.query(StudentTripModel).filter(StudentTripModel.id == student_trip_id).first()
    if not student_trip:
        raise HTTPException(status_code=404, detail="Student trip not found")
    
    trip_bus_stop = db.query(TripBusStopModel).filter(
        TripBusStopModel.trip_id == student_trip.trip_id,
        TripBusStopModel.bus_stop_id == point_id
    ).first()

    if trip_bus_stop and trip_bus_stop.status == TripBusStopStatusEnum.JA_PASSOU:
        raise HTTPException(status_code=400, detail="Bus stop has already passed")

    student_trip.point_id = point_id
    db.commit()
    db.refresh(student_trip)
    return student_trip

@router.put("/{student_trip_id}/update_trip", response_model=StudentTrip)
def update_student_trip(student_trip_id: int, new_trip_id: int, db: Session = Depends(get_db)):
    student_trip = db.query(StudentTripModel).filter(StudentTripModel.id == student_trip_id).first()
    if not student_trip:
        raise HTTPException(status_code=404, detail="Student trip not found")

    new_trip = db.query(TripModel).filter(TripModel.id == new_trip_id).first()
    if not new_trip:
        raise HTTPException(status_code=404, detail="New trip not found")

    if new_trip.status != TripStatusEnum.ATIVA:
        raise HTTPException(status_code=400, detail="New trip is not active")

    if not check_capacity(new_trip.id, db):
        raise HTTPException(status_code=400, detail="New trip is full")

    trip_bus_stop = db.query(TripBusStopModel).filter(
        TripBusStopModel.trip_id == new_trip.id,
        TripBusStopModel.bus_stop_id == student_trip.point_id
    ).first()

    if trip_bus_stop and trip_bus_stop.status == TripBusStopStatusEnum.JA_PASSOU:
        raise HTTPException(status_code=400, detail="Bus stop has already passed")

    student_trip.trip_id = new_trip.id
    db.commit()
    db.refresh(student_trip)
    return student_trip

@router.get("/active/{student_id}", response_model=dict)
async def get_active_trip(student_id: int, db: Session = Depends(get_db)):
    active_trip = db.query(StudentTripModel)\
        .join(TripModel)\
        .options(joinedload(StudentTripModel.trip))\
        .filter(
            StudentTripModel.student_id == student_id,
            TripModel.status == TripStatusEnum.ATIVA
        )\
        .first()

    if not active_trip:
        raise HTTPException(status_code=404, detail="No active trip found for this student")
    
    # Retorna o student_trip_id junto com os outros detalhes
    return {
        "student_trip_id": active_trip.id,  # Adiciona o ID do student_trip
        "trip_id": active_trip.trip.id,
        "trip_type": TripTypeEnum(active_trip.trip.trip_type).name,
        "trip_status": TripStatusEnum(active_trip.trip.status).name
    }
