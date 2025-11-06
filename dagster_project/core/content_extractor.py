from urllib.parse import urlparse

import structlog
from pydantic import BaseModel

from dagster_project.core.extractors.html_extractor import (
    HTMLExtractionError,
    extract_html_content,
)
from dagster_project.core.extractors.youtube_extractor import (
    YouTubeExtractionError,
    extract_youtube_content,
)

logger = structlog.get_logger()


class ExtractionRequest(BaseModel):
    url: str
    html_content: str | None = None


class ExtractionResult(BaseModel):
    url: str
    content_type: str
    title: str
    content: str
    metadata: dict
    success: bool
    error: str | None = None


class ContentExtractor:
    @staticmethod
    def is_youtube_url(url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc in [
            "youtube.com",
            "www.youtube.com",
            "youtu.be",
            "m.youtube.com",
        ]

    async def extract(self, request: ExtractionRequest) -> ExtractionResult:
        logger.info("extract.started", url=request.url)

        try:
            if self.is_youtube_url(request.url):
                return self._extract_youtube(request.url)
            else:
                return await self._extract_html(request.url, request.html_content)

        except (HTMLExtractionError, YouTubeExtractionError) as e:
            logger.warning(
                "extract.failed",
                url=request.url,
                error=str(e),
                error_type=type(e).__name__,
            )

            content_type = "youtube" if self.is_youtube_url(request.url) else "html"

            return ExtractionResult(
                url=request.url,
                content_type=content_type,
                title="Extraction Failed",
                content="",
                metadata={},
                success=False,
                error=str(e),
            )

    def _extract_youtube(self, url: str) -> ExtractionResult:
        yt_content = extract_youtube_content(url)

        logger.info("extract.youtube_success", url=url, title=yt_content.title)

        return ExtractionResult(
            url=url,
            content_type="youtube",
            title=yt_content.title,
            content=yt_content.transcript,
            metadata={
                "channel": yt_content.channel,
                "duration": yt_content.duration,
                "description": yt_content.description,
                **yt_content.metadata,
            },
            success=True,
        )

    async def _extract_html(self, url: str, html_content: str | None = None) -> ExtractionResult:
        html_result = await extract_html_content(url, html_content=html_content)

        logger.info("extract.html_success", url=url, title=html_result.title)

        return ExtractionResult(
            url=url,
            content_type="html",
            title=html_result.title,
            content=html_result.content,
            metadata={
                "author": html_result.author,
                "publish_date": html_result.publish_date,
                **html_result.metadata,
            },
            success=True,
        )
