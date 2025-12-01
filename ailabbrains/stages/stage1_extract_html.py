"""Stage 1.1: Extract HTML content from URLs."""

import structlog

from ailabbrains.core.content_types.generic_html import GenericHTMLExtractor
from ailabbrains.stages.stage0_classify_urls import URLMetadata
from ailabbrains.storage import BronzeTable, exists, load, save
from ailabbrains.utils.paths import get_bronze_path
from ailabbrains.utils.progress_utils import progress

logger = structlog.get_logger()


async def extract_html() -> None:
    """Auto-discover and extract HTML content from URLs."""
    base_dir = get_bronze_path()
    html_metadata_dir = base_dir / BronzeTable.URL_METADATA_HTML

    if not html_metadata_dir.exists():
        return

    urls_needing_extraction = [
        load(base_dir, BronzeTable.URL_METADATA_HTML, metadata_file.stem, model=URLMetadata)
        for metadata_file in html_metadata_dir.glob("*.json")
        if not exists(base_dir, BronzeTable.HTML, metadata_file.stem)
    ]

    # Process with progress bar
    for url_info in progress(urls_needing_extraction, "HTML Extraction..."):
        extractor = GenericHTMLExtractor()
        result = await extractor.extract(url_info.url)

        bronze_data = {**result.model_dump(), "url_hash": url_info.url_hash}
        save(base_dir, BronzeTable.HTML, url_info.url_hash, bronze_data)
