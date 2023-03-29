from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, Date, Text, Boolean

Base = declarative_base()

class Contact(Base):
    """
    Model of database table

    :attr id (Integer): Contact id in database
    :attr name (String): Contact name
    :attr surname (String): Contact surname
    :attr email (String): Contact email
    :attr password (String): Contact password encoded
    :attr phone (String): Contact phone
    :attr birthday (Date): Contact birthday
    :attr other (Text): Contact description
    :attr refresh_token (Text): Contact password_refresh_token
    :attr confirmed_email (Boolean): Contact email confirmation flag
    :attr avatar (String): URL to contact avatar
    """
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
    confirmed_email = Column(Boolean, default=False)
    avatar = Column(String(255))

# Base.metadata.create_all(bind=engine)
