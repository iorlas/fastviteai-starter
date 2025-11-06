import structlog
from pydantic import BaseModel, Field

from dagster_project.core.aggregators.detector import is_aggregator_url
from dagster_project.core.aggregators.hackernews import HackerNewsExtractor
from dagster_project.core.aggregators.lobsters import LobstersExtractor
from dagster_project.core.cache.hishel_cache import AsyncCacheClient, get_async_cache_client
from dagster_project.core.discussions.models import DiscussionLink

logger = structlog.get_logger()


class URLResolutionResult(BaseModel):
    resolved_url: str
    original_url: str
    was_aggregator: bool
    aggregator_type: str | None
    title: str | None = None
    discussion_links: list[DiscussionLink] = Field(default_factory=list)


class AggregatorResolver:
    def __init__(self, cache_client: AsyncCacheClient | None = None):
        self.cache_client = cache_client or get_async_cache_client()
        self.hn_extractor = HackerNewsExtractor(cache_client=self.cache_client)
        self.lobsters_extractor = LobstersExtractor(cache_client=self.cache_client)

    async def resolve_url(self, url: str) -> URLResolutionResult:
        is_agg, agg_type = is_aggregator_url(url)

        if not is_agg:
            return URLResolutionResult(
                resolved_url=url,
                original_url=url,
                was_aggregator=False,
                aggregator_type=None,
            )

        logger.info("aggregator.detected", url=url, aggregator_type=agg_type)

        if agg_type == "hackernews":
            result = await self.hn_extractor.extract_article_url(url)

            logger.info(
                "aggregator.resolved",
                original_url=url,
                resolved_url=result.article_url,
                aggregator_type=agg_type,
                title=result.title,
            )

            discussion_link = DiscussionLink(type="hackernews", url=url)

            return URLResolutionResult(
                resolved_url=result.article_url,
                original_url=url,
                was_aggregator=True,
                aggregator_type=agg_type,
                title=result.title,
                discussion_links=[discussion_link],
            )

        if agg_type == "lobsters":
            result = await self.lobsters_extractor.extract_article_url(url)

            logger.info(
                "aggregator.resolved",
                original_url=url,
                resolved_url=result.article_url,
                aggregator_type=agg_type,
                title=result.title,
            )

            discussion_link = DiscussionLink(type="lobsters", url=url)

            return URLResolutionResult(
                resolved_url=result.article_url,
                original_url=url,
                was_aggregator=True,
                aggregator_type=agg_type,
                title=result.title,
                discussion_links=[discussion_link],
            )

        raise ValueError(f"Unsupported aggregator type: {agg_type}")


async def resolve_url(url: str) -> URLResolutionResult:
    resolver = AggregatorResolver()
    return await resolver.resolve_url(url)
