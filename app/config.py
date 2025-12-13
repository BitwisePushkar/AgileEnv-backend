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
    API_KEY:str
    SMTP_HOST : str
    SMTP_PORT : int
    SMTP_USER : str
    SMTP_PASSWORD : str
    FROM_EMAIL : str
    GITHUB_CLIENT_ID:str
    GITHUB_CLIENT_SECRET:str
    GITHUB_REDIRECT_URI:str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI_WEB: str
    GOOGLE_REDIRECT_URI_MOBILE: str


    class Config:
        env_file="app/.env"
        env_file_encoding="utf-8"

