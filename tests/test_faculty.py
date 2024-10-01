import pytest
from pydantic import ValidationError
from app.models.faculty import FacultyCreate

# Teste 1: Verificar a criação de uma Faculty com dados válidos
def test_create_valid_faculty():
    faculty_data = {
        "name": "Engineering"
    }
    faculty = FacultyCreate(**faculty_data)
    assert faculty.name == "Engineering"

# Teste 2: Verificar se o nome da Faculty é obrigatório
def test_name_is_required():
    with pytest.raises(ValidationError):
        FacultyCreate()

# Teste 3: Verificar a criação de uma Faculty com nome muito curto (mínimo de 3 caracteres, por exemplo)
def test_name_min_length():
    with pytest.raises(ValidationError):
        FacultyCreate(name="AI")

# Teste 4: Verificar a criação de uma Faculty com nome muito longo (máximo de 50 caracteres, por exemplo)
def test_name_max_length():
    long_name = "A" * 51  # 51 caracteres
    with pytest.raises(ValidationError):
        FacultyCreate(name=long_name)

# Teste 5: Verificar se a Faculty aceita nome com caracteres especiais
def test_special_characters_in_name():
    faculty_data = {
        "name": "Design & Arts"
    }
    faculty = FacultyCreate(**faculty_data)
    assert faculty.name == "Design & Arts"
