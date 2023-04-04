from unittest.mock import MagicMock
from datetime import timedelta, datetime, date
import jwt
from src.conf.config import settings
import src
from src.data_base.models import Contact


def test_signup(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr('src.routes.contacts.send_email_in_backgrounds', mock_send_email)
    response = client.post(
        "/auth/signup",
        json=user,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user"]["email"] == user.get("email")
    assert "id" in data["user"]


def test_login(client, session, user):
    contact: Contact = session.query(Contact).filter(Contact.email == user.get('email')).first()
    contact.confirmed_email = True
    session.commit()

    response = client.post('/auth/login',
                           data={'username': user.get('email'), 'password': user.get('password')})
    data = response.json()

    assert response.status_code == 200, response.text
    assert data['token_type'] == 'bearer'


def test_repeat_create_user(client, user):
    response = client.post(
        "/auth/signup",
        json=user,
    )
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Account already exist"


def test_login_user_not_confirmed(client, user, session):
    contact: Contact = session.query(Contact).filter(Contact.email == user.get('email')).first()
    contact.confirmed_email = False
    response = client.post(
        "/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed"


def test_request_email_contact_not_confirmed_yet(client, user, monkeypatch, session):
    contact: Contact = session.query(Contact).filter(Contact.email == user.get('email')).first()
    contact.confirmed_email = False
    mock_send_email = MagicMock()
    monkeypatch.setattr('src.routes.contacts.send_email_in_backgrounds', mock_send_email)
    response = client.post(
        "/auth/request_email",
        json=user,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Check your email for confirmation."


def test_login_wrong_password(client, user):
    response = client.post(
        "/auth/login",
        data={"username": user.get("email"), "password": "password"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"


def test_login_wrong_email(client, user):
    response = client.post(
        "/auth/login",
        data={"username": "email", "password": user.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"


def test_request_email(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr('src.routes.contacts.send_email_in_backgrounds', mock_send_email)
    response = client.post(
        "/auth/request_email",
        json=user,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Your email is already confirmed."
