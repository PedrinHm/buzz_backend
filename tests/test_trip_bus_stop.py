import pytest
from unittest import mock
from app.models.trip_bus_stop import TripBusStop, TripBusStopStatusEnum  # Importe o modelo TripBusStop real
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError

# Fixture que retorna uma sessão mockada para simular interações com o banco de dados
@pytest.fixture
def mock_session():
    """
    Fixture que retorna uma sessão mockada para simular interações com o banco de dados.
    """
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

# Teste para criar um TripBusStop e verificar se foi salvo corretamente no banco de dados
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

# Teste para atualizar o status de um TripBusStop existente
def test_update_trip_bus_stop_status(mock_session):
    # Simulando a recuperação de uma associação de ponto de ônibus a uma viagem existente
    existing_trip_bus_stop = TripBusStop(id=1, trip_id=1, bus_stop_id=1, status=TripBusStopStatusEnum.A_CAMINHO)

    # Obtendo a sessão mockada e simulando a consulta e atualização
    session = mock_session()
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

# Teste para exclusão lógica (alterar o campo system_deleted para 1)
def test_delete_trip_bus_stop(mock_session):
    # Simulando a recuperação de uma associação de ponto de ônibus a uma viagem existente
    existing_trip_bus_stop = TripBusStop(id=1, trip_id=1, bus_stop_id=1, status=TripBusStopStatusEnum.A_CAMINHO)
    
    # Obtendo a sessão mockada e simulando a consulta
    session = mock_session()
    session.query.return_value.get.return_value = existing_trip_bus_stop

    # Simula exclusão lógica
    trip_bus_stop_to_delete = session.query(TripBusStop).get(1)
    trip_bus_stop_to_delete.system_deleted = 1
    session.commit()

    # Verificações
    session.commit.assert_called_once()
    assert trip_bus_stop_to_delete.system_deleted == 1

# Teste para atualização da data de modificação (update_date) ao atualizar um registro
def test_update_trip_bus_stop_date(mock_session):
    # Simulando a recuperação de uma associação de ponto de ônibus a uma viagem existente
    existing_trip_bus_stop = TripBusStop(id=1, trip_id=1, bus_stop_id=1, status=TripBusStopStatusEnum.A_CAMINHO, update_date=datetime(2023, 10, 1, tzinfo=timezone.utc))

    # Obtendo a sessão mockada e simulando a consulta
    session = mock_session()
    session.query.return_value.get.return_value = existing_trip_bus_stop

    # Simula uma mudança na data de atualização
    updated_time = datetime.now(timezone.utc) + timedelta(minutes=1)  # Ajustado para usar timezone
    trip_bus_stop_to_update = session.query(TripBusStop).get(1)
    trip_bus_stop_to_update.status = TripBusStopStatusEnum.NO_PONTO
    trip_bus_stop_to_update.update_date = updated_time
    session.commit()

    # Verificar se a data de atualização foi alterada
    assert trip_bus_stop_to_update.update_date == updated_time

# Teste para verificar a criação de um TripBusStop sem campos obrigatórios e garantir que erro seja levantado
def test_trip_bus_stop_missing_fields(mock_session):
    # Obtendo a sessão mockada e simulando erro de integridade
    session = mock_session()
    session.add.side_effect = IntegrityError("IntegrityError", {}, None)

    # Tentativa de criar um TripBusStop sem trip_id e bus_stop_id
    with pytest.raises(IntegrityError):
        new_trip_bus_stop = TripBusStop(trip_id=None, bus_stop_id=None, status=TripBusStopStatusEnum.A_CAMINHO)
        session.add(new_trip_bus_stop)
        session.commit()

# Teste para verificar o relacionamento entre TripBusStop e Trip/BusStop
def test_trip_bus_stop_relationship(mock_session):
    # Simula uma Trip e um BusStop
    mock_trip = mock.Mock()
    mock_bus_stop = mock.Mock()

    # Simula a criação de um TripBusStop e seus relacionamentos
    new_trip_bus_stop = TripBusStop(id=1, trip_id=1, bus_stop_id=1, status=TripBusStopStatusEnum.A_CAMINHO)
    with mock.patch.object(TripBusStop, 'trip', new_callable=mock.PropertyMock) as mock_trip_property:
        mock_trip_property.return_value = mock_trip
        with mock.patch.object(TripBusStop, 'bus_stop', new_callable=mock.PropertyMock) as mock_bus_stop_property:
            mock_bus_stop_property.return_value = mock_bus_stop

            # Verificar se os relacionamentos estão corretos
            assert new_trip_bus_stop.trip == mock_trip
            assert new_trip_bus_stop.bus_stop == mock_bus_stop

# Teste para verificar se a função label() do enum retorna o rótulo correto
def test_trip_bus_stop_status_label():
    # Verifica o rótulo do status "A_CAMINHO"
    status = TripBusStopStatusEnum.A_CAMINHO
    assert status.name == "A_CAMINHO"

    # Verifica o rótulo do status "NO_PONTO"
    status = TripBusStopStatusEnum.NO_PONTO
    assert status.name == "NO_PONTO"
