import pytest
from unittest import mock
from app.models.bus_stop import BusStop
from app.schemas.bus_stop import BusStopCreate, BusStopUpdate, BusStop as BusStopSchema
from datetime import datetime

@pytest.fixture
def mock_session():
    """
    Fixture que retorna uma sessão mockada para simular interações com o banco de dados.
    """
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

def test_create_bus_stop(mock_session):
    # Simulando a criação de um novo ponto de ônibus
    new_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1)

    session = mock_session()
    session.add.return_value = None
    session.commit.return_value = None

    session.add(new_bus_stop)
    session.commit()

    session.add.assert_called_once_with(new_bus_stop)
    session.commit.assert_called_once()

    assert new_bus_stop.name == "Bus Stop 1"
    assert new_bus_stop.faculty_id == 1

def test_update_bus_stop(mock_session):
    # Simulando a recuperação de um ponto de ônibus existente
    existing_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1)

    session = mock_session()
    session.query.return_value.get.return_value = existing_bus_stop

    bus_stop_to_update = session.query(BusStop).get(1)
    bus_stop_to_update.name = "Updated Bus Stop"

    session.commit()

    session.query.assert_called_once_with(BusStop)
    session.commit.assert_called_once()
    assert bus_stop_to_update.name == "Updated Bus Stop"

def test_soft_delete_bus_stop(mock_session):
    # Simulando exclusão lógica de um ponto de ônibus
    existing_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1, system_deleted=0)

    session = mock_session()
    session.query.return_value.get.return_value = existing_bus_stop

    bus_stop_to_delete = session.query(BusStop).get(1)
    bus_stop_to_delete.system_deleted = 1

    session.commit()

    session.query.assert_called_once_with(BusStop)
    session.commit.assert_called_once()
    assert bus_stop_to_delete.system_deleted == 1

def test_validate_bus_stop_create_schema():
    # Testando a validação do schema BusStopCreate
    bus_stop_data = {"name": "Bus Stop 1", "faculty_id": 1}
    bus_stop_create = BusStopCreate(**bus_stop_data)

    assert bus_stop_create.name == "Bus Stop 1"
    assert bus_stop_create.faculty_id == 1

def test_validate_bus_stop_update_schema():
    # Testando a validação do schema BusStopUpdate
    bus_stop_data = {"name": "Updated Bus Stop", "faculty_id": 1}
    bus_stop_update = BusStopUpdate(**bus_stop_data)

    assert bus_stop_update.name == "Updated Bus Stop"
    assert bus_stop_update.faculty_id == 1

def test_validate_bus_stop_schema():
    # Testando o schema completo BusStop
    bus_stop_data = {
        "id": 1,
        "name": "Bus Stop 1",
        "faculty_id": 1,
        "system_deleted": 0,
        "create_date": datetime.utcnow(),
        "update_date": datetime.utcnow(),
    }
    bus_stop = BusStopSchema(**bus_stop_data)

    assert bus_stop.id == 1
    assert bus_stop.name == "Bus Stop 1"
    assert bus_stop.faculty_id == 1
    assert bus_stop.system_deleted == 0
    assert isinstance(bus_stop.create_date, datetime)
    assert isinstance(bus_stop.update_date, datetime)

def test_fail_invalid_name():
    # Testando falha ao criar schema com nome inválido (vazio)
    with pytest.raises(ValueError):
        BusStopCreate(name="", faculty_id=1)
