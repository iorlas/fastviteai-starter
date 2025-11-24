"""Pipeline orchestrator - coordinates URL discovery, bronze extraction, and silver summarization."""

import asyncio
import json
import traceback
from datetime import UTC, datetime
from pathlib import Path

import structlog
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TaskID, TextColumn, TimeElapsedColumn
from url_normalize import url_normalize

from ailabbrains.config import settings
from ailabbrains.core.aggregator_resolver import resolve_url
from ailabbrains.core.cache.cached_openai_client import get_cached_openai_client
from ailabbrains.core.content_types.generic_html import GenericHTMLExtractor
from ailabbrains.core.content_types.youtube import YouTubeExtractor
from ailabbrains.core.discussions.discussion_fetcher import fetch_discussions_for_url
from ailabbrains.core.discussions.hn_client import HackerNewsClient
from ailabbrains.core.discussions.lobsters_client import LobstersClient
from ailabbrains.core.discussions.shared_models import DiscussionLink, DiscussionMetadata
from ailabbrains.core.discussions.unified_models import UnifiedDiscussion
from ailabbrains.core.extractors.watchers import RSSWatcher, RSSWatcherError
from ailabbrains.core.summary.article.summarizer import ArticleSummarizer
from ailabbrains.core.summary.discussion.summarizer import DiscussionSummarizer
from ailabbrains.core.summary.schema import ArticleAnalysis, CommunityTake
from ailabbrains.core.summary.synthesis.synthesizer import CommunitySynthesizer
from ailabbrains.core.tools.transcriber.transcriber import Transcriber
from ailabbrains.storage import BronzeTable, SilverTable, exists, get_path, load, save
from ailabbrains.utils.paths import MANUAL_LINKS_FILE, MONITORING_LINKS_FILE, get_article_summary_path, get_discussion_summary_dir
from ailabbrains.utils.url_utils import compute_url_hash

logger = structlog.get_logger()
console = Console()


def read_links_from_file(file_path: Path) -> list[str]:
    """Read URLs from input file, skipping comments and empty lines."""
    if not file_path.exists():
        return []

    links = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                links.append(line)

    return links


def _detect_content_type(url: str) -> str:
    """Detect content type based on URL pattern."""
    if YouTubeExtractor.matches(url):
        return "youtube"
    return "html"


async def discover_urls(source: str) -> list[dict]:
    """Discover URLs from input files with aggregator resolution and RSS expansion."""
    logger.info("Starting URL discovery", source=source)
    discovered_urls_list = []
    seen_hashes = set()

    # Determine which input file(s) to process
    if source == "manual":
        manual_links = read_links_from_file(MANUAL_LINKS_FILE)
        logger.info("Found manual links", count=len(manual_links), file=MANUAL_LINKS_FILE.name)

        for url in manual_links:
            await _process_discovered_url(url, "manual", seen_hashes, discovered_urls_list)

    elif source == "monitoring":
        monitoring_urls = read_links_from_file(MONITORING_LINKS_FILE)
        logger.info("Found monitoring URLs", count=len(monitoring_urls), file=MONITORING_LINKS_FILE.name)

        watcher = RSSWatcher()
        for feed_url in monitoring_urls:
            is_rss_feed = any(pattern in feed_url.lower() for pattern in [".xml", ".rss", "/feed", "/rss", "feeds/", "atom.xml"])

            if is_rss_feed:
                logger.info("Processing RSS feed", feed_url=feed_url)
                try:
                    discovered_links = watcher.fetch_links(feed_url)
                    logger.info("Discovered URLs from RSS feed", count=len(discovered_links), feed_url=feed_url)

                    for url in discovered_links:
                        await _process_discovered_url(url, f"rss:{feed_url}", seen_hashes, discovered_urls_list)

                except RSSWatcherError as e:
                    logger.warning("Failed to fetch RSS feed", feed_url=feed_url, error=str(e))
            else:
                await _process_discovered_url(feed_url, "monitoring_direct", seen_hashes, discovered_urls_list)

    logger.info("Discovery complete", total_urls=len(discovered_urls_list), source=source)
    return discovered_urls_list


