from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.main import app
from app.database import engine, get_db

test_engine = create_engine(
    engine.url.set(database="roombase_test")
)

def test_me_uses_test_database():
    used_databases = []

    def override_get_db():
        with Session(test_engine) as db:
            database_name = db.scalar(
                text("SELECT current_database()")
            )
            used_databases.append(database_name)
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/auth/me")

        assert response.status_code == 401
        assert used_databases == ["roombase_test"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        test_engine.dispose()