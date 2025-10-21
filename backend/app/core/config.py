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
    DAILY_UNIT_COST: int = 40000  # Deprecated: Use language-specific settings
    DAILY_UNIT_COST_JPY: int = 40000
    DAILY_UNIT_COST_USD: int = 500
    TAX_RATE_JA: int = 10
    TAX_RATE_EN: int = 0
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Language Setting
    LANGUAGE: str = "ja"  # Default: Japanese (ja or en)

    # Resilience Settings
    OPENAI_TIMEOUT: int = 30  # OpenAI API timeout in seconds
    OPENAI_MAX_RETRIES: int = 3  # Maximum retry attempts
    OPENAI_RETRY_INITIAL_DELAY: float = 1.0  # Initial retry delay in seconds
    OPENAI_RETRY_BACKOFF_FACTOR: float = 2.0  # Exponential backoff factor

    # Circuit Breaker Settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5  # Number of failures before opening circuit
    CIRCUIT_BREAKER_TIMEOUT: int = 60  # Timeout in seconds before attempting half-open

    # Resource Limit Settings
    MAX_CONCURRENT_ESTIMATES: int = 5  # Maximum number of concurrent estimate operations
    MAX_ITERATIONS: int = 10  # Maximum iterations for loop detection

    def get_daily_unit_cost(self) -> int:
        """言語設定に応じた単価を取得"""
        if self.LANGUAGE == "en":
            return self.DAILY_UNIT_COST_USD
        return self.DAILY_UNIT_COST_JPY

    def get_tax_rate(self) -> float:
        """言語設定に応じた税率を取得（%）"""
        if self.LANGUAGE == "en":
            return self.TAX_RATE_EN / 100.0
        return self.TAX_RATE_JA / 100.0

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8009
    CORS_ORIGINS: str = "http://localhost:3004,http://localhost:3000"
    API_V1_STR: str = "/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
