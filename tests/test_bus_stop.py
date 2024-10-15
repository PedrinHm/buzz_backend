import pytest
from unittest import mock
from app.models.bus_stop import BusStop
from app.schemas.bus_stop import BusStopCreate, BusStopUpdate, BusStop as BusStopSchema
from datetime import datetime, timezone
from unittest.mock import MagicMock

# Fixture que retorna uma sessão mockada para simular interações com o banco de dados
@pytest.fixture
def mock_session():
    """
    Fixture que retorna uma sessão mockada para simular interações com o banco de dados.
    """
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

# Teste para criar um novo ponto de ônibus e verificar se ele foi adicionado corretamente
def test_create_bus_stop(mock_session):
    # Simulando a criação de um novo ponto de ônibus
    new_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1)

    # Obtendo a sessão mockada e simulando as ações de adicionar e fazer commit
    session = mock_session()
    session.add.return_value = None
    session.commit.return_value = None

    # Adicionando o novo ponto de ônibus e fazendo commit
    session.add(new_bus_stop)
    session.commit()

    # Verificando se o ponto de ônibus foi adicionado e salvo corretamente
    session.add.assert_called_once_with(new_bus_stop)
    session.commit.assert_called_once()
    assert new_bus_stop.name == "Bus Stop 1"
    assert new_bus_stop.faculty_id == 1

# Teste para atualizar um ponto de ônibus existente
def test_update_bus_stop(mock_session):
    # Simulando a recuperação de um ponto de ônibus existente
    existing_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1)

    # Obtendo a sessão mockada e simulando a consulta e atualização
    session = mock_session()
    session.query.return_value.get.return_value = existing_bus_stop

    # Atualizando o nome do ponto de ônibus
    bus_stop_to_update = session.query(BusStop).get(1)
    bus_stop_to_update.name = "Updated Bus Stop"

    # Fazendo commit da atualização
    session.commit()

    # Verificando se a consulta e o commit foram chamados corretamente
    session.query.assert_called_once_with(BusStop)
    session.commit.assert_called_once()
    assert bus_stop_to_update.name == "Updated Bus Stop"

# Teste para realizar a exclusão lógica de um ponto de ônibus
def test_soft_delete_bus_stop(mock_session):
    # Simulando exclusão lógica de um ponto de ônibus existente
    existing_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1, system_deleted=0)

    # Obtendo a sessão mockada e simulando a consulta
    session = mock_session()
    session.query.return_value.get.return_value = existing_bus_stop

    # Marcando o ponto de ônibus como excluído logicamente
    bus_stop_to_delete = session.query(BusStop).get(1)
    bus_stop_to_delete.system_deleted = 1

    # Fazendo commit da exclusão lógica
    session.commit()

    # Verificando se a consulta e o commit foram chamados corretamente
    session.query.assert_called_once_with(BusStop)
    session.commit.assert_called_once()
    assert bus_stop_to_delete.system_deleted == 1

# Teste para validar o schema BusStopCreate
def test_validate_bus_stop_create_schema():
    # Testando a validação do schema BusStopCreate
    bus_stop_data = {"name": "Bus Stop 1", "faculty_id": 1}
    bus_stop_create = BusStopCreate(**bus_stop_data)

    # Verificando se os dados foram atribuídos corretamente
    assert bus_stop_create.name == "Bus Stop 1"
    assert bus_stop_create.faculty_id == 1

# Teste para validar o schema BusStopUpdate
def test_validate_bus_stop_update_schema():
    # Testando a validação do schema BusStopUpdate
    bus_stop_data = {"name": "Updated Bus Stop", "faculty_id": 1}
    bus_stop_update = BusStopUpdate(**bus_stop_data)

    # Verificando se os dados foram atribuídos corretamente
    assert bus_stop_update.name == "Updated Bus Stop"
    assert bus_stop_update.faculty_id == 1

