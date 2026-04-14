from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root (B-SPLTR/), so .env loads even when cwd is not the project directory
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "WealthSplit"

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/wealthsplit"

    # ── Supabase (single source of truth for auth) ──
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    # If empty, derived as {SUPABASE_URL}/auth/v1 — set explicitly if your JWT iss differs.
    SUPABASE_JWT_ISSUER: str = ""

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""

    # Stripe Issuing (virtual cards)
    STRIPE_ISSUING_ENABLED: bool = False

    # Feature flags
    FEATURE_VIRTUAL_CARDS: bool = False

    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_RECEIPT_VISION_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    GROQ_RECEIPT_CLEANUP_MODEL: str = "openai/gpt-oss-20b"

    UPLOAD_DIR: str = "./uploads"

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Base URL used in SMS links (must serve GET /pay/{token}, often API or app proxy)
    PUBLIC_PAYMENT_BASE_URL: str = "https://app.wealthsplit.com"

    # When Twilio is not configured, log SMS instead of sending (dev only)
    SMS_DEV_MODE: bool = True

    SMS_MAX_RETRIES: int = 3
    SMS_RETRY_BASE_DELAY_SEC: float = 0.5

    # Remind if still pending after N hours; at most one reminder per N hours
    REMINDER_UNPAID_AFTER_HOURS: int = 24
    REMINDER_MIN_INTERVAL_HOURS: int = 24

    # Optional: protect internal job endpoint
    INTERNAL_JOB_SECRET: str = ""

    # Run reminder job on interval (seconds); 0 disables in-process scheduler
    REMINDER_JOB_INTERVAL_SEC: int = 3600

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
