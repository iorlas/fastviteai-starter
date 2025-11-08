from dagster_project.core.content_types.base import BaseContentExtractor
from dagster_project.core.content_types.generic_html import GenericHTMLExtractor
from dagster_project.core.content_types.models import ExtractionResult
from dagster_project.core.content_types.registry import get_registry
from dagster_project.core.content_types.youtube import YouTubeExtractor

_registry = get_registry()
_registry.register(YouTubeExtractor())
_registry.register(GenericHTMLExtractor())

__all__ = [
    "BaseContentExtractor",
    "ExtractionResult",
    "get_registry",
    "YouTubeExtractor",
    "GenericHTMLExtractor",
]
