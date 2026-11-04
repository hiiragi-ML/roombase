from sqlalchemy.orm import Session

from app.models import User
from app.security import hash_password

def test_member_login(client, test_connection):
    email = "test_member@example.com"
    password = "TestPassword123!"

    # テスト用ユーザーを作成
    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        user = User(
            name="テスト会員",
            email=email,
            password_hash=hash_password(password),
            role="member"
        )

        db.add(user)
        db.commit()

        user_id = user.id

    # ログインAPI
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert response.status_code == 200
    assert response.json()["user"]["id"] == str(user_id)

    # ログイン状態を確認
    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["user"]["email"] == email