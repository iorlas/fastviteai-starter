import pytest

from dagster_project.core.content_types.base import BaseContentExtractor
from dagster_project.core.content_types.models import ExtractionResult
from dagster_project.core.content_types.registry import ExtractorRegistry


class MockExtractor(BaseContentExtractor):
    def __init__(self, domain: str):
        self.domain = domain

    def matches(self, url: str) -> bool:
        return self.domain in url

    async def extract(self, url: str, bronze_data: dict | None = None) -> ExtractionResult:
        return ExtractionResult(
            url=url,
            content_type="mock",
            title="Mock Title",
            content="Mock content",
            success=True,
        )


class FallbackExtractor(BaseContentExtractor):
    def matches(self, url: str) -> bool:
        return True

    async def extract(self, url: str, bronze_data: dict | None = None) -> ExtractionResult:
        return ExtractionResult(
            url=url,
            content_type="fallback",
            title="Fallback Title",
            content="Fallback content",
            success=True,
        )


def test_registry_register():
    registry = ExtractorRegistry()
    extractor = MockExtractor("example.com")

    registry.register(extractor)

    assert len(registry._extractors) == 1


def test_registry_get_extractor_matches():
    registry = ExtractorRegistry()
    youtube_extractor = MockExtractor("youtube.com")
    fallback_extractor = FallbackExtractor()

    registry.register(youtube_extractor)
    registry.register(fallback_extractor)

    result = registry.get_extractor("https://www.youtube.com/watch?v=test")
    assert result == youtube_extractor


def test_registry_get_extractor_fallback():
    registry = ExtractorRegistry()
    youtube_extractor = MockExtractor("youtube.com")
    fallback_extractor = FallbackExtractor()

    registry.register(youtube_extractor)
    registry.register(fallback_extractor)

    result = registry.get_extractor("https://example.com/article")
    assert result == fallback_extractor


def test_registry_priority_order():
    registry = ExtractorRegistry()
    first_extractor = MockExtractor("example.com")
    second_extractor = MockExtractor("example.com")

    registry.register(first_extractor)
    registry.register(second_extractor)

    result = registry.get_extractor("https://example.com/page")
    assert result == first_extractor


def test_registry_no_match_raises():
    registry = ExtractorRegistry()
    youtube_extractor = MockExtractor("youtube.com")

    registry.register(youtube_extractor)

    with pytest.raises(ValueError, match="No extractor found for URL"):
        registry.get_extractor("https://example.com/page")
