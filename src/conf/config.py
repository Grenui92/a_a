from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Gets data from '.env' with pydantic BaseSettings
    """
    sqlalchemy_database_url: str = 'postgresql+psycopg2://postgres:92062555Vv@localhost:5432/fast'
    secret_key: str = 'secret_key'
    algorithm: str = 'HS256'
    mail_username: str = 'grenui92@meta.ua'
    mail_password: str = 'password'
    mail_from: str = 'grenui92@meta.ua'
    mail_port: int = 465
    mail_server: str = 'smtp.meta.ua'
    redis_host: str = 'localhost'
    redis_port: int = 6379
    cloudinary_name: str = 'dn87oizpg'
    cloudinary_api_key: str = '154351211319561'
    cloudinary_api_secret: str = 'Aqa_6q0I0NQ4BmpizEbObkqCIc4'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
