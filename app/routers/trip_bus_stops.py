from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..config.database import get_db
from ..models.trip_bus_stop import TripBusStop as TripBusStopModel, TripBusStopStatusEnum
from ..schemas.trip_bus_stop import TripBusStopUpdate, TripBusStop
from ..models.student_trip import StudentTrip as StudentTripModel, StudentStatusEnum
from typing import List

router = APIRouter(
    prefix="/trip_bus_stops",
    tags=["Trip Bus Stops"]
)

@router.put("/{trip_bus_stop_id}", response_model=TripBusStop)
def update_trip_bus_stop_status(trip_bus_stop_id: int, trip_bus_stop: TripBusStopUpdate, db: Session = Depends(get_db)):
    db_trip_bus_stop = db.query(TripBusStopModel).filter(
        TripBusStopModel.id == trip_bus_stop_id,
        TripBusStopModel.system_deleted == 0
    ).first()
    if not db_trip_bus_stop:
        raise HTTPException(status_code=404, detail="Trip Bus Stop not found or has been deleted")

    # Validações de status
    if db_trip_bus_stop.status == TripBusStopStatusEnum.A_CAMINHO:
        if trip_bus_stop.status not in [TripBusStopStatusEnum.NO_PONTO, TripBusStopStatusEnum.PROXIMO_PONTO, TripBusStopStatusEnum.ONIBUS_COM_PROBLEMA]:
            raise HTTPException(status_code=400, detail="Invalid status transition")
    elif db_trip_bus_stop.status == TripBusStopStatusEnum.NO_PONTO:
        if trip_bus_stop.status not in [TripBusStopStatusEnum.JA_PASSOU, TripBusStopStatusEnum.ONIBUS_COM_PROBLEMA]:
            raise HTTPException(status_code=400, detail="Invalid status transition")
    elif db_trip_bus_stop.status == TripBusStopStatusEnum.PROXIMO_PONTO:
        if trip_bus_stop.status not in [TripBusStopStatusEnum.NO_PONTO, TripBusStopStatusEnum.ONIBUS_COM_PROBLEMA]:
            raise HTTPException(status_code=400, detail="Invalid status transition")
    elif db_trip_bus_stop.status == TripBusStopStatusEnum.JA_PASSOU:
        raise HTTPException(status_code=400, detail="Status cannot be changed from JA_PASSOU")
    elif db_trip_bus_stop.status == TripBusStopStatusEnum.ONIBUS_COM_PROBLEMA:
        if trip_bus_stop.status not in [TripBusStopStatusEnum.A_CAMINHO, TripBusStopStatusEnum.NO_PONTO, TripBusStopStatusEnum.PROXIMO_PONTO, TripBusStopStatusEnum.JA_PASSOU]:
            raise HTTPException(status_code=400, detail="Invalid status transition")

    # Verificação de status dos alunos antes de atualizar o status do ponto de ônibus
    if trip_bus_stop.status == TripBusStopStatusEnum.JA_PASSOU:
        students = db.query(StudentTripModel).filter(
            StudentTripModel.trip_id == db_trip_bus_stop.trip_id,
            StudentTripModel.point_id == db_trip_bus_stop.bus_stop_id
        ).all()
        for student in students:
            if student.status in (StudentStatusEnum.AGUARDANDO_NO_PONTO, StudentStatusEnum.EM_AULA):
                raise HTTPException(status_code=400, detail="Not all students have boarded the bus")

    db_trip_bus_stop.status = trip_bus_stop.status
    db.commit()
    db.refresh(db_trip_bus_stop)
    return db_trip_bus_stop

