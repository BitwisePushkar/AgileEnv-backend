from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET_KEY:str
    JWT_ALGORITHM:str
    JWT_ACCESS_TOKEN_EXPIRE_DAYS:int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS:int
    DB_CONNECTION:str
    DB_HOST:str
    DB_PORT:str
    DB_DATABASE:str
    DB_USERNAME:str
    DB_PASSWORD:str

    SMTP_HOST : str
    SMTP_PORT : int
    SMTP_USER : str
    SMTP_PASSWORD : str
    SMTP_FROM : str
    

    class Config:
        env_file="app/.env"
        env_file_encoding="utf-8"