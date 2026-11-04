from sqlalchemy import create_engine, text

from app.database import engine

TEST_DB_NAME = "roombase_test"

test_engine = create_engine(
    engine.url.set(database=TEST_DB_NAME)
)

def test_connect_to_test_database():
    with test_engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    assert result == TEST_DB_NAME