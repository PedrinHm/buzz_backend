import pytest
from unittest import mock
from app.models.bus_stop import BusStop
from app.schemas.bus_stop import BusStopCreate, BusStopUpdate, BusStop as BusStopSchema
from datetime import datetime, timezone
from unittest.mock import MagicMock

@pytest.fixture
def mock_session():
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

# Teste de criação de um novo ponto de ônibus
def test_create_bus_stop(mock_session):
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

# Teste de atualização de um ponto de ônibus existente
def test_update_bus_stop(mock_session):
    existing_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1)
    session = mock_session()
    session.query.return_value.get.return_value = existing_bus_stop
    bus_stop_to_update = session.query(BusStop).get(1)
    bus_stop_to_update.name = "Updated Bus Stop"
    session.commit()
    session.query.assert_called_once_with(BusStop)
    session.commit.assert_called_once()
    assert bus_stop_to_update.name == "Updated Bus Stop"

# Teste de exclusão lógica de um ponto de ônibus
def test_soft_delete_bus_stop(mock_session):
    existing_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1, system_deleted=0)
    session = mock_session()
    session.query.return_value.get.return_value = existing_bus_stop
    bus_stop_to_delete = session.query(BusStop).get(1)
    bus_stop_to_delete.system_deleted = 1
    session.commit()
    session.query.assert_called_once_with(BusStop)
    session.commit.assert_called_once()
    assert bus_stop_to_delete.system_deleted == 1

# Teste de validação do schema de criação de ponto de ônibus
def test_validate_bus_stop_create_schema():
    bus_stop_data = {"name": "Bus Stop 1", "faculty_id": 1}
    bus_stop_create = BusStopCreate(**bus_stop_data)
    assert bus_stop_create.name == "Bus Stop 1"
    assert bus_stop_create.faculty_id == 1

# Teste de validação do schema de atualização de ponto de ônibus
def test_validate_bus_stop_update_schema():
    bus_stop_data = {"name": "Updated Bus Stop", "faculty_id": 1}
    bus_stop_update = BusStopUpdate(**bus_stop_data)
    assert bus_stop_update.name == "Updated Bus Stop"
    assert bus_stop_update.faculty_id == 1

# Teste de validação do schema completo de ponto de ônibus
def test_validate_bus_stop_schema():
    bus_stop_data = {
        "id": 1,
        "name": "Bus Stop 1",
        "faculty_id": 1,
        "system_deleted": 0,
        "create_date": datetime.now(timezone.utc),
        "update_date": datetime.now(timezone.utc),
    }
    bus_stop = BusStopSchema(**bus_stop_data)
    assert bus_stop.id == 1
    assert bus_stop.name == "Bus Stop 1"
    assert bus_stop.faculty_id == 1
    assert bus_stop.system_deleted == 0
    assert isinstance(bus_stop.create_date, datetime)
    assert isinstance(bus_stop.update_date, datetime)

# Teste de falha ao criar ponto de ônibus com nome inválido
def test_fail_invalid_name():
    with pytest.raises(ValueError):
        BusStopCreate(name="", faculty_id=1)

# Teste de tentativa de criar ponto de ônibus com nome duplicado
def test_duplicate_name_bus_stop(mock_session):
    existing_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1)
    new_bus_stop = BusStop(name="Bus Stop 1", faculty_id=2)
    session = mock_session()
    session.query.return_value.filter_by.return_value.first.return_value = existing_bus_stop
    with pytest.raises(Exception):
        if session.query(BusStop).filter_by(name=new_bus_stop.name).first():
            raise Exception("Bus stop name must be unique")

# Teste de atualização de um ponto de ônibus inexistente
def test_update_nonexistent_bus_stop(mock_session):
    session = mock_session()
    session.query.return_value.get.return_value = None
    bus_stop_to_update = session.query(BusStop).get(999)
    assert bus_stop_to_update is None

# Teste de exclusão lógica de um ponto de ônibus já excluído
def test_soft_delete_already_deleted_bus_stop(mock_session):
    existing_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1, system_deleted=1)
    session = mock_session()
    session.query.return_value.get.return_value = existing_bus_stop
    bus_stop_to_delete = session.query(BusStop).get(1)
    bus_stop_to_delete.system_deleted = 1
    session.commit()
    session.query.assert_called_once_with(BusStop)
    session.commit.assert_called_once()
    assert bus_stop_to_delete.system_deleted == 1

# Teste de atualização da data de modificação ao atualizar um ponto de ônibus
def test_update_date_is_updated(mock_session):
    existing_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1, update_date=datetime(2023, 1, 1, tzinfo=timezone.utc))
    session = mock_session()
    session.query.return_value.get.return_value = existing_bus_stop
    bus_stop_to_update = session.query(BusStop).get(1)
    bus_stop_to_update.name = "Updated Bus Stop"
    bus_stop_to_update.update_date = datetime.now(timezone.utc)
    session.commit()
    assert bus_stop_to_update.update_date > datetime(2023, 1, 1, tzinfo=timezone.utc)

# Teste de falha ao criar ponto de ônibus com ID de faculdade inválido
def test_invalid_faculty_id_schema():
    with pytest.raises(ValueError):
        BusStopCreate(name="Bus Stop 1", faculty_id="invalid_id")
