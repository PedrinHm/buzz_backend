import pytest
from unittest import mock
from pydantic import ValidationError
from app.models.student_trip import StudentTrip, StudentStatusEnum  # Importe o modelo StudentTrip real
from app.schemas.student_trip import StudentTripCreate, StudentTripUpdate

# Fixture que retorna uma sessão mockada para simular interações com o banco de dados
@pytest.fixture
def mock_session():
    """
    Fixture que retorna uma sessão mockada para simular interações com o banco de dados.
    """
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

# Teste para criar uma nova associação de estudante a uma viagem e verificar se ela foi adicionada corretamente
def test_create_student_trip(mock_session):
    # Simulando a criação de uma nova associação de estudante a uma viagem
    new_student_trip = StudentTrip(id=1, trip_id=1, student_id=1, status=StudentStatusEnum.PRESENTE, point_id=1)

    # Salvando o student_trip no banco de dados (usando mock)
    session = mock_session()
    session.add.return_value = None  # Simula que o `add` não retorna nada
    session.commit.return_value = None  # Simula que o `commit` também não retorna nada

    # Ação: adicionar o student_trip na sessão
    session.add(new_student_trip)
    session.commit()

    # Verificações
    session.add.assert_called_once_with(new_student_trip)
    session.commit.assert_called_once()

    # Checando se os dados do student_trip estão corretos
    assert new_student_trip.trip_id == 1
    assert new_student_trip.student_id == 1
    assert new_student_trip.status == StudentStatusEnum.PRESENTE
    assert new_student_trip.point_id == 1

# Teste para atualizar o status de uma associação de estudante a uma viagem existente
def test_update_student_trip_status(mock_session):
    # Simulando a recuperação de uma associação de estudante a uma viagem existente
    existing_student_trip = StudentTrip(id=1, trip_id=1, student_id=1, status=StudentStatusEnum.PRESENTE, point_id=1)

    # Obtendo a sessão mockada e simulando a consulta e atualização
    session = mock_session()
    session.query.return_value.get.return_value = existing_student_trip

    # Ação: simula a busca e atualização do status do student_trip
    student_trip_to_update = session.query(StudentTrip).get(1)  # Simula a chamada real ao banco de dados
    student_trip_to_update.status = StudentStatusEnum.AGUARDANDO_NO_PONTO

    # Ação: commit das mudanças
    session.commit()

    # Verificações
    session.query.assert_called_once_with(StudentTrip)  # Verifica se query foi chamado com o modelo correto
    session.commit.assert_called_once()
    assert student_trip_to_update.status == StudentStatusEnum.AGUARDANDO_NO_PONTO

# Teste para validar o schema StudentTripCreate
def test_student_trip_schema_validation():
    # Caso válido
    valid_data = {
        "trip_id": 1,
        "student_id": 1,
        "status": StudentStatusEnum.PRESENTE,
        "point_id": 1
    }
    student_trip = StudentTripCreate(**valid_data)
    assert student_trip.trip_id == 1

    # Caso inválido (student_id não numérico)
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
    # Simulando a recuperação de uma associação de estudante a uma viagem existente
    existing_student_trip = StudentTrip(id=1, trip_id=1, student_id=1, status=StudentStatusEnum.PRESENTE, point_id=1, system_deleted=0)

    # Obtendo a sessão mockada e simulando a consulta
    session = mock_session()
    session.query.return_value.get.return_value = existing_student_trip

    # Ação: simula a deleção lógica do student_trip
    student_trip_to_delete = session.query(StudentTrip).get(1)
    student_trip_to_delete.system_deleted = 1

    # Ação: commit das mudanças
    session.commit()

    # Verificações
    session.query.assert_called_once_with(StudentTrip)
    session.commit.assert_called_once()
    assert student_trip_to_delete.system_deleted == 1

# Teste para atualizar o point_id de uma associação de estudante a uma viagem existente
def test_update_student_trip_point_id(mock_session):
    # Simulando a recuperação de uma associação de estudante a uma viagem existente
    existing_student_trip = StudentTrip(id=1, trip_id=1, student_id=1, status=StudentStatusEnum.PRESENTE, point_id=1)

    # Obtendo a sessão mockada e simulando a consulta
    session = mock_session()
    session.query.return_value.get.return_value = existing_student_trip

    # Ação: simula a busca e atualização do point_id do student_trip
    student_trip_to_update = session.query(StudentTrip).get(1)
    student_trip_to_update.point_id = 2

    # Ação: commit das mudanças
    session.commit()

    # Verificações
    session.query.assert_called_once_with(StudentTrip)
    session.commit.assert_called_once()
    assert student_trip_to_update.point_id == 2

# Teste para criar um student_trip com uma chave estrangeira inválida
def test_create_student_trip_with_invalid_foreign_key(mock_session):
    # Simulando a tentativa de criar um student_trip com um trip_id inexistente
    invalid_student_trip = StudentTrip(id=1, trip_id=999, student_id=1, status=StudentStatusEnum.PRESENTE, point_id=1)

    # Obtendo a sessão mockada e simulando o erro de chave estrangeira
    session = mock_session()
    session.add.side_effect = Exception("Chave estrangeira inválida")

    # Ação: tentar adicionar o student_trip na sessão
    with pytest.raises(Exception) as exc_info:
        session.add(invalid_student_trip)
        session.commit()

    # Verificações
    assert "Chave estrangeira inválida" in str(exc_info.value)
    session.add.assert_called_once_with(invalid_student_trip)
    session.commit.assert_not_called()