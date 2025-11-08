import structlog
import trafilatura

from dagster_project.core.cache.hishel_cache import get_async_cache_client
from dagster_project.core.content_types.models import ExtractionResult

logger = structlog.get_logger()


class HTMLExtractionError(Exception):
    pass


class GenericHTMLExtractor:
    def matches(self, url: str) -> bool:
        return True

    @staticmethod
    def _filter_metadata(metadata: dict) -> dict:
        """Filter out unnecessary HTML extraction metadata fields."""
        excluded_fields = {
            "hostname",
            "body",
            "commentsbody",
            "raw_text",
            "text",
        }
        return {k: v for k, v in metadata.items() if k not in excluded_fields}

    async def extract(self, url: str, timeout: int = 30) -> ExtractionResult:
        logger.info("html_extract.started", url=url)

        try:
            client = get_async_cache_client(timeout=timeout)
            response = await client.get(url)
            response.raise_for_status()

            metadata_obj = trafilatura.extract_metadata(response.text)
            content = trafilatura.extract(
                response.text,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
            )

            title = (metadata_obj.title if metadata_obj else None) or "Untitled"

            metadata = {
                "content_length": len(content or ""),
                "final_url": str(response.url),
            }

            logger.info("html_extract.success", url=url, title=title)

            return ExtractionResult(
                url=url,
                content_type="html",
                title=title,
                content=content or "",
                metadata=metadata,
                content_metadata=self._filter_metadata(metadata_obj.as_dict()) if metadata_obj else {},
                success=True,
            )

        except Exception as e:
            logger.warning("html_extract.failed", url=url, error=str(e))
            return ExtractionResult(
                url=url,
                content_type="html",
                title="Extraction Failed",
                content="",
                success=False,
                error=str(e),
            )
