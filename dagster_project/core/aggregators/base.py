from abc import ABC, abstractmethod

from pydantic import BaseModel


class ExtractionResult(BaseModel):
    article_url: str
    title: str | None


class AggregatorExtractor(ABC):
    @abstractmethod
    def extract_article_url(self, aggregator_url: str) -> ExtractionResult:
        pass
