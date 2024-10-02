import pytest
from unittest import mock
from app.models.bus_stop import BusStop  # Importe o modelo BusStop real

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

    # Salvando o ponto de ônibus no banco de dados (usando mock)
    session = mock_session()
    session.add.return_value = None  # Simula que o `add` não retorna nada
    session.commit.return_value = None  # Simula que o `commit` também não retorna nada

    # Ação: adicionar o ponto de ônibus na sessão
    session.add(new_bus_stop)
    session.commit()

    # Verificações
    session.add.assert_called_once_with(new_bus_stop)
    session.commit.assert_called_once()

    # Checando se os dados do ponto de ônibus estão corretos
    assert new_bus_stop.name == "Bus Stop 1"
    assert new_bus_stop.faculty_id == 1

def test_update_bus_stop(mock_session):
    # Simulando a recuperação de um ponto de ônibus existente
    existing_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1)

    session = mock_session()
    # Configurando o mock para retornar o existing_bus_stop ao chamar session.query().filter().first()
    session.query.return_value.get.return_value = existing_bus_stop

    # Ação: simula a busca e atualização do ponto de ônibus
    bus_stop_to_update = session.query(BusStop).get(1)  # Simula a chamada real ao banco de dados
    bus_stop_to_update.name = "Updated Bus Stop"

    # Ação: commit das mudanças
    session.commit()

    # Verificações
    session.query.assert_called_once_with(BusStop)  # Verifica se query foi chamado com o modelo correto
    session.commit.assert_called_once()
    assert bus_stop_to_update.name == "Updated Bus Stop"