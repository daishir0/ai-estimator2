from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database (SQLite3 デフォルト)
    DATABASE_URL: str = "sqlite:///./app.db"
    DB_SCHEMA: str = "estimator"  # PostgreSQL用。SQLiteでは未使用

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Config
    DAILY_UNIT_COST: int = 40000
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Language Setting
    LANGUAGE: str = "ja"  # Default: Japanese (ja or en)

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8009
    CORS_ORIGINS: str = "http://localhost:3004,http://localhost:3000"
    API_V1_STR: str = "/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