async def _process_discovered_url(
    url: str,
    source: str,
    seen_hashes: set[str],
    discovered_list: list[dict],
) -> bool:
    """Process a single URL: resolve aggregators, normalize, deduplicate."""
    resolved_url, discussion_link = await resolve_url(url)
    normalized = url_normalize(resolved_url.strip())
    canonical_url = normalized if normalized else resolved_url.strip()
    url_hash = compute_url_hash(canonical_url)

    if url_hash in seen_hashes:
        return False

    url_data = {
        "url": canonical_url,
        "url_hash": url_hash,
        "content_type": _detect_content_type(canonical_url),
        "source": source,
        "discussion_links": [discussion_link.model_dump()] if discussion_link else [],
    }

    if discussion_link:
        aggregator_type = discussion_link.type
        aggregator_url = discussion_link.url
        logger.info(
            "Aggregator resolved",
            aggregator_type=aggregator_type,
            aggregator_url=aggregator_url,
            canonical_url=canonical_url,
            source=source,
        )
    else:
        logger.info("URL added", url=canonical_url, source=source)

    discovered_list.append(url_data)
    seen_hashes.add(url_hash)
    return True


# ==================== BRONZE LAYER ====================


async def extract_html(url_data: dict, progress: Progress, task: TaskID) -> None:
    """Extract HTML content from URL."""
    base_dir = settings.artifacts_path / "bronze"
    url = url_data["url"]
    url_hash = url_data["url_hash"]

    if exists(base_dir, BronzeTable.HTML, url_hash):
        progress.update(task, advance=1, description=f"[cyan]HTML[/cyan] [dim]cached: {url}[/dim]")
        return

    extractor = GenericHTMLExtractor()
    result = await extractor.extract(url)

    bronze_data = {**result.model_dump(), "url_hash": url_hash}
    save(base_dir, BronzeTable.HTML, url_hash, bronze_data)

    if result.success:
        content_length = len(result.content) if result.content else 0
        progress.update(task, advance=1, description=f"[green]✓ HTML[/green] {result.title} ({content_length} chars)")
    else:
        progress.update(task, advance=1, description=f"[red]✗ HTML[/red] {url} - {result.error}")


async def download_youtube(url_data: dict, progress: Progress, task: TaskID) -> None:
    """Download YouTube video and metadata."""
    base_dir = settings.artifacts_path / "bronze"
    url = url_data["url"]
    url_hash = url_data["url_hash"]

    try:
        video_id = YouTubeExtractor.extract_video_id(url)
    except Exception as e:
        progress.update(task, advance=1, description=f"[red]✗ YouTube[/red] {url} - {e}")
        return

    if exists(base_dir, BronzeTable.YOUTUBE_DOWNLOADS, "metadata", sub_partition=video_id):
        progress.update(task, advance=1, description=f"[cyan]YouTube[/cyan] [dim]cached: {url}[/dim]")
        return

    extractor = YouTubeExtractor(proxy=settings.http_proxy)
    download_dir = get_path(base_dir, BronzeTable.YOUTUBE_DOWNLOADS, "metadata", sub_partition=video_id).parent

    try:
        result = await extractor.download_video(url, download_dir)

        save(
            base_dir,
            BronzeTable.YOUTUBE_DOWNLOADS,
            "metadata",
            result.model_dump(),
            sub_partition=result.video_id if result.video_id else url_hash,
        )

        if result.success:
            progress.update(task, advance=1, description=f"[green]✓ YouTube[/green] {result.title}")
        else:
            progress.update(task, advance=1, description=f"[red]✗ YouTube[/red] {url} - {result.error}")
    except Exception:
        progress.update(task, advance=1, description=f"[red]✗ YouTube[/red] {url} - Exception")
        logger.error("YouTube download exception", url=url, traceback=traceback.format_exc())


