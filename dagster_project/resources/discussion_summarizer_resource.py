from functools import cached_property

from dagster import ConfigurableResource
from pydantic import Field

from dagster_project.config import settings
from dagster_project.core.cache.cached_openai_client import get_cached_openai_client
from dagster_project.core.discussions.unified_models import UnifiedDiscussion
from dagster_project.core.summary.discussion.summarizer import DiscussionSummarizer


class DiscussionSummarizerResource(ConfigurableResource):
    api_key: str = Field(
        default_factory=lambda: settings.openai_api_key,
        description="OpenAI/OpenRouter API key",
    )
    base_url: str = Field(
        default_factory=lambda: settings.openai_base_url,
        description="API base URL",
    )
    model: str = Field(
        default_factory=lambda: settings.openai_model,
        description="Model to use for summarization",
    )

    @cached_property
    def _openai_client(self):
        return get_cached_openai_client()

    async def analyze_discussion(self, discussion: UnifiedDiscussion, semantic_summary: str):
        summarizer = DiscussionSummarizer(openai_client=self._openai_client, model=self.model)
        return await summarizer.analyze_discussion(discussion, semantic_summary)


discussion_summarizer_resource = DiscussionSummarizerResource()
