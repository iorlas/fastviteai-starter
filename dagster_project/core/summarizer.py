import time

import structlog
from openai import OpenAI
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from dagster_project.core.summary_schema import KnowledgeGraphSummary

logger = structlog.get_logger()

DEFAULT_MODEL = "mistralai/mistral-medium-3.1"

DEFAULT_SYSTEM_PROMPT = """Extract information from content into structured JSON \
for programmatic processing.

Focus on:
- What's the ONE-SENTENCE answer to the article title?
- What's UNIQUE or NOVEL here (vs typical articles on this topic)?
- How do concepts CONNECT (visual relationships)?
- What aids MEMORY (sticky phrases, metaphors)?

CRITICAL: Capture ALL details, including:
- Full context around quotes (who said it, when, why - not just the quote)
- Exact numbers and team sizes (e.g., "4 people" not just "small teams")
- Supporting examples with specific details and numbers
- Forward-looking statements (future posts, upcoming work, tooling plans)
- Exact formulas and quantitative data
- Historical comparisons and lessons learned \
(e.g., how SOA failed, what went wrong with predecessors)
- Cautionary tales and warnings about pitfalls
- Contrarian examples that illustrate principles"""

DEFAULT_USER_PROMPT_TEMPLATE = """Extract structured information from this {content_type}:

Title: {title}

Content:
{content}

Provide comprehensive extraction covering:
- Core answer (one sentence directly answering the title)
- Unique insights (novel/contrarian views, standout data)
- Classification (topics, content type, depth level)
- Core insights (with memory aids, supporting facts, quantitative data, connections)
- Knowledge graph ASCII (visual relationships with arrows and hierarchies)
- Entities (people with full quote context, organizations, concepts, formulas with exact \
numbers, examples with specific details)
- Forward-looking statements (future posts, planned content)
- Memory aids (key phrases with full context, visual metaphors, mnemonics)"""


class SummaryRequest(BaseModel):
    content: str
    title: str
    content_type: str
    url: str


class SummaryResult(BaseModel):
    structured_summary: KnowledgeGraphSummary
    model: str
    tokens_used: int
    latency_ms: int


class SummaryGenerator:
    def __init__(
        self,
        openai_client: OpenAI,
        model: str = DEFAULT_MODEL,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        user_prompt_template: str = DEFAULT_USER_PROMPT_TEMPLATE,
        response_schema: type[BaseModel] = KnowledgeGraphSummary,
        temperature: float = 0,
        max_tokens: int = 8192,
        max_retries: int = 2,
    ):
        self.client = openai_client
        self.model = model
        self.system_prompt = system_prompt
        self.user_prompt_template = user_prompt_template
        self.response_schema = response_schema
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self._retry_attempt = 0

    def generate(self, request: SummaryRequest) -> SummaryResult:
        self._retry_attempt = 0
        return self._generate_with_retry(request)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(ValidationError),
        reraise=True,
    )
    def _generate_with_retry(self, request: SummaryRequest) -> SummaryResult:
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

    def _create_prompt(self, request: SummaryRequest) -> list[dict[str, str]]:
        system_message = {"role": "system", "content": self.system_prompt}

        user_content = self.user_prompt_template.format(
            content_type=("video transcript" if request.content_type == "youtube" else "article"),
            title=request.title,
            content=request.content,
        )

        user_message = {"role": "user", "content": user_content}

        return [system_message, user_message]
