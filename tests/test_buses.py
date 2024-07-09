def test_create_bus(test_app):
    response = test_app.post("/buses/", json={
        "name": "Bus 1",
        "registration_number": "ABC1234",
        "model": "Model X",
        "capacity": 50
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Bus 1"

def test_read_buses(test_app):
    response = test_app.get("/buses/")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_update_bus(test_app):
    response = test_app.put("/buses/1", json={
        "name": "Updated Bus 1",
        "model": "Model Y",
        "capacity": 60
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Bus 1"

def test_delete_bus(test_app):
    response = test_app.delete("/buses/1")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