async def transcribe_youtube(url_data: dict, progress: Progress, task: TaskID) -> None:
    """Transcribe YouTube video audio."""
    base_dir = settings.artifacts_path / "bronze"
    url = url_data["url"]

    try:
        video_id = YouTubeExtractor.extract_video_id(url)
    except Exception:
        progress.update(task, advance=1, description=f"[yellow]⊘ Transcription[/yellow] {url} - Invalid video ID")
        return

    # Check if metadata exists
    if not exists(base_dir, BronzeTable.YOUTUBE_DOWNLOADS, "metadata", sub_partition=video_id):
        progress.update(task, advance=1, description=f"[yellow]⊘ Transcription[/yellow] {url} - No download metadata")
        return

    # Check transcription cache
    if exists(base_dir, BronzeTable.YOUTUBE_DOWNLOADS, "transcription", sub_partition=video_id):
        progress.update(task, advance=1, description=f"[cyan]Transcription[/cyan] [dim]cached: {url}[/dim]")
        return

    # Construct audio file path from directory structure
    audio_file = base_dir / BronzeTable.YOUTUBE_DOWNLOADS / video_id / "video.m4a"

    if not audio_file.exists():
        progress.update(task, advance=1, description=f"[yellow]⊘ Transcription[/yellow] {url} - Audio file missing")
        return

    transcriber = Transcriber(
        model=settings.whisper_model,
        device=settings.whisper_device,
        model_cache_dir=settings.whisper_cache_dir,
    )

    try:
        result = await transcriber.transcribe(audio_file)

        save(
            base_dir,
            BronzeTable.YOUTUBE_DOWNLOADS,
            "transcription",
            result.model_dump(),
            sub_partition=video_id,
        )

        progress.update(task, advance=1, description=f"[green]✓ Transcription[/green] {video_id}")
    except Exception:
        progress.update(task, advance=1, description=f"[red]✗ Transcription[/red] {video_id} - Exception")
        logger.error("Transcription exception", video_id=video_id, traceback=traceback.format_exc())


async def fetch_discussions(url_data: dict, progress: Progress, task: TaskID) -> None:
    """Fetch discussion threads for URL."""
    base_dir = settings.artifacts_path / "bronze"
    url = url_data["url"]
    url_hash = url_data["url_hash"]

    if exists(base_dir, BronzeTable.DISCUSSIONS, "metadata", sub_partition=url_hash):
        progress.update(task, advance=1, description=f"[cyan]Discussions[/cyan] [dim]cached: {url}[/dim]")
        return

    pre_saved_links = [DiscussionLink(**link) for link in url_data.get("discussion_links", [])]

    async with HackerNewsClient() as hn, LobstersClient() as lobsters:
        clients = [hn, lobsters]

        try:
            result = await fetch_discussions_for_url(url, clients, pre_saved_links)

            # Save all unified discussions
            for discussion in result.discussions:
                save(base_dir, BronzeTable.DISCUSSIONS, discussion.id, discussion.model_dump(), sub_partition=url_hash)

            metadata = DiscussionMetadata(
                url=url,
                discussion_links=result.discussion_links,
                discovered_at=datetime.now(UTC),
            )

            save(base_dir, BronzeTable.DISCUSSIONS, "metadata", metadata.model_dump(), sub_partition=url_hash)

            total_stories = len(result.discussions)
            progress.update(task, advance=1, description=f"[green]✓ Discussions[/green] {url} ({total_stories} found)")

        except Exception:
            progress.update(task, advance=1, description=f"[red]✗ Discussions[/red] {url} - Exception")
            logger.error("Discussions fetch exception", url=url, traceback=traceback.format_exc())


# ==================== SILVER LAYER ====================


