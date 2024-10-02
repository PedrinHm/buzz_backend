import pytest
from unittest import mock
from app.models.faculty import Faculty  # Importe o modelo Faculty real

@pytest.fixture
def mock_session():
    """
    Fixture que retorna uma sessão mockada para simular interações com o banco de dados.
    """
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

def test_create_faculty(mock_session):
    # Simulando a criação de uma nova faculdade
    new_faculty = Faculty(id=1, name="Engineering Faculty")

    # Salvando a faculdade no banco de dados (usando mock)
    session = mock_session()
    session.add.return_value = None  # Simula que o `add` não retorna nada
    session.commit.return_value = None  # Simula que o `commit` também não retorna nada

    # Ação: adicionar a faculdade na sessão
    session.add(new_faculty)
    session.commit()

    # Verificações
    session.add.assert_called_once_with(new_faculty)
    session.commit.assert_called_once()

    # Checando se os dados da faculdade estão corretos
    assert new_faculty.name == "Engineering Faculty"

def test_update_faculty(mock_session):
    # Simulando a recuperação de uma faculdade existente
    existing_faculty = Faculty(id=1, name="Engineering Faculty")

    session = mock_session()
    # Configurando o mock para retornar a existing_faculty ao chamar session.query().get()
    session.query.return_value.get.return_value = existing_faculty

    # Ação: simula a busca e atualização do nome da faculdade
    faculty_to_update = session.query(Faculty).get(1)  # Simula a chamada real ao banco de dados
    faculty_to_update.name = "Updated Faculty Name"

    # Ação: commit das mudanças
    session.commit()

    # Verificações
    session.query.assert_called_once_with(Faculty)  # Verifica se query foi chamado com o modelo correto
    session.commit.assert_called_once()
    assert faculty_to_update.name == "Updated Faculty Name"