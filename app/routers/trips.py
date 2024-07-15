from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..config.database import get_db
from ..models.trip import Trip as TripModel, TripTypeEnum, TripStatusEnum
from ..models.student_trip import StudentTrip as StudentTripModel, StudentStatusEnum
from ..models.trip_bus_stop import TripBusStop, TripBusStopStatusEnum
from ..schemas.trip import Trip, TripCreate

router = APIRouter(
    prefix="/trips",
    tags=["Trips"]
)

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

    return trip

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
