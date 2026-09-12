from functools import lru_cache
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "StuSkillLink"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./stuskilllink.db"
    jwt_secret_key: str = "stuskilllink-local-development-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    auto_seed_demo: bool = True
    langgraph_checkpoint_path: str = "./langgraph-checkpoints.sqlite"

    # NVIDIA NIM hosted endpoint. A self-hosted NIM can be supplied instead.
    nim_api_key: str | None = Field(default=None, validation_alias=AliasChoices("NVIDIA_NIM_API_KEY", "NIM_API_KEY"))
    nim_base_url: str = Field(default="https://integrate.api.nvidia.com/v1", validation_alias=AliasChoices("NVIDIA_NIM_BASE_URL", "NIM_BASE_URL"))
    nim_model: str = Field(default="meta/llama-3.1-8b-instruct", validation_alias=AliasChoices("NVIDIA_NIM_MODEL", "NIM_MODEL"))
    nim_embedding_model: str | None = Field(default=None, validation_alias=AliasChoices("NVIDIA_NIM_EMBEDDING_MODEL", "NIM_EMBEDDING_MODEL"))
    nim_timeout_seconds: int = 45
    nim_temperature: float = 0.2
    nim_max_tokens: int = 1200

    # Provider-agnostic LLM gateway. Providers are attempted in this order and
    # automatically fail over when a key is missing, rate-limited, or unhealthy.
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
    def llm_provider_order(self) -> list[str]:
        supported = {"nvidia", "openrouter", "groq", "gemini"}
        requested = [item.strip().lower() for item in self.llm_provider_priority.split(",")]
        return [item for item in requested if item in supported]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
