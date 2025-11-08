from urllib.parse import urlparse

import structlog
from bs4 import BeautifulSoup
from hishel.httpx import AsyncCacheClient

from dagster_project.core.cache.hishel_cache import get_async_cache_client
from dagster_project.core.discussions.base import DiscussionPlatformHandler
from dagster_project.core.discussions.hn_models import HNSearchResponse, HNStoryFull
from dagster_project.core.discussions.shared_models import DiscussionLink, ExtractionResult

logger = structlog.get_logger()


class HackerNewsClient(DiscussionPlatformHandler):
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
        """Search HN for discussions of URL, return discussion URLs."""
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

        return [f"https://news.ycombinator.com/item?id={s.story_id}" for s in search_response.hits]

    async def fetch_story(self, discussion_url: str, story_id: int | None = None) -> HNStoryFull:
        """Fetch full HN story with comments."""
        if story_id is None:
            story_id = self.extract_story_id(discussion_url)
        return await self.fetch_story_with_comments(story_id)

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

    def extract_story_id(self, discussion_url: str) -> int:
        """Extract story ID from HN URL."""
        return int(discussion_url.split("id=")[1].split("&")[0])

    def build_discussion_link(self, story_id: int) -> DiscussionLink:
        """Build DiscussionLink for HN story."""
        return DiscussionLink(type="hackernews", url=f"https://news.ycombinator.com/item?id={story_id}")

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
