from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field, model_validator


def coerce_to_str(v: Any) -> str:
    return str(v) if v is not None else ""


# Use Annotated with BeforeValidator for automatic int→str coercion
StrId = Annotated[str, BeforeValidator(coerce_to_str)]


class UnifiedComment(BaseModel):
    id: StrId  # Auto-coerces int → str
    author: str | None = None
    text: str | None = None
    points: int | None = None
    created_at: str
    children: list["UnifiedComment"] = Field(default_factory=list)

    model_config = {"extra": "allow"}  # Allow extra fields from APIs


class UnifiedDiscussion(BaseModel):
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
        if isinstance(data, dict) and "comments" in data:
            data["comment_count"] = cls._count_comments(data["comments"])
        return data

    @staticmethod
    def _count_comments(comments: list) -> int:
        count = len(comments)
        for comment in comments:
            if isinstance(comment, dict) and comment.get("children"):
                count += UnifiedDiscussion._count_comments(comment["children"])
        return count
