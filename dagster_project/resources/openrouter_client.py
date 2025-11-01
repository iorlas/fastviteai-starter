"""OpenRouter API client resource for Dagster."""

import os
from typing import Any

import httpx
from dagster import ConfigurableResource
from dotenv import load_dotenv
from pydantic import Field

# Load environment variables from .env file
load_dotenv()


class OpenRouterClient(ConfigurableResource):
    """OpenRouter API client resource for making LLM requests.

    Attributes:
        api_key: OpenRouter API key (loaded from OPENROUTER_API_KEY env var)
        model: Model identifier to use (default: openai/gpt-4o)
        api_endpoint: OpenRouter API endpoint URL
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
    api_endpoint: str = Field(
        default="https://openrouter.ai/api/v1/chat/completions",
        description="OpenRouter API endpoint",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")

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
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make a chat completion request to OpenRouter.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate (optional)
            **kwargs: Additional parameters to pass to the API

        Returns:
            API response as a dictionary

        Raises:
            httpx.HTTPError: If the request fails
        """
        self._validate_config()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {"model": self.model, "messages": messages, "temperature": temperature, **kwargs}

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self.api_endpoint, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    def get_completion_text(self, response: dict[str, Any]) -> str:
        """Extract the completion text from an API response.

        Args:
            response: API response dictionary from chat_completion()

        Returns:
            The generated text content
        """
        return response["choices"][0]["message"]["content"]


# Resource factory for Dagster definitions
openrouter_resource = OpenRouterClient()
