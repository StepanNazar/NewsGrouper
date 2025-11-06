import time

import pytest
from conftest import (
    assert_response_matches_resource,
    lf,
    profile,
    profile_data,
    source,
    source_data,
    updated_profile_data,
    updated_source_data,
)


@pytest.fixture
def base_api_path():
    return "/api"


@pytest.mark.parametrize(
    "resource_parent,resource_name,resource_data",
    [
        (lf(base_api_path), "profiles", profile_data),
        (lf(profile), "sources", source_data),
    ],
)
def test_post_resource(
    authenticated_client, resource_parent, resource_name, resource_data
):
    """General test case for testing creation of any resource."""
    response = authenticated_client.post(
        f"{resource_parent}/{resource_name}", json=resource_data.copy()
    )

    assert response.status_code == 201
    assert "Location" in response.headers
    assert_response_matches_resource(
        response, resource_data, additional_keys=["id", "created", "updated"]
    )


@pytest.mark.parametrize(
    "resource,resource_data",
    [
        (lf(profile), profile_data),
        (lf(source), source_data),
    ],
)
def test_get_resource(authenticated_client, resource, resource_data):
    """General test case for testing reading of any resource."""
    response = authenticated_client.get(resource)

    assert response.status_code == 200
    assert_response_matches_resource(
        response, resource_data, additional_keys=["id", "created", "updated"]
    )


@pytest.mark.parametrize(
    "resource,updated_resource_data",
    [
        (lf(profile), updated_profile_data),
        (lf(source), updated_source_data),
    ],
)
def test_put_resource(authenticated_client, resource, updated_resource_data):
    """General test case for testing updating of any resource."""
    time.sleep(0.01)  # Ensure the updated timestamp is different
    response = authenticated_client.put(resource, json=updated_resource_data.copy())

    assert response.status_code == 200
    assert_response_matches_resource(
        response, updated_resource_data, additional_keys=["id", "created", "updated"]
    )
    assert response.json["updated"] != response.json["created"]


@pytest.mark.parametrize(
    "resource",
    [lf(profile), lf(source)],
)
def test_delete_resource(authenticated_client, resource):
    """General test case for testing deletion of any resource."""
    response = authenticated_client.delete(resource)

    assert response.status_code == 204

    response = authenticated_client.get(resource)

    assert response.status_code == 404
