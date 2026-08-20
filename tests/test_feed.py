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


def test_feed_only_contains_followed_users(client):

    # Current user
    current_token = create_user(
        client,
        "feeduser",
        "feed@example.com"
    )

    # User we follow
    followed_token = create_user(
        client,
        "followeduser",
        "followed@example.com"
    )

    # User we DON'T follow
    stranger_token = create_user(
        client,
        "stranger",
        "stranger@example.com"
    )

    # Follow followeduser
    response = client.post(
        "/users/followeduser/follow",
        headers={
            "Authorization": f"Bearer {current_token}"
        }
    )

    assert response.status_code == 201

    # Followed user's tweet
    create_tweet(
        client,
        followed_token,
        "Tweet from followed user"
    )

    # Stranger's tweet
    create_tweet(
        client,
        stranger_token,
        "Tweet from stranger"
    )

    # Get feed
    response = client.get(
        "/feed/",
        headers={
            "Authorization": f"Bearer {current_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["tweets"]) == 1

    assert (
        data["tweets"][0]["username"]
        == "followeduser"
    )

    assert (
        data["tweets"][0]["text"]
        == "Tweet from followed user"
    )


def test_feed_includes_like_and_comment_counts(client):

    current_token = create_user(
        client,
        "feedviewer",
        "feedviewer@example.com"
    )

    followed_token = create_user(
        client,
        "feedcreator",
        "feedcreator@example.com"
    )

    # Follow creator
    response = client.post(
        "/users/feedcreator/follow",
        headers={
            "Authorization": f"Bearer {current_token}"
        }
    )

    assert response.status_code == 201

    tweet_id = create_tweet(
        client,
        followed_token,
        "Feed metadata test"
    )

    # Like the tweet
    like_response = client.post(
        f"/tweets/{tweet_id}/like",
        headers={
            "Authorization": f"Bearer {current_token}"
        }
    )

    assert like_response.status_code in [200, 201]

    # Add comment
    comment_response = client.post(
        f"/tweets/{tweet_id}/comments",
        headers={
            "Authorization": f"Bearer {current_token}"
        },
        json={
            "text": "Great tweet!"
        }
    )

    assert comment_response.status_code == 201

    # Get feed
    response = client.get(
        "/feed/",
        headers={
            "Authorization": f"Bearer {current_token}"
        }
    )

    assert response.status_code == 200

    tweet = response.json()["tweets"][0]

    assert tweet["like_count"] == 1
    assert tweet["liked_by_me"] is True
    assert tweet["comment_count"] == 1