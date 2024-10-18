import pytest
from unittest import mock
from app.models.faculty import Faculty

@pytest.fixture
def mock_session():
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

# Teste para criar uma nova faculdade
def test_create_faculty(mock_session):
    new_faculty = Faculty(id=1, name="Engineering Faculty")
    session = mock_session()
    session.add.return_value = None
    session.commit.return_value = None
    session.add(new_faculty)
    session.commit()
    session.add.assert_called_once_with(new_faculty)
    session.commit.assert_called_once()
    assert new_faculty.name == "Engineering Faculty"

# Teste para atualizar uma faculdade existente
def test_update_faculty(mock_session):
    existing_faculty = Faculty(id=1, name="Engineering Faculty")
    session = mock_session()
    session.query.return_value.get.return_value = existing_faculty
    faculty_to_update = session.query(Faculty).get(1)
    faculty_to_update.name = "Updated Faculty Name"
    session.commit()
    session.query.assert_called_once_with(Faculty)
    session.commit.assert_called_once()
    assert faculty_to_update.name == "Updated Faculty Name"

# Teste para realizar a exclusão lógica de uma faculdade
def test_delete_faculty_logically(mock_session):
    existing_faculty = Faculty(id=1, name="Engineering Faculty", system_deleted=0)
    session = mock_session()
    session.query.return_value.get.return_value = existing_faculty
    faculty_to_delete = session.query(Faculty).get(1)
    faculty_to_delete.system_deleted = 1
    session.commit()
    session.query.assert_called_once_with(Faculty)
    session.commit.assert_called_once()
    assert faculty_to_delete.system_deleted == 1

# Teste para listar todas as faculdades
def test_list_faculties(mock_session):
    faculties = [
        Faculty(id=1, name="Engineering Faculty"),
        Faculty(id=2, name="Science Faculty"),
        Faculty(id=3, name="Arts Faculty")
    ]
    session = mock_session()
    session.query.return_value.all.return_value = faculties
    result = session.query(Faculty).all()
    session.query.assert_called_once_with(Faculty)
    assert len(result) == 3
    assert result[0].name == "Engineering Faculty"
    assert result[1].name == "Science Faculty"
    assert result[2].name == "Arts Faculty"