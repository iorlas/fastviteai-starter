"""Main pipeline orchestrator - coordinates URL discovery, bronze extraction, and silver summarization."""

import asyncio

from ailabbrains.config import settings
from ailabbrains.stages.stage0_classify_urls import classify_urls
from ailabbrains.stages.stage0_discovery import discover_manual
from ailabbrains.stages.stage1_download_youtube import download_youtube
from ailabbrains.stages.stage1_extract_html import extract_html
from ailabbrains.stages.stage1_fetch_discussions import fetch_discussions
from ailabbrains.stages.stage1_transcribe_youtube import transcribe_youtube
from ailabbrains.stages.stage2_article_summaries import generate_article_summaries
from ailabbrains.stages.stage2_discussion_summaries import generate_discussion_summaries
from ailabbrains.stages.stage2_final_synthesis import synthesize_final_summaries


def process_urls() -> None:
    """Main pipeline orchestration (sync wrapper)."""
    asyncio.run(_async_process_urls())


async def _async_process_urls() -> None:
    """Main pipeline: Discovery → Classification → Bronze → Silver (auto-discovery pattern)."""
    await discover_manual()
    await classify_urls()

    await extract_html()
    await download_youtube()
    await transcribe_youtube()
    await fetch_discussions()

    if settings.enable_summarization:
        await generate_article_summaries()
        await generate_discussion_summaries()
        await synthesize_final_summaries()
