from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from ..config.database import get_db
from ..models.trip import Trip as TripModel, TripTypeEnum, TripStatusEnum
from ..models.student_trip import StudentTrip as StudentTripModel, StudentStatusEnum
from ..models.trip_bus_stop import TripBusStop, TripBusStopStatusEnum
from ..models.bus_stop import BusStop
from ..schemas.trip import Trip, TripCreate
from ..models.bus import Bus


router = APIRouter(
    prefix="/trips",
    tags=["Trips"]
)

@router.put("/{trip_id}/report_bus_issue", response_model=Trip)
def report_bus_issue(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip.bus_issue = not trip.bus_issue  # Alterna o estado do problema do ônibus
    db.commit()
    db.refresh(trip)
    return trip

@router.post("/", response_model=Trip)
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    active_trip = db.query(TripModel).filter(
        (TripModel.bus_id == trip.bus_id) | (TripModel.driver_id == trip.driver_id),
        TripModel.status == TripStatusEnum.ATIVA,
        TripModel.system_deleted == int(False)
    ).first()

    if active_trip:
        raise HTTPException(status_code=400, detail="There is already an active trip with this bus or driver.")

    db_trip = TripModel(
        trip_type=trip.trip_type,
        status=TripStatusEnum.ATIVA,
        bus_id=trip.bus_id,
        driver_id=trip.driver_id
    )
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip

@router.put("/{trip_id}/finalizar_ida", response_model=Trip)
def finalizar_viagem_ida(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.status != TripStatusEnum.ATIVA or trip.trip_type != TripTypeEnum.IDA:
        raise HTTPException(status_code=400, detail="Trip is not an active 'ida' trip.")

    trip.status = TripStatusEnum.CONCLUIDA
    db.commit()

    # Create return trip
    return_trip = TripModel(
        trip_type=TripTypeEnum.VOLTA,
        status=TripStatusEnum.ATIVA,
        bus_id=trip.bus_id,
        driver_id=trip.driver_id
    )
    db.add(return_trip)
    db.commit()
    db.refresh(return_trip)

    # Update student trips
    student_trips = db.query(StudentTripModel).filter(StudentTripModel.trip_id == trip.id).all()
    for student_trip in student_trips:
        student_trip.status = StudentStatusEnum.EM_AULA
        db.commit()

        # Add students to the return trip
        db_student_trip = StudentTripModel(
            trip_id=return_trip.id,
            student_id=student_trip.student_id,
            status=StudentStatusEnum.EM_AULA,
            point_id=student_trip.point_id
        )
        db.add(db_student_trip)
        db.commit()
        db.refresh(db_student_trip)

        # Add trip bus stops for return trip
        trip_bus_stop = db.query(TripBusStop).filter(
            TripBusStop.trip_id == return_trip.id,
            TripBusStop.bus_stop_id == student_trip.point_id
        ).first()
        if not trip_bus_stop:
            new_trip_bus_stop = TripBusStop(
                trip_id=return_trip.id,
                bus_stop_id=student_trip.point_id,
                status=TripBusStopStatusEnum.A_CAMINHO
            )
            db.add(new_trip_bus_stop)
            db.commit()
            db.refresh(new_trip_bus_stop)

    # Return the original trip with the new return trip ID
    response = trip.__dict__
    response['new_trip_id'] = return_trip.id

    return response


@router.get("/", response_model=List[Trip])
def read_trips(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    trips = db.query(TripModel).offset(skip).limit(limit).all()
    return trips

@router.get("/{trip_id}", response_model=Trip)
def read_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@router.delete("/{trip_id}", response_model=dict)
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    trip.system_deleted = int(True)
    db.commit()
    return {"status": "deleted"}

@router.put("/{trip_id}/finalizar_volta", response_model=Trip)
def finalizar_viagem_volta(trip_id: int, db: Session = Depends(get_db)):
    # Obter a viagem do banco de dados
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Verificar se a viagem é uma viagem de volta e se está ativa
    if trip.trip_type != TripTypeEnum.VOLTA:
        raise HTTPException(status_code=400, detail="Trip is not a return trip")
    if trip.status != TripStatusEnum.ATIVA:
        raise HTTPException(status_code=400, detail="Trip is not active")

    # Obter todos os pontos de ônibus associados à viagem
    bus_stops = db.query(TripBusStop).filter(TripBusStop.trip_id == trip_id).all()

    # Se não houver registros de trip_bus_stop, finalizar a viagem diretamente
    if not bus_stops:
        trip.status = TripStatusEnum.CONCLUIDA
        db.commit()
        db.refresh(trip)
        return trip

    # Verificar condições de finalização quando há registros de trip_bus_stop
    num_no_ponto = sum(1 for bus_stop in bus_stops if bus_stop.status == TripBusStopStatusEnum.NO_PONTO)
    num_ja_passou = sum(1 for bus_stop in bus_stops if bus_stop.status == TripBusStopStatusEnum.JA_PASSOU)

    if not (num_ja_passou == len(bus_stops) or (num_no_ponto == 1 and num_ja_passou == len(bus_stops) - 1)):
        raise HTTPException(status_code=400, detail="Conditions not met to finalize the trip")

    # Verificar se há alunos com status "Em aula" ou "Aguardando no ponto" em qualquer um dos pontos de ônibus
    for bus_stop in bus_stops:
        students_in_stop = db.query(StudentTripModel).filter(
            StudentTripModel.trip_id == trip_id,
            StudentTripModel.point_id == bus_stop.bus_stop_id,
            StudentTripModel.status.in_([StudentStatusEnum.AGUARDANDO_NO_PONTO, StudentStatusEnum.EM_AULA])
        ).all()

        if students_in_stop:
            print(f"Alunos aguardando ou em aula no ponto {bus_stop.bus_stop_id}: {students_in_stop}")
            raise HTTPException(status_code=400, detail="Cannot finalize the trip while students are still waiting at any bus stop")

    # Definir o status da viagem como "Concluída" se todas as condições forem atendidas
    trip.status = TripStatusEnum.CONCLUIDA
    db.commit()
    db.refresh(trip)

    return trip

@router.get("/active/{driver_id}", response_model=Trip)
def check_active_trip(driver_id: int, db: Session = Depends(get_db)):
    active_trip = db.query(TripModel).filter(
        TripModel.driver_id == driver_id,
        TripModel.status == TripStatusEnum.ATIVA,
        TripModel.system_deleted == 0
    ).first()

    if not active_trip:
        raise HTTPException(status_code=404, detail="No active trip found for this driver.")
    
    return active_trip

@router.get("/{trip_id}/details", response_model=List[dict])
def get_trip_student_details(trip_id: int, db: Session = Depends(get_db)):
    trip_details = db.query(StudentTripModel)\
        .options(
            joinedload(StudentTripModel.student), 
            joinedload(StudentTripModel.bus_stop)
        )\
        .filter(
            StudentTripModel.trip_id == trip_id, 
            StudentTripModel.system_deleted == 0
        ).all()
    
    if not trip_details:
        raise HTTPException(status_code=404, detail="No student trip details found for this trip")

    result = [
        {
            "student_name": detail.student.name,
            "bus_stop_name": detail.bus_stop.name,
            "student_status": StudentStatusEnum(detail.status).label(),
            "profile_picture": detail.student.profile_picture  # Adiciona o campo de imagem do estudante
        } for detail in trip_details
    ]

    print(result)  # Imprime os dados no console para depuração

    return result

@router.get("/{trip_id}/bus_stops", response_model=dict)
def get_trip_bus_stops(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    bus_stops = db.query(
        BusStop.name,
        TripBusStop.status
    ).join(
        TripBusStop, BusStop.id == TripBusStop.bus_stop_id
    ).filter(
        TripBusStop.trip_id == trip_id,
        TripBusStop.system_deleted == 0  # Assume que há uma flag para soft deletion
    ).all()

    if not bus_stops:
        raise HTTPException(status_code=404, detail="No bus stops found for this trip")

    return {
        "bus_issue": trip.bus_issue,  # Flag de problema no ônibus
        "bus_stops": [{"name": name, "status": TripBusStopStatusEnum(status).label()} for name, status in bus_stops]
    }