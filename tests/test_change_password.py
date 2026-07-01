"""Tests for the authenticated Change Password endpoint."""


def _register_and_get_token(client, email="pwuser@example.com", password="Aa@12345"):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Password User",
            "email": email,
            "password": password,
            "role": "needy",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_change_password_requires_auth(client):
    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "Aa@12345",
            "new_password": "Bb@67890",
            "confirm_password": "Bb@67890",
        },
    )
    assert response.status_code == 401


def test_change_password_success_and_old_password_invalidated(client):
    token = _register_and_get_token(client, "pwsuccess@example.com", "Aa@12345")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "Aa@12345",
            "new_password": "Bb@67890",
            "confirm_password": "Bb@67890",
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully."

    # Old password must no longer work.
    old_login = client.post(
        "/auth/login",
        data={"username": "pwsuccess@example.com", "password": "Aa@12345"},
    )
    assert old_login.status_code == 401

    # New password must work immediately.
    new_login = client.post(
        "/auth/login",
        data={"username": "pwsuccess@example.com", "password": "Bb@67890"},
    )
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()

    # The original JWT (issued before the change) is still valid, since the
    # existing stateless-JWT design has no revocation store.
    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200


def test_change_password_wrong_current_password(client):
    token = _register_and_get_token(client, "pwwrongcurrent@example.com", "Aa@12345")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "WrongOne@1",
            "new_password": "Bb@67890",
            "confirm_password": "Bb@67890",
        },
        headers=headers,
    )
    assert response.status_code == 401


def test_change_password_mismatched_confirmation(client):
    token = _register_and_get_token(client, "pwmismatch@example.com", "Aa@12345")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "Aa@12345",
            "new_password": "Bb@67890",
            "confirm_password": "Cc@67890",
        },
        headers=headers,
    )
    assert response.status_code == 400


def test_change_password_weak_new_password(client):
    token = _register_and_get_token(client, "pwweak@example.com", "Aa@12345")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "Aa@12345",
            "new_password": "weakpass",
            "confirm_password": "weakpass",
        },
        headers=headers,
    )
    assert response.status_code == 400


def test_change_password_same_as_current(client):
    token = _register_and_get_token(client, "pwsame@example.com", "Aa@12345")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "Aa@12345",
            "new_password": "Aa@12345",
            "confirm_password": "Aa@12345",
        },
        headers=headers,
    )
    assert response.status_code == 400
