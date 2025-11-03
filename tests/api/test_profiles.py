import uuid

import pytest
from conftest import (
    assert_pagination_response,
    assert_resources_order_match,
    create_profile,
    profile_data,
)


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
