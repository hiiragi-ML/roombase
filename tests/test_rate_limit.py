from app.rate_limit import limiter

def test_login_rate_limit(client):
    # このテストだけレート制限を有効化
    limiter.enabled = True

    login_data = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword123!"
    }

    # 最初の10回
    for i in range(10):
        response = client.post(
            "/api/auth/login",
            json=login_data
        )

        assert response.status_code == 401

    response = client.post(
        "/api/auth/login",
        json=login_data
    )

    assert response.status_code == 429