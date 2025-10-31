import time
import uuid

import pytest


@pytest.fixture
def profile_data():
    return {
        "name": "Test Profile",
        "description": "This is a test profile",
    }


@pytest.fixture
def post_profile(authenticated_client, profile_data):
    response = authenticated_client.post("/api/profiles", json=profile_data)
    return response


def test_post_profile(authenticated_client, profile_data):
    response = authenticated_client.post("/api/profiles", json=profile_data)

    assert response.status_code == 201
    assert "Location" in response.headers
    assert_profile_response(response, profile_data)


def test_post_profile_unauthorized(client, profile_data):
    response = client.post("/api/profiles", json=profile_data)

    assert response.status_code == 401


def test_get_profile(authenticated_client, profile_data):
    location = create_profile(authenticated_client, profile_data)

    response = authenticated_client.get(location)

    assert response.status_code == 200
    assert_profile_response(response, profile_data)


def test_get_profile_not_found(authenticated_client, post_profile):
    non_existent_id = random_id()
    response = authenticated_client.get(
        f"/api/profiles/{non_existent_id}"
    )  # breaks sqlite

    assert response.status_code == 404


def test_get_profile_unauthorized(client):
    response = client.get("/api/profiles/1")

    assert response.status_code == 401


def test_get_unowned_profile(authenticated_client, authenticated_client2, profile_data):
    location = create_profile(authenticated_client, profile_data)
    location2 = create_profile(authenticated_client2, profile_data)

    response = authenticated_client2.get(location)
    response2 = authenticated_client.get(location2)

    assert response.status_code == 404
    assert response2.status_code == 404


def test_put_profile(authenticated_client, profile_data):
    location = create_profile(authenticated_client, profile_data)
    updated_profile = profile_data.copy()
    updated_profile["name"] = "Updated Profile"

    time.sleep(0.01)  # Ensure updated timestamp is different
    response = authenticated_client.put(location, json=updated_profile)

    assert response.status_code == 200
    assert_profile_response(response, updated_profile)
    assert response.json["updated"] != response.json["created"]


def test_put_profile_not_found(authenticated_client, post_profile):
    non_existent_id = random_id()
    response = authenticated_client.put(f"/api/profiles/{non_existent_id}")

    assert response.status_code == 404


def test_put_profile_unauthorized(client, profile_data):
    response = client.put("/api/profiles/1", json=profile_data)

    assert response.status_code == 401


def test_put_unowned_profile(authenticated_client, authenticated_client2, profile_data):
    location = create_profile(authenticated_client, profile_data)
    location2 = create_profile(authenticated_client2, profile_data)
    updated_profile = profile_data.copy()
    updated_profile["name"] = "Updated Profile"

    response = authenticated_client2.put(location, json=updated_profile)
    response2 = authenticated_client.put(location2, json=updated_profile)

    assert response.status_code == 404
    assert response2.status_code == 404

    response = authenticated_client.get(location)
    response2 = authenticated_client2.get(location2)

    assert_profile_response(response, profile_data)
    assert_profile_response(response2, profile_data)


def test_delete_profile(authenticated_client, profile_data):
    location = create_profile(authenticated_client, profile_data)

    response = authenticated_client.delete(location)

    assert response.status_code == 204

    response = authenticated_client.get(location)
    assert response.status_code == 404


def test_delete_profile_not_found(authenticated_client, post_profile):
    not_existent_id = random_id()
    response = authenticated_client.delete(f"/api/profiles/{not_existent_id}")

    assert response.status_code == 404


def test_delete_profile_unauthorized(client):
    response = client.delete("/api/profiles/1")

    assert response.status_code == 401


def test_delete_unowned_profile(
    authenticated_client, authenticated_client2, profile_data
):
    location = create_profile(authenticated_client, profile_data)
    location2 = create_profile(authenticated_client2, profile_data)

    response = authenticated_client2.delete(location)
    response2 = authenticated_client.delete(location2)

    assert response.status_code == 404
    assert response2.status_code == 404

    response = authenticated_client.get(location)
    response2 = authenticated_client2.get(location2)

    assert response.status_code == 200
    assert response2.status_code == 200


def test_get_profiles(authenticated_client, profile_data):
    for i in range(3):
        new_profile = profile_data.copy()
        new_profile["name"] = f"Profile {i + 1}"
        authenticated_client.post("/api/profiles", json=new_profile)

    response = authenticated_client.get("/api/profiles")

    assert response.status_code == 200
    assert "items" in response.json
    assert len(response.json["items"]) == 3


def test_get_profiles_unauthorized(client):
    response = client.get("/api/profiles")

    assert response.status_code == 401


def create_profile(client, profile_data):
    response = client.post("/api/profiles", json=profile_data)
    return response.headers["Location"]


def assert_profile_response(response, profile):
    for key, value in profile.items():
        assert response.json[key] == value
    assert "id" in response.json
    assert "created" in response.json
    assert "updated" in response.json


def random_id() -> int:
    non_existent_id = int(uuid.uuid4().hex, 16)
    return non_existent_id
