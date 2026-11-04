from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session

from app.models import User, Room, Reservation
from app.security import hash_password
from app.reservation_rules import JST

def test_cancel_own_reservation(client, test_connection):
    email = "cancel_test@example.com"
    password = "TestPassword123!"

    reservation_date = (
        datetime.now(JST).date()
         + timedelta(days=2)
    )

    start_at = datetime.combine(
        reservation_date, time(8, 50), tzinfo=JST
    )

    end_at = datetime.combine(
        reservation_date, time(10, 30), tzinfo=JST
    )

    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        if db.get(Room, "main") is None:
            db.add(Room(
                id="main",
                name="テスト部室",
                description="テスト用",
                capacity=10,
                color="#6658df",
                amenities=[]
            ))

        user = User(
            name="キャンセルテスト会員",
            email=email,
            password_hash=hash_password(password),
            role="member"
        )

        db.add(user)
        db.flush()

        reservation = Reservation(
            room_id="main",
            user_id=user.id,
            reservation_date=reservation_date,
            slot_id=1,
            title="キャンセルテスト",
            note="",
            start_at=start_at,
            end_at=end_at
        )

        db.add(reservation)
        db.commit()

        reservation_id = reservation.id

    # ログイン
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert login_response.status_code == 200

    # 予約をキャンセル
    response = client.delete(
        f"/api/reservations/{reservation_id}"
    )

    assert response.status_code == 204

    second_response = client.delete(
        f"/api/reservations/{reservation_id}"
    )

    assert second_response.status_code == 404

def test_cannot_cancel_others_reservaion(client, test_connection):
    password = "TestPassword123!"

    reservation_date = (
        datetime.now(JST).date()
         + timedelta(days=2)
    )

    start_at = datetime.combine(
        reservation_date, time(8, 50), tzinfo=JST
    )

    end_at = datetime.combine(
        reservation_date, time(10, 30), tzinfo=JST
    )

    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        # テスト用部室
        if db.get(Room, "main") is None:
            db.add(Room(
                id="main",
                name="テスト部室",
                description="テスト用",
                capacity=10,
                color="#6658df",
                amenities=[]
            ))

        # 予約者
        owner = User(
            name="Aさん",
            email="owner@example.com",
            password_hash=hash_password(password),
            role="member"
        )

        # 別の一般メンバー
        other = User(
            name="Bさん",
            email="other@example.com",
            password_hash=hash_password(password),
            role="member"
        )

        db.add_all([owner, other])
        db.flush()

        # Aさんの予約を作成
        reservation = Reservation(
            room_id="main",
            user_id=owner.id,
            reservation_date=reservation_date,
            slot_id=1,
            title="Aさんの予約",
            note="",
            start_at=start_at,
            end_at=end_at
        )

        db.add(reservation)
        db.commit()

        reservation_id = reservation.id

    # Bさんとしてログイン
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "other@example.com",
            "password": password
        }
    )

    assert login_response.status_code == 200

    # BさんがAさんの予約をキャンセル
    response = client.delete(
        f"/api/reservations/{reservation_id}"
    )

    assert response.status_code == 403

    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        saved_reservation = db.get(Reservation, reservation_id)

        assert saved_reservation is not None

def test_cannot_cancel_started_reservation(client, test_connection):
    email = "past_test@example.com"
    password = "TestPassword123!"

    # 昨日の日付
    reservation_date = (
        datetime.now(JST).date()
         - timedelta(days=1)
    )

    start_at = datetime.combine(
        reservation_date,
        time(8, 50),
        tzinfo=JST
    )

    end_at = datetime.combine(
        reservation_date,
        time(10, 30),
        tzinfo=JST
    )

    with Session(
            bind=test_connection,
            join_transaction_mode="create_savepoint"
    ) as db:
        # テスト用部室
        if db.get(Room, "main") is None:
            db.add(Room(
                id="main",
                name="テスト部室",
                description="テスト用",
                capacity=10,
                color="#6658df",
                amenities=[]
            ))

        user = User(
            name="過去予約テスト会員",
            email=email,
            password_hash=hash_password(password),
            role="member"
        )

        db.add(user)
        db.flush()

        reservation = Reservation(
            room_id="main",
            user_id=user.id,
            reservation_date=reservation_date,
            slot_id=1,
            title="昨日の予約",
            note="",
            start_at=start_at,
            end_at=end_at
        )

        db.add(reservation)
        db.commit()

        reservation_id = reservation.id

    # 本人としてログイン
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert login_response.status_code == 200

    response = client.delete(
        f"/api/reservations/{reservation_id}"
    )

    assert response.status_code == 409

    # 予約がDBに残っているか確認
    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        saved_reservation = db.get(Reservation, reservation_id)

        assert saved_reservation is not None

def test_admin_can_cancel_reservation(client, test_connection):
    password = "TestPassword123!"

    reservation_date = (
        datetime.now(JST).date()
         + timedelta(days=2)
    )
    
    start_at = datetime.combine(
        reservation_date,
        time(8, 50),
        tzinfo=JST
    )

    end_at = datetime.combine(
        reservation_date,
        time(10, 30),
        tzinfo=JST
    )

    with Session(
                bind=test_connection,
                join_transaction_mode="create_savepoint"
    ) as db:
        # テスト用部室
        if db.get(Room, "main") is None:
            db.add(Room(
                id="main",
                name="テスト部室",
                description="テスト用",
                capacity=10,
                color="#6658df",
                amenities=[]
            ))

        owner = User(
            name="予約者",
            email="admin_test_owner@example.com",
            password_hash=hash_password(password),
            role="member"
        )

        admin = User(
            name="テスト管理者",
            email="admin_test@example.com",
            password_hash=hash_password(password),
            role="admin"
        )

        db.add_all([owner, admin])
        db.flush()

        # 一般メンバーの予約を登録
        reservation = Reservation(
            room_id="main",
            user_id=owner.id,
            reservation_date=reservation_date,
            slot_id=1,
            title="管理者キャンセルテスト",
            note="",
            start_at=start_at,
            end_at=end_at
        )

        db.add(reservation)
        db.commit()

        reservation_id = reservation.id

    # 管理者としてログイン
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "admin_test@example.com",
            "password": password
        }
    )

    assert login_response.status_code == 200

    # 他人の予約を削除
    response = client.delete(
        f"/api/reservations/{reservation_id}"
    )

    assert response.status_code == 204

    # 予約が削除されたことをDBで確認
    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        saved_reservation = db.get(Reservation, reservation_id)

        assert saved_reservation is None