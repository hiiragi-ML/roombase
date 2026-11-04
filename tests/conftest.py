import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.main import app
from app.database import engine, get_db
from app.rate_limit import limiter

TEST_DB_NAME = "roombase_test"

test_url = engine.url.set(database=TEST_DB_NAME)

if test_url.host not in ("localhost", "127.0.0.1"):
    raise RuntimeError("ローカルのテストDB以外には接続できません")

test_engine = create_engine(test_url)

@pytest.fixture
def test_connection():
    with test_engine.connect() as connection:
        transaction = connection.begin()

        try:
            current_db = connection.scalar(
                text("SELECT current_database()")
            )
            if current_db != TEST_DB_NAME:
                raise RuntimeError("テストDBではありません")

            yield connection
        finally:
            transaction.rollback()

@pytest.fixture
def client(test_connection):
    def override_get_db():
        with Session(
            bind=test_connection,
            join_transaction_mode="create_savepoint"
        ) as db:
            yield db

    previous_enabled = limiter.enabled
    limiter.enabled = False

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            test_client.headers.update({
                "Origin": "http://localhost:5173"
            })
            yield test_client
    finally:
        limiter.enabled = previous_enabled
        app.dependency_overrides.pop(get_db, None)