def test_main_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"<!DOCTYPE html>" in response.data
    assert b"News Grouper" in response.data
