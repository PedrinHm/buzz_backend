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
        raise HTTPException(status_code=404, detail="Parada de ônibus da viagem não encontrada ou foi excluída")

    # Validações de status
    if db_trip_bus_stop.status == TripBusStopStatusEnum.A_CAMINHO:
        if trip_bus_stop.status not in [TripBusStopStatusEnum.NO_PONTO, TripBusStopStatusEnum.PROXIMO_PONTO, TripBusStopStatusEnum.ONIBUS_COM_PROBLEMA]:
            raise HTTPException(status_code=400, detail="Transição de status inválida")
    elif db_trip_bus_stop.status == TripBusStopStatusEnum.NO_PONTO:
        if trip_bus_stop.status not in [TripBusStopStatusEnum.JA_PASSOU, TripBusStopStatusEnum.ONIBUS_COM_PROBLEMA]:
            raise HTTPException(status_code=400, detail="Transição de status inválida")
    elif db_trip_bus_stop.status == TripBusStopStatusEnum.PROXIMO_PONTO:
        if trip_bus_stop.status not in [TripBusStopStatusEnum.NO_PONTO, TripBusStopStatusEnum.ONIBUS_COM_PROBLEMA]:
            raise HTTPException(status_code=400, detail="Transição de status inválida")
    elif db_trip_bus_stop.status == TripBusStopStatusEnum.JA_PASSOU:
        raise HTTPException(status_code=400, detail="O status não pode ser alterado de JA_PASSOU")
    elif db_trip_bus_stop.status == TripBusStopStatusEnum.ONIBUS_COM_PROBLEMA:
        if trip_bus_stop.status not in [TripBusStopStatusEnum.A_CAMINHO, TripBusStopStatusEnum.NO_PONTO, TripBusStopStatusEnum.PROXIMO_PONTO, TripBusStopStatusEnum.JA_PASSOU]:
            raise HTTPException(status_code=400, detail="Transição de status inválida")

    # Verificação de status dos alunos antes de atualizar o status do ponto de ônibus
    if trip_bus_stop.status == TripBusStopStatusEnum.JA_PASSOU:
        students = db.query(StudentTripModel).filter(
            StudentTripModel.trip_id == db_trip_bus_stop.trip_id,
            StudentTripModel.point_id == db_trip_bus_stop.bus_stop_id
        ).all()
        for student in students:
            if student.status in (StudentStatusEnum.AGUARDANDO_NO_PONTO, StudentStatusEnum.EM_AULA):
                raise HTTPException(status_code=400, detail="Nem todos os alunos embarcaram no ônibus")

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
        raise HTTPException(status_code=404, detail="Parada de ônibus da viagem não encontrada ou foi excluída")
    return trip_bus_stop

@router.delete("/{trip_bus_stop_id}", response_model=dict)
def delete_trip_bus_stop(trip_bus_stop_id: int, db: Session = Depends(get_db)):
    trip_bus_stop = db.query(TripBusStopModel).filter(TripBusStopModel.id == trip_bus_stop_id).first()
    if not trip_bus_stop:
        raise HTTPException(status_code=404, detail="Parada de ônibus da viagem não encontrada")
    trip_bus_stop.system_deleted = 1
    db.commit()
    return {"status": "excluído"}

@router.put("/update_next_bus_stop/{trip_id}", response_model=TripBusStop)
def update_next_to_at_stop(trip_id: int, db: Session = Depends(get_db)):
    # Encontre o ponto de ônibus que está como "Próximo ponto"
    db_trip_bus_stop = db.query(TripBusStopModel).filter(
        TripBusStopModel.trip_id == trip_id,
        TripBusStopModel.status == TripBusStopStatusEnum.PROXIMO_PONTO,
        TripBusStopModel.system_deleted == 0
    ).first()

    if not db_trip_bus_stop:
        raise HTTPException(status_code=404, detail="Nenhuma parada de ônibus com status 'Próximo ponto' encontrada para esta viagem")

    # Atualize o status para "No ponto"
    db_trip_bus_stop.status = TripBusStopStatusEnum.NO_PONTO
    db.commit()
    db.refresh(db_trip_bus_stop)
    
    return db_trip_bus_stop

