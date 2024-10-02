import pytest
from unittest import mock
from app.models.bus import Bus  # Importe o modelo Bus real

@pytest.fixture
def mock_session():
    """
    Fixture que retorna uma sessão mockada para simular interações com o banco de dados.
    """
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

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

def test_update_bus(mock_session):
    # Simulando a recuperação de um ônibus existente
    existing_bus = Bus(id=1, registration_number="ABC1234", name="Bus 1", capacity=50)

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

def test_soft_delete_bus(mock_session):
    # Simulando a exclusão lógica de um ônibus
    existing_bus = Bus(id=1, registration_number="ABC1234", name="Bus 1", capacity=50, system_deleted=0)

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
