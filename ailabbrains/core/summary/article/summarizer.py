from openai import AsyncOpenAI
from pydantic import BaseModel

from ailabbrains.core.summary.base_summarizer import BaseSummarizer
from ailabbrains.core.summary.schema import ArticleAnalysis

DEFAULT_SYSTEM_PROMPT = """You're an expert analyst talking to another expert. Be dense, technical, direct.

ANALYZE:
- <content>: Article/video (NO discussions in this stage)

OUTPUT: Your assessment
- triage: Quick action recommendation
- article: Type, novelty, depth, key points, technical tags
- signals: New info, controversial, actionable, impact
- signal_quality: Signal-to-noise analysis
- llm: Your technical verdict

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

Respect all field constraints. Cut every unnecessary word.
NOTE: community field will be added later from discussion analysis - leave it as null."""

DEFAULT_USER_TEMPLATE = """<content>
Title: {title}
URL: {url}
Type: {content_type}

{content}
</content>"""


class ArticleSummarizer(BaseSummarizer):
    def __init__(
        self,
        openai_client: AsyncOpenAI,
        max_tokens: int = 8192,
        model: str | None = None,
        system_prompt: str | None = None,
        user_template: str | None = None,
        response_model: type[BaseModel] | None = None,
    ):
        super().__init__(
            openai_client,
            system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
            user_template=user_template or DEFAULT_USER_TEMPLATE,
            model=model,  # Pass model to BaseSummarizer (uses default if None)
            max_tokens=max_tokens,
        )
        self.response_model = response_model or ArticleAnalysis

    async def summarize(
        self,
        content: str,
        title: str,
        url: str,
        content_type: str,
    ) -> ArticleAnalysis:
        # Validate content length
        content_length = len(content.strip())
        if content_length < 100:
            raise ValueError(
                f"Content too short ({content_length} chars) - likely a JS-only site or failed extraction. "
                "Cannot generate meaningful summary from empty/minimal content."
            )

        # Format user content
        content_type_label = "video transcript" if content_type == "youtube" else "article"
        user_content = self.user_template.format(
            title=title,
            url=url,
            content_type=content_type_label,
            content=content,
        )

        # Call OpenAI with logging context
        log_context = {"url": url, "title": title, "stage": "article"}
        return await self._call_openai(user_content, self.response_model, log_context)
