"""HackerNews API response models.

Only contains models for search API responses. Discussion data uses UnifiedDiscussion.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class HNStory(BaseModel):
    """HN story from search API response."""

    id: int | None = None
    story_id: int
    title: str
    url: str | None = None
    author: str
    points: int
    num_comments: int
    created_at: datetime
    created_at_i: int


class HNSearchResponse(BaseModel):
    """HN Algolia search API response."""

    hits: list[HNStory]
    nb_hits: int = Field(alias="nbHits")
    page: int
    nb_pages: int = Field(alias="nbPages")
    hits_per_page: int = Field(alias="hitsPerPage")
    processing_time_ms: int = Field(alias="processingTimeMS")

    model_config = {"populate_by_name": True}
