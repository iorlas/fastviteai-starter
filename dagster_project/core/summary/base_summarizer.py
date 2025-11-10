import time
from typing import TypeVar

import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from dagster_project.core.cache.openai_parse_cache import cached_parse

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODEL = "mistralai/mistral-medium-3.1"


class BaseSummarizer:
    def __init__(
        self,
        openai_client: AsyncOpenAI,
        system_prompt: str,
        user_template: str,
        model: str = DEFAULT_MODEL,
        temperature: float = 0,
        max_tokens: int = 8192,
    ):
        self.client = openai_client
        self.system_prompt = system_prompt
        self.user_template = user_template
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._retry_attempt = 0

    async def _call_openai(
        self,
        user_content: str,
        response_model: type[T],
        log_context: dict | None = None,
    ) -> T:
        self._retry_attempt = 0
        return await self._call_with_retry(user_content, response_model, log_context or {})

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(ValidationError),
        reraise=True,
    )
    async def _call_with_retry(
        self,
        user_content: str,
        response_model: type[T],
        log_context: dict,
    ) -> T:
        self._retry_attempt += 1

        if self._retry_attempt > 1:
            logger.warning(
                "summarizer.retry",
                **log_context,
                attempt=self._retry_attempt,
                max_tokens=self.max_tokens * self._retry_attempt,
            )

        logger.info(
            "summarizer.started",
            **log_context,
            attempt=self._retry_attempt,
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content},
        ]

        max_tokens_for_attempt = self.max_tokens * self._retry_attempt

        start_time = time.time()
        structured_output = await cached_parse(
            client=self.client,
            model=self.model,
            messages=messages,
            response_model=response_model,
            temperature=self.temperature,
            max_tokens=max_tokens_for_attempt,
        )
        latency_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "summarizer.success",
            **log_context,
            model=self.model,
            schema=response_model.__name__,
            latency_ms=latency_ms,
            attempt=self._retry_attempt,
            max_tokens_used=max_tokens_for_attempt,
        )

        return structured_output
