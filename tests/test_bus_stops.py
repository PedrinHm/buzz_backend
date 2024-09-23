import pytest

def test_create_bus_stop(test_app):
    response = test_app.post("/bus_stops/", json={
        "name": "Bus Stop 1",
        "faculty_id": 1  # Utiliza o faculty_id existente
    })
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["name"] == "Bus Stop 1"
    assert json_response["faculty_id"] == 1
    assert "system_deleted" in json_response
    assert json_response["system_deleted"] == 0  # Verifica o valor padrão
    assert "create_date" in json_response
    assert "update_date" in json_response

def test_read_bus_stops(test_app):
    # Cria um ponto de ônibus para garantir que há algo para ler
    test_app.post("/bus_stops/", json={
        "name": "Bus Stop 2",
        "faculty_id": 1  # Utiliza o faculty_id existente
    })
    
    response = test_app.get("/bus_stops/")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_update_bus_stop(test_app):
    # Cria um ponto de ônibus para garantir que há algo para atualizar
    response = test_app.post("/bus_stops/", json={
        "name": "Bus Stop 3",
        "faculty_id": 1  # Utiliza o faculty_id existente
    })
    assert response.status_code == 200
    bus_stop_id = response.json()["id"]
    
    response = test_app.put(f"/bus_stops/{bus_stop_id}", json={
        "name": "Updated Bus Stop 3",
        "faculty_id": 1  # Mantém o mesmo faculty_id
    })
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["name"] == "Updated Bus Stop 3"
    assert "update_date" in json_response  # Verifica se a data de atualização foi alterada

def test_delete_bus_stop(test_app):
    # Cria um ponto de ônibus para garantir que há algo para deletar
    response = test_app.post("/bus_stops/", json={
        "name": "Bus Stop 4",
        "faculty_id": 1  # Utiliza o faculty_id existente
    })
    assert response.status_code == 200
    bus_stop_id = response.json()["id"]
    
    response = test_app.delete(f"/bus_stops/{bus_stop_id}")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
