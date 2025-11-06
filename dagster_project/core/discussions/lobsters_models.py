from datetime import datetime

from pydantic import BaseModel, Field


class LobstersComment(BaseModel):
    short_id: str
    comment: str
    comment_plain: str
    score: int
    created_at: datetime
    commenting_user: str | None = None
    parent_comment: str | None = None
    depth: int = 0
    is_deleted: bool = False
    is_moderated: bool = False
    children: list["LobstersComment"] = Field(default_factory=list)


class LobstersStory(BaseModel):
    short_id: str
    title: str
    url: str | None = None
    score: int
    comment_count: int
    created_at: datetime
    submitter_user: str
    user_is_author: bool = False
    tags: list[str] = Field(default_factory=list)
    description: str | None = None
    description_plain: str | None = None
    short_id_url: str
    comments_url: str


class LobstersStoryFull(BaseModel):
    short_id: str
    title: str
    url: str | None = None
    score: int
    created_at: datetime
    submitter_user: str
    user_is_author: bool = False
    tags: list[str] = Field(default_factory=list)
    description: str | None = None
    description_plain: str | None = None
    short_id_url: str
    comments_url: str
    comments: list[LobstersComment] = Field(default_factory=list)

    def count_total_comments(self) -> int:
        """Count all nested comments recursively."""
        from dagster_project.utils.discussion_utils import count_comments_recursive

        return count_comments_recursive(self.comments)

    def get_comments(self) -> list[LobstersComment]:
        """Get comment list (for polymorphic access)."""
        return self.comments
