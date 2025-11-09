"""Unified discussion models - platform-agnostic discussion representation."""

from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field, model_validator


def coerce_to_str(v: Any) -> str:
    """Coerce any value to string (handles int IDs from APIs)."""
    return str(v) if v is not None else ""


# Use Annotated with BeforeValidator for automatic int→str coercion
StrId = Annotated[str, BeforeValidator(coerce_to_str)]


class UnifiedComment(BaseModel):
    """Platform-agnostic comment representation.

    Using BaseModel instead of TypedDict for proper validation and type coercion.
    """

    id: StrId  # Auto-coerces int → str
    author: str | None = None
    text: str | None = None
    points: int | None = None
    created_at: str
    children: list["UnifiedComment"] = Field(default_factory=list)

    model_config = {"extra": "allow"}  # Allow extra fields from APIs


class UnifiedDiscussion(BaseModel):
    """Platform-agnostic discussion thread.

    All discussion clients return this unified format, abstracting away
    platform-specific field names and structures.
    """

    platform: str  # "hackernews" | "lobsters"
    id: StrId  # Auto-coerces int → str
    discussion_url: str  # URL to the discussion page
    article_url: str | None = None  # URL to the linked article (None for self-posts)
    title: str
    author: str  # Normalized: HN "author" / Lobsters "submitter_user"
    points: int  # Normalized: HN "points" / Lobsters "score"
    comment_count: int = 0  # Auto-calculated from comments if not provided
    created_at: str
    fetched_at: str
    comments: list[UnifiedComment] = Field(default_factory=list)  # Normalized: HN "children" / Lobsters "comments"

    model_config = {"extra": "allow"}  # Allow extra fields from APIs

    @model_validator(mode="before")
    @classmethod
    def calculate_comment_count(cls, data: Any) -> Any:
        """Auto-calculate comment_count from comments if not provided."""
        if isinstance(data, dict) and "comments" in data:
            data["comment_count"] = cls._count_comments(data["comments"])
        return data

    @staticmethod
    def _count_comments(comments: list) -> int:
        """Recursively count all comments including nested children."""
        count = len(comments)
        for comment in comments:
            if isinstance(comment, dict) and comment.get("children"):
                count += UnifiedDiscussion._count_comments(comment["children"])
        return count
