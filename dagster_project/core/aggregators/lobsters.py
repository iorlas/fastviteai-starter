import structlog

from dagster_project.core.aggregators.base import AggregatorExtractor, ExtractionResult
from dagster_project.core.cache.hishel_cache import AsyncCacheClient, get_async_cache_client

logger = structlog.get_logger()


class LobstersExtractor(AggregatorExtractor):
    def __init__(self, cache_client: AsyncCacheClient | None = None):
        self.cache_client = cache_client or get_async_cache_client(ttl=86400)

    async def extract_article_url(self, lobsters_url: str) -> ExtractionResult:
        logger.info("lobsters_extraction_start", url=lobsters_url)

        try:
            json_url = lobsters_url.rstrip("/") + ".json"
            response = await self.cache_client.get(json_url)
            response.raise_for_status()

            data = response.json()

            article_url = data.get("url")
            title = data.get("title")

            if not article_url:
                logger.info("lobsters_self_post_detected", lobsters_url=lobsters_url, title=title, type="self_post")
                return ExtractionResult(article_url=lobsters_url, title=title)

            logger.info(
                "lobsters_extraction_success",
                lobsters_url=lobsters_url,
                article_url=article_url,
                title=title,
            )

            return ExtractionResult(article_url=article_url, title=title)

        except Exception as e:
            logger.error("lobsters_extraction_failed", url=lobsters_url, error=str(e))
            raise
