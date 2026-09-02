from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import os
from pathlib import Path


class Settings(BaseSettings):
    model_config = {
        "extra": "ignore",
        "env_file": "/app/.env",
        "case_sensitive": True
    }

    # Database Configuration — PostgreSQL for ZKTeco ADMS
    DATABASE_URL: str = "postgresql://pob_user:pob_password@postgres:5432/pob_system"
    DATABASE_HOST: str = "postgres"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "pob_system"
    DATABASE_USER: str = "pob_user"
    DATABASE_PASSWORD: str = "pob_password"

    # PostgreSQL Connection Pooling (for ZKTeco ADMS concurrent requests)
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True

    # Operating timezone.
    # Punches are stored as UTC instants, but shift start/end times are entered
    # by an administrator as local wall-clock. Comparing the two without
    # converting made every employee read an hour early in Lagos (UTC+1) —
    # lateness under-reported, early departure over-reported.
    TIMEZONE: str = "Africa/Lagos"

    # Redis Configuration
    # REDIS_URL is derived from REDIS_HOST/PORT/DB/PASSWORD unless it is set
    # explicitly. Deployments only ever set REDIS_HOST, so a hardcoded default
    # here silently pointed pub/sub at a host that does not exist.
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = ""

    @validator("REDIS_URL", pre=True, always=True)
    def _build_redis_url(cls, v, values):
        if v:
            return v
        auth = f":{values.get('REDIS_PASSWORD')}@" if values.get("REDIS_PASSWORD") else ""
        host = values.get("REDIS_HOST", "redis")
        port = values.get("REDIS_PORT", 6379)
        db   = values.get("REDIS_DB", 0)
        return f"redis://{auth}{host}:{port}/{db}"

    # JWT Configuration
    SECRET_KEY: str = "pob-system-production-secret-key-2024-secure-jwt-auth"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 24

    # API / Application Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Apex POB"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "Personnel On Board Management System for Oil & Gas Operations"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_SQL: bool = False  # separate from DEBUG — avoids SQLAlchemy echo spam in dev
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # File paths
    BASE_DIR: str = str(Path(__file__).parent.parent.parent)

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://localhost:5173",
        # The native clock app. Inside Capacitor the page is served from a
        # local scheme, so every API call is cross-origin — "https://localhost"
        # on Android and "capacitor://localhost" on iOS. Without these the app
        # signs in against a CORS error and nothing else works.
        "https://localhost",
        "capacitor://localhost",
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # ZKTeco / ADMS Configuration
    # ZKTECO_ADMS_SERVER / ZKTECO_ADMS_PORT — ZKTeco cloud ADMS base URL
    ZKTECO_ADMS_SERVER: str = "https://adms.zkteco.com"
    ZKTECO_ADMS_PORT: str = "443"
    # ZKTECO_COMPANY_ID / ZKTECO_ADMS_TOKEN — credentials for ZKTeco cloud ADMS
    ZKTECO_COMPANY_ID: str = ""
    ZKTECO_ADMS_TOKEN: str = ""
    # ZKTECO_API_BASE_URL / credentials — for direct device HTTP API (optional)
    ZKTECO_API_BASE_URL: str = ""
    ZKTECO_USERNAME: str = ""
    ZKTECO_PASSWORD: str = ""
    ZKTECO_TIMEOUT: int = 30
    # Auto-register unknown devices that check in via ADMS /iclock/cdata
    ZKTECO_AUTO_REGISTER_DEVICES: bool = True

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    RATE_LIMIT_AUTH_REQUESTS: int = 10
    RATE_LIMIT_AUTH_WINDOW: int = 300

    # File Upload
    MAX_FILE_SIZE: int = 10485760  # 10 MB

    # Security Headers
    SECURE_SSL_REDIRECT: bool = False
    SECURE_HSTS_SECONDS: int = 31536000
    SECURE_CONTENT_TYPE_NOSNIFF: bool = True

    # License / Subscription
    LICENSE_SECRET: str = "pob-vendor-license-secret-change-this"
    GLOBAL_ADMIN_PASSWORD: str = "GlobalAdmin@2026"

    # Emergency webhook — required for external fire/gas panel integration
    # Must be set explicitly; left empty to disable the webhook endpoint entirely
    EMERGENCY_WEBHOOK_KEY: str = ""

    # Notification channels (SMTP, SMS, WhatsApp)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    SMTP_TLS: bool = True
    SMS_API_URL: str = ""
    SMS_API_KEY: str = ""
    WHATSAPP_API_URL: str = ""
    WHATSAPP_API_KEY: str = ""
    FCM_KEY: str = ""

    @validator("SECRET_KEY")
    def secret_key_must_be_strong(cls, v, values):
        import os
        insecure_defaults = {
            "pob-system-production-secret-key-2024-secure-jwt-auth",
            "changethis",
            "secret",
            "your-secret-key",
        }
        # Read ENVIRONMENT order-independently — the validated `values` may not
        # yet contain ENVIRONMENT depending on field order, which silently
        # disabled this guard. The container always sets it as an env var.
        env = os.getenv("ENVIRONMENT") or values.get("ENVIRONMENT", "development")
        if env == "production":
            # Reject known defaults AND any low-entropy key — not just exact matches.
            if v in insecure_defaults or len(v) < 32:
                raise ValueError(
                    "SECRET_KEY is weak or a known default (needs >=32 chars in production). "
                    "Generate one: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
                )
        return v

    @validator("GLOBAL_ADMIN_PASSWORD")
    def global_admin_password_must_be_changed(cls, v, values):
        import os
        insecure_defaults = {"GlobalAdmin@2026", "changethis", "admin", "password", "admin123"}
        env = os.getenv("ENVIRONMENT") or values.get("ENVIRONMENT", "development")
        if env == "production":
            # Reject known defaults AND anything that fails a basic complexity floor.
            import re
            weak = (
                v in insecure_defaults
                or len(v) < 12
                or not re.search(r"[A-Z]", v)
                or not re.search(r"[a-z]", v)
                or not re.search(r"\d", v)
            )
            if weak:
                raise ValueError(
                    "GLOBAL_ADMIN_PASSWORD is a default or too weak. "
                    "Set a strong value in .env.prod (min 12 chars, upper+lower+digit)."
                )
        return v

    @validator("LICENSE_SECRET")
    def license_secret_must_be_changed(cls, v, values):
        import os
        env = os.getenv("ENVIRONMENT") or values.get("ENVIRONMENT", "development")
        if v == "pob-vendor-license-secret-change-this" and env == "production":
            raise ValueError(
                "LICENSE_SECRET is using the default value. "
                "Set a unique secret in .env.prod to prevent unauthorized license generation."
            )
        return v


settings = Settings()
