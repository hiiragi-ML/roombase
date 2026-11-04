def test_reject_invalid_origin(client):
    response = client.post(
        "/api/auth/logout",
        headers={
            "Origin": "https://attacker.example"
        }
    )

    assert response.status_code == 403

def test_reject_missing_origin(client):
    response = client.post(
        "/api/auth/logout",
        headers={"Origin": ""}
    )

    assert response.status_code == 403

def test_allow_valid_origin(client):
    response = client.post("/api/auth/logout")

    assert response.status_code == 204