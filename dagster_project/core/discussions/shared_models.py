from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DiscussionLink(BaseModel):
    type: Literal["hackernews", "lobsters"]
    url: str


class ExtractionResult(BaseModel):
    article_url: str
    title: str | None


class DiscussionMetadata(BaseModel):
    url: str
    total_stories: int
    platforms: list[str]
    hn_story_ids: list[int] = Field(default_factory=list)
    lobsters_story_ids: list[str] = Field(default_factory=list)
    discussion_links: list[DiscussionLink] = Field(default_factory=list)
    discovered_at: datetime
    cache_ttl_hours: int = 24
