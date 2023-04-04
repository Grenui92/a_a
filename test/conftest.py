from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from src.data_base.models import Contact

from main import app
from src.data_base.db import Base, get_db

SQL_DB_URL = "sqlite:///./test.db"
engine = create_engine(SQL_DB_URL, connect_args={'check_same_thread': False})
TestingSessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)


# Contact.metadata.create_all(engine)

@pytest.fixture(scope='module')
def session():
    Contact.metadata.drop_all(bind=engine)
    Contact.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope='module')
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


@pytest.fixture(scope='module')
def user():
    return {'name': 'Stas',
            'surname': 'Vasilenko',
            'email': 'grenui@gmail.com',
            'password': '92062555Vv',
            'phone': '+380887778899',
            'other': 'Good person',
            'refresh_token': 'asdb',
            'confirmed_email': 'False',
            'avatar': 'None'}
