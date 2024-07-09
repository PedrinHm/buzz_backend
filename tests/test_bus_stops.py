import pytest

def test_create_bus_stop(test_app):
    response = test_app.post("/bus_stops/", json={
        "name": "Bus Stop 1",
        "university": "University 1"
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Bus Stop 1"

def test_read_bus_stops(test_app):
    # Primeiro, crie um ponto de ônibus para garantir que há algo para ler
    test_app.post("/bus_stops/", json={
        "name": "Bus Stop 2",
        "university": "University 2"
    })
    
    response = test_app.get("/bus_stops/")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_update_bus_stop(test_app):
    # Primeiro, crie um ponto de ônibus para garantir que há algo para atualizar
    response = test_app.post("/bus_stops/", json={
        "name": "Bus Stop 3",
        "university": "University 3"
    })
    bus_stop_id = response.json()["id"]
    
    response = test_app.put(f"/bus_stops/{bus_stop_id}", json={
        "name": "Updated Bus Stop 3",
        "university": "Updated University 3"
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Bus Stop 3"

def test_delete_bus_stop(test_app):
    # Primeiro, crie um ponto de ônibus para garantir que há algo para deletar
    response = test_app.post("/bus_stops/", json={
        "name": "Bus Stop 4",
        "university": "University 4"
    })
    bus_stop_id = response.json()["id"]
    
    response = test_app.delete(f"/bus_stops/{bus_stop_id}")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
