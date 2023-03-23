from pydantic import BaseModel, EmailStr, Field
from datetime import date

class ContactBase(BaseModel):
    name: str = Field(default='Stas')
    surname: str = Field(default='Vasilenko')
    email: str = Field(default='grenui@gmail.com')
    password: str = Field(default='92062555Vv')
    phone: str = Field(default='+380887778899')
    birthday: date = Field(default=date(1992, 6, 25))
    other: str = Field(default='Good person')

class ContactResponse(ContactBase):
    id: int

    class Config:
        orm_mode = True

class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'

class EmailSchemas(BaseModel):
    email: EmailStr