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
