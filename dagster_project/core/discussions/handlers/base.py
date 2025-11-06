from typing import Protocol

from dagster_project.core.discussions.models import DiscussionLink


class DiscussionPlatformHandler(Protocol):
    """Protocol for platform-specific discussion handling.

    Handlers return data only - no file I/O. Asset handles orchestration and persistence.
    """

    async def search_by_url(self, url: str) -> list[str]:
        """Search for discussions of URL, return discussion URLs."""
        ...

    async def fetch_story(self, discussion_url: str):
        """Fetch full story with comments. Returns HNStoryFull or LobstersStoryFull."""
        ...

    def extract_story_id(self, discussion_url: str) -> str | int:
        """Extract story ID from discussion URL."""
        ...

    def build_discussion_link(self, story_id: str | int) -> DiscussionLink:
        """Build DiscussionLink from story ID."""
        ...
