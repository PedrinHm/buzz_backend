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

@router.put("/{trip_id}/finalizar_ida")
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

    student_trips = db.query(StudentTripModel).filter(StudentTripModel.trip_id == trip.id).all()
    for student_trip in student_trips:
        if student_trip.status == StudentStatusEnum.FILA_DE_ESPERA:
            student_trip.status = StudentStatusEnum.FILA_DE_ESPERA
        else:
            student_trip.status = StudentStatusEnum.EM_AULA
        db.commit()

        db_student_trip = StudentTripModel(
            trip_id=return_trip.id,
            student_id=student_trip.student_id,
            status=student_trip.status, 
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

    response = {
        "trip": {
            "trip_type": trip.trip_type,
            "status": trip.status,
            "bus_id": trip.bus_id,
            "driver_id": trip.driver_id,
            "bus_issue": trip.bus_issue,
            "id": trip.id,
            "system_deleted": trip.system_deleted,
            "update_date": trip.update_date,
            "create_date": trip.create_date
        },
        "new_trip_id": return_trip.id
    }

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
    print(f"Recebido trip_id: {trip_id}")
    
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    print(f"Trip encontrada: {trip}")

    if not trip:
        print("Viagem não encontrada")
        raise HTTPException(status_code=404, detail="Trip not found")

    print(f"Tipo da viagem: {trip.trip_type}, Status da viagem: {trip.status}")

    if trip.trip_type != TripTypeEnum.VOLTA:
        print("Viagem não é do tipo VOLTA")
        raise HTTPException(status_code=400, detail="Trip is not a return trip")
    if trip.status != TripStatusEnum.ATIVA:
        print("Viagem não está ativa")
        raise HTTPException(status_code=400, detail="Trip is not active")

    bus_stops = db.query(TripBusStop).filter(TripBusStop.trip_id == trip_id).all()
    print(f"Paradas de ônibus encontradas: {bus_stops}")

    if not bus_stops:
        print("Nenhuma parada de ônibus encontrada, finalizando viagem")
        trip.status = TripStatusEnum.CONCLUIDA
        db.commit()
        db.refresh(trip)
        print(f"Viagem {trip_id} concluída")
        return trip

    filtered_bus_stops = []
    for bus_stop in bus_stops:
        students_in_stop = db.query(StudentTripModel).filter(
            StudentTripModel.trip_id == trip_id,
            StudentTripModel.point_id == bus_stop.bus_stop_id,
            StudentTripModel.status.in_([
                StudentStatusEnum.PRESENTE,
                StudentStatusEnum.EM_AULA,
                StudentStatusEnum.AGUARDANDO_NO_PONTO
            ])
        ).all()

        print(f"Parada de ônibus {bus_stop.id}: Alunos na parada: {students_in_stop}")

        if students_in_stop:
            filtered_bus_stops.append(bus_stop)

    print(f"Filtered bus stops: {filtered_bus_stops}")

    # Novo código: Verificar se ainda há alunos presentes ou aguardando nas paradas
    if any(filtered_bus_stops):
        print("Ainda há alunos presentes nas paradas, não é possível finalizar a viagem.")
        raise HTTPException(status_code=400, detail="Ainda há alunos presentes ou aguardando no ponto")

    print("Nenhuma parada de ônibus com alunos presentes, finalizando viagem")
    trip.status = TripStatusEnum.CONCLUIDA
    db.commit()
    db.refresh(trip)
    print(f"Viagem {trip_id} concluída")
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

    # Lista de status permitidos para os alunos
    allowed_student_statuses = [
        StudentStatusEnum.PRESENTE,
        StudentStatusEnum.EM_AULA,
        StudentStatusEnum.AGUARDANDO_NO_PONTO
    ]

    # Consulta para buscar as paradas de ônibus que possuem alunos com status permitido e o mesmo trip_id
    bus_stops = db.query(
        BusStop.name,
        TripBusStop.status
    ).join(
        TripBusStop, BusStop.id == TripBusStop.bus_stop_id
    ).join(
        StudentTripModel, StudentTripModel.point_id == TripBusStop.bus_stop_id
    ).filter(
        TripBusStop.trip_id == trip_id,  # Garante que o trip_id seja o mesmo em TripBusStop
        StudentTripModel.trip_id == trip_id,  # Garante que o trip_id seja o mesmo em StudentTripModel
        TripBusStop.system_deleted == 0,  # Filtra apenas paradas não deletadas
        StudentTripModel.status.in_(allowed_student_statuses),  # Verifica os status dos alunos
        StudentTripModel.system_deleted == 0  # Filtra apenas student_trips não deletados
    ).distinct().all()  # Usando distinct() para evitar duplicatas

    if not bus_stops:
        raise HTTPException(status_code=404, detail="No bus stops found for this trip")

    return {
        "bus_issue": trip.bus_issue,  # Flag de problema no ônibus
        "bus_stops": [{"name": name, "status": TripBusStopStatusEnum(status).label()} for name, status in bus_stops]
    }

@router.delete("/{trip_id}/cancel", response_model=dict)
def cancel_trip(trip_id: int, db: Session = Depends(get_db)):
    # Verificar se a viagem existe
    trip = db.query(TripModel).filter(TripModel.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Verificar se existem registros vinculados à viagem em 'student_trip' e 'trip_bus_stop' com system_deleted = 0
    active_student_trips = db.query(StudentTripModel).filter(
        StudentTripModel.trip_id == trip_id,
        StudentTripModel.system_deleted == 0
    ).first()

    active_trip_bus_stops = db.query(TripBusStop).filter(
        TripBusStop.trip_id == trip_id,
        TripBusStop.system_deleted == 0
    ).first()

    # Se houver registros ativos vinculados à viagem, não permitir o cancelamento
    if active_student_trips or active_trip_bus_stops:
        raise HTTPException(status_code=400, detail="Cannot cancel trip with active student or bus stop records")

    # Marcar a viagem como cancelada (atualizar o campo system_deleted)
    trip.system_deleted = 1
    db.commit()

    return {"status": "Trip canceled successfully"}