@router.get("/", response_model=List[TripBusStop])
def read_trip_bus_stops(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    trip_bus_stops = db.query(TripBusStopModel).filter(TripBusStopModel.system_deleted == 0).offset(skip).limit(limit).all()
    return trip_bus_stops

@router.get("/{trip_bus_stop_id}", response_model=TripBusStop)
def read_trip_bus_stop(trip_bus_stop_id: int, db: Session = Depends(get_db)):
    trip_bus_stop = db.query(TripBusStopModel).filter(
        TripBusStopModel.id == trip_bus_stop_id,
        TripBusStopModel.system_deleted == 0
    ).first()
    if not trip_bus_stop:
        raise HTTPException(status_code=404, detail="Trip Bus Stop not found or has been deleted")
    return trip_bus_stop

@router.delete("/{trip_bus_stop_id}", response_model=dict)
def delete_trip_bus_stop(trip_bus_stop_id: int, db: Session = Depends(get_db)):
    trip_bus_stop = db.query(TripBusStopModel).filter(TripBusStopModel.id == trip_bus_stop_id).first()
    if not trip_bus_stop:
        raise HTTPException(status_code=404, detail="Trip Bus Stop not found")
    trip_bus_stop.system_deleted = 1
    db.commit()
    return {"status": "deleted"}

@router.put("/atualizar_proximo_para_no_ponto/{trip_id}", response_model=TripBusStop)
def update_next_to_at_stop(trip_id: int, db: Session = Depends(get_db)):
    # Encontre o ponto de ônibus que está como "Próximo ponto"
    db_trip_bus_stop = db.query(TripBusStopModel).filter(
        TripBusStopModel.trip_id == trip_id,
        TripBusStopModel.status == TripBusStopStatusEnum.PROXIMO_PONTO,
        TripBusStopModel.system_deleted == 0
    ).first()

    if not db_trip_bus_stop:
        raise HTTPException(status_code=404, detail="No bus stop with status 'Próximo ponto' found for this trip")

    # Atualize o status para "No ponto"
    db_trip_bus_stop.status = TripBusStopStatusEnum.NO_PONTO
    db.commit()
    db.refresh(db_trip_bus_stop)
    
    return db_trip_bus_stop

@router.put("/selecionar_proximo_ponto/{trip_id}", response_model=TripBusStop)
def select_next_stop(trip_id: int, new_stop_id: int, db: Session = Depends(get_db)):
    # Obter o ponto atual com status "No ponto"
    current_stop = db.query(TripBusStopModel).filter(
        TripBusStopModel.trip_id == trip_id,
        TripBusStopModel.status == TripBusStopStatusEnum.NO_PONTO,
        TripBusStopModel.system_deleted == 0
    ).first()

    if not current_stop:
        raise HTTPException(status_code=404, detail="No bus stop with status 'No ponto' found")

    # Verificar se há alunos com status "Em aula" ou "Aguardando no ponto" no ponto atual
    students_in_current_stop = db.query(StudentTripModel).filter(
        StudentTripModel.trip_id == trip_id,
        StudentTripModel.point_id == current_stop.bus_stop_id,
        StudentTripModel.status.in_([StudentStatusEnum.AGUARDANDO_NO_PONTO, StudentStatusEnum.EM_AULA])
    ).all()

    if students_in_current_stop:
        raise HTTPException(status_code=400, detail="Cannot proceed to the next stop while students are still waiting at the current stop")

    # Definir o status do ponto atual como "Já passou"
    current_stop.status = TripBusStopStatusEnum.JA_PASSOU
    db.commit()

    # Definir o status do novo ponto como "Próximo ponto"
    new_stop = db.query(TripBusStopModel).filter(
        TripBusStopModel.id == new_stop_id,
        TripBusStopModel.trip_id == trip_id,
        TripBusStopModel.system_deleted == 0
    ).first()

    if not new_stop:
        raise HTTPException(status_code=404, detail="New bus stop not found")

    new_stop.status = TripBusStopStatusEnum.PROXIMO_PONTO
    db.commit()
    db.refresh(new_stop)

    return new_stop

@router.get("/pontos_a_caminho/{trip_id}", response_model=List[dict])
def get_stops_on_the_way(trip_id: int, db: Session = Depends(get_db)):
    stops_on_the_way = db.query(TripBusStopModel).options(
        joinedload(TripBusStopModel.bus_stop)  # Fazendo o join com a tabela de pontos de ônibus
    ).filter(
        TripBusStopModel.trip_id == trip_id,
        TripBusStopModel.status == TripBusStopStatusEnum.A_CAMINHO,
        TripBusStopModel.system_deleted == 0
    ).all()

    if not stops_on_the_way:
        raise HTTPException(status_code=404, detail="No stops on the way found")

    # Transformando o resultado para incluir o nome do ponto de ônibus
    result = [
        {
            "trip_id": stop.trip_id,
            "bus_stop_id": stop.bus_stop_id,
            "status": stop.status,
            "id": stop.id,
            "name": stop.bus_stop.name  # Incluindo o nome do ponto de ônibus
        } for stop in stops_on_the_way
    ]

    return result

@router.put("/finalizar_ponto_atual/{trip_id}", response_model=TripBusStop)
def finalize_current_stop(trip_id: int, db: Session = Depends(get_db)):
    # Obter o ponto atual com status "No ponto"
    current_stop = db.query(TripBusStopModel).filter(
        TripBusStopModel.trip_id == trip_id,
        TripBusStopModel.status == TripBusStopStatusEnum.NO_PONTO,
        TripBusStopModel.system_deleted == 0
    ).first()

    if not current_stop:
        raise HTTPException(status_code=404, detail="No bus stop with status 'No ponto' found")

    # Verificar se há alunos com status "Em aula" ou "Aguardando no ponto" no ponto atual
    students_in_current_stop = db.query(StudentTripModel).filter(
        StudentTripModel.trip_id == trip_id,
        StudentTripModel.point_id == current_stop.bus_stop_id,
        StudentTripModel.status.in_([StudentStatusEnum.AGUARDANDO_NO_PONTO, StudentStatusEnum.EM_AULA])
    ).all()

    if students_in_current_stop:
        print(f"Alunos aguardando ou em aula: {students_in_current_stop}")
        raise HTTPException(status_code=400, detail="Cannot finalize the stop while students are still waiting at the current stop")

    # Definir o status do ponto atual como "Já passou"
    current_stop.status = TripBusStopStatusEnum.JA_PASSOU
    db.commit()
    db.refresh(current_stop)

    return current_stop

