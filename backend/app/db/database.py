from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from app.core.config import settings

if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"options": f"-csearch_path={settings.DB_SCHEMA},public"},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """DB初期化: schemaとテーブルを作成する

    database/init.sql を実行して確実にスキーマとテーブルを用意する。
    """
    # SQLiteはORMメタデータで作成、PostgreSQLはinit.sqlを実行
    if settings.DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    else:
        init_sql_path = Path(__file__).resolve().parents[2] / "database" / "init.sql"
        if not init_sql_path.exists():
            Base.metadata.create_all(bind=engine)
            return
        sql = init_sql_path.read_text(encoding="utf-8")
        with engine.begin() as conn:
            for stmt in [s.strip() for s in sql.split(";\n") if s.strip()]:
                conn.execute(text(stmt))
