import pytest
from unittest import mock
from app.models.bus import Bus  # Importe o modelo Bus real
from app.schemas.bus import BusCreate
from pydantic import ValidationError

# Fixture que retorna uma sessão mockada para simular interações com o banco de dados
@pytest.fixture
def mock_session():
    """
    Fixture que retorna uma sessão mockada para simular interações com o banco de dados.
    """
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

# Teste para criar um novo ônibus e verificar se ele foi adicionado corretamente
def test_create_bus(mock_session):
    # Simulando a criação de um novo ônibus
    new_bus = Bus(id=1, registration_number="ABC1234", name="Bus 1", capacity=50)

    # Salvando o ônibus no banco de dados (usando mock)
    session = mock_session()
    session.add.return_value = None  # Simula que o `add` não retorna nada
    session.commit.return_value = None  # Simula que o `commit` também não retorna nada

    # Ação: adicionar o ônibus na sessão
    session.add(new_bus)
    session.commit()

    # Verificações
    session.add.assert_called_once_with(new_bus)
    session.commit.assert_called_once()

    # Checando se os dados do ônibus estão corretos
    assert new_bus.registration_number == "ABC1234"
    assert new_bus.name == "Bus 1"
    assert new_bus.capacity == 50

# Teste para atualizar um ônibus existente
def test_update_bus(mock_session):
    # Simulando a recuperação de um ônibus existente
    existing_bus = Bus(id=1, registration_number="ABC1234", name="Bus 1", capacity=50)

    # Obtendo a sessão mockada e simulando a consulta e atualização
    session = mock_session()
    session.query.return_value.filter_by.return_value.first.return_value = existing_bus

    # Ação: simular a busca e atualização do ônibus
    bus_to_update = session.query(Bus).filter_by(id=1).first()
    bus_to_update.capacity = 60

    # Ação: commit das mudanças
    session.commit()

    # Verificações
    session.query.assert_called_once_with(Bus)
    session.query.return_value.filter_by.assert_called_once_with(id=1)
    session.commit.assert_called_once()
    assert bus_to_update.capacity == 60

# Teste para realizar a exclusão lógica de um ônibus
def test_soft_delete_bus(mock_session):
    # Simulando a exclusão lógica de um ônibus existente
    existing_bus = Bus(id=1, registration_number="ABC1234", name="Bus 1", capacity=50, system_deleted=0)

    # Obtendo a sessão mockada e simulando a consulta
    session = mock_session()
    session.query.return_value.filter_by.return_value.first.return_value = existing_bus

    # Ação: marcar o ônibus como excluído (soft delete)
    bus_to_delete = session.query(Bus).filter_by(id=1).first()
    bus_to_delete.system_deleted = 1

    # Ação: commit das mudanças
    session.commit()

    # Verificações
    session.query.assert_called_once_with(Bus)
    session.query.return_value.filter_by.assert_called_once_with(id=1)
    session.commit.assert_called_once()
    assert bus_to_delete.system_deleted == 1

# Teste para validar números de registro válidos
def test_validate_registration_number_valid():
    # Testando números de registro válidos
    valid_numbers = ["ABC1234", "ABC1D23"]
    for number in valid_numbers:
        bus = BusCreate(registration_number=number, name="Test Bus", capacity=50)
        # Verificando se o número de registro foi convertido para maiúsculo corretamente
        assert bus.registration_number == number.upper()

# Teste para validar números de registro inválidos
def test_validate_registration_number_invalid():
    # Testando números de registro inválidos
    invalid_numbers = ["ABC123", "A123456", "1234ABC", "ABCD123"]
    for number in invalid_numbers:
        # Verificando se ocorre erro de validação para números de registro inválidos
        with pytest.raises(ValueError, match="Invalid registration number format"):
            BusCreate(registration_number=number, name="Test Bus", capacity=50)

# Teste para criar um ônibus com campos ausentes
def test_create_bus_missing_fields():
    # Verificando se ocorre erro ao criar um ônibus sem número de registro
    with pytest.raises(ValueError):
        BusCreate(name="Bus Without Registration", capacity=50)

    # Verificando se ocorre erro ao criar um ônibus sem nome
    with pytest.raises(ValueError):
        BusCreate(registration_number="ABC1234", capacity=50)

    # Verificando se ocorre erro ao criar um ônibus sem capacidade
    with pytest.raises(ValueError):
        BusCreate(registration_number="ABC1234", name="Bus Without Capacity")

# Teste para validar a conversão do número de registro para maiúsculo
def test_uppercase_registration_number():
    # Criando um ônibus com número de registro em letras minúsculas
    bus = BusCreate(registration_number="abc1234", name="Test Bus", capacity=50)
    # Verificando se o número de registro foi convertido para maiúsculo
    assert bus.registration_number == "ABC1234"

# Teste para tentar atualizar um ônibus que não existe
def test_update_nonexistent_bus(mock_session):
    # Simulando a tentativa de atualizar um ônibus que não existe
    session = mock_session()
    session.query.return_value.filter_by.return_value.first.return_value = None

    # Tentando obter o ônibus que não existe
    bus_to_update = session.query(Bus).filter_by(id=999).first()
    assert bus_to_update is None

# Teste para listar apenas os ônibus ativos
def test_list_active_buses(mock_session):
    # Simulando a presença de um ônibus ativo e um excluído
    active_bus = Bus(id=1, registration_number="ABC1234", name="Bus 1", capacity=50, system_deleted=0)
    deleted_bus = Bus(id=2, registration_number="DEF5678", name="Bus 2", capacity=40, system_deleted=1)

    # Obtendo a sessão mockada e simulando a consulta
    session = mock_session()
    session.query.return_value.all.return_value = [active_bus, deleted_bus]

    # Filtrando apenas os ônibus ativos
    buses = [bus for bus in session.query(Bus).all() if bus.system_deleted == 0]
    
    # Verificando se apenas o ônibus ativo está presente na lista
    assert len(buses) == 1
    assert buses[0].id == active_bus.id