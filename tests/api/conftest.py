from datetime import UTC, datetime
from types import MappingProxyType

import pytest
from pytest_lazy_fixtures import lf as _lf

from news_grouper.api import create_app
from news_grouper.api import db as _db
from news_grouper.api.common.models import Post
from news_grouper.api.config import TestConfig
from news_grouper.api.news_sources.news_parsers import NewsParser


@pytest.fixture(autouse=True, scope="session")
def app():
    """
    Application instantiator for each unit test session.

    1) Build the application base at beginning of session
    2) Create database tables, yield the app for individual tests
    3) Final tear down logic at the end of the session
    """
    app = create_app(TestConfig)

    with app.app_context():
        _db.create_all()

        yield app

        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def db(app):
    """Database fixture with table truncation after each test."""
    yield _db

    for table in reversed(_db.metadata.sorted_tables):
        _db.session.execute(table.delete())
    _db.session.expunge_all()
    _db.session.commit()


@pytest.fixture
def client(app, db):
    """A test client for the app. Truncates tables after each test."""
    return app.test_client()


class AuthenticatedClient:
    def __init__(self, client, first_name, last_name, email, password):
        self.client = client
        response = client.post(
            "/api/register",
            json={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": password,
            },
        )
        self.access_token = response.json["access_token"]

    def add_auth_header(self, kwargs):
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        kwargs["headers"] = headers

    def get(self, *args, **kwargs):
        self.add_auth_header(kwargs)
        return self.client.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.add_auth_header(kwargs)
        return self.client.post(*args, **kwargs)

    def put(self, *args, **kwargs):
        self.add_auth_header(kwargs)
        return self.client.put(*args, **kwargs)

    def patch(self, *args, **kwargs):
        self.add_auth_header(kwargs)
        return self.client.patch(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.add_auth_header(kwargs)
        return self.client.delete(*args, **kwargs)


@pytest.fixture
def authenticated_client(client) -> AuthenticatedClient:
    return AuthenticatedClient(
        client,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        password="SecurePassw0rd!",  # noqa: S106
    )


@pytest.fixture
def authenticated_client2(client) -> AuthenticatedClient:
    return AuthenticatedClient(
        client,
        first_name="Test",
        last_name="User",
        email="test.user@test.com",
        password="TestPassw0rd!",  # noqa: S106
    )


def lf(fixture):
    """Converts a fixture to a lazy fixture which can be used in parametrize."""
    fixture_name = fixture.__name__
    return _lf(fixture_name)


def assert_pagination_response(response, total, page, total_pages, items_count):
    """Verify pagination metadata."""
    assert response.status_code == 200
    assert "items" in response.json
    assert response.json["total_items"] == total
    assert response.json["total_pages"] == total_pages
    assert response.json["page"] == page
    assert len(response.json["items"]) == items_count


def assert_resources_order_match(returned_resources, expected_resources):
    """Verify returned resources match expected resources."""
    for i, expected_source in enumerate(expected_resources):
        for key, value in expected_source.items():
            assert returned_resources[i][key] == value


def assert_response_matches_resource(response, resource_data, additional_keys=None):
    """Asserts that the response matches the resource data and has additional keys."""
    for key, value in resource_data.items():
        assert response.json[key] == value
    if additional_keys:
        for key in additional_keys:
            assert key in response.json


profile_data = MappingProxyType(  # immutable dict view to ensure test isolation
    {
        "name": "Test Profile",
        "description": "This is a test profile",
    }
)
updated_profile_data = MappingProxyType(
    {
        "name": "Updated Profile",
        "description": "This is a test profile",
    }
)
source_data = MappingProxyType(
    {
        "name": "Test Source",
        "parser_name": "mock_parser",
        "link": "https://example.com/feed",
    }
)
updated_source_data = MappingProxyType(
    {
        "name": "Updated Source",
        "parser_name": "mock_parser",
        "link": "https://example.com/feed",
    }
)


def create_profile(client, profile_data: dict | MappingProxyType = profile_data):
    response = client.post("/api/profiles", json=profile_data.copy())
    return response.headers["Location"]


@pytest.fixture
def profile(authenticated_client):
    """Sets up a test case with a profile with profile_data. Returns the profile's url."""
    return create_profile(authenticated_client)


def create_source(
    client, profile_url, source_data: dict | MappingProxyType = source_data
):
    """Helper to create a source."""
    profile_id = profile_url.rsplit("/", maxsplit=1)[1]
    response = client.post(
        f"/api/profiles/{profile_id}/sources", json=source_data.copy()
    )
    return response.headers["Location"]


@pytest.fixture
def source(authenticated_client, profile):
    """Sets up a test case with a source. Returns the source's url."""
    return create_source(authenticated_client, profile)


class MockParser(NewsParser):
    name = "mock_parser"
    description = "Mock parser"
    link_hint = "https://example.com"

    @classmethod
    def get_posts(
        cls, link: str, from_datetime: datetime, to_datetime: datetime | None
    ) -> list[Post]:
        return [
            Post(
                title="Test Post",
                link="https://example.com/post",
                body="Test body",
                author="Test Author",
                published_time=datetime.now(tz=UTC),
            )
        ]

    @classmethod
    def check_source_link(cls, link: str) -> bool:
        return link != "https://invalid.com"


class MockParser2(MockParser):
    name = "mock_parser2"
    description = "Mock parser"
    link_hint = "https://example.com"
