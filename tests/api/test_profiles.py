import time
import uuid

import pytest
from conftest import (
    assert_pagination_response,
    assert_resources_order_match,
    assert_response_matches_resource,
    create_profile,
    profile_data,
    updated_profile_data,
)


def test_post_profile(authenticated_client):
    response = authenticated_client.post("/api/profiles", json=profile_data.copy())

    assert response.status_code == 201
    assert "Location" in response.headers
    assert_response_matches_resource(
        response, profile_data, additional_keys=["id", "created", "updated"]
    )


def test_get_profile(authenticated_client, profile):
    response = authenticated_client.get(profile)

    assert response.status_code == 200
    assert_response_matches_resource(
        response, profile_data, additional_keys=["id", "created", "updated"]
    )


def test_put_profile(authenticated_client, profile):
    time.sleep(0.01)  # Ensure the updated timestamp is different
    response = authenticated_client.put(profile, json=updated_profile_data.copy())

    assert response.status_code == 200
    assert_response_matches_resource(
        response, updated_profile_data, additional_keys=["id", "created", "updated"]
    )
    assert response.json["updated"] != response.json["created"]


def test_delete_profile(authenticated_client, profile):
    response = authenticated_client.delete(profile)

    assert response.status_code == 204

    response = authenticated_client.get(profile)

    assert response.status_code == 404


def test_get_profiles(authenticated_client, authenticated_client2):
    profiles = []
    for i in range(3):
        new_profile = profile_data.copy()
        new_profile["name"] = f"Profile {3 - i}"
        profiles.append(new_profile)
    for new_profile in profiles:
        create_profile(authenticated_client, new_profile)
    # create a profile in another user to ensure profiles from other users are not included in the response
    create_profile(authenticated_client2, profile_data)

    response = authenticated_client.get("/api/profiles?order=asc")

    assert_pagination_response(response, total=3, page=1, total_pages=1, items_count=3)
    assert_resources_order_match(response.json["items"], profiles)

    response = authenticated_client.get("/api/profiles?sort_by=name")

    assert_pagination_response(response, total=3, page=1, total_pages=1, items_count=3)
    assert_resources_order_match(response.json["items"], profiles)

    response = authenticated_client.get("/api/profiles?per_page=2&page=2")

    assert_pagination_response(response, total=3, page=2, total_pages=2, items_count=1)
    assert_resources_order_match(response.json["items"], [profiles[0]])


@pytest.mark.parametrize(
    "method,payload",
    [
        ("get", None),
        ("put", profile_data.copy()),
        ("delete", None),
    ],
)
def test_profile_not_found(authenticated_client, method, payload, profile):
    prefix, id = profile.rsplit("/", maxsplit=1)
    non_existent_profile_url = f"{prefix}/{int(id) + 1}"

    response = getattr(authenticated_client, method)(
        non_existent_profile_url, json=payload
    )
    assert response.status_code == 404


def test_get_with_huge_id(authenticated_client):
    response = authenticated_client.get(f"/api/profiles/{int(uuid.uuid4().hex, 16)}")

    assert response.status_code == 404
