from datetime import datetime, timedelta, timezone

import jwt

from app.settings import settings


def test_register_user(client):

    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "Password123"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "created_at" in data


def test_duplicate_username(client):

    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Password123"
    }

    first_response = client.post(
        "/auth/register",
        json=payload
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "another@example.com",
            "password": "Password123"
        }
    )

    assert second_response.status_code in [400, 409]


def test_login(client):

    register_response = client.post(
        "/auth/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "Password123"
        }
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "username": "loginuser",
            "password": "Password123"
        }
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):

    client.post(
        "/auth/register",
        json={
            "username": "wrongpass",
            "email": "wrong@example.com",
            "password": "Password123"
        }
    )

    response = client.post(
        "/auth/login",
        json={
            "username": "wrongpass",
            "password": "WrongPassword"
        }
    )

    assert response.status_code in [400, 401]


def test_missing_token(client):

    response = client.get(
        "/auth/me"
    )

    assert response.status_code == 401


def test_invalid_token(client):

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer definitely-not-a-real-token"
        }
    )

    assert response.status_code == 401


def test_malformed_authorization_header(client):

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "NotBearer token"
        }
    )

    assert response.status_code == 401


def test_unknown_user_token(client):

    token = jwt.encode(
        {
            "sub": "999999999",
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 401


def test_expired_token(client):

    token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(
                minutes=5
            )
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 401


def test_protected_endpoints_require_auth(client):

    protected_endpoints = [
        ("/auth/me", "get"),
        ("/tweets/", "get"),
        ("/feed/", "get"),
    ]

    for path, method in protected_endpoints:

        if method == "get":
            response = client.get(path)

        assert response.status_code == 401