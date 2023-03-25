from pathlib import Path
from pydantic import EmailStr

from fastapi_mail import ConnectionConfig, MessageSchema, MessageType, FastMail
from fastapi_mail.errors import ConnectionErrors
from fastapi import BackgroundTasks

from src.services.auth import auth_services

conf = ConnectionConfig(
    MAIL_USERNAME="example@meta.ua",
    MAIL_PASSWORD="secretPassword",
    MAIL_FROM=EmailStr("example@meta.ua"),
    MAIL_PORT=465,
    MAIL_SERVER="smtp.meta.ua",
    MAIL_FROM_NAME="Desired Name",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / 'templates',
)


async def send_email_in_backgrounds(background_task: BackgroundTasks, email: EmailStr, username: str, host: str):
    try:
        token_verification = auth_services.create_email_token({"sub": email})
        message = MessageSchema(
            subjects="Confirm your email ",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            meassage_type=MessageType.html
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_template.html")
    except ConnectionErrors as e:
        print(e)
