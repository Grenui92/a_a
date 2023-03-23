import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request, UploadFile, File
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.schemas import ContactBase, ContactResponse, TokenModel, EmailSchemas
from src.contact import contact_func
from db import get_db, Contact
from src.services.auth import auth_services
from src.services.email import send_email_in_backgrounds
from src.conf.config import settings

router = APIRouter(prefix='/auth', tags=['auth'])
security = HTTPBearer()


@router.post('/signup', response_model=dict, status_code=status.HTTP_201_CREATED)
async def signup(body: ContactBase, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
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
    await authorization(credentials, db)

    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    setattr(contact, field, new_data)
    db.commit()
    db.refresh(contact)
    return contact


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
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
    user = await contact_func.get_user_by_email(body.email, db)
    if user.confirmed_email:
        return {'message': 'Your email is already confirmed'}
    if user:
        background_task.add_task(send_email_in_backgrounds, user.email, user.name, request.base_url)
    return {'message': 'Check your email for confirmation'}


async def authorization(credentials, db: Session = Depends(get_db)):
    token = credentials.credentials
    email = await auth_services.decode_refresh_token(token)
    user = await contact_func.get_user_by_email(email, db)
    if user.refresh_token != token:
        await contact_func.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')
    return token, email, user
