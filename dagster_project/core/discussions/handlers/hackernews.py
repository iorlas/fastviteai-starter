from dagster_project.core.discussions.hn_client import HNClient
from dagster_project.core.discussions.models import DiscussionLink, HNStoryFull


class HNHandler:
    """HackerNews discussion handler - returns data, no I/O."""

    def __init__(self, client: HNClient):
        self.client = client

    async def search_by_url(self, url: str) -> list[str]:
        """Search HN for discussions of URL, return discussion URLs."""
        stories = await self.client.search_by_url(url)
        return [f"https://news.ycombinator.com/item?id={s.story_id}" for s in stories]

    async def fetch_story(self, discussion_url: str, story_id: int | None = None) -> HNStoryFull:
        """Fetch full HN story with comments."""
        if story_id is None:
            story_id = self.extract_story_id(discussion_url)
        return await self.client.fetch_story_with_comments(story_id)

    def extract_story_id(self, discussion_url: str) -> int:
        """Extract story ID from HN URL."""
        return int(discussion_url.split("id=")[1].split("&")[0])

    def build_discussion_link(self, story_id: int) -> DiscussionLink:
        """Build DiscussionLink for HN story."""
        return DiscussionLink(type="hackernews", url=f"https://news.ycombinator.com/item?id={story_id}")
