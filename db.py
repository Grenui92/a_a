from sqlalchemy import create_engine, Column, String, Date, Text, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings


DB_URL = settings.sqlalchemy_database_url
engine = create_engine(DB_URL)
session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Contact(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    surname = Column(String(50))
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    phone = Column(String(50))
    birthday = Column(Date)
    other = Column(Text)
    refresh_token = Column(Text)
    avatar = Column(Text)

# Base.metadata.create_all(bind=engine)

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()
