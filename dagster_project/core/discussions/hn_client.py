from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urlparse

import structlog
from bs4 import BeautifulSoup
from hishel.httpx import AsyncCacheClient

from dagster_project.core.cache.hishel_cache import get_async_cache_client
from dagster_project.core.discussions.hn_models import HNSearchResponse
from dagster_project.core.discussions.shared_models import DiscussionLink, ExtractionResult
from dagster_project.core.discussions.unified_models import UnifiedDiscussion
from dagster_project.utils.url_utils import normalize_url

logger = structlog.get_logger()


class HackerNewsClient:
    @classmethod
    def platform_name(cls) -> Literal["hackernews"]:
        return "hackernews"

    @classmethod
    def can_handle(cls, url: str) -> bool:
        parsed = urlparse(url)
        return "news.ycombinator.com" in parsed.netloc and "/item" in parsed.path

    def __init__(self, timeout: int = 30, cache_client: AsyncCacheClient | None = None):
        self.algolia_base = "https://hn.algolia.com/api/v1"
        self.timeout = timeout
        self.client = cache_client or get_async_cache_client(timeout=timeout)

    async def extract_article_url(self, hn_url: str) -> ExtractionResult:
        logger.info("hn_extraction_start", url=hn_url)

        try:
            response = await self.client.get(hn_url)
            response.raise_for_status()
            html_content = response.text

            soup = BeautifulSoup(html_content, "html.parser")

            titleline = soup.find("span", class_="titleline")
            if not titleline:
                raise ValueError("Could not find titleline element in HN page")

            link = titleline.find("a")
            if not link or not link.get("href"):
                raise ValueError("Could not find article link in titleline")

            article_url = link["href"]
            title = link.get_text(strip=True)

            if article_url.startswith("item?"):
                logger.info("hn_self_post_detected", hn_url=hn_url, title=title, type="self_post")
                return ExtractionResult(article_url=hn_url, title=title)

            logger.info(
                "hn_extraction_success",
                hn_url=hn_url,
                article_url=article_url,
                title=title,
            )

            return ExtractionResult(article_url=article_url, title=title)

        except Exception as e:
            logger.error("hn_extraction_failed", url=hn_url, error=str(e))
            raise

    async def close(self):
        await self.client.aclose()

    async def search_by_url(self, url: str) -> list[str]:
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

        # Filter for exact URL matches using normalized comparison
        normalized_search_url = normalize_url(url)
        exact_matches = [s for s in search_response.hits if s.url and normalize_url(s.url) == normalized_search_url]

        logger.info(
            "hn_search_complete",
            url=url,
            total_hits=len(search_response.hits),
            exact_matches=len(exact_matches),
            filtered_out=len(search_response.hits) - len(exact_matches),
        )

        return [f"https://news.ycombinator.com/item?id={s.story_id}" for s in exact_matches]

    async def fetch_story(self, discussion_url: str, story_id: int | None = None) -> UnifiedDiscussion:
        if story_id is None:
            story_id = self.extract_story_id(discussion_url)
        return await self.fetch_story_with_comments(story_id, discussion_url)

    async def fetch_story_with_comments(self, story_id: int, discussion_url: str | None = None) -> UnifiedDiscussion:
        logger.info("fetching_hn_story_comments", story_id=story_id)

        response = await self.client.get(f"{self.algolia_base}/items/{story_id}")
        response.raise_for_status()

        data = response.json()

        # Manual validation of required fields
        required_fields = ["id", "author", "title", "points"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise ValueError(f"Invalid HN API response for story {story_id}: missing fields {missing_fields}")

        # Build unified discussion structure (raw data with int IDs)
        comments = data.get("children", [])

        if discussion_url is None:
            discussion_url = f"https://news.ycombinator.com/item?id={story_id}"

        # Let Pydantic BaseModel handle type coercion (int→str for IDs) and auto-calculate comment_count
        story = UnifiedDiscussion(
            platform="hackernews",
            id=data.get("story_id", data["id"]),  # Auto-coerces int → str
            discussion_url=discussion_url,
            article_url=data.get("url"),
            title=data["title"],
            author=data["author"],
            points=data["points"],
            created_at=data.get("created_at", ""),
            fetched_at=datetime.now(UTC).isoformat(),
            comments=comments,  # Pydantic handles nested coercion + auto-calculates comment_count
        )

        logger.info(
            "hn_story_fetched",
            story_id=story_id,
            comments=story.comment_count,
            points=story.points,
        )

        return story

    def extract_story_id(self, discussion_url: str) -> int:
        return int(discussion_url.split("id=")[1].split("&")[0])

    def build_discussion_link(self, story_id: int) -> DiscussionLink:
        return DiscussionLink(type="hackernews", url=f"https://news.ycombinator.com/item?id={story_id}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
