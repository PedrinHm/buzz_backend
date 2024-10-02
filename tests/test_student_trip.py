import pytest
from unittest import mock
from app.models.student_trip import StudentTrip, StudentStatusEnum  # Importe o modelo StudentTrip real

@pytest.fixture
def mock_session():
    """
    Fixture que retorna uma sessão mockada para simular interações com o banco de dados.
    """
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

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

def test_update_student_trip_status(mock_session):
    # Simulando a recuperação de uma associação de estudante a uma viagem existente
    existing_student_trip = StudentTrip(id=1, trip_id=1, student_id=1, status=StudentStatusEnum.PRESENTE, point_id=1)

    session = mock_session()
    # Configurando o mock para retornar o existing_student_trip ao chamar session.query().get()
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
