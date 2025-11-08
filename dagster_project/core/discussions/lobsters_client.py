import re
from typing import Literal
from urllib.parse import urlparse

import structlog
from bs4 import BeautifulSoup

from dagster_project.core.cache.hishel_cache import AsyncCacheClient, get_async_cache_client
from dagster_project.core.discussions.lobsters_models import LobstersStoryFull
from dagster_project.core.discussions.shared_models import DiscussionLink, ExtractionResult

logger = structlog.get_logger()


class LobstersClient:
    @classmethod
    def platform_name(cls) -> Literal["lobsters"]:
        return "lobsters"

    @classmethod
    def can_handle(cls, url: str) -> bool:
        parsed = urlparse(url)
        return "lobste.rs" in parsed.netloc and "/s/" in parsed.path

    def __init__(
        self,
        cache_client: AsyncCacheClient | None = None,
        timeout: int = 30,
    ):
        self.base_url = "https://lobste.rs"
        self.timeout = timeout
        self.client = cache_client or get_async_cache_client(timeout=timeout, ttl=86400)

    async def close(self):
        await self.client.aclose()

    async def extract_article_url(self, lobsters_url: str) -> ExtractionResult:
        logger.info("lobsters_extraction_start", url=lobsters_url)

        try:
            json_url = lobsters_url.rstrip("/") + ".json"
            response = await self.client.get(json_url)
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

    async def search_by_url(self, url: str) -> list[str]:
        logger.info("searching_lobsters_discussions", url=url)

        search_url = f"{self.base_url}/search?q={url}"
        response = await self.client.get(search_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        discussion_urls = []

        for link in soup.select("ol.stories li.story .u-url"):
            story_url = link.get("href", "")
            if story_url and story_url.startswith("/s/"):
                full_url = f"{self.base_url}{story_url}"
                discussion_urls.append(full_url)

        logger.info(
            "lobsters_search_complete",
            url=url,
            stories_found=len(discussion_urls),
        )

        return discussion_urls

    async def fetch_story(self, discussion_url: str, story_id: str | None = None) -> LobstersStoryFull:
        if story_id is None:
            story_id = self.extract_story_id(discussion_url)
        return await self.fetch_story_with_comments(story_id)

    async def fetch_story_with_comments(self, short_id: str) -> LobstersStoryFull:
        logger.info("fetching_lobsters_story_comments", short_id=short_id)

        story_url = f"{self.base_url}/s/{short_id}.json"

        response = await self.client.get(story_url)
        response.raise_for_status()
        data = response.json()

        story = LobstersStoryFull(**data)
        story.comment_count = self._count_comments(story.comments)

        logger.info(
            "lobsters_story_fetched",
            short_id=short_id,
            comments=story.comment_count,
            score=story.score,
        )

        return story

    def extract_story_id(self, discussion_url: str) -> str:
        short_id = self.extract_short_id_from_url(discussion_url)
        if not short_id:
            msg = f"Could not extract story ID from {discussion_url}"
            raise ValueError(msg)
        return short_id

    def build_discussion_link(self, story_id: str) -> DiscussionLink:
        return DiscussionLink(type="lobsters", url=f"https://lobste.rs/s/{story_id}")

    def _count_comments(self, comments: list) -> int:
        count = len(comments)
        for comment in comments:
            if hasattr(comment, "children") and comment.children:
                count += self._count_comments(comment.children)
        return count

    @staticmethod
    def extract_short_id_from_url(url: str) -> str | None:
        match = re.search(r"/s/([a-z0-9]+)", url)
        return match.group(1) if match else None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
