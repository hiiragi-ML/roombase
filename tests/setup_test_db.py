from sqlalchemy import create_engine, text, inspect

from app.database import Base, engine
from app import models

TEST_DB_NAME = "roombase_test"

# ローカルのテストDB以外は触らない
if engine.url.host not in ("localhost", "127.0.0.1"):
    raise RuntimeError("ローカルDB以外には実行できません")

test_engine = create_engine(
    engine.url.set(database=TEST_DB_NAME)
)

try:
    with test_engine.begin() as connection:
        current_db = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if current_db != TEST_DB_NAME:
            raise RuntimeError("接続先がテストDBではありません")

        # ここでテスト用テーブルを作成
        Base.metadata.create_all(bind=connection)

        table_names = inspect(connection).get_table_names()

        print("接続先:", current_db)
        print("作成済みテーブル:", sorted(table_names))
finally:
    test_engine.dispose()