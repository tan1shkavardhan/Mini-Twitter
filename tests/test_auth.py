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

    # Register user first
    register_response = client.post(
        "/auth/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "Password123"
        }
    )

    assert register_response.status_code == 201

    # Login
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