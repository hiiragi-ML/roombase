from sqlalchemy.orm import Session

from app.models import User
from app.security import hash_password

def test_logout_revokes_session(client, test_connection):
    email = "logout_test@example.com"
    password = "TestPassword123!"

    # テスト用ユーザーの作成
    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        user = User(
            name="ログアウトテスト",
            email=email,
            password_hash=hash_password(password),
            role="member"
        )

        db.add(user)
        db.commit()

    # ログイン
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert login_response.status_code == 200

    # ログイン時に発行されたCookieを保存
    token = login_response.cookies.get("roombase_session")
    assert token is not None

    # ログイン状態を確認
    me_response = client.get("/api/auth/me")

    assert me_response.status_code == 200

    # ログアウト
    logout_response = client.post("/api/auth/logout")

    assert logout_response.status_code == 204

    # 古いCookieを再設定
    client.cookies.set(
        "roombase_session",
        token,
        path="/"
    )

    # 古いCookieで認証を試す
    after_logout = client.get("/api/auth/me")

    assert after_logout.status_code == 401