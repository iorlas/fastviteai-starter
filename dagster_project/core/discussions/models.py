from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DiscussionLink(BaseModel):
    type: Literal["hackernews", "lobsters"]
    url: str


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
    url_hash: str
    total_stories: int
    platforms: list[str]
    hn_story_ids: list[int] = Field(default_factory=list)
    lobsters_story_ids: list[str] = Field(default_factory=list)
    discussion_links: list[DiscussionLink] = Field(default_factory=list)
    discovered_at: datetime
    cache_ttl_hours: int = 24
