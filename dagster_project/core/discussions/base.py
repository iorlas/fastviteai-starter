from abc import ABC, abstractmethod

from dagster_project.core.discussions.models import DiscussionLink, ExtractionResult


class DiscussionPlatformHandler(ABC):
    """Abstract base class for platform-specific discussion handling.

    Handlers return data only - no file I/O. Asset handles orchestration and persistence.
    """

    @abstractmethod
    async def extract_article_url(self, aggregator_url: str) -> ExtractionResult:
        """Extract the linked article URL from aggregator discussion page."""
        ...

    @abstractmethod
    async def search_by_url(self, url: str) -> list[str]:
        """Search for discussions of URL, return discussion URLs."""
        ...

    @abstractmethod
    async def fetch_story(self, discussion_url: str, story_id: str | int | None = None):
        """Fetch full story with comments. Returns HNStoryFull or LobstersStoryFull."""
        ...

    @abstractmethod
    def extract_story_id(self, discussion_url: str) -> str | int:
        """Extract story ID from discussion URL."""
        ...

    @abstractmethod
    def build_discussion_link(self, story_id: str | int) -> DiscussionLink:
        """Build DiscussionLink from story ID."""
        ...
