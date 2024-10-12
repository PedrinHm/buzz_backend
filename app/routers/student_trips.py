from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from ..config.database import get_db
from ..models.student_trip import StudentTrip as StudentTripModel, StudentStatusEnum
from ..models.trip import Trip as TripModel, TripStatusEnum, TripTypeEnum
from ..models.trip_bus_stop import TripBusStop as TripBusStopModel, TripBusStopStatusEnum
from ..models.bus import Bus as BusModel
from ..models.user import User  
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

    # Se o novo status for "NAO_VOLTARA", enviar notificação para os alunos na "FILA_DE_ESPERA"
    if new_status == StudentStatusEnum.NAO_VOLTARA:
        notify_students_in_waiting_list(student_trip.trip_id, db)

    # Atualiza o status do aluno
    student_trip.status = new_status
    db.commit()
    db.refresh(student_trip)
    return student_trip

def notify_students_in_waiting_list(trip_id: int, db: Session):
    students_in_waiting_list = db.query(StudentTripModel).filter(
        StudentTripModel.trip_id == trip_id,
        StudentTripModel.status == StudentStatusEnum.FILA_DE_ESPERA
    ).all()

    for student in students_in_waiting_list:
        user = db.query(User).filter(User.id == student.student_id).first()
        if user and user.device_token:
            # Envia a notificação para o aluno com status "FILA_DE_ESPERA"
            title = "Vaga disponível!"
            message = "Uma vaga no ônibus foi liberada. Verifique se você pode ser alocado."
            notify_user(user.device_token, title, message)

    
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
def create_student_trip(student_trip: StudentTripCreate, db: Session = Depends(get_db), waitlist: bool = False):
    print("Iniciando a criação do student_trip...")

    trip = db.query(TripModel).filter(TripModel.id == student_trip.trip_id).first()
    if not trip:
        print("Erro: Trip not found")
        raise HTTPException(status_code=404, detail="Trip not found")
    
    print("Viagem encontrada. Verificando se o aluno já está cadastrado...")
    # Verificar se o aluno já está cadastrado na viagem
    existing_trip = db.query(StudentTripModel).filter(
        StudentTripModel.trip_id == student_trip.trip_id,
        StudentTripModel.student_id == student_trip.student_id
    ).first()
    if existing_trip:
        print("Erro: Aluno já cadastrado nesta viagem")
        raise HTTPException(status_code=400, detail="Aluno já cadastrado nesta viagem")
    
    print("Aluno não está cadastrado na viagem. Verificando a capacidade do ônibus...")
    # Verificar capacidade do ônibus e adicionar à fila de espera se necessário
    if not check_capacity(trip.id, db):
        print("Capacidade do ônibus atingida.")
        if waitlist:
            print("Aluno será colocado na fila de espera.")
            # Coloca o aluno na fila de espera se a capacidade estiver cheia
            student_status = StudentStatusEnum.FILA_DE_ESPERA
        else:
            print("Erro: Capacidade do onibus atingida.")
            raise HTTPException(status_code=400, detail="Capacidade do onibus atingida")
    else:
        print("Capacidade do ônibus disponível. Aluno será adicionado com status inicial.")
        # Define o status inicial com base no tipo da viagem
        student_status = StudentStatusEnum.PRESENTE if trip.trip_type == TripTypeEnum.IDA else StudentStatusEnum.EM_AULA
    
    print("Criando a viagem do estudante...")
    # Criar a viagem do estudante com o status apropriado
    db_student_trip = StudentTripModel(
        trip_id=student_trip.trip_id,
        student_id=student_trip.student_id,
        status=student_status,
        point_id=student_trip.point_id
    )
    db.add(db_student_trip)
    db.commit()
    db.refresh(db_student_trip)
    
    print("Criando ou atualizando TripBusStop...")
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

    print("Student trip criado com sucesso!")
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
    # Busca o registro de viagem do estudante
    student_trip = db.query(StudentTripModel).filter(StudentTripModel.id == student_trip_id).first()
    if not student_trip:
        raise HTTPException(status_code=404, detail="Student trip not found")
    
    # Busca os detalhes da viagem do estudante
    trip = db.query(TripModel).filter(TripModel.id == student_trip.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Armazena o ponto anterior
    old_point_id = student_trip.point_id

    # Verifica se o novo ponto de ônibus já existe na tabela trip_bus_stop para essa viagem
    trip_bus_stop = db.query(TripBusStopModel).filter(
        TripBusStopModel.trip_id == student_trip.trip_id,
        TripBusStopModel.bus_stop_id == point_id
    ).first()

    # Se o ponto já existe e estava deletado (system_deleted = 1), reativa o ponto
    if trip_bus_stop and trip_bus_stop.system_deleted == 1:
        print(f"Reactivating bus stop {point_id} for trip {student_trip.trip_id}")
        trip_bus_stop.system_deleted = 0
        db.commit()
        db.refresh(trip_bus_stop)

    # Se o ponto de ônibus já passou, lança exceção
    elif trip_bus_stop and trip_bus_stop.status == TripBusStopStatusEnum.JA_PASSOU:
        raise HTTPException(status_code=400, detail="Bus stop has already passed")

    # Define o status padrão dependendo do tipo da viagem
    elif not trip_bus_stop:
        status_padrao = TripBusStopStatusEnum.DESENBARQUE if trip.trip_type == TripTypeEnum.IDA else TripBusStopStatusEnum.A_CAMINHO
        
        # Cria um novo registro na tabela trip_bus_stop
        new_trip_bus_stop = TripBusStopModel(
            trip_id=student_trip.trip_id,
            bus_stop_id=point_id,
            status=status_padrao,  # Define o status padrão baseado no tipo da viagem
            system_deleted=0  # Marca o novo ponto como ativo
        )
        db.add(new_trip_bus_stop)
        db.commit()
        db.refresh(new_trip_bus_stop)

    # Atualiza o ponto de ônibus no registro de viagem do estudante
    student_trip.point_id = point_id
    db.commit()
    db.refresh(student_trip)

    # Verifica se há outros estudantes vinculados ao ponto anterior **na mesma viagem**
    student_count = db.query(StudentTripModel).filter(
        StudentTripModel.trip_id == student_trip.trip_id,  # Certifica que é a mesma viagem
        StudentTripModel.point_id == old_point_id,  # Mesmo ponto de ônibus
        StudentTripModel.system_deleted == 0
    ).count()

    # Exibe o valor de student_count no terminal
    print(f"Number of students linked to bus stop {old_point_id} in trip {student_trip.trip_id}: {student_count}")

    # Se não houver mais estudantes vinculados ao ponto anterior na mesma viagem, inativa o ponto
    if student_count == 0:
        old_trip_bus_stop = db.query(TripBusStopModel).filter(
            TripBusStopModel.trip_id == student_trip.trip_id,  # Mesma viagem
            TripBusStopModel.bus_stop_id == old_point_id  # Mesmo ponto de ônibus
        ).first()

        # Verifica se encontrou o registro correto
        if not old_trip_bus_stop:
            print(f"Trip bus stop with trip_id {student_trip.trip_id} and bus_stop_id {old_point_id} not found.")
            raise HTTPException(status_code=404, detail="Trip bus stop not found")

        # Exibe informações sobre o registro encontrado
        print(f"Found TripBusStop with id {old_trip_bus_stop.id}, current system_deleted: {old_trip_bus_stop.system_deleted}")

        # Inativa o ponto de ônibus e faz commit
        old_trip_bus_stop.system_deleted = 1
        db.commit()

        # Verifica se o commit foi bem-sucedido
        db.refresh(old_trip_bus_stop)
        print(f"Updated TripBusStop {old_trip_bus_stop.id}, system_deleted is now {old_trip_bus_stop.system_deleted}")

    return student_trip


@router.put("/{student_trip_id}/update_trip", response_model=StudentTrip)
def update_student_trip(student_trip_id: int, new_trip_id: int, db: Session = Depends(get_db), waitlist: bool = False):
    # Busca pelo registro de student_trip
    student_trip = db.query(StudentTripModel).filter(StudentTripModel.id == student_trip_id).first()
    if not student_trip:
        raise HTTPException(status_code=404, detail="Student trip not found")

    # Busca pela nova trip_id
    new_trip = db.query(TripModel).filter(TripModel.id == new_trip_id).first()
    if not new_trip:
        raise HTTPException(status_code=404, detail="New trip not found")

    if new_trip.status != TripStatusEnum.ATIVA:
        raise HTTPException(status_code=400, detail="New trip is not active")

    # Verifica a capacidade e trata a lógica da fila de espera
    if not check_capacity(new_trip.id, db):
        if waitlist:
            student_trip.status = StudentStatusEnum.FILA_DE_ESPERA
        else:
            raise HTTPException(status_code=400, detail="New trip is full")

    # Validações e atualização de trip_bus_stop
    validate_and_update_trip_bus_stop(student_trip, db)

    # Verificar se já existe um trip_bus_stop para a nova trip_id e point_id
    new_trip_bus_stop = db.query(TripBusStopModel).filter(
        TripBusStopModel.trip_id == new_trip.id,
        TripBusStopModel.bus_stop_id == student_trip.point_id,
        TripBusStopModel.system_deleted == 0
    ).first()

    # Se não existe, criar um novo trip_bus_stop com base no tipo da viagem (ida ou volta)
    if not new_trip_bus_stop:
        if new_trip.trip_type == 1:  # Supondo que 'ida' e 'volta' sejam valores de trip_type
            new_trip_bus_stop_status = TripBusStopStatusEnum.DESENBARQUE
        elif new_trip.trip_type == 2:
            new_trip_bus_stop_status = TripBusStopStatusEnum.A_CAMINHO
        else:
            raise HTTPException(status_code=400, detail="Invalid trip type")

        new_trip_bus_stop = TripBusStopModel(
            trip_id=new_trip.id,
            bus_stop_id=student_trip.point_id,
            status=new_trip_bus_stop_status
        )
        db.add(new_trip_bus_stop)
        db.commit()

    # Atualizar o student_trip para a nova trip_id
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

    return {
        "student_trip_id": active_trip.id,
        "trip_id": active_trip.trip.id,
        "trip_type": TripTypeEnum(active_trip.trip.trip_type).name,
        "trip_status": TripStatusEnum(active_trip.trip.status).name
    }

def validate_and_update_trip_bus_stop(student_trip: StudentTripModel, db: Session):
    # Consulta na tabela student_trip para encontrar registros com mesmo trip_id e point_id que não estejam deletados
    matching_trips = db.query(StudentTripModel).filter(
        StudentTripModel.trip_id == student_trip.trip_id,
        StudentTripModel.point_id == student_trip.point_id,
        StudentTripModel.system_deleted == 0  # Ignorar registros deletados
    ).all()

    # Print da lista de matching_trips com detalhes
    print("Lista de matching_trips:")
    for trip in matching_trips:
        print(f"ID: {trip.id}, Trip ID: {trip.trip_id}, Point ID: {trip.point_id}, Status: {trip.status}")

    # Se retornar apenas o próprio registro de referência ou se houver um registro válido
    if len(matching_trips) == 1 and matching_trips[0].id == student_trip.id:
        # Verificar se o trip_bus_stop correspondente que não está deletado existe
        trip_bus_stop = db.query(TripBusStopModel).filter(
            TripBusStopModel.trip_id == student_trip.trip_id,
            TripBusStopModel.bus_stop_id == student_trip.point_id,
            TripBusStopModel.system_deleted == 0  # Considerar apenas o não deletado
        ).first()

        if trip_bus_stop:
            print(f"Atualizando system_deleted para o trip_bus_stop ID: {trip_bus_stop.id}")
            trip_bus_stop.system_deleted = 1
            db.commit()
            db.refresh(trip_bus_stop)  # Atualiza o objeto para garantir que o valor foi persistido
        else:
            print("Nenhum trip_bus_stop não deletado encontrado para esta combinação de trip_id e bus_stop_id")
    else:
        print("Mais de um matching_trips encontrado ou o ID de referência não corresponde.")

    return
