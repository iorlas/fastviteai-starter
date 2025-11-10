from functools import cached_property

from dagster import ConfigurableResource
from pydantic import Field

from dagster_project.config import settings
from dagster_project.core.cache.cached_openai_client import get_cached_openai_client
from dagster_project.core.summary.schema import CommunityTake
from dagster_project.core.summary.synthesis.synthesizer import CommunitySynthesizer


class CommunitySynthesizerResource(ConfigurableResource):
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

    async def synthesize(self, discussion_summaries: list[CommunityTake], semantic_summary: str):
        synthesizer = CommunitySynthesizer(openai_client=self._openai_client, model=self.model)
        return await synthesizer.synthesize(discussion_summaries, semantic_summary)


community_synthesizer_resource = CommunitySynthesizerResource()
