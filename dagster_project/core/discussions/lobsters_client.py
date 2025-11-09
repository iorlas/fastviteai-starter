import re
from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urlparse

import structlog
from bs4 import BeautifulSoup

from dagster_project.core.cache.hishel_cache import AsyncCacheClient, get_async_cache_client
from dagster_project.core.discussions.shared_models import DiscussionLink, ExtractionResult
from dagster_project.core.discussions.unified_models import UnifiedDiscussion

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

    async def fetch_story(self, discussion_url: str, story_id: str | None = None) -> UnifiedDiscussion:
        if story_id is None:
            story_id = self.extract_story_id(discussion_url)
        return await self.fetch_story_with_comments(story_id, discussion_url)

    async def fetch_story_with_comments(self, short_id: str, discussion_url: str | None = None) -> UnifiedDiscussion:
        logger.info("fetching_lobsters_story_comments", short_id=short_id)

        story_url = f"{self.base_url}/s/{short_id}.json"

        response = await self.client.get(story_url)
        response.raise_for_status()
        data = response.json()

        # Manual validation of required fields
        required_fields = ["short_id", "submitter_user", "title", "score"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise ValueError(f"Invalid Lobsters API response for story {short_id}: missing fields {missing_fields}")

        # Build unified discussion structure (map Lobsters fields to unified names)
        raw_comments = data.get("comments", [])
        normalized_comments = self._normalize_comments(raw_comments)

        if discussion_url is None:
            discussion_url = f"https://lobste.rs/s/{short_id}"

        # Let Pydantic BaseModel handle type coercion and auto-calculate comment_count
        story = UnifiedDiscussion(
            platform="lobsters",
            id=data["short_id"],
            discussion_url=discussion_url,
            article_url=data.get("url"),
            title=data["title"],
            author=data["submitter_user"],  # Map to unified field name
            points=data["score"],  # Map to unified field name
            created_at=data.get("created_at", ""),
            fetched_at=datetime.now(UTC).isoformat(),
            comments=normalized_comments,  # Normalized: short_id → id, auto-calculates comment_count
        )

        logger.info(
            "lobsters_story_fetched",
            short_id=short_id,
            comments=story.comment_count,
            points=story.points,
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

    def _normalize_comments(self, comments: list) -> list:
        """Normalize Lobsters comment structure to unified format.

        Lobsters uses 'short_id' field, UnifiedComment expects 'id'.
        """
        normalized = []
        for comment in comments:
            if not isinstance(comment, dict):
                continue

            # Copy comment and rename short_id → id
            normalized_comment = comment.copy()
            if "short_id" in normalized_comment:
                normalized_comment["id"] = normalized_comment.pop("short_id")

            # Recursively normalize children
            if "children" in normalized_comment and normalized_comment["children"]:
                normalized_comment["children"] = self._normalize_comments(normalized_comment["children"])

            normalized.append(normalized_comment)

        return normalized

    @staticmethod
    def extract_short_id_from_url(url: str) -> str | None:
        match = re.search(r"/s/([a-z0-9]+)", url)
        return match.group(1) if match else None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
