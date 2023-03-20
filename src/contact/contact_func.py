from sqlalchemy.orm import Session

from src.data_base.models import Contact
from src.schemas import ContactBase, ContactResponse

async def get_user_by_email(email: str, db: Session) -> Contact|None:
    return db.query(Contact).filter(Contact.email == email).first()

async def create_user(body: ContactBase, db: Session) -> ContactResponse|None:
    new_contact = Contact(**body.dict())
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact

async def update_token(user: Contact, token: str|None, db: Session) -> None:
    user.refresh_token = token
    db.commit()
