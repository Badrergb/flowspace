from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FlowSpace Backend"

    FIREBASE_CREDENTIALS_JSON: str = ""

    ALLOWED_ORIGINS: str = "*"

    AI_DAILY_REQUEST_LIMIT: int = 10

    RESEND_API_KEY: str = ""
    EMAIL_SENDER: str = "FlowSpace <hello@flowspace.app>"

    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ADMIN_SECRET_KEY: str = "super-secret-admin-key-change-in-prod"
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()