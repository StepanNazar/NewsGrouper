import pytest
from conftest import (
    assert_response_matches_resource,
    create_profile,
    create_source,
    profile_data,
    source_data,
    updated_profile_data,
    updated_source_data,
)

from tests.api.conftest import lf


@pytest.fixture
def cross_user_profiles(authenticated_client, authenticated_client2):
    """Creates profiles for two different users.
    :returns profile's url of one user, profile's url of another user, and the original profile data used
    """
    return (
        create_profile(authenticated_client),
        create_profile(authenticated_client2),
        profile_data,
    )


@pytest.fixture
def cross_user_sources(
    authenticated_client, authenticated_client2, cross_user_profiles
):
    """Creates sources for two different users.
    :returns source's url of one user, source's url of another user, and the original source data used
    """
    profile1, profile2, _ = cross_user_profiles
    source1 = create_source(authenticated_client, profile1)
    source2 = create_source(authenticated_client2, profile2)
    return source1, source2, source_data


@pytest.mark.parametrize(
    "method,url,payload",
    [
        ("post", "/api/profiles", profile_data.copy()),
        ("get", "/api/profiles/1", None),
        ("put", "/api/profiles/1", profile_data.copy()),
        ("delete", "/api/profiles/1", None),
        ("get", "/api/profiles", None),
        ("post", "/api/profiles/1/sources", source_data.copy()),
        ("get", "/api/profiles/1/sources", None),
        ("get", "/api/sources/1", None),
        ("put", "/api/sources/1", source_data.copy()),
        ("delete", "/api/sources/1", None),
    ],
)
def test_unauthorized_access(client, method, url, payload):
    response = getattr(client, method)(url, json=payload)

    assert response.status_code == 401


@pytest.mark.parametrize(
    "method,payload,cross_user_resources",
    [
        ("get", None, lf(cross_user_profiles)),
        ("put", updated_profile_data.copy(), lf(cross_user_profiles)),
        ("delete", None, lf(cross_user_profiles)),
        ("get", None, lf(cross_user_sources)),
        ("put", updated_source_data.copy(), lf(cross_user_sources)),
        ("delete", None, lf(cross_user_sources)),
    ],
)
def test_access_unowned_profile(
    authenticated_client,
    authenticated_client2,
    cross_user_resources,
    method,
    payload,
):
    client_resource, client2_resource, original_resource_data = cross_user_resources

    response = getattr(authenticated_client2, method)(client_resource, json=payload)

    assert response.status_code == 404

    response = getattr(authenticated_client, method)(client2_resource, json=payload)

    assert response.status_code == 404

    if method != "get":
        assert_resource_unchanged(
            authenticated_client, client_resource, original_resource_data
        )
        assert_resource_unchanged(
            authenticated_client2, client2_resource, original_resource_data
        )


def assert_resource_unchanged(client, url, expected_data):
    """Verify the resource wasn't modified."""
    response = client.get(url)

    assert response.status_code == 200
    assert_response_matches_resource(
        response, expected_data, additional_keys=["id", "created", "updated"]
    )
