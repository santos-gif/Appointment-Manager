from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Core Application
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "Hierarchical Resource Governance & Scheduling Engine"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/appointment_db"
    TEST_DATABASE_URL: Optional[str] = "sqlite+aiosqlite:///:memory:"

    # JWT Authentication
    SECRET_KEY: str = "enterprise_super_secret_signing_key_change_in_production_32bytes!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Exactly 15 minutes as requested
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # Exactly 7 days as requested

    # Cookie Security Settings
    COOKIE_SECURE: bool = False             # Set to True in production (HTTPS)
    COOKIE_SAMESITE: str = "lax"           # 'lax' or 'strict'
    COOKIE_DOMAIN: Optional[str] = None

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:3000",
    ]

    # Integration Configuration (Mock / Prod)
    STRIPE_SECRET_KEY: str = "sk_test_mock_enterprise_stripe_key"
    PAYPAL_CLIENT_ID: str = "mock_paypal_client_id"
    GOOGLE_CLIENT_ID: str = "mock_google_oauth_client_id"
    MS_OUTLOOK_CLIENT_ID: str = "mock_outlook_client_id"


settings = Settings()
