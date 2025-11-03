import pytest
from conftest import (
    MockParser,
    assert_pagination_response,
    assert_resources_order_match,
    create_profile,
    create_source,
    profile_data,
    source_data,
)


def test_get_parsers(client):
    """Test getting a list of available parsers."""
    response = client.get("/api/parsers")

    assert response.status_code == 200
    assert isinstance(response.json, list)
    mock_parser_data = {
        "name": MockParser.name,
        "description": MockParser.description,
        "link_hint": MockParser.link_hint,
    }
    assert mock_parser_data in response.json


def test_post_source_with_invalid_link(authenticated_client, profile):
    """Test creating a source with an invalid link for parser."""
    invalid_source_data = source_data.copy()
    invalid_source_data["link"] = "https://invalid.com"

    response = authenticated_client.post(f"{profile}/sources", json=invalid_source_data)

    assert response.status_code == 400


def test_post_source_with_invalid_parser_name(authenticated_client, profile):
    """Test creating a source with an invalid parser name."""
    invalid_source_data = source_data.copy()
    invalid_source_data["parser_name"] = "fdyhbjnrfedufduhjnijnkrfd"

    response = authenticated_client.post(f"{profile}/sources", json=invalid_source_data)

    assert response.status_code == 422


def test_put_source_with_invalid_link(authenticated_client, source):
    """Test updating a source with an invalid link."""
    updated_source = source_data.copy()
    updated_source["link"] = "https://invalid.com"

    response = authenticated_client.put(source, json=updated_source)

    assert response.status_code == 400


def test_put_source_with_invalid_parser_name(authenticated_client, source):
    """Test updating a source with an invalid parser name."""
    updated_source = source_data.copy()
    updated_source["parser_name"] = "fdyhbjnrfedufduhjnijnkrfd"

    response = authenticated_client.put(source, json=updated_source)

    assert response.status_code == 422


def test_get_sources(authenticated_client, profile):
    """Test getting paginated list of sources."""
    sources = []
    for i in range(3):
        new_source = source_data.copy()
        new_source["name"] = f"Source {3 - i}"
        sources.append(new_source)
        create_source(authenticated_client, profile, new_source)
    # create a source in another profile to ensure sources from other profiles are not included in the response
    profile_data2 = profile_data.copy()
    profile_data2["name"] = "Another Profile"
    another_profile = create_profile(authenticated_client, profile_data2)
    create_source(authenticated_client, another_profile, source_data)

    response = authenticated_client.get(f"{profile}/sources?order=asc")

    assert_pagination_response(response, total=3, page=1, total_pages=1, items_count=3)
    assert_resources_order_match(response.json["items"], sources)

    response = authenticated_client.get(f"{profile}/sources?sort_by=name")

    assert_pagination_response(response, total=3, page=1, total_pages=1, items_count=3)
    assert_resources_order_match(response.json["items"], sources)

    response = authenticated_client.get(f"{profile}/sources?per_page=2&page=2")

    assert_pagination_response(response, total=3, page=2, total_pages=2, items_count=1)
    assert_resources_order_match(response.json["items"], [sources[0]])


def test_get_sources_filter_by_parser(authenticated_client, profile):
    """Test filtering sources by parser name."""
    source1 = source_data.copy()
    source1["parser_name"] = "mock_parser"
    source2 = source_data.copy()
    source2["parser_name"] = "mock_parser2"
    create_source(authenticated_client, profile, source1)
    create_source(authenticated_client, profile, source2)
    create_source(authenticated_client, profile, source2)

    response = authenticated_client.get(f"{profile}/sources?parser_name=mock_parser")

    assert_pagination_response(response, total=1, page=1, total_pages=1, items_count=1)

    response = authenticated_client.get(f"{profile}/sources?parser_name=mock_parser2")

    assert_pagination_response(response, total=2, page=1, total_pages=1, items_count=2)


@pytest.mark.parametrize(
    "method,payload",
    [
        ("get", None),
        ("put", source_data.copy()),
        ("delete", None),
    ],
)
def test_source_not_found(authenticated_client, method, payload, source):
    """Test that non-existent sources return 404."""
    prefix, id = source.rsplit("/", maxsplit=1)
    non_existent_source_url = f"{prefix}/{int(id) + 1}"

    response = getattr(authenticated_client, method)(
        non_existent_source_url, json=payload
    )

    assert response.status_code == 404


def test_profile_not_found_on_creating_source(authenticated_client):
    """Test creating a source for a non-existent profile."""
    response = authenticated_client.post(
        "/api/profiles/99999/sources", json=source_data.copy()
    )

    assert response.status_code == 404


def test_profile_not_found_on_getting_sources(authenticated_client):
    """Test getting sources for non-existent profile."""
    response = authenticated_client.get("/api/profiles/99999/sources")

    assert response.status_code == 404
