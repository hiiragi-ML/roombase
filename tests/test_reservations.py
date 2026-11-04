from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session

from app.models import User, Room
from app.security import hash_password
from app.reservation_rules import JST

def test_create_reservation(client, test_connection):
    email = "reservation_test@example.com"
    password = "TestPassword123!"

    # テスト用データを登録
    with Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint"
    ) as db:
        if db.get(Room, "main") is None:
            room = Room(
                id="main",
                name="テスト部室",
                description="テスト用",
                capacity=10,
                color="#6658df",
                amenities=[]
            )
            db.add(room)

        user = User(
            name="予約テスト会員",
            email=email,
            password_hash=hash_password(password),
            role="member"
        )

        db.add(user)
        db.commit()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert login_response.status_code == 200

    reservation_date = datetime.now(JST).date() + timedelta(days=2)

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

    reservation_data = {
        "room_id": "main",
        "title": "自動テスト用予約",
        "note": "pytestで作成",
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat()
    }

    response = client.post(
        "/api/reservations",
        json=reservation_data
    )

    assert response.status_code == 201
    assert response.json()["reservation"]["title"] == "自動テスト用予約"

    duplicate_response = client.post(
        "/api/reservations",
        json=reservation_data
    )

    assert duplicate_response.status_code == 409