import time

import structlog
from openai import OpenAI
from pydantic import BaseModel

logger = structlog.get_logger()


class SummaryRequest(BaseModel):
    content: str
    title: str
    content_type: str
    url: str


class SummaryResult(BaseModel):
    summary: str
    model: str
    tokens_used: int
    latency_ms: int


class SummaryGenerator:
    def __init__(self, openai_client: OpenAI, model: str = "gpt-4o"):
        self.client = openai_client
        self.model = model

    def generate(self, request: SummaryRequest) -> SummaryResult:
        logger.info("summarize.started", url=request.url, title=request.title)

        messages = self._create_prompt(request)

        start_time = time.time()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )
        latency_ms = int((time.time() - start_time) * 1000)

        summary_text = response.choices[0].message.content

        tokens_used = (
            response.usage.total_tokens
            if hasattr(response, "usage") and hasattr(response.usage, "total_tokens")
            else 0
        )

        model_used = response.model if hasattr(response, "model") else self.model

        logger.info(
            "summarize.success",
            url=request.url,
            title=request.title,
            model=model_used,
            tokens=tokens_used,
            latency_ms=latency_ms,
        )

        return SummaryResult(
            summary=summary_text,
            model=model_used,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )

    def _create_prompt(self, request: SummaryRequest) -> list[dict[str, str]]:
        system_message = {
            "role": "system",
            "content": (
                "You are a helpful assistant that creates concise, informative summaries "
                "of articles and videos. Focus on key points, main ideas, and actionable insights."
            ),
        }

        content_type = "video transcript" if request.content_type == "youtube" else "article"

        user_message = {
            "role": "user",
            "content": (
                f"Please summarize this {content_type}:\n\n"
                f"Title: {request.title}\n\n"
                f"Content:\n{request.content}\n\n"
                f"Provide a clear, structured summary covering:\n"
                f"1. Main topic and key points\n"
                f"2. Important details and supporting information\n"
                f"3. Key takeaways or conclusions"
            ),
        }

        return [system_message, user_message]
