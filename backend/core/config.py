from __future__ import annotations
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from typing import Optional


class AppSettings(BaseSettings):
    """
    🎯 Ilovaning global konfiguratsiyasi (FastAPI, DB, JWT, Redis, S3, Celery, va h.k.)
    Barcha xizmatlar uchun yagona `Settings` manbai.
    """

    # =======================
    # 🏛 Asosiy app sozlamalari
    # =======================
    APP_NAME: str = Field(default="University Attendance System")
    APP_ENV: str = Field(default="development")  # development | production | test
    DEBUG: bool = Field(default=True)
    API_V1_PREFIX: str = ""
    TIMEZONE: str = Field(default="Asia/Tashkent")

    # =======================
    # 🗄 Ma’lumotlar bazasi (PostgreSQL/Timescale)
    # =======================
    DB_USER: str = Field(default="turnikeuser")
    DB_PASSWORD: str = Field(default="StrongSecurePass123!")
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5436)
    DB_NAME: str = Field(default="turnikedb")

    @property
    def DATABASE_URL(self) -> str:
        """Async SQLAlchemy/SQLModel uchun to‘liq DSN."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Sync versiya (Alembic uchun)"""
        return self.DATABASE_URL.replace("+asyncpg", "")

    # =======================
    # 🔐 JWT / Authentication
    # =======================
    JWT_SECRET_KEY: str = Field(default="change_this_super_secret_key")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)       # 1 soat
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=43200)   # 30 kun

    PASSWORD_MIN_LENGTH: int = Field(default=8)
    PASSWORD_MAX_LENGTH: int = Field(default=64)

    # =======================
    # 🧠 Redis (cache + Celery broker)
    # =======================
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # =======================
    # ⚙️ Celery (task queue)
    # =======================
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    CELERY_TIMEZONE: str = Field(default="Asia/Tashkent")

    def get_celery_broker(self) -> str:
        """Celery broker avtomatik aniqlanadi (Redis orqali)"""
        return self.CELERY_BROKER_URL or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    def get_celery_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    # =======================
    # ☁️ S3 / MinIO
    # =======================
    S3_ENDPOINT: str = Field(default="http://localhost:9000")
    S3_ACCESS_KEY: str = Field(default="minioadmin")
    S3_SECRET_KEY: str = Field(default="minioadmin")
    S3_BUCKET: str = Field(default="uploads")
    S3_REGION: str = Field(default="us-east-1")
    S3_SECURE: bool = Field(default=False)

    # =======================
    # 📧 Email (SMTP)
    # =======================
    SMTP_SERVER: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = Field(default=True)
    SMTP_FROM_EMAIL: Optional[str] = None

    # =======================
    # 🧾 Logging
    # =======================
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE_PATH: str = Field(default="logs/app.log")
    LOG_ROTATION: str = Field(default="10 MB")
    LOG_RETENTION: str = Field(default="10 days")

    # =======================
    # 🧩 Validatorlar
    # =======================
    @validator("APP_ENV")
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "production", "test"}
        if v not in allowed:
            raise ValueError(f"APP_ENV must be one of: {', '.join(allowed)}")
        return v

    @validator("PASSWORD_MIN_LENGTH")
    def validate_password_length(cls, v: int) -> int:
        if v < 6:
            raise ValueError("Minimum password length must be >= 6")
        return v

    @validator("DB_HOST")
    def validate_db_host(cls, v: str) -> str:
        if not v:
            raise ValueError("DB_HOST cannot be empty")
        return v

    # =======================
    # ⚙️ Model config
    # =======================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


# =======================
# 🧠 Cached instance (singleton)
# =======================
@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Caching orqali konfiguratsiyani tezkor olish."""
    return AppSettings()
