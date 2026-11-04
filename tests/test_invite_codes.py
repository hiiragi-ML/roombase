import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, InviteCode
from app.security import hash_password

def test_reusable_invite_code(client, test_connection):
    invite_code = "ROOMBASE-TEST-CODE"

    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        # 管理者を作成
        admin = User(
            name="テスト管理者",
            email="invite_admin@example.com",
            password_hash=hash_password("TestPassword123!"),
            role="admin"
        )

        db.add(admin)
        db.flush()

        # 招待コードのハッシュを作る
        code_hash = hashlib.sha256(
            invite_code.encode("utf-8")
        ).hexdigest()

        # 有効な招待コードを登録
        invite = InviteCode(
            code_hash=code_hash,
            created_by=admin.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            revoked_at=None
        )

        db.add(invite)
        db.commit()

    # Aさんが登録
    response_a = client.post(
        "/api/auth/register",
        json={
            "name": "テスト会員A",
            "email": "invite_a@example.com",
            "password": "TestPassword123!",
            "invite_code": invite_code
        }
    )

    assert response_a.status_code == 201
    assert response_a.json()["user"]["role"] == "member"

    response_b = client.post(
        "/api/auth/register",
        json={
            "name": "テスト会員B",
            "email": "invite_b@example.com",
            "password": "TestPassword123!",
            "invite_code": invite_code
        }
    )

    assert response_b.status_code == 201
    assert response_b.json()["user"]["role"] == "member"

def test_expired_invite_code(client, test_connection):
    invite_code = "EXPIRED-TEST-CODE"
    email = "expired_test@example.com"

    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        # テスト用管理者
        admin = User(
            name="期限切れテスト管理者",
            email="expired_admin@example.com",
            password_hash=hash_password("TestPassword123!"),
            role="admin"
        )

        db.add(admin)
        db.flush()

        code_hash = hashlib.sha256(
            invite_code.encode("utf-8")
        ).hexdigest()

        # 期限切れの招待コード
        invite = InviteCode(
            code_hash=code_hash,
            created_by=admin.id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            revoked_at=None
        )

        db.add(invite)
        db.commit()

    # 期限切れコードで登録を試す
    response = client.post(
        "/api/auth/register",
        json={
            "name": "登録できない会員",
            "email": email,
            "password": "TestPassword123!",
            "invite_code": invite_code
        }
    )

    assert response.status_code != 201
    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        saved_user = db.scalar(
            select(User).where(User.email == email)
        )

        assert saved_user is None

def test_revoked_invite_code(client, test_connection):
    invite_code = "REVOKED-TEST-CODE"
    email = "revoked_test@example.com"

    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        # テスト用管理者
        admin = User(
            name="無効化テスト管理者",
            email="revoked_admin@example.com",
            password_hash=hash_password("TestPassword123!"),
            role="admin"
        )

        db.add(admin)
        db.flush()

        code_hash = hashlib.sha256(
            invite_code.encode("utf-8")
        ).hexdigest()

        # 無効化済み招待コード
        invite = InviteCode(
            code_hash=code_hash,
            created_by=admin.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            revoked_at=datetime.now(timezone.utc)
        )

        db.add(invite)
        db.commit()

    # 無効化済みコードで登録を試す
    response = client.post(
        "/api/auth/register",
        json={
            "name": "登録できない会員",
            "email": email,
            "password": "TestPassword123!",
            "invite_code": invite_code
        }
    )

    assert response.status_code != 201
    
    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        saved_user = db.scalar(
            select(User).where(User.email == email)
        )

        assert saved_user is None

def test_invalid_invite_code(client, test_connection):
    email = "invalid_invite@example.com"

    response = client.post(
        "/api/auth/register",
        json={
            "name": "不正コードテスト",
            "email": email,
            "password": "TestPassword123!",
            "invite_code": "INVALID_CODE-123"
        }
    )

    assert response.status_code != 201

    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        saved_user = db.scalar(
            select(User).where(User.email == email)
        )

        assert saved_user is None

def test_duplicate_email(client, test_connection):
    email = "duplicate@example.com"
    invite_code = "DUPLICATE-EMAIL-TEST"

    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        # 管理者を作成
        admin = User(
            name="テスト管理者",
            email="duplicate_admin@example.com",
            password_hash=hash_password("TestPassword123!"),
            role="admin"
        )

        # 既存ユーザーを作成
        existing_user = User(
            name="既存会員",
            email=email,
            password_hash=hash_password("TestPassword123!"),
            role="member"
        )

        db.add_all([admin, existing_user])
        db.flush()

        # 有効な招待コードを作成
        code_hash = hashlib.sha256(
            invite_code.encode("utf-8")
        ).hexdigest()

        invite = InviteCode(
            code_hash=code_hash,
            created_by=admin.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            revoked_at=None
        )

        db.add(invite)
        db.commit()

    # 同じメールアドレスで登録を試す
    response = client.post(
        "/api/auth/register",
        json={
            "name": "重複登録テスト",
            "email": email,
            "password": "AnotherPassword123!",
            "invite_code": invite_code
        }
    )

    assert response.status_code == 409

    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        users = db.scalars(
            select(User).where(User.email == email)
        ).all()

        assert len(users) == 1