"""Smoke tests covering health check, registration, login, and admin bootstrap."""


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_login(client):
    register_payload = {
        "full_name": "Test Donor",
        "email": "donor@example.com",
        "password": "Aa@12345",
        "role": "donor",
    }
    register_response = client.post("/auth/register", json=register_payload)
    assert register_response.status_code == 200
    body = register_response.json()
    assert body["role"] == "donor"
    assert "access_token" in body

    login_response = client.post(
        "/auth/login",
        data={"username": "donor@example.com", "password": "Aa@12345"},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


def test_register_rejects_weak_password(client):
    response = client.post(
        "/auth/register",
        json={"full_name": "Weak Pw", "email": "weak@example.com", "password": "weak", "role": "needy"},
    )
    assert response.status_code == 400


def test_admin_login_with_env_credentials(client):
    response = client.post("/admin/login", json={"password": "TestAdmin@123"})
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_admin_login_wrong_password(client):
    response = client.post("/admin/login", json={"password": "wrong-password"})
    assert response.status_code == 401


def test_protected_route_requires_auth(client):
    response = client.get("/auth/me")
    assert response.status_code == 401
