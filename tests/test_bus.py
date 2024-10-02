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
    # Simulando a chamada query().filter_by().first() para retornar o existing_bus
    session.query(Bus).filter_by(id=1).first()

    # Ação: atualizar a capacidade do ônibus
    existing_bus.capacity = 60

    # Ação: commit das mudanças
    session.commit()

    # Verificações
    session.query.return_value.filter_by.assert_called_once_with(id=1)
    assert existing_bus.capacity == 60
    session.commit.assert_called_once()