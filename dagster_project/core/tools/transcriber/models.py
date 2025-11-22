from datetime import UTC, datetime

from pydantic import BaseModel, Field


class TranscriptionResult(BaseModel):
    text: str | None = Field(default=None, description="LLM-optimized formatted transcript")
    segments: list[dict] | None = Field(default=None, description="Raw Whisper segment data")
    metadata: dict = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
