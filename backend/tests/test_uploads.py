from io import BytesIO

from PIL import Image


def create_user(client):
    client.post(
        "/auth/register",
        json={
            "username": "uploaduser",
            "email": "upload@example.com",
            "password": "Password123"
        }
    )

    response = client.post(
        "/auth/login",
        json={
            "username": "uploaduser",
            "password": "Password123"
        }
    )

    return response.json()["access_token"]


def create_test_image(
    image_format="JPEG"
):
    image = Image.new(
        "RGB",
        (100, 100)
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format=image_format
    )

    buffer.seek(0)

    return buffer


def test_valid_jpeg_upload(client):

    token = create_user(client)

    image = create_test_image("JPEG")

    response = client.post(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "text": "Tweet with JPEG"
        },
        files={
            "photo": (
                "test.jpg",
                image,
                "image/jpeg"
            )
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["photo"] is not None


def test_valid_png_upload(client):

    token = create_user(client)

    image = create_test_image("PNG")

    response = client.post(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "text": "Tweet with PNG"
        },
        files={
            "photo": (
                "test.png",
                image,
                "image/png"
            )
        }
    )

    assert response.status_code == 201


def test_fake_image_rejected(client):

    token = create_user(client)

    fake_file = BytesIO(
        b"This is not actually an image"
    )

    response = client.post(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "text": "Fake image"
        },
        files={
            "photo": (
                "fake.jpg",
                fake_file,
                "image/jpeg"
            )
        }
    )

    assert response.status_code == 400


def test_wrong_content_type_rejected(client):

    token = create_user(client)

    image = create_test_image("JPEG")

    response = client.post(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "text": "Wrong content type"
        },
        files={
            "photo": (
                "test.jpg",
                image,
                "text/plain"
            )
        }
    )

    assert response.status_code == 400


def test_empty_image_rejected(client):

    token = create_user(client)

    empty_file = BytesIO(b"")

    response = client.post(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "text": "Empty image"
        },
        files={
            "photo": (
                "empty.jpg",
                empty_file,
                "image/jpeg"
            )
        }
    )

    assert response.status_code == 400


def test_invalid_extension_rejected(client):

    token = create_user(client)

    image = create_test_image("JPEG")

    response = client.post(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "text": "Invalid extension"
        },
        files={
            "photo": (
                "test.exe",
                image,
                "image/jpeg"
            )
        }
    )

    assert response.status_code == 400

def test_oversized_image_rejected(client):

    token = create_user(client)

    oversized_file = BytesIO(
        b"x" * (5 * 1024 * 1024 + 1)
    )

    response = client.post(
        "/tweets/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data={
            "text": "Oversized image"
        },
        files={
            "photo": (
                "large.jpg",
                oversized_file,
                "image/jpeg"
            )
        }
    )

    assert response.status_code == 413
    