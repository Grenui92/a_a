import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request, UploadFile, File
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.schemas import ContactBase, ContactResponse, TokenModel, EmailSchemas
from src.contact import contact_func
from src.data_base.db import get_db
from src.data_base.models import Contact
from src.services.auth import auth_services
from src.services.email import send_email_in_backgrounds
from src.conf.config import settings

router = APIRouter(prefix='/auth', tags=['auth'])
security = HTTPBearer()


@router.post('/signup', response_model=dict, status_code=status.HTTP_201_CREATED)
async def signup(body: ContactBase, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    The signup function creates a new user in the database.
        It takes a ContactBase object as input, which contains the following fields:
            - email (required): The email address of the user to be created. Must be unique.
            - password (required): The password for this account, hashed using Argon2 hashing algorithm and stored in DB.

    :param body: ContactBase: Get the data from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the server
    :param db: Session: Get the database session
    :return: A dictionary with the user and a message
    :doc-author: Trelent
    """
    exist_user = await contact_func.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Account already exist')
    body.password = auth_services.get_password_hash(body.password)
    new_user = await contact_func.create_user(body, db)
    background_tasks.add_task(send_email_in_backgrounds, new_user.email, new_user.name, request.base_url)
    return {'user': new_user, 'detail': 'User successfully created. Check your email for confirmation.'}


@router.patch('/avatar', response_model=ContactResponse)
async def set_avatar(file: UploadFile = File(),
                     current_user: Contact = Depends(auth_services.get_current_user),
                     db: Session = Depends(get_db)):
    """
    The set_avatar function allows a user to upload an avatar image.
    The function takes in the file, current_user and db as parameters.
    It then uses cloudinary to upload the file with a public id of NotesApp + current_user's name.
    It overwrites any previous images with that same public id (i.e., it replaces them).
    Then it builds a url for the image using cloudinary's build_url method, which is used by
    the frontend to display the avatar on screen.

    :param file: UploadFile: Get the file from the frontend
    :param current_user: Contact: Get the current user's email
    :param db: Session: Access the database
    :return: The user object
    :doc-author: Trelent
    """
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True)
    cloudinary.uploader.upload(file.file, public_id=f'NotesApp{current_user.name}', overwrite=True)
    src_url = cloudinary.CloudinaryImage(f'NotesApp/{current_user.name}') \
        .build_url(width=250, height=250, crop='fill')
    user = await contact_func.set_avatar(current_user.email, src_url, db)
    return user

@router.post('/login', response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    The login function is used to authenticate a user.
        It takes in the email and password of the user, and returns an access token if successful.
        The access token can be used to make requests on behalf of that user.

    :param body: OAuth2PasswordRequestForm: Get the username and password from the request body
    :param db: Session: Access the database
    :return: A dictionary with the access_token, refresh_token and token type
    :doc-author: Trelent
    """
    user = await contact_func.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email')
    if not user.confirmed_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Email not confirmed')
    if not auth_services.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid password')

    access_token = await auth_services.create_access_token(data={'sub': user.email})
    refresh_token = await auth_services.create_refresh_token(data={'sub': user.email})
    await contact_func.update_token(user, refresh_token, db)
    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security),
                        db: Session = Depends(get_db)
                        ):
    """
    The refresh_token function is used to refresh the access token.
        The function takes in a credentials object, which contains the authorization header information.
        It then calls the authorization function to verify that this user exists and has a valid refresh token.
        If so, it creates new tokens for them and returns them as well as their type.

    :param credentials: HTTPAuthorizationCredentials: Get the credentials from the request header
    :param db: Session: Get a database session
    :return: The access_token and refresh_token
    :doc-author: Trelent
    """
    token, email, user = await authorization(credentials, db)

    access_token = await auth_services.create_access_token(data={'sub': email})
    refresh_token = await auth_services.create_refresh_token(data={'sub': email})
    await contact_func.update_token(user, refresh_token, db)
    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}


@router.put('/{contact_id}', response_model=ContactResponse)
async def update_contact(contact_body: ContactBase,
                         contact_id: int,
                         credentials: HTTPAuthorizationCredentials = Security(security),
                         db: Session = Depends(get_db)
                         ):
    """
    The update_contact function updates a contact in the database.
        The function takes a ContactBase object, which is used to update the contact's name, surname, email address and phone number.
        It also takes an integer representing the ID of the contact to be updated.
        The function returns an HTTP status code 200 if successful.

    :param contact_body: ContactBase: Get the data from the request body
    :param contact_id: int: Identify the contact to be deleted
    :param credentials: HTTPAuthorizationCredentials: Pass the credentials to the function
    :param db: Session: Access the database
    :return: The updated contact
    :doc-author: Trelent
    """
    await authorization(credentials, db)

    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not found')
    contact.name = contact_body.name
    contact.surname = contact_body.surname
    contact.email = contact_body.email
    contact.phone = contact_body.phone
    contact.birthday = contact_body.birthday
    contact.other = contact_body.other

    db.commit()
    db.refresh(contact)
    return contact


