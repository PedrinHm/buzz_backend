import pytest
from unittest import mock
from app.models.trip_bus_stop import TripBusStop, TripBusStopStatusEnum  # Importe o modelo TripBusStop real

@pytest.fixture
def mock_session():
    """
    Fixture que retorna uma sessão mockada para simular interações com o banco de dados.
    """
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

def test_create_trip_bus_stop(mock_session):
    # Simulando a criação de uma nova associação de ponto de ônibus a uma viagem
    new_trip_bus_stop = TripBusStop(id=1, trip_id=1, bus_stop_id=1, status=TripBusStopStatusEnum.A_CAMINHO)

    # Salvando o trip_bus_stop no banco de dados (usando mock)
    session = mock_session()
    session.add.return_value = None  # Simula que o `add` não retorna nada
    session.commit.return_value = None  # Simula que o `commit` também não retorna nada

    # Ação: adicionar o trip_bus_stop na sessão
    session.add(new_trip_bus_stop)
    session.commit()

    # Verificações
    session.add.assert_called_once_with(new_trip_bus_stop)
    session.commit.assert_called_once()

    # Checando se os dados do trip_bus_stop estão corretos
    assert new_trip_bus_stop.trip_id == 1
    assert new_trip_bus_stop.bus_stop_id == 1
    assert new_trip_bus_stop.status == TripBusStopStatusEnum.A_CAMINHO

def test_update_trip_bus_stop_status(mock_session):
    # Simulando a recuperação de uma associação de ponto de ônibus a uma viagem existente
    existing_trip_bus_stop = TripBusStop(id=1, trip_id=1, bus_stop_id=1, status=TripBusStopStatusEnum.A_CAMINHO)

    session = mock_session()
    # Configurando o mock para retornar o existing_trip_bus_stop ao chamar session.query().get()
    session.query.return_value.get.return_value = existing_trip_bus_stop

    # Ação: simula a busca e atualização do status do trip_bus_stop
    trip_bus_stop_to_update = session.query(TripBusStop).get(1)  # Simula a chamada real ao banco de dados
    trip_bus_stop_to_update.status = TripBusStopStatusEnum.NO_PONTO

    # Ação: commit das mudanças
    session.commit()

    # Verificações
    session.query.assert_called_once_with(TripBusStop)  # Verifica se query foi chamado com o modelo correto
    session.commit.assert_called_once()
    assert trip_bus_stop_to_update.status == TripBusStopStatusEnum.NO_PONTO