async def generate_article_summary(url_data: dict, progress: Progress, task: TaskID) -> None:
    """Generate Stage 1 article summary."""
    if not settings.enable_summarization:
        progress.update(task, advance=1, description="[yellow]⊘ Article Summary[/yellow] (summarization disabled)")
        return

    base_dir_bronze = settings.artifacts_path / "bronze"
    url = url_data["url"]
    url_hash = url_data["url_hash"]

    article_summary_path = get_article_summary_path(url_hash)
    if article_summary_path.exists():
        progress.update(task, advance=1, description=f"[cyan]Article Summary[/cyan] [dim]cached: {url}[/dim]")
        return

    # Determine content type and load bronze data
    content_type = url_data["content_type"]

    if content_type == "html":
        if not exists(base_dir_bronze, BronzeTable.HTML, url_hash):
            progress.update(task, advance=1, description=f"[yellow]⊘ Article Summary[/yellow] {url} - No HTML data")
            return

        bronze_data = load(base_dir_bronze, BronzeTable.HTML, url_hash)
        content = bronze_data.get("content", "")
        title = bronze_data.get("title", "Untitled")

    elif content_type == "youtube":
        video_id = YouTubeExtractor.extract_video_id(url)
        if not exists(base_dir_bronze, BronzeTable.YOUTUBE_DOWNLOADS, "transcription", sub_partition=video_id):
            progress.update(task, advance=1, description=f"[yellow]⊘ Article Summary[/yellow] {url} - No transcription")
            return

        transcription_data = load(base_dir_bronze, BronzeTable.YOUTUBE_DOWNLOADS, "transcription", sub_partition=video_id)
        content = transcription_data.get("text", "")
        metadata = load(base_dir_bronze, BronzeTable.YOUTUBE_DOWNLOADS, "metadata", sub_partition=video_id)
        title = metadata.get("title", "Untitled Video")

    else:
        progress.update(task, advance=1, description=f"[yellow]⊘ Article Summary[/yellow] {url} - Unknown content type")
        return

    openai_client = get_cached_openai_client()
    summarizer = ArticleSummarizer(
        openai_client=openai_client,
        model=settings.openai_model,
    )

    try:
        analysis = await summarizer.summarize(
            content=content,
            title=title,
            url=url,
            content_type=content_type,
        )

        summary_data = {
            "url": url,
            "url_hash": url_hash,
            "title": title,
            "content_type": content_type,
            "analysis": analysis.model_dump(),
            "created_at": datetime.now(UTC).isoformat(),
        }

        article_summary_path.parent.mkdir(parents=True, exist_ok=True)
        article_summary_path.write_text(json.dumps(summary_data, indent=2, default=str))

        progress.update(task, advance=1, description=f"[green]✓ Article Summary[/green] {title}")

    except Exception:
        progress.update(task, advance=1, description=f"[red]✗ Article Summary[/red] {url} - Exception")
        logger.error("Article summary exception", url=url, traceback=traceback.format_exc())


