from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, Date, Text

from db import engine


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

# Base.metadata.create_all(bind=engine)
