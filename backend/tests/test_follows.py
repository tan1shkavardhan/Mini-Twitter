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


def test_follow_user(client):

    token = create_user(
        client,
        "follower",
        "follower@example.com"
    )

    create_user(
        client,
        "target",
        "target@example.com"
    )

    response = client.post(
        "/users/target/follow",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "target"


def test_duplicate_follow_rejected(client):

    token = create_user(
        client,
        "duplicatefollower",
        "duplicatefollower@example.com"
    )

    create_user(
        client,
        "duplicatetarget",
        "duplicatetarget@example.com"
    )

    first = client.post(
        "/users/duplicatetarget/follow",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert first.status_code == 201

    second = client.post(
        "/users/duplicatetarget/follow",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert second.status_code in [400, 409]


def test_cannot_follow_self(client):

    token = create_user(
        client,
        "selffollower",
        "selffollower@example.com"
    )

    response = client.post(
        "/users/selffollower/follow",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 400


def test_followers_list(client):

    follower_token = create_user(
        client,
        "listfollower",
        "listfollower@example.com"
    )

    create_user(
        client,
        "listtarget",
        "listtarget@example.com"
    )

    client.post(
        "/users/listtarget/follow",
        headers={
            "Authorization": f"Bearer {follower_token}"
        }
    )

    response = client.get(
        "/users/listtarget/followers",
        headers={
            "Authorization": f"Bearer {follower_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["followers_count"] == 1
    assert data["followers"][0]["username"] == "listfollower"


def test_following_list(client):

    token = create_user(
        client,
        "followinguser",
        "following@example.com"
    )

    create_user(
        client,
        "followeduser",
        "followed@example.com"
    )

    client.post(
        "/users/followeduser/follow",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    response = client.get(
        "/users/followinguser/following",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["following_count"] == 1
    assert data["following"][0]["username"] == "followeduser"


def test_unfollow_user(client):

    token = create_user(
        client,
        "unfollower",
        "unfollower@example.com"
    )

    create_user(
        client,
        "unfollowtarget",
        "unfollowtarget@example.com"
    )

    client.post(
        "/users/unfollowtarget/follow",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    response = client.delete(
        "/users/unfollowtarget/follow",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    following = client.get(
        "/users/unfollower/following",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert following.status_code == 200
    assert following.json()["following_count"] == 0


def test_unfollow_when_not_following(client):

    token = create_user(
        client,
        "notfollowing",
        "notfollowing@example.com"
    )

    create_user(
        client,
        "neverfollowed",
        "neverfollowed@example.com"
    )

    response = client.delete(
        "/users/neverfollowed/follow",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 404

def test_follow_state_after_unfollow(client):

    follower_token = create_user(
        client,
        "statefollower",
        "statefollower@example.com"
    )

    create_user(
        client,
        "statetarget",
        "statetarget@example.com"
    )

    # Follow
    follow_response = client.post(
        "/users/statetarget/follow",
        headers={
            "Authorization": f"Bearer {follower_token}"
        }
    )

    assert follow_response.status_code == 201

    # Check profile
    profile_response = client.get(
        "/users/statetarget",
        headers={
            "Authorization": f"Bearer {follower_token}"
        }
    )

    assert profile_response.status_code == 200

    profile = profile_response.json()

    assert profile["following"] is True

    # Unfollow
    unfollow_response = client.delete(
        "/users/statetarget/follow",
        headers={
            "Authorization": f"Bearer {follower_token}"
        }
    )

    assert unfollow_response.status_code == 200

    # Check profile again
    profile_response = client.get(
        "/users/statetarget",
        headers={
            "Authorization": f"Bearer {follower_token}"
        }
    )

    assert profile_response.status_code == 200

    profile = profile_response.json()

    assert profile["following"] is False