async def generate_discussion_summaries(url_data: dict, progress: Progress, task: TaskID) -> None:
    """Generate Stage 2 discussion summaries."""
    if not settings.enable_summarization:
        progress.update(task, advance=1, description="[yellow]⊘ Discussion Summary[/yellow] (summarization disabled)")
        return

    base_dir_bronze = settings.artifacts_path / "bronze"
    url = url_data["url"]
    url_hash = url_data["url_hash"]

    # Check if article summary exists
    article_summary_path = get_article_summary_path(url_hash)
    if not article_summary_path.exists():
        progress.update(task, advance=1, description=f"[yellow]⊘ Discussion Summary[/yellow] {url} - No article summary")
        return

    # Check if discussions exist
    if not exists(base_dir_bronze, BronzeTable.DISCUSSIONS, "metadata", sub_partition=url_hash):
        progress.update(task, advance=1, description=f"[cyan]Discussion Summary[/cyan] {url} - No discussions")
        return

    metadata_file = load(base_dir_bronze, BronzeTable.DISCUSSIONS, "metadata", sub_partition=url_hash)
    discussion_links = metadata_file.get("discussion_links", [])

    if not discussion_links:
        progress.update(task, advance=1, description=f"[cyan]Discussion Summary[/cyan] {url} - No discussions")
        return

    # Load article semantic summary for context
    article_data = json.loads(article_summary_path.read_text())
    semantic_summary = article_data["analysis"]["article"]["semantic_summary"]

    openai_client = get_cached_openai_client()
    summarizer = DiscussionSummarizer(
        openai_client=openai_client,
        model=settings.openai_model,
    )

    discussion_summary_dir = get_discussion_summary_dir(url_hash)
    discussion_summary_dir.mkdir(parents=True, exist_ok=True)

    # Load all discussion files from bronze layer (excluding metadata.json)
    discussions_dir = base_dir_bronze / BronzeTable.DISCUSSIONS / url_hash
    if not discussions_dir.exists():
        progress.update(task, advance=1, description=f"[yellow]⊘ Discussion Summary[/yellow] {url} - No discussions")
        return

    processed_count = 0
    for discussion_file in discussions_dir.glob("*.json"):
        if discussion_file.name == "metadata.json":
            continue

        discussion_data = json.loads(discussion_file.read_text())
        discussion_id = discussion_data["id"]
        platform = discussion_data["platform"]

        # Check cache
        discussion_summary_file = discussion_summary_dir / f"{platform}_{discussion_id}.json"
        if discussion_summary_file.exists():
            continue

        try:
            discussion = UnifiedDiscussion(**discussion_data)
            community_take = await summarizer.analyze_discussion(
                discussion=discussion,
                semantic_summary=semantic_summary,
            )

            summary_data = {
                "url": url,
                "discussion_id": discussion_id,
                "platform": platform,
                "discussion_url": discussion_data.get("discussion_url"),
                "community_take": community_take.model_dump(),
                "created_at": datetime.now(UTC).isoformat(),
            }

            discussion_summary_file.write_text(json.dumps(summary_data, indent=2, default=str))
            processed_count += 1

        except Exception:
            logger.error("Discussion summary exception", discussion_id=discussion_id, traceback=traceback.format_exc())

    progress.update(task, advance=1, description=f"[green]✓ Discussion Summary[/green] {url} ({processed_count} processed)")


async def synthesize_final_summary(url_data: dict, progress: Progress, task: TaskID) -> None:
    """Generate Stage 3 final synthesis."""
    if not settings.enable_summarization:
        progress.update(task, advance=1, description="[yellow]⊘ Final Summary[/yellow] (summarization disabled)")
        return

    base_dir_silver = settings.artifacts_path / "silver"
    url = url_data["url"]
    url_hash = url_data["url_hash"]

    if exists(base_dir_silver, SilverTable.SUMMARIES, url_hash):
        progress.update(task, advance=1, description=f"[cyan]Final Summary[/cyan] [dim]cached: {url}[/dim]")
        return

    # Load article summary
    article_summary_path = get_article_summary_path(url_hash)
    if not article_summary_path.exists():
        progress.update(task, advance=1, description=f"[yellow]⊘ Final Summary[/yellow] {url} - No article summary")
        return

    article_data = json.loads(article_summary_path.read_text())
    article_analysis = ArticleAnalysis(**article_data["analysis"])

    # Load discussion summaries
    discussion_summaries_dir = get_discussion_summary_dir(url_hash)
    discussion_summaries = []

    if discussion_summaries_dir.exists():
        for summary_file in discussion_summaries_dir.glob("*.json"):
            discussion_data = json.loads(summary_file.read_text())
            community_take = CommunityTake(**discussion_data["community_take"])
            discussion_summaries.append(community_take)

    # Synthesize based on number of discussions
    if len(discussion_summaries) == 0:
        final_analysis = article_analysis  # No discussions
    elif len(discussion_summaries) == 1:
        article_analysis.community = discussion_summaries[0]  # Single discussion
        final_analysis = article_analysis
    else:
        # Multiple discussions - synthesize
        openai_client = get_cached_openai_client()
        synthesizer = CommunitySynthesizer(
            openai_client=openai_client,
            model=settings.openai_model,
        )

        try:
            semantic_summary = article_analysis.article.semantic_summary
            synthesized_community = await synthesizer.synthesize(
                discussion_summaries=discussion_summaries,
                semantic_summary=semantic_summary,
            )
            article_analysis.community = synthesized_community
            final_analysis = article_analysis
        except Exception:
            progress.update(task, advance=1, description=f"[red]✗ Final Summary[/red] {url} - Synthesis exception")
            logger.error("Synthesis exception", url=url, traceback=traceback.format_exc())
            return

    # Save final summary
    summary_data = {
        "url": url,
        "title": article_data["title"],
        "status": "success",
        "content_type": article_data["content_type"],
        "structured_summary": final_analysis.model_dump(),
        "discussion_count": len(discussion_summaries),
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }

    save(base_dir_silver, SilverTable.SUMMARIES, url_hash, summary_data)
    progress.update(task, advance=1, description=f"[green]✓ Final Summary[/green] {url} ({len(discussion_summaries)} discussions)")


