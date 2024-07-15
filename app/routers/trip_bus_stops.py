from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..models.trip_bus_stop import TripBusStop as TripBusStopModel, TripBusStopStatusEnum
from ..schemas.trip_bus_stop import TripBusStopUpdate, TripBusStop
from ..models.student_trip import StudentTrip as StudentTripModel, StudentStatusEnum

router = APIRouter(
    prefix="/trip_bus_stops",
    tags=["Trip Bus Stops"]
)

@router.put("/{trip_bus_stop_id}", response_model=TripBusStop)
def update_trip_bus_stop_status(trip_bus_stop_id: int, trip_bus_stop: TripBusStopUpdate, db: Session = Depends(get_db)):
    db_trip_bus_stop = db.query(TripBusStopModel).filter(TripBusStopModel.id == trip_bus_stop_id).first()
    if not db_trip_bus_stop:
        raise HTTPException(status_code=404, detail="Trip Bus Stop not found")

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
        raise HTTPException(status_code=400, detail="Ônibus já passou por esse ponto de ônibus.")
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