@router.put("/select_next_stop/{trip_id}", response_model=TripBusStop)
def select_next_stop(trip_id: int, new_stop_id: int, db: Session = Depends(get_db)):
    # Obter o ponto atual com status "No ponto"
    current_stop = db.query(TripBusStopModel).filter(
        TripBusStopModel.trip_id == trip_id,
        TripBusStopModel.status == TripBusStopStatusEnum.NO_PONTO,
        TripBusStopModel.system_deleted == 0
    ).first()

    # Caso exista um ponto com status "No ponto", execute a lógica
    if current_stop:
        # Verificar se há alunos com status "Em aula" ou "Aguardando no ponto" no ponto atual
        students_in_current_stop = db.query(StudentTripModel).filter(
            StudentTripModel.trip_id == trip_id,
            StudentTripModel.point_id == current_stop.bus_stop_id,
            StudentTripModel.status.in_([StudentStatusEnum.AGUARDANDO_NO_PONTO, StudentStatusEnum.EM_AULA])
        ).all()

        if students_in_current_stop:
            raise HTTPException(status_code=400, detail="Não é possível prosseguir para a próxima parada enquanto há alunos aguardando na parada atual")

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
        raise HTTPException(status_code=404, detail="Nova parada de ônibus não encontrada")

    new_stop.status = TripBusStopStatusEnum.PROXIMO_PONTO
    db.commit()
    db.refresh(new_stop)

    return new_stop


@router.get("/stops_on_the_way/{trip_id}", response_model=List[dict])
def get_stops_on_the_way(trip_id: int, db: Session = Depends(get_db)):
    # Lista de status permitidos para os alunos
    allowed_student_statuses = [
        StudentStatusEnum.PRESENTE,
        StudentStatusEnum.EM_AULA,
        StudentStatusEnum.AGUARDANDO_NO_PONTO
    ]

    # Consulta para buscar as paradas de ônibus que estão "A caminho" e possuem alunos com status permitido
    stops_on_the_way = db.query(TripBusStopModel).options(
        joinedload(TripBusStopModel.bus_stop)  # Fazendo o join com a tabela de pontos de ônibus
    ).join(
        StudentTripModel, StudentTripModel.point_id == TripBusStopModel.bus_stop_id
    ).filter(
        TripBusStopModel.trip_id == trip_id,  # Garante que o trip_id seja o mesmo em TripBusStop
        StudentTripModel.trip_id == trip_id,  # Garante que o trip_id seja o mesmo em StudentTripModel
        TripBusStopModel.status == TripBusStopStatusEnum.A_CAMINHO,
        TripBusStopModel.system_deleted == 0,  # Filtra apenas paradas não deletadas
        StudentTripModel.status.in_(allowed_student_statuses),  # Verifica os status dos alunos
        StudentTripModel.system_deleted == 0  # Filtra apenas student_trips não deletados
    ).distinct().all()  # Usando distinct() para evitar duplicatas

    if not stops_on_the_way:
        raise HTTPException(status_code=404, detail="Nenhuma parada no caminho encontrada")

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


@router.put("/finalize_current_stop/{trip_id}", response_model=TripBusStop)
def finalize_current_stop(trip_id: int, db: Session = Depends(get_db)):
    # Obter o ponto atual com status "No ponto"
    current_stop = db.query(TripBusStopModel).filter(
        TripBusStopModel.trip_id == trip_id,
        TripBusStopModel.status == TripBusStopStatusEnum.NO_PONTO,
        TripBusStopModel.system_deleted == 0
    ).first()

    if not current_stop:
        raise HTTPException(status_code=404, detail="Nenhuma parada de ônibus com status 'No ponto' encontrada")

    # Verificar se há alunos com status "Em aula" ou "Aguardando no ponto" no ponto atual
    students_in_current_stop = db.query(StudentTripModel).filter(
        StudentTripModel.trip_id == trip_id,
        StudentTripModel.point_id == current_stop.bus_stop_id,
        StudentTripModel.status.in_([StudentStatusEnum.AGUARDANDO_NO_PONTO, StudentStatusEnum.EM_AULA])
    ).all()

    if students_in_current_stop:
        print(f"Alunos aguardando ou em aula: {students_in_current_stop}")
        raise HTTPException(status_code=400, detail="Não é possível finalizar a parada enquanto há alunos aguardando na parada atual")

    # Definir o status do ponto atual como "Já passou"
    current_stop.status = TripBusStopStatusEnum.JA_PASSOU
    db.commit()
    db.refresh(current_stop)

    return current_stop
