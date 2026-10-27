import ipaddress
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: Literal["development", "test", "staging", "production"] = "development"
    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://quickbuddy:REPLACE_ME@127.0.0.1:5432/quickbuddy_dev"
    )
    database_ssl: bool = False
    db_pool_size: int = Field(default=5, ge=1, le=100)
    db_max_overflow: int = Field(default=10, ge=0, le=100)
    redis_url: SecretStr = SecretStr("redis://127.0.0.1:6379/0")
    metrics_enabled: bool = False
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
    calling_enabled: bool = True
    call_stun_urls: list[str] = ["stun:stun.l.google.com:19302"]
    call_turn_urls: list[str] = []
    call_turn_secret: SecretStr = SecretStr("")
    sandbox_webhook_secret: SecretStr = SecretStr("")
    payment_provider: Literal["razorpay"] = "razorpay"
    razorpay_enabled: bool = False
    razorpay_mode: Literal["disabled", "test", "live"] = "disabled"
    razorpay_key_id: SecretStr = SecretStr("")
    razorpay_key_secret: SecretStr = SecretStr("")
    razorpay_webhook_secret: SecretStr = SecretStr("")
    razorpay_webhook_secret_previous: SecretStr = SecretStr("")
    razorpay_auto_capture: bool = True
    razorpay_route_enabled: bool = False
    razorpay_payouts_enabled: bool = False
    razorpay_live_approval: bool = False
    otp_pepper: SecretStr = SecretStr("")
    auth_rate_limit_per_minute: int = Field(default=20, ge=1, le=10000)
    api_requests_per_minute: int = Field(default=600, ge=30, le=100000)
    max_request_body_bytes: int = Field(default=6 * 1024 * 1024, ge=1024, le=10 * 1024 * 1024)
    trusted_proxy_cidrs: list[str] = []
    pilot_location_fresh_seconds: int = Field(default=90, ge=15, le=300)
    pilot_location_history_interval_seconds: int = Field(default=15, ge=5, le=300)
    pilot_location_retention_days: int = Field(default=7, ge=1, le=30)
    tracking_websocket_ticket_seconds: int = Field(default=60, ge=15, le=120)
    tracking_websocket_max_connections: int = Field(default=2000, ge=1, le=20000)
    pickup_handling_seconds: int = Field(default=180, ge=0, le=1800)
    delivery_handling_seconds: int = Field(default=120, ge=0, le=1800)
    ai_provider: Literal["disabled", "openai_compatible", "local"] = "disabled"
    ai_base_url: str = ""
    ai_model: str = ""
    ai_api_key: SecretStr = SecretStr("")
    ai_timeout_seconds: float = Field(default=8.0, gt=0, le=30)
    ai_max_output_tokens: int = Field(default=400, ge=32, le=1200)

    @model_validator(mode="after")
    def validate_config(self):
        if any(not url.startswith(("stun:", "stuns:")) for url in self.call_stun_urls):
            raise ValueError("CALL_STUN_URLS requires STUN URLs")
        if any(not url.startswith(("turn:", "turns:")) for url in self.call_turn_urls):
            raise ValueError("CALL_TURN_URLS requires TURN URLs")
        if self.call_turn_urls and len(self.call_turn_secret.get_secret_value()) < 32:
            raise ValueError("TURN requires CALL_TURN_SECRET of at least 32 characters")
        url = make_url(self.database_url.get_secret_value())
        if url.drivername != "postgresql+asyncpg":
            raise ValueError("DATABASE_URL requires postgresql+asyncpg")
        if self.app_env == "development" and url.database != "quickbuddy_dev":
            raise ValueError("Use the dedicated quickbuddy_dev database in development")
        if self.app_env == "test" and url.database not in {"quickbuddy_dev", "quickbuddy_test"}:
            raise ValueError("Use a dedicated quickbuddy_dev or quickbuddy_test database")
        if any("*" in origin for origin in self.cors_origins):
            raise ValueError("Explicit CORS origins required")
        try:
            for proxy_cidr in self.trusted_proxy_cidrs:
                ipaddress.ip_network(proxy_cidr, strict=False)
        except ValueError as exc:
            raise ValueError("TRUSTED_PROXY_CIDRS must contain valid IP networks") from exc
        if self.app_env in {"staging", "production"}:
            if self.auth_private_key_path:
                raise ValueError("Local password authentication is forbidden in staging/production")
            if not self.database_ssl or "REPLACE_ME" in self.database_url.get_secret_value():
                raise ValueError(
                    "Staging/production database requires credentials and verified TLS"
                )
            if not all((self.oidc_issuer, self.oidc_audience, self.oidc_jwks_url)):
                raise ValueError("Staging/production requires OIDC configuration")
            if any(
                not value.startswith("https://")
                for value in [self.oidc_issuer, self.oidc_jwks_url, *self.cors_origins]
            ):
                raise ValueError("Staging/production OIDC and origins require HTTPS")
        if self.app_env == "production":
            if self.sandbox_payments_enabled:
                raise ValueError("Sandbox payment adapter is forbidden in production")
        if self.razorpay_enabled:
            if self.razorpay_mode == "disabled":
                raise ValueError("RAZORPAY_ENABLED requires test or live mode")
            if not all(
                (
                    self.razorpay_key_id.get_secret_value(),
                    self.razorpay_key_secret.get_secret_value(),
                )
            ):
                raise ValueError("Enabled Razorpay requires server-side API credentials")
            if self.razorpay_mode == "test" and self.app_env == "production":
                raise ValueError("Razorpay test mode cannot be enabled in production")
            if self.razorpay_mode == "live" and (
                self.app_env != "production" or not self.razorpay_live_approval
            ):
                raise ValueError("Razorpay live mode requires production and explicit approval")
            if self.razorpay_mode == "live" and not self.razorpay_webhook_secret.get_secret_value():
                raise ValueError("Live Razorpay mode requires a webhook secret")
        elif self.razorpay_mode != "disabled":
            raise ValueError("Set RAZORPAY_ENABLED=true to activate the configured Razorpay mode")
        if self.razorpay_route_enabled or self.razorpay_payouts_enabled:
            raise ValueError("Razorpay Route and payouts are not implemented or activatable")
        if self.ai_provider != "disabled" and (not self.ai_base_url or not self.ai_model):
            raise ValueError("Enabled AI provider requires AI_BASE_URL and AI_MODEL")
        if self.ai_provider == "openai_compatible" and not self.ai_api_key.get_secret_value():
            raise ValueError("OpenAI-compatible AI provider requires AI_API_KEY")
        if (
            self.app_env in {"staging", "production"}
            and self.ai_provider != "disabled"
            and not self.ai_base_url.startswith("https://")
        ):
            raise ValueError("Production AI provider endpoint must use HTTPS")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
