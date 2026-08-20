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


def test_create_comment(client):

    token = create_user(
        client,
        "commentuser",
        "comment@example.com"
    )

    tweet_id = create_tweet(
        client,
        token,
        "Tweet for commenting"
    )

    response = client.post(
        f"/tweets/{tweet_id}/comments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "text": "This is a test comment"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["text"] == "This is a test comment"
    assert data["username"] == "commentuser"
    assert data["tweet_id"] == tweet_id


def test_get_comments(client):

    token = create_user(
        client,
        "reader",
        "reader@example.com"
    )

    tweet_id = create_tweet(
        client,
        token,
        "Tweet with comments"
    )

    client.post(
        f"/tweets/{tweet_id}/comments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "text": "First comment"
        }
    )

    client.post(
        f"/tweets/{tweet_id}/comments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "text": "Second comment"
        }
    )

    response = client.get(
        f"/tweets/{tweet_id}/comments",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["comments"]) == 2


def test_comment_count_in_tweet(client):

    token = create_user(
        client,
        "counter",
        "counter@example.com"
    )

    tweet_id = create_tweet(
        client,
        token,
        "Comment count test"
    )

    response = client.get(
        f"/tweets/{tweet_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["comment_count"] == 0

    client.post(
        f"/tweets/{tweet_id}/comments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "text": "One comment"
        }
    )

    response = client.get(
        f"/tweets/{tweet_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["comment_count"] == 1


def test_update_own_comment(client):

    token = create_user(
        client,
        "commenteditor",
        "editor@example.com"
    )

    tweet_id = create_tweet(
        client,
        token,
        "Edit comment test"
    )

    create_response = client.post(
        f"/tweets/{tweet_id}/comments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "text": "Original comment"
        }
    )

    comment_id = create_response.json()["id"]

    response = client.put(
        f"/comments/{comment_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "text": "Updated comment"
        }
    )

    assert response.status_code == 200
    assert response.json()["text"] == "Updated comment"


def test_delete_own_comment(client):

    token = create_user(
        client,
        "commentdeleter",
        "deleter@example.com"
    )

    tweet_id = create_tweet(
        client,
        token,
        "Delete comment test"
    )

    create_response = client.post(
        f"/tweets/{tweet_id}/comments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "text": "Comment to delete"
        }
    )

    comment_id = create_response.json()["id"]

    response = client.delete(
        f"/comments/{comment_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/tweets/{tweet_id}/comments",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert get_response.status_code == 200
    assert get_response.json()["total"] == 0


def test_cannot_modify_another_users_comment(client):

    owner_token = create_user(
        client,
        "commentowner",
        "owner@example.com"
    )

    tweet_id = create_tweet(
        client,
        owner_token,
        "Ownership test"
    )

    create_response = client.post(
        f"/tweets/{tweet_id}/comments",
        headers={
            "Authorization": f"Bearer {owner_token}"
        },
        json={
            "text": "Owner comment"
        }
    )

    comment_id = create_response.json()["id"]

    attacker_token = create_user(
        client,
        "commentattacker",
        "attacker@example.com"
    )

    update_response = client.put(
        f"/comments/{comment_id}",
        headers={
            "Authorization": f"Bearer {attacker_token}"
        },
        json={
            "text": "Trying to change it"
        }
    )

    assert update_response.status_code == 403

    delete_response = client.delete(
        f"/comments/{comment_id}",
        headers={
            "Authorization": f"Bearer {attacker_token}"
        }
    )

    assert delete_response.status_code == 403