import time

import structlog
from openai import OpenAI
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from dagster_project.core.summary.schema import KnowledgeGraphSummary

logger = structlog.get_logger()

DEFAULT_MODEL = "mistralai/mistral-medium-3.1"

DEFAULT_SYSTEM_PROMPT = """You're an expert analyst talking to another expert. Be dense, technical, direct.

ANALYZE:
- <content>: Article/video
- <discussions>: HN/Lobsters threads

OUTPUT: Two independent takes
1. YOUR assessment (llm)
2. COMMUNITY assessment (community)

STYLE:
- Arrows over words: "X → Y", "problem → solution"
- Numbers always: "2s → 200ms", "team of 4", "100K req/day"
- Direct phrases: "Missing error handling" (not "doesn't discuss")
- Concrete terms: "B-tree indexes" (not "indexing strategies")
- No fluff: skip "interesting", "nice", "good"

EXAMPLES:
Good: "Partial indexes → 100x speedup, 3x write penalty"
Bad: "The article discusses how partial indexes improve performance"

Good: "Ignores connection pooling"
Bad: "The article doesn't cover connection pooling considerations"

For tags: specific tech (redis-clustering, not caching)
For semantic_summary: pack concepts densely

Respect all field constraints. Cut every unnecessary word."""


class SummaryInput(BaseModel):
    content: str
    title: str
    content_type: str
    url: str
    discussions: str | None = None  # Formatted plain text with tab-indented replies


class SummaryResult[T: BaseModel](BaseModel):
    structured_summary: T
    model: str
    tokens_used: int
    latency_ms: int


class SummaryGenerator[T: BaseModel]:
    def __init__(
        self,
        openai_client: OpenAI,
        model: str = DEFAULT_MODEL,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        response_schema: type[T] = KnowledgeGraphSummary,
        temperature: float = 0,
        max_tokens: int = 8192,
        max_retries: int = 2,
    ):
        self.client = openai_client
        self.model = model
        self.system_prompt = system_prompt
        self.response_schema = response_schema
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self._retry_attempt = 0

    def generate(self, request: SummaryInput) -> SummaryResult[T]:
        content_length = len(request.content.strip())

        if content_length < 100:
            logger.warning(
                "summarize.empty_content",
                url=request.url,
                title=request.title,
                content_length=content_length,
            )
            raise ValueError(
                f"Content too short ({content_length} chars) - likely a JS-only site or failed extraction. "
                "Cannot generate meaningful summary from empty/minimal content."
            )

        self._retry_attempt = 0
        return self._generate_with_retry(request)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(ValidationError),
        reraise=True,
    )
    def _generate_with_retry(self, request: SummaryInput) -> SummaryResult[T]:
        self._retry_attempt += 1

        if self._retry_attempt > 1:
            logger.warning(
                "summarize.retry",
                url=request.url,
                attempt=self._retry_attempt,
                max_tokens=self.max_tokens * self._retry_attempt,
            )

        logger.info(
            "summarize.started",
            url=request.url,
            title=request.title,
            attempt=self._retry_attempt,
        )

        messages = self._create_prompt(request)

        max_tokens_for_attempt = self.max_tokens * self._retry_attempt

        start_time = time.time()
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=max_tokens_for_attempt,
            response_format=self.response_schema,
        )
        latency_ms = int((time.time() - start_time) * 1000)

        structured_summary = response.choices[0].message.parsed

        tokens_used = response.usage.total_tokens if hasattr(response, "usage") and hasattr(response.usage, "total_tokens") else 0

        model_used = response.model if hasattr(response, "model") else self.model

        logger.info(
            "summarize.success",
            url=request.url,
            title=request.title,
            model=model_used,
            tokens=tokens_used,
            latency_ms=latency_ms,
            attempt=self._retry_attempt,
            max_tokens_used=max_tokens_for_attempt,
        )

        return SummaryResult(
            structured_summary=structured_summary,
            model=model_used,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )

    def _create_prompt(self, request: SummaryInput) -> list[dict[str, str]]:
        system_message = {"role": "system", "content": self.system_prompt}

        content_type_label = "video transcript" if request.content_type == "youtube" else "article"

        # Build user content with XML structure
        user_content_parts = [
            "<content>",
            f"Title: {request.title}",
            f"URL: {request.url}",
            f"Type: {content_type_label}",
            "",
            request.content,
            "</content>",
        ]

        if request.discussions:
            user_content_parts.extend(
                [
                    "",
                    "<discussions>",
                    request.discussions,
                    "</discussions>",
                ]
            )

        user_content = "\n".join(user_content_parts)
        user_message = {"role": "user", "content": user_content}

        return [system_message, user_message]
