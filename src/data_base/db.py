from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.conf.config import settings


DB_URL = settings.sqlalchemy_database_url
engine = create_engine(DB_URL)
session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """
    The get_db function is a context manager that returns the database session.
    It also handles closing the session when it goes out of scope.

    :return: A database connection, which is used by the
    :doc-author: Trelent
    """
    db = session()
    try:
        yield db
    finally:
        db.close()
