from datetime import datetime
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass


class DiscussionLink(BaseModel):
    type: Literal["hackernews", "lobsters"]
    url: str


class ExtractionResult(BaseModel):
    article_url: str
    title: str | None


class HNComment(BaseModel):
    id: int
    author: str | None = None
    text: str | None = None
    parent_id: int | None = None
    story_id: int
    points: int | None = None
    created_at: datetime
    created_at_i: int
    children: list["HNComment"] = Field(default_factory=list)


class HNStory(BaseModel):
    id: int | None = None
    story_id: int
    title: str
    url: str | None = None
    author: str
    points: int
    num_comments: int
    created_at: datetime
    created_at_i: int


class HNStoryFull(BaseModel):
    id: int
    story_id: int
    title: str
    url: str | None = None
    author: str
    points: int
    created_at: datetime
    created_at_i: int
    children: list[HNComment] = Field(default_factory=list)

    def count_total_comments(self) -> int:
        """Count all nested comments recursively."""
        from dagster_project.utils.discussion_utils import count_comments_recursive

        return count_comments_recursive(self.children)

    def get_comments(self) -> list[HNComment]:
        """Get comment list (for polymorphic access)."""
        return self.children


class HNSearchResponse(BaseModel):
    hits: list[HNStory]
    nb_hits: int = Field(alias="nbHits")
    page: int
    nb_pages: int = Field(alias="nbPages")
    hits_per_page: int = Field(alias="hitsPerPage")
    processing_time_ms: int = Field(alias="processingTimeMS")

    model_config = {"populate_by_name": True}


class DiscussionMetadata(BaseModel):
    url: str
    total_stories: int
    platforms: list[str]
    hn_story_ids: list[int] = Field(default_factory=list)
    lobsters_story_ids: list[str] = Field(default_factory=list)
    discussion_links: list[DiscussionLink] = Field(default_factory=list)
    discovered_at: datetime
    cache_ttl_hours: int = 24


def _get_discussion_story_union():
    """Lazy union type to avoid circular import."""
    from dagster_project.core.discussions.lobsters_models import LobstersStoryFull

    return HNStoryFull | LobstersStoryFull


DiscussionStory = _get_discussion_story_union()
