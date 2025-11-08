from functools import cached_property

from dagster import ConfigurableResource
from pydantic import Field

from dagster_project.config import settings
from dagster_project.core.summary import SummaryGenerator


class SummaryGeneratorResource(ConfigurableResource):
    api_key: str = Field(
        default_factory=lambda: settings.openai_api_key,
        description="OpenAI/OpenRouter API key",
    )
    base_url: str = Field(
        default_factory=lambda: settings.openai_base_url,
        description="API base URL",
    )

    @cached_property
    def _openai_client(self):
        from openai import OpenAI

        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            max_retries=3,
            timeout=30.0,
        )

    @cached_property
    def generator(self) -> SummaryGenerator:
        return SummaryGenerator(openai_client=self._openai_client)


summary_generator_resource = SummaryGeneratorResource()
