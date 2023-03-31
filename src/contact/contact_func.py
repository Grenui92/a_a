import unittest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from src.data_base.models import Contact
from src.schemas import ContactBase, ContactResponse


async def get_user_by_email(email: str, db: Session) -> Contact | None:
    """
    The get_user_by_email function takes in an email and a database session,
    and returns the user with that email if it exists. If not, it returns None.

    :param email: str: Pass in the email address of the user
    :param db: Session: Pass the database session to the function
    :return: The first user with the given email address
    :doc-author: Trelent
    """

    print('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqq')
    return db.query(Contact).filter(Contact.email == email).first()


async def create_user(body: ContactBase, db: Session) -> ContactResponse | None:
    """
    The create_user function creates a new user in the database.

    :param body: ContactBase: Pass the request body to the function
    :param db: Session: Pass the database session to the function
    :return: A contactresponse object
    :doc-author: Trelent
    """
    new_contact = Contact(**body.dict())
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact


async def update_token(user: Contact, token: str | None, db: Session) -> None:
    """
    The update_token function updates the refresh token for a user in the database.

    :param user: Contact: Identify the user in the database
    :param token: str|None: Specify the type of token
    :param db: Session: Pass in the database session
    :return: None
    :doc-author: Trelent
    """
    user.refresh_token = token
    db.commit()


async def confirmed_email(email: str, db: Session):
    """
    The confirmed_email function takes in an email and a database session,
        then finds the user with that email address. It sets their confirmed_email
        field to True, and commits the change to the database.

    :param email: str: Get the email of the user
    :param db: Session: Access the database
    :return: A boolean value
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.confirmed_email = True
    db.commit()


async def set_avatar(email, url: str, db: Session) -> Contact:
    """
    The set_avatar function takes in an email and a url, then sets the avatar of the user with that email to be
    the given url. It returns the updated contact.

    :param email: Find the user in the database
    :param url: str: Set the avatar url for a user
    :param db: Session: Pass the database session to the function
    :return: A contact object
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user
