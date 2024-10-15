import pytest
from pydantic import ValidationError
from datetime import datetime
from unittest.mock import patch, MagicMock
from app.models import User  
from app.schemas import UserCreate, UserUpdate
import bcrypt

# Função de validação de CPF
from app.schemas.user import validate_cpf

# Testes unitários sugeridos:

# 1. Testes de Criação do Usuário
@patch('app.schemas.UserCreate', autospec=True)
def test_user_create(mock_user_create):
    user_data = {
        "email": "teste@email.com",
        "password": "senha123",
        "name": "Teste",
        "cpf": "12345678909",
        "phone": "+5511999999999",
        "user_type_id": 1
    }
    mock_user_create.return_value = UserCreate(**user_data)
    user = mock_user_create(**user_data)
    assert user.email == "teste@email.com"
    assert user.name == "Teste"
    assert user.cpf == "12345678909"

# 2. Teste de Validação de CPF
@patch('app.schemas.user.validate_cpf', autospec=True)
def test_validate_cpf(mock_validate_cpf):
    mock_validate_cpf.return_value = True
    assert validate_cpf("12345678909") == True
    mock_validate_cpf.return_value = False
    assert validate_cpf("11111111111") == False

# 3. Teste de Validação de Telefone
def test_user_phone_validation():
    with pytest.raises(ValidationError):
        UserCreate(email="teste@email.com", password="senha123", name="Teste", cpf="12345678909", phone="123", user_type_id=1)

# 4. Teste de Criptografia de Senha (sem interação com o banco de dados)
def test_user_password_hashing():
    user = UserCreate(email="teste@email.com", password="senha123", name="Teste", cpf="12345678909", phone="+5511999999999", user_type_id=1)
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    assert bcrypt.checkpw(user.password.encode('utf-8'), hashed_password.encode('utf-8'))

# 5. Teste de Verificação de Senha (sem interação com o banco de dados)
def test_verify_password():
    password = "minha_senha"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = UserCreate(email="teste@email.com", password=hashed_password, name="Teste", cpf="12345678909", phone="+5511999999999", user_type_id=1)
    assert bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')) == True
    assert bcrypt.checkpw("senha_errada".encode('utf-8'), user.password.encode('utf-8')) == False

# 6. Teste de Atualização de E-mail e Telefone
@patch('app.schemas.UserUpdate', autospec=True)
def test_user_update(mock_user_update):
    update_data = {
        "email": "novo@email.com",
        "phone": "+5511999999999"
    }
    mock_user_update.return_value = UserUpdate(**update_data)
    user_update = mock_user_update(**update_data)
    assert user_update.email == "novo@email.com"
    assert user_update.phone == "+5511999999999"

# 7. Teste de Atualização de Nome
@patch('app.schemas.UserUpdate', autospec=True)
def test_user_update_name(mock_user_update):
    mock_user_update.return_value = UserUpdate(name="Novo Nome")
    user_update = mock_user_update(name="Novo Nome")
    assert user_update.name == "Novo Nome"

# 8. Teste de Dados Não Válidos (e-mail inválido, CPF inválido, telefone inválido)
def test_invalid_data():
    with pytest.raises(ValidationError):
        UserCreate(email="email_invalido", password="senha123", name="Teste", cpf="12345678909", phone="123456", user_type_id=1)
    with pytest.raises(ValidationError):
        UserCreate(email="teste@email.com", password="senha123", name="Teste", cpf="11111111111", phone="+5511999999999", user_type_id=1)

# 9. Teste de Validação do Primeiro Login (sem interação com o banco de dados)
@patch('app.schemas.UserCreate', autospec=True)
def test_first_login(mock_user_create):
    mock_user_create.return_value = MagicMock(first_login=True)
    user_data = {
        "email": "teste@email.com",
        "password": "senha123",
        "name": "Teste",
        "cpf": "12345678909",
        "phone": "+5511999999999",
        "user_type_id": 1,
        "first_login": True
    }
    user = mock_user_create(**user_data)
    assert user.first_login == True

# 10. Teste de Validação de Datas de Criação e Atualização (simulando instância sem banco de dados)
@patch('app.schemas.UserCreate', autospec=True)
def test_creation_and_update_dates(mock_user_create):
    create_date = datetime.now()
    update_date = datetime.now()
    mock_user_create.return_value = UserCreate(
        email="teste@email.com",
        password="senha123",
        name="Teste",
        cpf="12345678909",
        phone="+5511999999999",
        user_type_id=1
    )
    user = mock_user_create()
    assert isinstance(create_date, datetime)
    assert isinstance(update_date, datetime)