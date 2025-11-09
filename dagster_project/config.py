from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    artifacts_path: Path = Field(
        default_factory=lambda: Path("artifacts"),
        description="Artifacts directory for all persistent data (inputs, bronze, silver, cache)",
    )

    openai_api_key: str = Field(
        default="",
        description="OpenAI/OpenRouter API key",
    )
    openai_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenAI/OpenRouter API base URL",
    )
    openai_model: str = Field(
        default="openai/gpt-4o",
        description="OpenAI model to use for summarization",
    )

    enable_summarization: bool = Field(
        default=True,
        description="Enable/disable AI summarization",
    )

    http_proxy: str | None = Field(
        default=None,
        description="HTTP/HTTPS/SOCKS5 proxy URL for all HTTP operations (e.g., http://proxy:port or socks5://proxy:port)",
    )


settings = Settings()
