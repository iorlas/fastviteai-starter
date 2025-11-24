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
    discussion_links: list[DiscussionLink] = Field(default_factory=list)
    discovered_at: datetime
