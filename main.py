import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import date, timedelta

import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from src.data_base.db import get_db
from src.data_base.models import Contact
from src.schemas import ContactResponse, ContactBase
from src.routes import contacts

origins = [
    'http://localhost:3000'
]



app = FastAPI()
app.include_router(contacts.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.on_event('startup')
async def startup():
    """
    The startup function is called when the application starts up.
    It's a good place to initialize things that are needed by your app,
    like connecting to databases or initializing external APIs.

    :return: A dictionary of the objects you want to make available in your routes
    :doc-author: Trelent
    """
    r = redis.Redis(host='localhost', port=6379, db=0, encoding='utf-8', decode_responses=True)
    await FastAPILimiter.init(r)


@app.get('/', response_model=list[ContactResponse])
async def get_all_contacts(db: Session = Depends(get_db)):
    """
    The get_all_contacts function returns a list of all contacts in the database.
        :return: A list of Contact objects.

    :param db: Session: Pass in the database session
    :return: A list of contact objects
    :doc-author: Trelent
    """
    contacts = db.query(Contact).all()
    for contact in contacts:
        print(type(contact.birthday))
    return contacts


@app.post('/contact',
          response_model=ContactResponse,
          description='Only ten registrations in one hour.',
          dependencies=[Depends(RateLimiter(times=10, minutes=60))])
async def create_new_contact(contact_body: ContactBase,
                             db: Session = Depends(get_db)):
    """
    The create_new_contact function creates a new contact in the database.
    It takes a ContactBase object as input and returns the newly created Contact object.

    :param contact_body: ContactBase: Get the request body and
    :param db: Session: Get the database session
    :return: A contact object
    :doc-author: Trelent
    """
    contact = Contact(**contact_body.dict())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@app.get('/contact/{contact_id}', response_model=ContactResponse)
async def get_one_contact(contact_id: int,
                          db: Session = Depends(get_db)):
    """
    The get_one_contact function returns a single contact from the database.

    :param contact_id: int: Specify the contact id to be retrieved
    :param db: Session: Get the database session
    :return: A contact object
    :doc-author: Trelent
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not found')
    return contact


@app.get('/contact/search_by_name/{name}', response_model=ContactResponse)
async def search_by_name(name: str = 'Stas',
                         db: Session = Depends(get_db)):
    """
    The search_by_name function searches for a contact by name.

    :param name: str: Pass the name of the contact to search for
    :param db: Session: Get the database session
    :return: A contact object
    :doc-author: Trelent
    """
    contact = db.query(Contact).filter(Contact.name == name).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not Found')
    return contact


@app.get('/contact/search/{info}', response_model=ContactResponse)
async def search(data: str, db: Session = Depends(get_db)):
    """
    The search function is used to search for a contact in the database.
    It takes a string as an argument and searches for it in the name, surname and email fields of all contacts.
    If there are no matches, it returns 404 Not Found.

    :param data: str: Pass the data to the function
    :param db: Session: Get the database session
    :return: The contact object if it is found in the database, otherwise returns an error
    :doc-author: Trelent
    """

    contact = db.query(Contact).filter(or_(Contact.name == data,
                                           Contact.surname == data,
                                           Contact.email == data)).first()

    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not Found')
    return contact


@app.get('/nearest_birthdays', response_model=list[ContactResponse])
async def nearest_birthdays(db: Session = Depends(get_db)):
    """
    The nearest_birthdays function returns a list of contacts whose birthdays are within the next 7 days.


    :param db: Session: Pass the database session to the function
    :return: A list of contacts with birthdays in the next 7 days
    :doc-author: Trelent
    """
    contacts = db.query(Contact).all()
    contacts = [contact for contact in contacts
                if abs(contact.birthday - date(contact.birthday.year, date.today().day, date.today().month)) < timedelta(7)]

    return contacts


if __name__ == '__main__':
    uvicorn.run(app)
