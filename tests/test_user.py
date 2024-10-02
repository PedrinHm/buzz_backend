import pytest
from unittest import mock
from app.models.user import User  # Importe o modelo User real
import bcrypt

@pytest.fixture
def mock_session():
    """
    Fixture que retorna uma sessão mockada para simular interações com o banco de dados.
    """
    with mock.patch('app.config.database.SessionLocal') as mock_session:
        yield mock_session

def test_create_user(mock_session):
    # Simulando a criação de um novo usuário
    new_user = User(id=1, name="John Doe", email="johndoe@example.com", cpf="12345678900", phone="5551999999999")

    # Salvando o usuário no banco de dados (usando mock)
    session = mock_session()
    session.add.return_value = None  # Simula que o `add` não retorna nada
    session.commit.return_value = None  # Simula que o `commit` também não retorna nada

    # Ação: adicionar o usuário na sessão
    session.add(new_user)
    session.commit()

    # Verificações
    session.add.assert_called_once_with(new_user)
    session.commit.assert_called_once()

    # Checando se os dados do usuário estão corretos
    assert new_user.name == "John Doe"
    assert new_user.email == "johndoe@example.com"

def test_update_user(mock_session):
    # Simulando a recuperação de um usuário existente
    existing_user = User(id=1, name="John Doe", email="johndoe@example.com")

    session = mock_session()
    # Configurando o mock para retornar o existing_user ao chamar session.query().get()
    session.query.return_value.get.return_value = existing_user

    # Ação: simula a busca e atualização do nome do usuário
    user_to_update = session.query(User).get(1)  # Simula a chamada real ao banco de dados
    user_to_update.name = "John Updated"

    # Ação: commit das mudanças
    session.commit()

    # Verificações
    session.query.assert_called_once_with(User)  # Verifica se query foi chamado com o modelo correto
    session.commit.assert_called_once()
    assert user_to_update.name == "John Updated"

def test_verify_password():
    # Simulando um usuário com senha definida
    user = User(id=1, name="John Doe")
    user.set_password("strong_password")

    # Verificando a senha correta
    assert user.verify_password("strong_password") is True

    # Verificando uma senha incorreta
    assert user.verify_password("wrong_password") is False