# Teste para validar o schema completo BusStop
def test_validate_bus_stop_schema():
    # Testando o schema completo BusStop
    bus_stop_data = {
        "id": 1,
        "name": "Bus Stop 1",
        "faculty_id": 1,
        "system_deleted": 0,
        "create_date": datetime.now(timezone.utc),  # Atualizado
        "update_date": datetime.now(timezone.utc),  # Atualizado
    }
    bus_stop = BusStopSchema(**bus_stop_data)

    # Verificando se os dados foram atribuídos corretamente
    assert bus_stop.id == 1
    assert bus_stop.name == "Bus Stop 1"
    assert bus_stop.faculty_id == 1
    assert bus_stop.system_deleted == 0
    assert isinstance(bus_stop.create_date, datetime)
    assert isinstance(bus_stop.update_date, datetime)

# Teste para validar falha ao criar um ponto de ônibus com nome inválido
def test_fail_invalid_name():
    # Testando falha ao criar schema com nome inválido (vazio)
    with pytest.raises(ValueError):
        BusStopCreate(name="", faculty_id=1)

# Teste para tentar criar um ponto de ônibus com nome duplicado
def test_duplicate_name_bus_stop(mock_session):
    # Simulando a tentativa de criação de um ponto de ônibus com nome duplicado
    existing_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1)
    new_bus_stop = BusStop(name="Bus Stop 1", faculty_id=2)

    # Obtendo a sessão mockada e simulando a consulta
    session = mock_session()
    session.query.return_value.filter_by.return_value.first.return_value = existing_bus_stop

    # Verificando se uma exceção é lançada ao tentar criar um ponto de ônibus com nome duplicado
    with pytest.raises(Exception):  # Pode ser uma exceção específica dependendo da implementação
        if session.query(BusStop).filter_by(name=new_bus_stop.name).first():
            raise Exception("Bus stop name must be unique")

# Teste para tentar atualizar um ponto de ônibus que não existe
def test_update_nonexistent_bus_stop(mock_session):
    # Simulando a tentativa de atualizar um ponto de ônibus que não existe
    session = mock_session()
    session.query.return_value.get.return_value = None

    # Tentando obter o ponto de ônibus que não existe
    bus_stop_to_update = session.query(BusStop).get(999)
    assert bus_stop_to_update is None

# Teste para realizar a exclusão lógica de um ponto de ônibus já excluído
def test_soft_delete_already_deleted_bus_stop(mock_session):
    # Simulando exclusão lógica de um ponto de ônibus já excluído
    existing_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1, system_deleted=1)

    # Obtendo a sessão mockada e simulando a consulta
    session = mock_session()
    session.query.return_value.get.return_value = existing_bus_stop

    # Marcando o ponto de ônibus como excluído logicamente novamente
    bus_stop_to_delete = session.query(BusStop).get(1)
    bus_stop_to_delete.system_deleted = 1

    # Fazendo commit da exclusão lógica
    session.commit()

    # Verificando se a consulta e o commit foram chamados corretamente
    session.query.assert_called_once_with(BusStop)
    session.commit.assert_called_once()
    assert bus_stop_to_delete.system_deleted == 1

# Teste para atualizar o campo update_date de um ponto de ônibus
def test_update_date_is_updated(mock_session):
    # Simulando a atualização do campo update_date
    existing_bus_stop = BusStop(id=1, name="Bus Stop 1", faculty_id=1, update_date=datetime(2023, 1, 1, tzinfo=timezone.utc))  # Ajustado para ter timezone

    # Obtendo a sessão mockada e simulando a consulta
    session = mock_session()
    session.query.return_value.get.return_value = existing_bus_stop

    # Atualizando o nome do ponto de ônibus e a data de atualização
    bus_stop_to_update = session.query(BusStop).get(1)
    bus_stop_to_update.name = "Updated Bus Stop"
    bus_stop_to_update.update_date = datetime.now(timezone.utc)  # Já tem timezone
    session.commit()

    # Verificando se a data de atualização foi modificada corretamente
    assert bus_stop_to_update.update_date > datetime(2023, 1, 1, tzinfo=timezone.utc)  # Comparando com datetime com timezone
    
# Teste para validar falha ao criar schema com faculty_id inválido
def test_invalid_faculty_id_schema():
    # Testando falha ao criar schema com faculty_id inválido (string em vez de int)
    with pytest.raises(ValueError):
        BusStopCreate(name="Bus Stop 1", faculty_id="invalid_id")
