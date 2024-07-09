def test_create_user(test_app):
    response = test_app.post("/users/", json={
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "testpassword",
        "cpf": "12345678909",
        "phone": "5511999999999",
        "user_type_id": 1  # Certifique-se de que esse ID existe na tabela user_types
    })
    assert response.status_code == 200
    assert response.json()["email"] == "testuser@example.com"

def test_read_users(test_app):
    response = test_app.get("/users/")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_update_user(test_app):
    response = test_app.put("/users/1", json={
        "email": "updateduser@example.com",
        "phone": "5511988888888"
    })
    assert response.status_code == 200
    assert response.json()["email"] == "updateduser@example.com"

def test_delete_user(test_app):
    response = test_app.delete("/users/1")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
