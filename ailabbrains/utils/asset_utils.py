import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class Stats(BaseModel):
    total: int = Field(default=0, description="Total items to process")
    processed: int = Field(default=0, description="Successfully processed items")
    cached: int = Field(default=0, description="Items found in cache")
    skipped: int = Field(default=0, description="Items skipped (e.g., 0-comment discussions)")
    failed: int = Field(default=0, description="Failed items")

    def log_and_return(self, message: str) -> dict:
        logger.info(message, **self.model_dump())
        return self.model_dump()
