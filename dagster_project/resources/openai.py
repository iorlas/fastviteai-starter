import os
from functools import cached_property
from typing import Any

from dagster import ConfigurableResource
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import Field

# Load environment variables from .env file
load_dotenv()


class OpenAIClient(ConfigurableResource):
    api_key: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", ""),
        description="OpenAI API key",
    )
    model: str = Field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "openai/gpt-4o"),
        description="Model identifier",
    )
    base_url: str = Field(
        default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
        description="OpenAI API base URL",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")

    @cached_property
    def client(self) -> OpenAI:
        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            max_retries=3,
            timeout=self.timeout,
        )

    def _validate_config(self) -> None:
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required but not set. "
                "Please set it in your .env file or environment."
            )

    def setup_for_execution(self, context) -> None:
        self._validate_config()
        context.log.info(f"OpenAI client initialized with model: {self.model}")

    def chat_completion(
        self,
        context,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Any:
        self._validate_config()

        # Log request metadata
        context.log.debug(
            f"OpenAI API request: model={self.model}, "
            f"messages={len(messages)}, temp={temperature}, "
            f"max_tokens={max_tokens or 'unlimited'}"
        )

        # Make API call using OpenAI client
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        # Log response metadata (token usage, model)
        context.log.debug(
            f"OpenAI API response: model={response.model}, "
            f"completion_tokens={response.usage.completion_tokens}, "
            f"prompt_tokens={response.usage.prompt_tokens}, "
            f"total_tokens={response.usage.total_tokens}"
        )

        return response

    def get_completion_text(self, response: Any) -> str:
        return response.choices[0].message.content


# Resource factory for Dagster definitions
openai_resource = OpenAIClient()
