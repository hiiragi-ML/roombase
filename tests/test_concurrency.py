from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import datetime, timedelta , time
from uuid import uuid4

from sqlalchemy import create_engine, select, delete, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import engine
from app.models import Room, User, Reservation
from app.security import hash_password
from app.reservation_rules import JST

TEST_DB_NAME = "roombase_test"

test_url = engine.url.set(database=TEST_DB_NAME)

if test_url.host not in ("localhost", "127.0.0.1"):
    raise RuntimeError("ローカルDB以外には接続できません")

test_engine = create_engine(test_url)

def test_parallel_execution():
    barrier = Barrier(2)

    def worker(number):
        barrier.wait(timeout=10)
        return number * 2

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(worker, 3)
        future_b = executor.submit(worker, 5)

        result_a = future_a.result()
        result_b = future_b.result()


    assert result_a == 6
    assert result_b == 10

def test_concurrent_reservations():
    tag = uuid4().hex

    reservation_date = (
        datetime.now(JST).date() + timedelta(days=30 + int(tag[:6], 16) % 365)
    )

    start_at = datetime.combine(
        reservation_date, time(8, 50), tzinfo=JST
    )

    end_at = datetime.combine(
        reservation_date, time(10, 30), tzinfo=JST
    )

    user_ids = []
    created_room = False
    setup_complete = False

    try:
        # テスト用の部室とユーザーを準備
        with Session(test_engine) as db:
            current_db = db.scalar(
                text("SELECT current_database()")
            )
            assert current_db == TEST_DB_NAME

            if db.get(Room, "main") is None:
                db.add(Room(
                    id="main",
                    name="テスト部室",
                    description="同時予約テスト",
                    capacity=10,
                    color="#6658df",
                    amenities=[]
                ))
                created_room = True

            users = [
                User(
                    name=f"同時予約テスト{i}",
                    email=f"race_{tag}_{i}@example.com",
                    password_hash=hash_password("TestPassword123!"),
                    role="member"
                ) for i in range(2)
            ]

            db.add_all(users)
            db.flush()
            user_ids = [user.id for user in users]
            db.commit()
            setup_complete = True

        # 同時書き込み用の関数
        barrier = Barrier(2)

        def worker(user_id):
            with Session(test_engine) as db:
                reservation = Reservation(
                    room_id="main",
                    user_id=user_id,
                    reservation_date=reservation_date,
                    slot_id=1,
                    title=f"同時予約テスト_{tag}",
                    note="",
                    start_at=start_at,
                    end_at=end_at
                )

                db.add(reservation)

                # 2つのスレッドがそろうまで待つ
                barrier.wait(timeout=10)

                try:
                    db.commit()
                    return "created"
                except IntegrityError as exc:
                    db.rollback()

                    constraint_name = getattr(
                        getattr(exc.orig, "diag", None),
                        "constraint_name",
                        None
                    )

                    if constraint_name == "uq_reservation_room_date_slot":
                        return "conflict"
                    raise

        # 2つのスレッドを実行
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_a = executor.submit(worker, user_ids[0])
            future_b = executor.submit(worker, user_ids[1])

            results = [
                future_a.result(),
                future_b.result()
            ]

        assert sorted(results) == ["conflict", "created"]

        # DB上の予約件数を確認
        with Session(test_engine) as d:
            reservations = db.scalars(
                select(Reservation).where(
                    Reservation.user_id.in_(user_ids)
                )
            ).all()
            assert len(reservations) == 1

    finally:
        # このテストで作成したデータだけ削除
        if setup_complete:
            with Session(test_engine) as db:
                current_db = db.scalar(
                    text("SELECT current_database()")
                )
                if current_db != TEST_DB_NAME:
                    raise RuntimeError("テストDBではありません")

                db.execute(
                    delete(Reservation).where(
                        Reservation.user_id.in_(user_ids)
                    )
                )
                db.execute(
                    delete(User).where(
                        User.id.in_(user_ids)
                    )
                )

                if created_room:
                    room = db.get(Room, "main")
                    if room is not None:
                        db.delete(room)

                db.commit()

