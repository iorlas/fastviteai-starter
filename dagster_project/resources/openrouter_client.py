"""OpenRouter API client resource for Dagster."""

import os
from functools import cached_property
from typing import Any

from dagster import ConfigurableResource
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import Field

# Load environment variables from .env file
load_dotenv()


class OpenRouterClient(ConfigurableResource):
    """OpenRouter API client resource for making LLM requests.

    Attributes:
        api_key: OpenRouter API key (loaded from OPENROUTER_API_KEY env var)
        model: Model identifier to use (default: openai/gpt-4o)
        base_url: OpenRouter API base URL
        timeout: Request timeout in seconds
    """

    api_key: str = Field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""),
        description="OpenRouter API key",
    )
    model: str = Field(
        default_factory=lambda: os.getenv("OPENROUTER_MODEL", "openai/gpt-4o"),
        description="Model identifier",
    )
    base_url: str = Field(
        default_factory=lambda: os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        description="OpenRouter API base URL",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")

    @cached_property
    def client(self) -> OpenAI:
        """OpenAI client instance (lazy initialized on first access).

        Returns:
            Configured OpenAI client for OpenRouter API
        """
        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            max_retries=3,
            timeout=self.timeout,
        )

    def _validate_config(self) -> None:
        """Validate that required configuration is present."""
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required but not set. "
                "Please set it in your .env file or environment."
            )

    def setup_for_execution(self, context) -> None:
        """Called by Dagster when the resource is initialized."""
        self._validate_config()
        context.log.info(f"OpenRouter client initialized with model: {self.model}")

    def chat_completion(
        self,
        context,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Make a chat completion request to OpenRouter.

        Args:
            context: Dagster execution context for logging
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate (optional)
            **kwargs: Additional parameters to pass to the API

        Returns:
            OpenAI response object

        Raises:
            openai.APIError: If the request fails
        """
        self._validate_config()

        # Log request metadata
        context.log.debug(
            f"OpenRouter API request: model={self.model}, "
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
            f"OpenRouter API response: model={response.model}, "
            f"completion_tokens={response.usage.completion_tokens}, "
            f"prompt_tokens={response.usage.prompt_tokens}, "
            f"total_tokens={response.usage.total_tokens}"
        )

        return response

    def get_completion_text(self, response: Any) -> str:
        """Extract the completion text from an API response.

        Args:
            response: OpenAI response object from chat_completion()

        Returns:
            The generated text content
        """
        return response.choices[0].message.content


# Resource factory for Dagster definitions
openrouter_resource = OpenRouterClient()
