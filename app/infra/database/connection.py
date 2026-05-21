import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

_engine = None
_session_factory = None


def _build_db_url() -> str:
    return (
        f"postgresql+psycopg2://{os.environ.get('POSTGRES_USER', 'hackathon')}:"
        f"{os.environ.get('POSTGRES_PASSWORD', 'hackathon123')}@"
        f"{os.environ.get('POSTGRES_HOST', 'localhost')}:"
        f"{os.environ.get('POSTGRES_PORT', '5432')}/"
        f"{os.environ.get('POSTGRES_DB', 'hackathon_db')}"
    )


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            _build_db_url(),
            pool_pre_ping=True,
            pool_size=3,
        )
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


def get_db():
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
