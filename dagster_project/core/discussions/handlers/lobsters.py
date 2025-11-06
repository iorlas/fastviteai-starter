from dagster_project.core.discussions.lobsters_client import LobstersClient
from dagster_project.core.discussions.lobsters_models import LobstersStoryFull
from dagster_project.core.discussions.models import DiscussionLink


class LobstersHandler:
    """Lobsters discussion handler - returns data, no I/O."""

    def __init__(self, client: LobstersClient):
        self.client = client

    async def search_by_url(self, url: str) -> list[str]:
        """Search Lobsters for discussions of URL, return discussion URLs."""
        return await self.client.search_by_url(url)

    async def fetch_story(self, discussion_url: str, story_id: str | None = None) -> LobstersStoryFull:
        """Fetch full Lobsters story with comments."""
        if story_id is None:
            story_id = self.extract_story_id(discussion_url)
        return await self.client.fetch_story_with_comments(story_id)

    def extract_story_id(self, discussion_url: str) -> str:
        """Extract short_id from Lobsters URL."""
        short_id = LobstersClient.extract_short_id_from_url(discussion_url)
        if not short_id:
            msg = f"Could not extract story ID from {discussion_url}"
            raise ValueError(msg)
        return short_id

    def build_discussion_link(self, story_id: str) -> DiscussionLink:
        """Build DiscussionLink for Lobsters story."""
        return DiscussionLink(type="lobsters", url=f"https://lobste.rs/s/{story_id}")
