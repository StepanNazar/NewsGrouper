import pytest


@pytest.mark.skip
def test_which_fills_db_with_rows(client):
    client.post(
        "/api/register",
        json={
            "first_name": "testuser",
            "last_name": "testuser",
            "email": "test@example.com",
            "password": "Test@1234",
        },
    )


@pytest.mark.skip
def test_db_is_cleared_at_teardown_of_previous_test(client, db):
    from news_grouper.api.auth.models import User

    assert db.session.query(User).count() == 0