# ==================== MAIN ORCHESTRATION ====================


def process_urls(source: str) -> None:
    """Main pipeline orchestration with Rich progress bars."""
    asyncio.run(_async_process_urls(source))


async def _async_process_urls(source: str) -> None:
    """Async implementation of the pipeline."""
    # Stage 0: Discovery
    console.print(f"\n[bold]Stage 0:[/bold] URL Discovery ([cyan]{source}[/cyan])\n")
    discovered_urls = await discover_urls(source)

    if not discovered_urls:
        console.print("[yellow]No URLs discovered. Exiting.[/yellow]")
        return

    console.print(f"[green]✓ Discovered {len(discovered_urls)} unique URLs[/green]\n")

    # Filter by content type
    html_urls = [u for u in discovered_urls if u["content_type"] == "html"]
    youtube_urls = [u for u in discovered_urls if u["content_type"] == "youtube"]

    # Stage 1: Bronze Layer
    console.print("[bold]Stage 1:[/bold] Bronze Layer Extraction\n")

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        # HTML extraction
        if html_urls:
            html_task = progress.add_task("[cyan]HTML Extraction...", total=len(html_urls))
            for url_data in html_urls:
                await extract_html(url_data, progress, html_task)

        # YouTube download
        if youtube_urls:
            youtube_task = progress.add_task("[cyan]YouTube Download...", total=len(youtube_urls))
            for url_data in youtube_urls:
                await download_youtube(url_data, progress, youtube_task)

        # YouTube transcription
        if youtube_urls:
            transcription_task = progress.add_task("[cyan]YouTube Transcription...", total=len(youtube_urls))
            for url_data in youtube_urls:
                await transcribe_youtube(url_data, progress, transcription_task)

        # Discussions
        discussions_task = progress.add_task("[cyan]Discussion Fetch...", total=len(discovered_urls))
        for url_data in discovered_urls:
            await fetch_discussions(url_data, progress, discussions_task)

    console.print("\n[green]✓ Bronze layer extraction complete[/green]\n")

    # Stage 2: Silver Layer
    if settings.enable_summarization:
        console.print("[bold]Stage 2:[/bold] Silver Layer Summarization\n")

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            # Article summaries
            article_task = progress.add_task("[cyan]Article Summaries...", total=len(discovered_urls))
            for url_data in discovered_urls:
                await generate_article_summary(url_data, progress, article_task)

            # Discussion summaries
            discussion_task = progress.add_task("[cyan]Discussion Summaries...", total=len(discovered_urls))
            for url_data in discovered_urls:
                await generate_discussion_summaries(url_data, progress, discussion_task)

            # Final synthesis
            synthesis_task = progress.add_task("[cyan]Final Synthesis...", total=len(discovered_urls))
            for url_data in discovered_urls:
                await synthesize_final_summary(url_data, progress, synthesis_task)

        console.print("\n[green]✓ Silver layer summarization complete[/green]\n")
    else:
        console.print("\n[yellow]⊘ Summarization disabled (ENABLE_SUMMARIZATION=false)[/yellow]\n")
