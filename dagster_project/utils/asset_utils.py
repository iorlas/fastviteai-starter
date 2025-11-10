from dagster import AssetExecutionContext
from pydantic import BaseModel, Field


class Stats(BaseModel):
    total: int = Field(default=0, description="Total items to process")
    processed: int = Field(default=0, description="Successfully processed items")
    cached: int = Field(default=0, description="Items found in cache")
    skipped: int = Field(default=0, description="Items skipped (e.g., 0-comment discussions)")
    failed: int = Field(default=0, description="Failed items")

    def log_and_return(self, context: AssetExecutionContext, message: str) -> dict:
        context.log.info(message)
        stats_dict = self.model_dump()
        context.add_output_metadata(stats_dict)
        return stats_dict
