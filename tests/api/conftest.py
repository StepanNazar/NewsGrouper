import pytest

from news_grouper.api import create_app
from news_grouper.api import db as _db
from news_grouper.api.config import TestConfig


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


@pytest.fixture
def authenticated_client(client):
    return make_authenticated_client(
        client,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        password="SecurePassw0rd!",  # noqa: S106
    )


@pytest.fixture
def authenticated_client2(client):
    return make_authenticated_client(
        client,
        first_name="Test",
        last_name="User",
        email="test.user@test.com",
        password="TestPassw0rd!",  # noqa: S106
    )


def make_authenticated_client(client, first_name, last_name, email, password):
    response = client.post(
        "/api/register",
        json={
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
        },
    )
    access_token = response.json["access_token"]

    def make_request(method, url, **kwargs):
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {access_token}"
        kwargs["headers"] = headers
        return getattr(client, method.lower())(url, **kwargs)

    return make_request
