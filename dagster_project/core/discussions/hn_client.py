from urllib.parse import urlparse

import structlog
from hishel.httpx import AsyncCacheClient

from dagster_project.core.cache.hishel_cache import get_async_cache_client
from dagster_project.core.discussions.models import (
    HNSearchResponse,
    HNStory,
    HNStoryFull,
)

logger = structlog.get_logger()


class HNClient:
    def __init__(self, timeout: int = 30, cache_client: AsyncCacheClient | None = None):
        self.algolia_base = "https://hn.algolia.com/api/v1"
        self.timeout = timeout
        self.client = cache_client or get_async_cache_client(timeout=timeout)

    async def close(self):
        await self.client.aclose()

    async def search_by_url(self, url: str) -> list[HNStory]:
        domain = urlparse(url).netloc or url

        logger.info("searching_hn_discussions", url=url, domain=domain)

        response = await self.client.get(
            f"{self.algolia_base}/search",
            params={
                "query": url,
                "tags": "story",
                "restrictSearchableAttributes": "url",
                "hitsPerPage": 100,
            },
        )
        response.raise_for_status()

        data = response.json()
        search_response = HNSearchResponse(**data)

        logger.info(
            "hn_search_complete",
            url=url,
            stories_found=len(search_response.hits),
            total_hits=search_response.nb_hits,
        )

        return search_response.hits

    async def fetch_story_with_comments(self, story_id: int) -> HNStoryFull:
        logger.info("fetching_hn_story_comments", story_id=story_id)

        response = await self.client.get(f"{self.algolia_base}/items/{story_id}")
        response.raise_for_status()

        data = response.json()
        story = HNStoryFull(**data)

        comment_count = self._count_comments(story.children)
        logger.info(
            "hn_story_fetched",
            story_id=story_id,
            comments=comment_count,
            points=story.points,
        )

        return story

    def _count_comments(self, comments: list) -> int:
        count = len(comments)
        for comment in comments:
            if hasattr(comment, "children") and comment.children:
                count += self._count_comments(comment.children)
        return count

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