@router.delete('/{contact_id}',
               response_model=dict)
async def delete_contact(contact_id: int,
                         credentials: HTTPAuthorizationCredentials = Security(security),
                         db: Session = Depends(get_db)):
    """
    The delete_contact function deletes a contact from the database.

    :param contact_id: int: Specify the id of the contact that is to be deleted
    :param credentials: HTTPAuthorizationCredentials: Get the credentials from the http request header
    :param db: Session: Get the database session
    :return: A message that the contact was deleted
    :doc-author: Trelent
    """
    await authorization(credentials, db)

    db.query(Contact).filter(Contact.id == contact_id).delete()
    db.commit()
    return {'message': 'Contact was deleted'}


@router.patch('/{contact_id}', response_model=ContactResponse)
async def edit_contact(field: str,
                       new_data: str,
                       contact_id: int = 3,
                       credentials: HTTPAuthorizationCredentials = Security(security),
                       db: Session = Depends(get_db)):
    """
    The edit_contact function allows the user to edit a contact's information.
    The function takes in three arguments: field, new_data, and contact_id. The field argument is a string that specifies which attribute of the Contact object will be edited (e.g., &quot;firstname&quot;, &quot;lastname&quot;, etc.). The new_data argument is also a string that contains the data to replace whatever was previously stored in the specified attribute of Contact object with id equal to contact_id (the third argument).


    :param field: str: Determine which field in the contact table to update
    :param new_data: str: Pass the new data to be stored in the database
    :param contact_id: int: Specify which contact to edit
    :param credentials: HTTPAuthorizationCredentials: Authenticate the user
    :param db: Session: Pass the database session to the function
    :return: The edited contact
    :doc-author: Trelent
    """
    await authorization(credentials, db)

    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    setattr(contact, field, new_data)
    db.commit()
    db.refresh(contact)
    return contact


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    The confirmed_email function is used to confirm a user's email address.
        It takes the token from the URL and uses it to get the user's email address.
        Then, it checks if that email exists in our database, and if not, returns an error message.
        If so, then we check whether or not their account has already been confirmed;
            if so, we return a message saying as much;
            otherwise (if they haven't yet confirmed their account), we call contact_func.confirmed_email() on them.

    :param token: str: Get the token from the url
    :param db: Session: Get the database session
    :return: A message that the email is already confirmed
    :doc-author: Trelent
    """
    email = await auth_services.get_email_from_token(token)
    user = await contact_func.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Verification error')
    if user.confirmed_email:
        return {'message': 'Your email is already confirmed'}
    await contact_func.confirmed_email(email, db)
    return {'message': 'Email confirmed'}


@router.post('/request_email')
async def request_email(body: EmailSchemas, background_task: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    The request_email function is used to send an email to the user's email address.
    The function takes in a body of type EmailSchemas, which contains the user's email address.
    It then checks if that user exists in our database and if they have already confirmed their account.
    If they have not yet confirmed their account, it sends them an email with a link for confirmation.

    :param body: EmailSchemas: Validate the request body
    :param background_task: BackgroundTasks: Add a task to the background tasks
    :param request: Request: Get the base_url of the server
    :param db: Session: Get the database session
    :return: A message that the email has been sent
    :doc-author: Trelent
    """
    user = await contact_func.get_user_by_email(body.email, db)
    if user.confirmed_email:
        return {'message': 'Your email is already confirmed'}
    if user:
        background_task.add_task(send_email_in_backgrounds, user.email, user.name, request.base_url)
    return {'message': 'Check your email for confirmation'}


async def authorization(credentials, db: Session = Depends(get_db)):
    """
    The authorization function is used to validate the user's credentials.
    It takes in a token and an email, then checks if the token matches with the one stored in our database.
    If it does not match, we update their refresh_token to None so that they can no longer access any of our endpoints.

    :param credentials: Get the refresh token from the request
    :param db: Session: Pass the database session to the function
    :return: A token, email and user
    :doc-author: Trelent
    """
    token = credentials.credentials
    email = await auth_services.decode_refresh_token(token)
    user = await contact_func.get_user_by_email(email, db)
    if user.refresh_token != token:
        await contact_func.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')
    return token, email, user
