from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch
from datetime import date

from sqlalchemy.orm import Session

import src
from src.contact.contact_func import (get_user_by_email,
                                      create_user,
                                      update_token,
                                      confirmed_email,
                                      set_avatar)
from src.schemas import ContactBase, TokenModel, EmailSchemas
from src.data_base.models import Contact


class TestContact(IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.contact = Contact(id=1,
                               name='Stas',
                               surname='Vasilenko',
                               email='grenui@gmail.com',
                               password='123',
                               phone='8050',
                               birthday=date(year=1992, day=25, month=6),
                               other='Good boy',
                               refresh_token='1',
                               confirmed_email=False,
                               avatar='url')

    async def test_get_user_by_email(self):
        self.session.query().filter().first.return_value = self.contact
        email = 'grenui@gmail.com'
        result = await get_user_by_email(email=email, db=self.session)
        self.assertEqual(result, self.contact)

    async def test_create_contact(self):
        body = ContactBase(name='Stas',
                           surname='Vasilenko',
                           email='grenui@gmail.com',
                           password='123',
                           phone='8050',
                           birthday=date(year=1992, day=25, month=6),
                           other='Good boy',
                           refresh_token='1',
                           confirmed_email=False,
                           avatar='url')

        result = await create_user(body=body, db=self.session)

        self.assertEqual(result.name, body.name)
        self.assertEqual(result.surname, body.surname)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.email, body.email)

    async def test_update_token(self):
        contact = Contact()
        initial_token = contact.refresh_token
        new_token = 'asd'
        await update_token(user=contact, token=new_token, db=self.session)
        self.assertNotEqual(contact.refresh_token, initial_token)

    async def test_confirmed_email(self):
        with patch.object(src.contact.contact_func, "get_user_by_email") as get_mock:
            get_mock.return_value = self.contact

            await confirmed_email(email=self.contact.email, db=self.session)

            self.assertTrue(self.contact.confirmed_email)

    async def test_set_avatar(self):
        with patch.object(src.contact.contact_func, 'get_user_by_email') as get_mock:
            get_mock.return_value = self.contact
            avatar = 'bon jovi'
            await set_avatar(email=self.contact.email, url=avatar, db=self.session)
            self.assertEqual(self.contact.avatar, avatar)
