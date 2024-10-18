import pytest
from unittest import mock
from app.models.bus import Bus
from app.schemas.bus import BusCreate
from pydantic import ValidationError

@pytest.fixture
def mock_session():
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

# Teste de criação de um novo ônibus
def test_create_bus(mock_session):
    new_bus = Bus(id=1, registration_number="ABC1234", name="Bus 1", capacity=50)
    session = mock_session()
    session.add.return_value = None
    session.commit.return_value = None
    session.add(new_bus)
    session.commit()
    session.add.assert_called_once_with(new_bus)
    session.commit.assert_called_once()
    assert new_bus.registration_number == "ABC1234"
    assert new_bus.name == "Bus 1"
    assert new_bus.capacity == 50

# Teste de atualização de um ônibus existente
def test_update_bus(mock_session):
    existing_bus = Bus(id=1, registration_number="ABC1234", name="Bus 1", capacity=50)
    session = mock_session()
    session.query.return_value.filter_by.return_value.first.return_value = existing_bus
    bus_to_update = session.query(Bus).filter_by(id=1).first()
    bus_to_update.capacity = 60
    session.commit()
    session.query.assert_called_once_with(Bus)
    session.query.return_value.filter_by.assert_called_once_with(id=1)
    session.commit.assert_called_once()
    assert bus_to_update.capacity == 60

# Teste de exclusão lógica de um ônibus
def test_soft_delete_bus(mock_session):
    existing_bus = Bus(id=1, registration_number="ABC1234", name="Bus 1", capacity=50, system_deleted=0)
    session = mock_session()
    session.query.return_value.filter_by.return_value.first.return_value = existing_bus
    bus_to_delete = session.query(Bus).filter_by(id=1).first()
    bus_to_delete.system_deleted = 1
    session.commit()
    session.query.assert_called_once_with(Bus)
    session.query.return_value.filter_by.assert_called_once_with(id=1)
    session.commit.assert_called_once()
    assert bus_to_delete.system_deleted == 1

# Teste de validação de números de registro válidos
def test_validate_registration_number_valid():
    valid_numbers = ["ABC1234", "ABC1D23"]
    for number in valid_numbers:
        bus = BusCreate(registration_number=number, name="Test Bus", capacity=50)
        assert bus.registration_number == number.upper()

# Teste de validação de números de registro inválidos
def test_validate_registration_number_invalid():
    invalid_numbers = ["ABC123", "A123456", "1234ABC", "ABCD123"]
    for number in invalid_numbers:
        with pytest.raises(ValueError, match="Invalid registration number format"):
            BusCreate(registration_number=number, name="Test Bus", capacity=50)

# Teste de criação de ônibus com campos ausentes
def test_create_bus_missing_fields():
    with pytest.raises(ValueError):
        BusCreate(name="Bus Without Registration", capacity=50)
    with pytest.raises(ValueError):
        BusCreate(registration_number="ABC1234", capacity=50)
    with pytest.raises(ValueError):
        BusCreate(registration_number="ABC1234", name="Bus Without Capacity")

# Teste de conversão do número de registro para maiúsculo
def test_uppercase_registration_number():
    bus = BusCreate(registration_number="abc1234", name="Test Bus", capacity=50)
    assert bus.registration_number == "ABC1234"

# Teste de tentativa de atualização de um ônibus inexistente
def test_update_nonexistent_bus(mock_session):
    session = mock_session()
    session.query.return_value.filter_by.return_value.first.return_value = None
    bus_to_update = session.query(Bus).filter_by(id=999).first()
    assert bus_to_update is None

# Teste de listagem apenas de ônibus ativos
def test_list_active_buses(mock_session):
    active_bus = Bus(id=1, registration_number="ABC1234", name="Bus 1", capacity=50, system_deleted=0)
    deleted_bus = Bus(id=2, registration_number="DEF5678", name="Bus 2", capacity=40, system_deleted=1)
    session = mock_session()
    session.query.return_value.all.return_value = [active_bus, deleted_bus]
    buses = [bus for bus in session.query(Bus).all() if bus.system_deleted == 0]
    assert len(buses) == 1
    assert buses[0].id == active_bus.id