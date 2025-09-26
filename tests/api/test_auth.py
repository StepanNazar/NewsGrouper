from http.cookies import SimpleCookie


def test_register(client):
    response = register_user(client)

    assert response.status_code == 201
    assert_jwt_tokens(response)


def test_register_with_short_password(client):
    response = register_user(client, password="short")  # noqa: S106

    assert response.status_code == 422


def test_register_with_weak_password(client):
    response = register_user(client, password="1234567890")  # noqa: S106

    assert response.status_code == 400


def test_register_with_existing_email(client):
    register_user(client)

    response = register_user(client)

    assert response.status_code == 409


def test_login(client):
    register_user(client)

    response = login_user(client)

    assert response.status_code == 200
    assert_jwt_tokens(response)


def test_login_with_invalid_password(client):
    register_user(client)

    response = login_user(client, password="WrongPassw0rd!")  # noqa: S106

    assert response.status_code == 401


def test_login_with_nonexistent_email(client):
    register_user(client)

    response = login_user(client, email="wrong@example.com")

    assert response.status_code == 401


def test_whoami(client):
    response = register_user(
        client, first_name="First", last_name="Last", email="abcdemail@example.com"
    )
    access_token = response.json["access_token"]

    response = client.get(
        "/api/whoami", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json
    assert data["email"] == "abcdemail@example.com"
    assert data["first_name"] == "First"
    assert data["last_name"] == "Last"
    assert "id" in data
    assert "created" in data
    assert "updated" in data


def test_whoami_unauthorized(client):
    response = client.get("/api/whoami")

    assert response.status_code == 401


def test_refresh(client):
    response = register_user(client)
    access_token = response.json["access_token"]
    csrf_token = get_cookie_value(response, "csrf_refresh_token")

    response = client.post(
        "/api/refresh",
        headers={"X-CSRF-TOKEN": csrf_token},
    )

    assert response.status_code == 200
    assert "access_token" in response.json
    old_access_token = access_token
    access_token = response.json["access_token"]
    assert access_token != old_access_token

    response = client.get(
        "/api/whoami", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200


def test_refresh_missing_csrf(client):
    register_user(client)

    response = client.post("/api/refresh")

    assert response.status_code == 401


def test_refresh_invalid_csrf(client):
    register_user(client)

    response = client.post(
        "/api/refresh",
        headers={"X-CSRF-TOKEN": "invalid"},
    )

    assert response.status_code == 401


def test_logout(client):
    response = register_user(client)
    access_token = response.json["access_token"]

    response = client.post(
        "/api/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    cookies = SimpleCookie()
    for cookie_str in response.headers.get_all("Set-Cookie"):
        cookies.load(cookie_str)
    assert cookies["refresh_token_cookie"].value == ""
    assert cookies["csrf_refresh_token"].value == ""


def test_logout_without_token(client):
    response = register_user(client)

    response = client.post("/api/logout")

    assert response.status_code == 401


def assert_jwt_tokens(response):
    assert "access_token" in response.json

    assert "Set-Cookie" in response.headers
    cookies = SimpleCookie()
    for cookie_str in response.headers.get_all("Set-Cookie"):
        cookies.load(cookie_str)
    assert "refresh_token_cookie" in cookies
    assert "csrf_refresh_token" in cookies

    assert cookies["refresh_token_cookie"]["httponly"] is True
    assert cookies["refresh_token_cookie"]["secure"] is True
    assert cookies["refresh_token_cookie"]["samesite"].lower() == "strict"
    assert cookies["refresh_token_cookie"]["path"] == "/api/refresh"

    assert not cookies["csrf_refresh_token"]["httponly"]
    assert cookies["csrf_refresh_token"]["secure"] is True
    assert cookies["csrf_refresh_token"]["samesite"].lower() == "strict"
    assert cookies["csrf_refresh_token"]["path"] == "/api/refresh"


def get_cookie_value(response, cookie_name):
    cookies = SimpleCookie()
    for cookie_str in response.headers.get_all("Set-Cookie"):
        cookies.load(cookie_str)
    if cookie_name in cookies:
        return cookies[cookie_name].value
    return None


def register_user(
    client,
    first_name="Test",
    last_name="User",
    email="john.doe@example.com",
    password="SecurePassw0rd!",  # noqa: S107
):
    return client.post(
        "/api/register",
        json={
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
        },
    )


def login_user(client, email="john.doe@example.com", password="SecurePassw0rd!"):  # noqa: S107
    return client.post(
        "/api/login",
        json={
            "email": email,
            "password": password,
        },
    )
