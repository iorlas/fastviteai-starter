from typing import Protocol

from ailabbrains.core.content_types.models import ExtractionResult


class BaseContentExtractor(Protocol):
    async def extract(self, url: str) -> ExtractionResult: ...

    def matches(self, url: str) -> bool: ...
