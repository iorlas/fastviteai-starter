import re

import httpx
import structlog
from bs4 import BeautifulSoup

from dagster_project.core.cache.http_cache import HTTPCache
from dagster_project.core.discussions.lobsters_models import LobstersStoryFull

logger = structlog.get_logger()


class LobstersClient:
    def __init__(self, http_cache: HTTPCache | None = None, timeout: int = 30):
        self.base_url = "https://lobste.rs"
        self.timeout = timeout
        self.http_cache = http_cache or HTTPCache()
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        await self.client.aclose()

    async def search_by_url(self, url: str) -> list[str]:
        logger.info("searching_lobsters_discussions", url=url)

        search_url = f"{self.base_url}/search?q={url}"
        html_content = self.http_cache.fetch(search_url, ttl_seconds=3600)

        soup = BeautifulSoup(html_content, "html.parser")
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

    async def fetch_story_with_comments(self, short_id: str) -> LobstersStoryFull:
        logger.info("fetching_lobsters_story_comments", short_id=short_id)

        story_url = f"{self.base_url}/s/{short_id}.json"

        cached = self.http_cache.get(story_url)
        if cached:
            data = httpx.Response(
                status_code=cached.status_code,
                content=cached.response_text.encode(),
                request=httpx.Request("GET", story_url),
            ).json()
        else:
            response = await self.client.get(story_url)
            response.raise_for_status()
            self.http_cache.set(story_url, response, ttl_seconds=86400)
            data = response.json()

        story = LobstersStoryFull(**data)

        comment_count = self._count_comments(story.comments)
        logger.info(
            "lobsters_story_fetched",
            short_id=short_id,
            comments=comment_count,
            score=story.score,
        )

        return story

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
