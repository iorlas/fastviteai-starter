from datetime import UTC, datetime

import httpx
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class DownloadResult(BaseModel):
    url: str
    html_content: str
    status_code: int | None
    headers: dict[str, str]
    final_url: str
    download_timestamp: str
    success: bool
    error: str | None = None
    error_type: str | None = None


class HTTPDownloader:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def download(self, url: str) -> DownloadResult:
        logger.info("download.started", url=url)

        try:
            response = httpx.get(url, timeout=self.timeout, follow_redirects=True)
            response.raise_for_status()

            result = DownloadResult(
                url=url,
                html_content=response.text,
                status_code=response.status_code,
                headers=dict(response.headers),
                final_url=str(response.url),
                download_timestamp=datetime.now(UTC).isoformat(),
                success=True,
            )

            logger.info(
                "download.success",
                url=url,
                status_code=response.status_code,
                content_length=len(response.text),
            )

            return result

        except httpx.HTTPError as e:
            logger.warning(
                "download.http_error",
                url=url,
                error=str(e),
                error_type=type(e).__name__,
            )

            return DownloadResult(
                url=url,
                html_content="",
                status_code=getattr(e.response, "status_code", None) if hasattr(e, "response") else None,
                headers={},
                final_url=url,
                download_timestamp=datetime.now(UTC).isoformat(),
                success=False,
                error=str(e),
                error_type=type(e).__name__,
            )

        except Exception as e:
            logger.error(
                "download.unexpected_error",
                url=url,
                error=str(e),
                error_type=type(e).__name__,
            )

            return DownloadResult(
                url=url,
                html_content="",
                status_code=None,
                headers={},
                final_url=url,
                download_timestamp=datetime.now(UTC).isoformat(),
                success=False,
                error=str(e),
                error_type=type(e).__name__,
            )
