from typing import Protocol

from dagster_project.core.content_types.models import ExtractionResult


class BaseContentExtractor(Protocol):
    async def extract(self, url: str) -> ExtractionResult: ...

    def matches(self, url: str) -> bool: ...
