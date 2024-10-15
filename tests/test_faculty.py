import pytest
from unittest import mock
from app.models.faculty import Faculty  # Importe o modelo Faculty real

# Fixture que retorna uma sessão mockada para simular interações com o banco de dados
@pytest.fixture
def mock_session():
    """
    Fixture que retorna uma sessão mockada para simular interações com o banco de dados.
    """
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

# Teste para criar uma nova faculdade e verificar se ela foi adicionada corretamente
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

# Teste para atualizar uma faculdade existente
def test_update_faculty(mock_session):
    # Simulando a recuperação de uma faculdade existente
    existing_faculty = Faculty(id=1, name="Engineering Faculty")

    # Obtendo a sessão mockada e simulando a consulta e atualização
    session = mock_session()
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

# Teste para realizar a exclusão lógica de uma faculdade
def test_delete_faculty_logically(mock_session):
    # Simulando a recuperação de uma faculdade existente
    existing_faculty = Faculty(id=1, name="Engineering Faculty", system_deleted=0)

    # Obtendo a sessão mockada e simulando a consulta
    session = mock_session()
    session.query.return_value.get.return_value = existing_faculty

    # Ação: marcar como deletado logicamente
    faculty_to_delete = session.query(Faculty).get(1)
    faculty_to_delete.system_deleted = 1

    # Ação: commit das mudanças
    session.commit()

    # Verificações
    session.query.assert_called_once_with(Faculty)
    session.commit.assert_called_once()
    assert faculty_to_delete.system_deleted == 1

# Teste para listar todas as faculdades
def test_list_faculties(mock_session):
    # Simulando a criação de várias faculdades
    faculties = [
        Faculty(id=1, name="Engineering Faculty"),
        Faculty(id=2, name="Science Faculty"),
        Faculty(id=3, name="Arts Faculty")
    ]

    # Obtendo a sessão mockada e simulando a consulta
    session = mock_session()
    session.query.return_value.all.return_value = faculties

    # Ação: listar todas as faculdades
    result = session.query(Faculty).all()

    # Verificações
    session.query.assert_called_once_with(Faculty)
    assert len(result) == 3
    assert result[0].name == "Engineering Faculty"
    assert result[1].name == "Science Faculty"
    assert result[2].name == "Arts Faculty"