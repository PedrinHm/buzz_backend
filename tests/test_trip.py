import pytest
from unittest import mock
from app.models.trip import Trip, TripStatusEnum, TripTypeEnum  # Importe o modelo Trip real

@pytest.fixture
def mock_session():
    """
    Fixture que retorna uma sessão mockada para simular interações com o banco de dados.
    """
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

def test_create_trip(mock_session):
    # Simulando a criação de uma nova viagem
    new_trip = Trip(id=1, trip_type=TripTypeEnum.IDA, status=TripStatusEnum.ATIVA, bus_id=1, driver_id=1)

    # Salvando a viagem no banco de dados (usando mock)
    session = mock_session()
    session.add.return_value = None  # Simula que o `add` não retorna nada
    session.commit.return_value = None  # Simula que o `commit` também não retorna nada

    # Ação: adicionar a viagem na sessão
    session.add(new_trip)
    session.commit()

    # Verificações
    session.add.assert_called_once_with(new_trip)
    session.commit.assert_called_once()

    # Checando se os dados da viagem estão corretos
    assert new_trip.trip_type == TripTypeEnum.IDA
    assert new_trip.status == TripStatusEnum.ATIVA
    assert new_trip.bus_id == 1
    assert new_trip.driver_id == 1

def test_update_trip_status(mock_session):
    # Simulando a recuperação de uma viagem existente
    existing_trip = Trip(id=1, trip_type=TripTypeEnum.IDA, status=TripStatusEnum.ATIVA, bus_id=1, driver_id=1)

    session = mock_session()
    # Configurando o mock para retornar o existing_trip ao chamar session.query().get()
    session.query.return_value.get.return_value = existing_trip

    # Ação: simula a busca e atualização do status da viagem
    trip_to_update = session.query(Trip).get(1)  # Simula a chamada real ao banco de dados
    trip_to_update.status = TripStatusEnum.CONCLUIDA

    # Ação: commit das mudanças
    session.commit()

    # Verificações
    session.query.assert_called_once_with(Trip)  # Verifica se query foi chamado com o modelo correto
    session.commit.assert_called_once()
    assert trip_to_update.status == TripStatusEnum.CONCLUIDA

def test_update_trip_bus_issue(mock_session):
    # Simulando a recuperação de uma viagem existente
    existing_trip = Trip(id=1, trip_type=TripTypeEnum.VOLTA, status=TripStatusEnum.ATIVA, bus_id=1, driver_id=1)

    session = mock_session()
    # Configurando o mock para retornar o existing_trip ao chamar session.query().get()
    session.query.return_value.get.return_value = existing_trip

    # Ação: simula a busca e atualização do campo bus_issue
    trip_to_update = session.query(Trip).get(1)  # Simula a chamada real ao banco de dados
    trip_to_update.bus_issue = True

    # Ação: commit das mudanças
    session.commit()

    # Verificações
    session.query.assert_called_once_with(Trip)  # Verifica se query foi chamado com o modelo correto
    session.commit.assert_called_once()
    assert trip_to_update.bus_issue is True
