from sqlalchemy import text

def test_test_database_connection(test_connection):
    result = test_connection.scalar(
        text("SELECT current_database()")
    )

    assert result == "roombase_test"

def test_client_requires_login(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401