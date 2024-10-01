import pytest
from pydantic import ValidationError
from app.models.bus_stop import BusStopCreate, BusStopUpdate

# Teste 1: Verificar a criação de um BusStop com dados válidos
def test_create_valid_bus_stop():
    bus_stop_data = {
        "name": "Main Entrance",
        "faculty_id": 1
    }
    bus_stop = BusStopCreate(**bus_stop_data)
    assert bus_stop.name == "Main Entrance"
    assert bus_stop.faculty_id == 1

# Teste 2: Verificar se o nome do BusStop é obrigatório
def test_name_is_required():
    with pytest.raises(ValidationError):
        BusStopCreate(faculty_id=1)

# Teste 3: Verificar se o faculty_id é obrigatório
def test_faculty_id_is_required():
    with pytest.raises(ValidationError):
        BusStopCreate(name="Library Stop")

# Teste 4: Verificar a atualização parcial do BusStop (somente o nome)
def test_update_bus_stop_name():
    bus_stop_data = {
        "name": "Main Entrance",
        "faculty_id": 1
    }
    update_data = {"name": "Updated Entrance"}
    bus_stop = BusStopUpdate(**{**bus_stop_data, **update_data})
    assert bus_stop.name == "Updated Entrance"
    assert bus_stop.faculty_id == 1

# Teste 5: Verificar se o sistema rejeita faculty_id inválido (ex.: negativo)
def test_invalid_faculty_id():
    invalid_data = {"name": "Side Gate", "faculty_id": -1}
    with pytest.raises(ValidationError):
        BusStopCreate(**invalid_data)
