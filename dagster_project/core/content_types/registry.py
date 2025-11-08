import structlog

from dagster_project.core.content_types.base import BaseContentExtractor

logger = structlog.get_logger()


class ExtractorRegistry:
    def __init__(self):
        self._extractors: list[BaseContentExtractor] = []

    def register(self, extractor: BaseContentExtractor) -> None:
        self._extractors.append(extractor)
        logger.debug(
            "registry.extractor_registered",
            extractor_class=extractor.__class__.__name__,
            total_extractors=len(self._extractors),
        )

    def get_extractor(self, url: str) -> BaseContentExtractor:
        for extractor in self._extractors:
            if extractor.matches(url):
                logger.debug(
                    "registry.extractor_found",
                    url=url,
                    extractor_class=extractor.__class__.__name__,
                )
                return extractor

        raise ValueError(f"No extractor found for URL: {url}")


_global_registry = ExtractorRegistry()


def get_registry() -> ExtractorRegistry:
    return _global_registry
