"""Application settings, read from environment / .env via pydantic-settings."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    PROJECT_NAME: str = "AI Commerce Platform"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://commerce:commerce@localhost:5432/commerce"

    # Cache
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-me-in-production-please"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"

    # CORS — comma-separated string; parsed into a list below.
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Commerce / market
    CURRENCY: str = "EGP"

    # Drop-shipping agents
    # assisted:   agent prepares everything, operator approves & confirms the buy
    # simulation: agent auto-executes with fake refs (demo/testing only)
    # api:        official supplier API connectors (must be configured)
    AGENT_MODE: str = "assisted"
    MARGIN_MIN_PERCENT: float = 15.0  # minimum gross margin the sourcing agent requires

    # Payments (cod = cash on delivery; gateway needs a configured provider)
    PAYMENT_PROVIDER: str = "cod"

    # Generic official drop-ship supplier API connector.
    # Works with any supplier that exposes a conventional REST order API.
    # Empty base/key → connector stays inert (assisted flow is used).
    DROPSHIP_API_BASE: str = ""           # e.g. https://api.my-supplier.com/v1
    DROPSHIP_API_KEY: str = ""            # your supplier API key/token
    DROPSHIP_API_AUTH_STYLE: str = "bearer"   # bearer | x-api-key
    # JSON field in the supplier's create-order response that holds the order id.
    DROPSHIP_ORDER_ID_FIELD: str = "order_id"

    # Amazon Business API connector (official B2B procurement path).
    # Empty by default → the connector stays inert (assisted flow is used).
    # Fill these once your Amazon Business account + API access are approved.
    AMAZON_BUSINESS_CLIENT_ID: str = ""
    AMAZON_BUSINESS_CLIENT_SECRET: str = ""
    AMAZON_BUSINESS_REFRESH_TOKEN: str = ""
    # LWA token endpoint (region-specific for some accounts; default is global).
    AMAZON_BUSINESS_TOKEN_URL: str = "https://api.amazon.com/auth/o2/token"
    # Base URL of the Amazon Business API for your region/integration.
    AMAZON_BUSINESS_API_BASE: str = ""
    # Your Amazon Business marketplace id (e.g. Egypt) — from account setup.
    AMAZON_BUSINESS_MARKETPLACE_ID: str = ""

    # AI layer
    AI_PROVIDER: str = "stub"  # stub | anthropic | openai
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-haiku-4-5-20251001"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
