import pytest
from pydantic import ValidationError
from your_module.models.bus import BusCreate, BusUpdate

# Teste 1: Verificar se o número de registro está sendo convertido para letras maiúsculas
def test_uppercase_registration_number():
    bus_data = {
        "registration_number": "abc1234",
        "name": "Bus One",
        "capacity": 50
    }
    bus = BusCreate(**bus_data)
    assert bus.registration_number == "ABC1234"

# Teste 2: Verificar validação do formato correto do número de registro (padrão válido)
def test_valid_registration_number():
    valid_data = [
        {"registration_number": "ABC1234", "name": "Bus One", "capacity": 50},
        {"registration_number": "ABC1A23", "name": "Bus Two", "capacity": 45}
    ]
    for data in valid_data:
        bus = BusCreate(**data)
        assert bus.registration_number == data["registration_number"]

# Teste 3: Verificar se a validação falha quando o número de registro está no formato inválido
def test_invalid_registration_number():
    invalid_data = [
        {"registration_number": "ABC12", "name": "Bus One", "capacity": 50},
        {"registration_number": "1234ABC", "name": "Bus Two", "capacity": 45}
    ]
    for data in invalid_data:
        with pytest.raises(ValidationError):
            BusCreate(**data)

# Teste 4: Verificar se a capacidade não pode ser nula ao criar um ônibus
def test_capacity_is_required():
    with pytest.raises(ValidationError):
        BusCreate(registration_number="ABC1234", name="Bus Without Capacity")

# Teste 5: Verificar atualização do nome do ônibus com sucesso
def test_update_bus_name():
    bus_data = {
        "registration_number": "ABC1234",
        "name": "Bus One",
        "capacity": 50
    }
    bus_update_data = {"name": "Updated Bus"}
    bus = BusUpdate(**{**bus_data, **bus_update_data})
    assert bus.name == "Updated Bus"
