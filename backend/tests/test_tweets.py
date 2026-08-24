def get_auth_token(client):
    client.post(
        "/auth/register",
        json={
            "username": "tweetuser",
            "email": "tweet@example.com",
            "password": "Password123"
        }
    )

    response = client.post(
        "/auth/login",
        json={
            "username": "tweetuser",
            "password": "Password123"
        }
    )

    return response.json()["access_token"]


def test_create_tweet(client):

    token = get_auth_token(client)

    response = client.post(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "text": "Hello from pytest!"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["text"] == "Hello from pytest!"
    assert data["username"] == "tweetuser"
    assert data["like_count"] == 0
    assert data["liked_by_me"] is False
    assert data["comment_count"] == 0


def test_get_tweets(client):

    token = get_auth_token(client)

    client.post(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "text": "First test tweet"
        }
    )

    client.post(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "text": "Second test tweet"
        }
    )

    response = client.get(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["tweets"]) == 2
    assert data["tweets"][0]["text"] == "Second test tweet"


def test_update_own_tweet(client):

    token = get_auth_token(client)

    create_response = client.post(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "text": "Original tweet"
        }
    )

    tweet_id = create_response.json()["id"]

    response = client.put(
        f"/tweets/{tweet_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "text": "Updated tweet"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["text"] == "Updated tweet"


def test_delete_own_tweet(client):

    token = get_auth_token(client)

    create_response = client.post(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "text": "Tweet to delete"
        }
    )

    tweet_id = create_response.json()["id"]

    response = client.delete(
        f"/tweets/{tweet_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/tweets/{tweet_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert get_response.status_code == 404


def test_cannot_modify_another_users_tweet(client):

    # -------------------------
    # Create user 1
    # -------------------------

    client.post(
        "/auth/register",
        json={
            "username": "userone",
            "email": "userone@example.com",
            "password": "Password123"
        }
    )

    login_one = client.post(
        "/auth/login",
        json={
            "username": "userone",
            "password": "Password123"
        }
    )

    token_one = login_one.json()["access_token"]

    # -------------------------
    # User 1 creates tweet
    # -------------------------

    create_response = client.post(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token_one}"
        },
        data={
            "text": "User one's private tweet"
        }
    )

    tweet_id = create_response.json()["id"]

    # -------------------------
    # Create user 2
    # -------------------------

    client.post(
        "/auth/register",
        json={
            "username": "usertwo",
            "email": "usertwo@example.com",
            "password": "Password123"
        }
    )

    login_two = client.post(
        "/auth/login",
        json={
            "username": "usertwo",
            "password": "Password123"
        }
    )

    token_two = login_two.json()["access_token"]

    # -------------------------
    # User 2 tries to edit
    # -------------------------

    update_response = client.put(
        f"/tweets/{tweet_id}",
        headers={
            "Authorization": f"Bearer {token_two}"
        },
        json={
            "text": "Hacked tweet"
        }
    )

    assert update_response.status_code == 403

    # -------------------------
    # User 2 tries to delete
    # -------------------------

    delete_response = client.delete(
        f"/tweets/{tweet_id}",
        headers={
            "Authorization": f"Bearer {token_two}"
        }
    )

    assert delete_response.status_code == 403