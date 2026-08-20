def create_user(client, username, email):
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "Password123"
        }
    )

    assert response.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": "Password123"
        }
    )

    assert login.status_code == 200

    return login.json()["access_token"]


def create_tweet(client, token, text):
    response = client.post(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "text": text
        }
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_like_tweet(client):

    token = create_user(
        client,
        "likeuser",
        "like@example.com"
    )

    tweet_id = create_tweet(
        client,
        token,
        "Tweet to like"
    )

    response = client.post(
        f"/tweets/{tweet_id}/like",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code in [200, 201]


def test_like_count_and_liked_by_me(client):

    token = create_user(
        client,
        "countuser",
        "count@example.com"
    )

    tweet_id = create_tweet(
        client,
        token,
        "Like count test"
    )

    like_response = client.post(
        f"/tweets/{tweet_id}/like",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert like_response.status_code in [200, 201]

    response = client.get(
        f"/tweets/{tweet_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["like_count"] == 1
    assert data["liked_by_me"] is True


def test_duplicate_like_rejected(client):

    token = create_user(
        client,
        "duplicateuser",
        "duplicate@example.com"
    )

    tweet_id = create_tweet(
        client,
        token,
        "Duplicate like test"
    )

    first_like = client.post(
        f"/tweets/{tweet_id}/like",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert first_like.status_code in [200, 201]

    second_like = client.post(
        f"/tweets/{tweet_id}/like",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert second_like.status_code in [400, 409]


def test_unlike_tweet(client):

    token = create_user(
        client,
        "unlikeuser",
        "unlike@example.com"
    )

    tweet_id = create_tweet(
        client,
        token,
        "Tweet to unlike"
    )

    like_response = client.post(
        f"/tweets/{tweet_id}/like",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert like_response.status_code in [200, 201]

    unlike_response = client.delete(
        f"/tweets/{tweet_id}/like",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert unlike_response.status_code == 200

    tweet_response = client.get(
        f"/tweets/{tweet_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    data = tweet_response.json()

    assert data["like_count"] == 0
    assert data["liked_by_me"] is False
    