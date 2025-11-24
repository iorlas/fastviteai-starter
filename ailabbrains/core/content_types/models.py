from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ExtractionResult(BaseModel):
    url: str
    content_type: str
    title: str
    content: str
    metadata: dict = Field(default_factory=dict)
    content_metadata: dict = Field(default_factory=dict)
    success: bool
    error: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    url_hash: str | None = None
