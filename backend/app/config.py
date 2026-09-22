from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_DEFAULT_JWT_SECRETS = {
    "stuskilllink-local-development-secret-change-me",
    "stuskilllink-local-change-me",
    "change-this-before-production-use-32-plus-characters",
    "REPLACE_WITH_AT_LEAST_32_RANDOM_CHARACTERS",
}


def sqlalchemy_database_url(value: str) -> str:
    """Select SQLAlchemy's installed psycopg v3 driver for plain Render URLs."""
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


class Settings(BaseSettings):
    app_name: str = "StuSkillLink"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./stuskilllink.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "stuskilllink-local-development-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    refresh_token_days: int = 14
    access_cookie_name: str = "stuskilllink_access"
    refresh_cookie_name: str = "stuskilllink_refresh"
    secure_cookies: bool = False
    cookie_samesite: str = "lax"
    cookie_domain: str | None = None
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080"
    allowed_hosts: str = "localhost,127.0.0.1,testserver"
    auto_seed_demo: bool = False
    auto_create_schema: bool = True
    require_email_verification: bool = False
    langgraph_checkpoint_path: str = "./langgraph-checkpoints.sqlite"
    max_resume_bytes: int = 3 * 1024 * 1024
    login_rate_limit_attempts: int = 8
    login_rate_limit_window_seconds: int = 900

    # Notification/connectors. Production email verification requires SMTP_URL.
    smtp_url: str | None = None
    smtp_from_email: str = "noreply@stuskilllink.local"
    email_token_minutes: int = 30
    password_reset_minutes: int = 20
    public_app_url: str = "http://localhost:5173"
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from_number: str | None = None
    mongodb_uri: str | None = None

    # NVIDIA NIM hosted endpoint. A self-hosted NIM can be supplied instead.
    nim_api_key: str | None = Field(default=None, validation_alias=AliasChoices("NVIDIA_NIM_API_KEY", "NIM_API_KEY"))
    nim_base_url: str = Field(default="https://integrate.api.nvidia.com/v1", validation_alias=AliasChoices("NVIDIA_NIM_BASE_URL", "NIM_BASE_URL"))
    nim_model: str = Field(default="meta/llama-3.1-8b-instruct", validation_alias=AliasChoices("NVIDIA_NIM_MODEL", "NIM_MODEL"))
    nim_embedding_model: str | None = Field(default=None, validation_alias=AliasChoices("NVIDIA_NIM_EMBEDDING_MODEL", "NIM_EMBEDDING_MODEL"))
    nim_timeout_seconds: int = 45
    nim_temperature: float = 0.2
    nim_max_tokens: int = 1200

    # Provider-agnostic LLM gateway.
    llm_provider_priority: str = "nvidia,groq,gemini,openrouter"
    llm_timeout_seconds: int = 30
    llm_temperature: float = 0.2
    llm_max_tokens: int = 700

    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openrouter/free"

    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "openai/gpt-oss-20b"

    gemini_api_key: str | None = Field(default=None, validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"))
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_model: str = "gemini-2.5-flash-lite"

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def allowed_host_list(self) -> list[str]:
        return [item.strip() for item in self.allowed_hosts.split(",") if item.strip()]

    @property
    def llm_provider_order(self) -> list[str]:
        supported = {"nvidia", "openrouter", "groq", "gemini"}
        requested = [item.strip().lower() for item in self.llm_provider_priority.split(",")]
        return [item for item in requested if item in supported]

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in {"production", "prod"}

    @field_validator("cookie_samesite")
    @classmethod
    def validate_cookie_samesite(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("COOKIE_SAMESITE must be lax, strict, or none")
        return normalized

    @model_validator(mode="after")
    def validate_production_settings(self):
        if not self.is_production:
            return self
        errors: list[str] = []
        if self.debug:
            errors.append("DEBUG must be false in production")
        if self.auto_seed_demo:
            errors.append("AUTO_SEED_DEMO must be false in production")
        if self.auto_create_schema:
            errors.append("AUTO_CREATE_SCHEMA must be false in production; run Alembic migrations")
        if not self.database_url.lower().startswith(("postgresql://", "postgresql+psycopg://")):
            errors.append("Production DATABASE_URL must use PostgreSQL")
        secret_upper = self.jwt_secret_key.upper()
        if (
            len(self.jwt_secret_key) < 32
            or self.jwt_secret_key in _DEFAULT_JWT_SECRETS
            or any(marker in secret_upper for marker in ("CHANGE_ME", "CHANGEME", "REPLACE_WITH"))
        ):
            errors.append("JWT_SECRET_KEY must be a unique 32+ character secret and not a template placeholder")
        redis_upper = self.redis_url.upper()
        if not self.redis_url.lower().startswith(("redis://", "rediss://")) or self.redis_url == "redis://localhost:6379/0" or any(marker in redis_upper for marker in ("CHANGE_ME", "CHANGEME", "REPLACE_WITH")):
            errors.append("REDIS_URL must be explicitly configured for production")
        if any(marker in self.database_url.upper() for marker in ("CHANGE_ME", "CHANGEME", "REPLACE_WITH")):
            errors.append("Production DATABASE_URL must not contain template placeholder credentials")
        if self.smtp_url and any(marker in self.smtp_url.upper() for marker in ("CHANGE_ME", "CHANGEME", "REPLACE_WITH")):
            errors.append("SMTP_URL must not contain template placeholder credentials")
        if not self.cors_list or "*" in self.cors_list:
            errors.append("Production CORS_ORIGINS must contain explicit trusted origins")
        if not self.allowed_host_list or "*" in self.allowed_host_list:
            errors.append("Production ALLOWED_HOSTS must contain explicit host names")
        if not self.public_app_url.lower().startswith("https://"):
            errors.append("PUBLIC_APP_URL must use HTTPS in production")
        if any(not origin.lower().startswith("https://") for origin in self.cors_list):
            errors.append("All production CORS_ORIGINS must use HTTPS")
        if not self.secure_cookies:
            errors.append("SECURE_COOKIES must be true in production")
        if self.cookie_samesite == "none" and not self.secure_cookies:
            errors.append("COOKIE_SAMESITE=none requires SECURE_COOKIES=true")
        if self.require_email_verification and not self.smtp_url:
            errors.append("SMTP_URL is required when email verification is enabled")
        if errors:
            raise ValueError("; ".join(errors))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
