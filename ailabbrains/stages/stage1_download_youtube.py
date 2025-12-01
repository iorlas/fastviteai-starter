"""Stage 1.2: Download YouTube videos."""

import structlog

from ailabbrains.config import settings
from ailabbrains.core.content_types.youtube import YouTubeExtractor
from ailabbrains.stages.stage0_classify_urls import URLMetadata
from ailabbrains.storage import BronzeTable, exists, get_path, load, save
from ailabbrains.utils.paths import get_bronze_path
from ailabbrains.utils.progress_utils import progress

logger = structlog.get_logger()


async def download_youtube() -> None:
    """Auto-discover and download YouTube videos."""
    base_dir = get_bronze_path()
    youtube_metadata_dir = base_dir / BronzeTable.URL_METADATA_YOUTUBE

    urls_needing_download = []
    for metadata_file in youtube_metadata_dir.glob("*.json"):
        url_data = load(base_dir, BronzeTable.URL_METADATA_YOUTUBE, metadata_file.stem, model=URLMetadata)

        try:
            video_id = YouTubeExtractor.extract_video_id(url_data.url)
            if not exists(base_dir, BronzeTable.YOUTUBE_DOWNLOADS, "metadata", sub_partition=video_id):
                urls_needing_download.append(url_data)
        except Exception:
            continue  # Skip invalid video IDs

    # Process with progress bar
    extractor = YouTubeExtractor(proxy=settings.http_proxy)

    for url_info in progress(urls_needing_download, "YouTube Download..."):
        video_id = YouTubeExtractor.extract_video_id(url_info.url)
        download_dir = get_path(base_dir, BronzeTable.YOUTUBE_DOWNLOADS, "metadata", sub_partition=video_id).parent

        result = await extractor.download_video(url_info.url, download_dir)

        save(
            base_dir,
            BronzeTable.YOUTUBE_DOWNLOADS,
            "metadata",
            result,
            sub_partition=result.video_id,
        )
