import pytest
from unittest import mock
from pydantic import ValidationError
from app.models.student_trip import StudentTrip, StudentStatusEnum
from app.schemas.student_trip import StudentTripCreate, StudentTripUpdate

@pytest.fixture
def mock_session():
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

# Teste para criar uma nova associação de estudante a uma viagem
def test_create_student_trip(mock_session):
    new_student_trip = StudentTrip(id=1, trip_id=1, student_id=1, status=StudentStatusEnum.PRESENTE, point_id=1)
    session = mock_session()
    session.add.return_value = None
    session.commit.return_value = None
    session.add(new_student_trip)
    session.commit()
    session.add.assert_called_once_with(new_student_trip)
    session.commit.assert_called_once()
    assert new_student_trip.trip_id == 1
    assert new_student_trip.student_id == 1
    assert new_student_trip.status == StudentStatusEnum.PRESENTE
    assert new_student_trip.point_id == 1

# Teste para atualizar o status de uma associação de estudante a uma viagem existente
def test_update_student_trip_status(mock_session):
    existing_student_trip = StudentTrip(id=1, trip_id=1, student_id=1, status=StudentStatusEnum.PRESENTE, point_id=1)
    session = mock_session()
    session.query.return_value.get.return_value = existing_student_trip
    student_trip_to_update = session.query(StudentTrip).get(1)
    student_trip_to_update.status = StudentStatusEnum.AGUARDANDO_NO_PONTO
    session.commit()
    session.query.assert_called_once_with(StudentTrip)
    session.commit.assert_called_once()
    assert student_trip_to_update.status == StudentStatusEnum.AGUARDANDO_NO_PONTO

# Teste para validar o schema StudentTripCreate
def test_student_trip_schema_validation():
    valid_data = {
        "trip_id": 1,
        "student_id": 1,
        "status": StudentStatusEnum.PRESENTE,
        "point_id": 1
    }
    student_trip = StudentTripCreate(**valid_data)
    assert student_trip.trip_id == 1
    invalid_data = {
        "trip_id": 1,
        "student_id": "não_numérico",
        "status": StudentStatusEnum.PRESENTE,
        "point_id": 1
    }
    with pytest.raises(ValidationError) as exc_info:
        student_trip = StudentTripCreate(**invalid_data)
    assert "student_id" in str(exc_info.value)

# Teste para realizar a exclusão lógica de uma associação de estudante a uma viagem
def test_delete_student_trip_logical(mock_session):
    existing_student_trip = StudentTrip(id=1, trip_id=1, student_id=1, status=StudentStatusEnum.PRESENTE, point_id=1, system_deleted=0)
    session = mock_session()
    session.query.return_value.get.return_value = existing_student_trip
    student_trip_to_delete = session.query(StudentTrip).get(1)
    student_trip_to_delete.system_deleted = 1
    session.commit()
    session.query.assert_called_once_with(StudentTrip)
    session.commit.assert_called_once()
    assert student_trip_to_delete.system_deleted == 1

# Teste para atualizar o point_id de uma associação de estudante a uma viagem existente
def test_update_student_trip_point_id(mock_session):
    existing_student_trip = StudentTrip(id=1, trip_id=1, student_id=1, status=StudentStatusEnum.PRESENTE, point_id=1)
    session = mock_session()
    session.query.return_value.get.return_value = existing_student_trip
    student_trip_to_update = session.query(StudentTrip).get(1)
    student_trip_to_update.point_id = 2
    session.commit()
    session.query.assert_called_once_with(StudentTrip)
    session.commit.assert_called_once()
    assert student_trip_to_update.point_id == 2

# Teste para criar um student_trip com uma chave estrangeira inválida
def test_create_student_trip_with_invalid_foreign_key(mock_session):
    invalid_student_trip = StudentTrip(id=1, trip_id=999, student_id=1, status=StudentStatusEnum.PRESENTE, point_id=1)
    session = mock_session()
    session.add.side_effect = Exception("Chave estrangeira inválida")
    with pytest.raises(Exception) as exc_info:
        session.add(invalid_student_trip)
        session.commit()
    assert "Chave estrangeira inválida" in str(exc_info.value)
    session.add.assert_called_once_with(invalid_student_trip)
    session.commit.assert_not_called()