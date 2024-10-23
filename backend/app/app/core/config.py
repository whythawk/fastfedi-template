import secrets
from typing import Any, List, Optional
from typing_extensions import Self

from pydantic import field_validator, AnyHttpUrl, EmailStr, HttpUrl, PostgresDsn, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_core import MultiHostUrl


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")
    SERVER_NAME: str
    SERVER_HOST: AnyHttpUrl
    SERVER_BOT: str = "Symona"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    TOTP_SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 0  # access tokens don't expire -- they must be revoked
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * 30
    USE_REFRESH_TOKEN: bool = False  # don't use refresh tokens
    FORCE_TOTP: bool = True
    JWT_ALGO: str = "HS512"
    TOTP_ALGO: str = "SHA-1"
    HASH_ALGO: List[str] = ["argon2"]
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", "http://localhost:8080"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str
    SENTRY_DSN: Optional[HttpUrl] = None

    # ACTIVITYPUB SETTINGS
    JSONLD_MAX_SIZE: int = 1024 * 50  # 50 KB

    # NODEINFO 2.1
    SOFTWARE_NAME: str = "fastfedi"
    SOFTWARE_VERSION: str = "0.1.0"
    SOFTWARE_REPOSITORY: AnyHttpUrl = "https://github.com/whythawk/full-stack-fastfedi-template"
    SOFTWARE_HOMEPAGE: AnyHttpUrl = "https://github.com/whythawk/full-stack-fastfedi-template"
    OPEN_REGISTRATION: bool = True

    # GENERAL SETTINGS

    MULTI_MAX: int = 20

    # COMPONENT SETTINGS

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[misc]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    EMAILS_TO_EMAIL: Optional[EmailStr] = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_TEMPLATES_DIR: str = "/app/app/email-templates/build"

    @computed_field  # type: ignore[misc]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_PORT and self.EMAILS_FROM_EMAIL)

    EMAIL_TEST_USER: EmailStr = "test@example.com"  # type: ignore
    FIRST_ADMIN: EmailStr
    FIRST_ADMIN_PASSWORD: str

    # Redis cache settings
    DOCKER_IMAGE_CACHE: str = "cache"
    REDIS_PASSWORD: str
    REDIS_PORT: int = 6379


settings = Settings()
