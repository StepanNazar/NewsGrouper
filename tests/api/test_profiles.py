import time
import uuid
from types import MappingProxyType

import pytest

profile_data = MappingProxyType(
    {  # immutable dict view to ensure test isolation
        "name": "Test Profile",
        "description": "This is a test profile",
    }
)


def create_profile(client, profile_data: dict | MappingProxyType = profile_data):
    response = client.post("/api/profiles", json=profile_data.copy())
    return response.headers["Location"]


@pytest.fixture
def profile(authenticated_client):
    """Sets up a test case with a profile with profile_data"""
    return create_profile(authenticated_client)


@pytest.fixture
def cross_user_profiles(authenticated_client, authenticated_client2):
    """Creates profiles for two different users."""
    return (create_profile(authenticated_client), create_profile(authenticated_client2))


def test_post_profile(authenticated_client):
    response = authenticated_client.post("/api/profiles", json=profile_data.copy())

    assert response.status_code == 201
    assert "Location" in response.headers
    assert_response_matches_profile(response, profile_data)


def test_get_profile(authenticated_client, profile):
    response = authenticated_client.get(profile)

    assert response.status_code == 200
    assert_response_matches_profile(response, profile_data)


def test_put_profile(authenticated_client, profile):
    updated_profile = profile_data.copy()
    updated_profile["name"] = "Updated Profile"

    time.sleep(0.01)  # Ensure the updated timestamp is different
    response = authenticated_client.put(profile, json=updated_profile)

    assert response.status_code == 200
    assert_response_matches_profile(response, updated_profile)
    assert response.json["updated"] != response.json["created"]


def test_delete_profile(authenticated_client, profile):
    response = authenticated_client.delete(profile)

    assert response.status_code == 204

    response = authenticated_client.get(profile)

    assert response.status_code == 404


def test_get_profiles(authenticated_client):
    profiles = []
    for i in range(3):
        new_profile = profile_data.copy()
        new_profile["name"] = f"Profile {i + 1}"
        profiles.append(new_profile)
    for new_profile in profiles:
        create_profile(authenticated_client, new_profile)

    response = authenticated_client.get("/api/profiles?order=asc")

    assert response.status_code == 200
    assert "items" in response.json
    assert len(response.json["items"]) == 3
    for i, expected_profile in enumerate(profiles):
        returned_profile = response.json["items"][i]
        for key, value in expected_profile.items():
            assert returned_profile[key] == value


@pytest.mark.parametrize(
    "method,payload",
    [
        ("get", None),
        ("put", {"name": "Updated", "description": "Updated"}),
        ("delete", None),
    ],
)
def test_access_unowned_profile(
    authenticated_client, authenticated_client2, cross_user_profiles, method, payload
):
    client_profile, client2_profile = cross_user_profiles

    assert_clients_cant_access_unowned_profiles(
        authenticated_client,
        authenticated_client2,
        client_profile,
        client2_profile,
        method,
        payload,
    )

    if method != "get":
        assert_profile_unchanged(authenticated_client, client_profile, profile_data)
        assert_profile_unchanged(authenticated_client2, client2_profile, profile_data)


@pytest.mark.parametrize(
    "method,url,payload",
    [
        ("post", "/api/profiles", profile_data.copy()),
        ("get", "/api/profiles/1", None),
        ("put", "/api/profiles/1", profile_data.copy()),
        ("delete", "/api/profiles/1", None),
        ("get", "/api/profiles", None),
    ],
)
def test_unauthorized_access(client, method, url, payload):
    response = getattr(client, method)(url, json=payload)

    assert response.status_code == 401


@pytest.mark.parametrize(
    "method,payload",
    [
        ("get", None),
        ("put", profile_data.copy()),
        ("delete", None),
    ],
)
def test_profile_not_found(authenticated_client, method, payload):
    # create a profile to check it won't be returned
    profile_url = create_profile(authenticated_client)
    prefix, id = profile_url.rsplit("/", maxsplit=1)
    non_existent_profile_url = f"{prefix}/{int(id) + 1}"

    response = getattr(authenticated_client, method)(
        non_existent_profile_url, json=payload
    )
    assert response.status_code == 404


def test_get_with_huge_id(authenticated_client):
    response = authenticated_client.get(
        f"/api/profiles/{int(uuid.uuid4().hex, 16)}"
    )  # breaks sqlite

    assert response.status_code == 404


def assert_profile_unchanged(client, url, expected_data):
    """Verify profile wasn't modified."""
    response = client.get(url)
    assert response.status_code == 200
    assert_response_matches_profile(response, expected_data)


def assert_clients_cant_access_unowned_profiles(
    authenticated_client,
    authenticated_client2,
    client_profile,
    client2_profile,
    method,
    payload=None,
):
    response = getattr(authenticated_client2, method)(client_profile, json=payload)
    response2 = getattr(authenticated_client, method)(client2_profile, json=payload)

    assert response.status_code == 404
    assert response2.status_code == 404


def assert_response_matches_profile(response, profile):
    for key, value in profile.items():
        assert response.json[key] == value
    assert "id" in response.json
    assert "created" in response.json
    assert "updated" in response.json
