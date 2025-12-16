from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_DAYS: int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int
    DB_CONNECTION: str
    DB_HOST: str
    DB_PORT: str
    DB_DATABASE: str
    DB_USERNAME: str
    DB_PASSWORD: str
    API_KEY: str
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    FROM_EMAIL: str
    GITHUB_CLIENT_ID_WEB: str
    GITHUB_CLIENT_SECRET_WEB: str
    GITHUB_REDIRECT_URI_WEB: str
    GITHUB_CLIENT_ID_MOBILE: str
    GITHUB_CLIENT_SECRET_MOBILE: str
    GITHUB_REDIRECT_URI_MOBILE: str
    GOOGLE_CLIENT_ID_WEB: str
    GOOGLE_CLIENT_SECRET_WEB: str
    GOOGLE_REDIRECT_URI_WEB: str
    GOOGLE_CLIENT_ID_MOBILE: str
    GOOGLE_CLIENT_SECRET_MOBILE: str
    GOOGLE_REDIRECT_URI_MOBILE: str
    FRONTEND_WEB_URL: str
    FRONTEND_MOBILE_SCHEME: str
    REDIS_HOST: str
    REDIS_PORT: int
 
    class Config:
        env_file = "app/.env"
        env_file_encoding = "utf-8"