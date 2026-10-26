from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: Literal["development", "test", "production"] = "development"
    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://quickbuddy:REPLACE_ME@127.0.0.1:5432/quickbuddy_dev"
    )
    database_ssl: bool = False
    db_pool_size: int = Field(default=5, ge=1, le=100)
    db_max_overflow: int = Field(default=10, ge=0, le=100)
    redis_url: SecretStr = SecretStr("redis://127.0.0.1:6379/0")
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8082",
    ]
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_jwks_url: str = ""
    auth_private_key_path: str = ""
    auth_issuer: str = "quickbuddy-local"
    auth_audience: str = "quickbuddy-api"
    access_token_seconds: int = Field(default=900, ge=60, le=3600)
    refresh_token_days: int = Field(default=30, ge=1, le=90)
    sandbox_payments_enabled: bool = False
    sandbox_webhook_secret: SecretStr = SecretStr("")
    otp_pepper: SecretStr = SecretStr("")
    auth_rate_limit_per_minute: int = Field(default=20, ge=1, le=10000)

    @model_validator(mode="after")
    def validate_config(self):
        url = make_url(self.database_url.get_secret_value())
        if url.drivername != "postgresql+asyncpg":
            raise ValueError("DATABASE_URL requires postgresql+asyncpg")
        expected = "quickbuddy_test" if self.app_env == "test" else "quickbuddy_dev"
        if self.app_env != "production" and url.database not in (
            {"quickbuddy_dev", "quickbuddy_test"} if self.app_env == "test" else {expected}
        ):
            raise ValueError("Use a dedicated quickbuddy_dev or quickbuddy_test database")
        if any("*" in origin for origin in self.cors_origins):
            raise ValueError("Explicit CORS origins required")
        if self.app_env == "production":
            if self.sandbox_payments_enabled:
                raise ValueError("Sandbox payment adapter is forbidden in production")
            if not self.database_ssl or "REPLACE_ME" in self.database_url.get_secret_value():
                raise ValueError("Production database requires credentials and verified TLS")
            if not all((self.oidc_issuer, self.oidc_audience, self.oidc_jwks_url)):
                raise ValueError("Production requires OIDC configuration")
            if any(
                not value.startswith("https://")
                for value in [self.oidc_issuer, self.oidc_jwks_url, *self.cors_origins]
            ):
                raise ValueError("Production OIDC and origins require HTTPS")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
