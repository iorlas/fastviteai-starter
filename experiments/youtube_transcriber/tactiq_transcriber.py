from dataclasses import dataclass
from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeoutError
import structlog

logger = structlog.get_logger()


@dataclass
class TranscriptResult:
    success: bool
    transcript: str | None
    error: str | None
    duration_seconds: float
    video_title: str | None = None
    channel_name: str | None = None
    video_duration: str | None = None


class TactiqTranscriber:
    TACTIQ_URL = "https://tactiq.io/tools/youtube-transcript"
    DEFAULT_TIMEOUT = 30000  # 30 seconds

    def __init__(self, headless: bool = True, timeout_ms: int = DEFAULT_TIMEOUT):
        self.headless = headless
        self.timeout_ms = timeout_ms

    async def get_transcript(self, youtube_url: str) -> TranscriptResult:
        import time
        start_time = time.time()

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()

                transcript, metadata = await self._extract_transcript(page, youtube_url)

                await browser.close()

                duration = time.time() - start_time
                return TranscriptResult(
                    success=transcript is not None,
                    transcript=transcript,
                    error=None if transcript else "Failed to extract transcript",
                    duration_seconds=duration,
                    video_title=metadata.get('title'),
                    channel_name=metadata.get('channel'),
                    video_duration=metadata.get('duration')
                )

        except PlaywrightTimeoutError as e:
            duration = time.time() - start_time
            logger.error("timeout_error", error=str(e), url=youtube_url)
            return TranscriptResult(
                success=False,
                transcript=None,
                error=f"Timeout: {str(e)}",
                duration_seconds=duration,
                video_title=None,
                channel_name=None,
                video_duration=None
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error("extraction_error", error=str(e), url=youtube_url)
            return TranscriptResult(
                success=False,
                transcript=None,
                error=str(e),
                duration_seconds=duration,
                video_title=None,
                channel_name=None,
                video_duration=None
            )

    async def _extract_transcript(self, page: Page, youtube_url: str) -> tuple[str | None, dict]:
        from pathlib import Path
        screenshots_dir = Path("experiments/youtube_transcriber/screenshots")
        screenshots_dir.mkdir(exist_ok=True)

        logger.info("navigating_to_tactiq", url=self.TACTIQ_URL)
        await page.goto(self.TACTIQ_URL, wait_until="domcontentloaded", timeout=self.timeout_ms)
        await page.screenshot(path=str(screenshots_dir / "01_initial_page.png"))

        # Find the input field for YouTube URL
        logger.info("locating_input_field")
        input_selector = 'input[placeholder*="youtube" i], input[placeholder*="URL" i], input[type="text"]'
        await page.wait_for_selector(input_selector, timeout=self.timeout_ms)

        # Input the YouTube URL
        logger.info("entering_youtube_url", url=youtube_url)
        await page.fill(input_selector, youtube_url)
        await page.screenshot(path=str(screenshots_dir / "02_url_entered.png"))

        # Find and click the submit button
        logger.info("clicking_submit_button")
        button_selector = 'button:has-text("Get Video Transcript"), input[type="submit"], button[type="submit"]'
        await page.click(button_selector)

        # Wait a bit for the page to process
        await page.wait_for_timeout(3000)
        await page.screenshot(path=str(screenshots_dir / "03_after_submit.png"))

        # Wait for transcript to appear - look for timestamp pattern
        logger.info("waiting_for_transcript")

        # Wait for any element containing a timestamp (format: 00:00:00.000)
        timestamp_found = False
        for attempt in range(15):  # 15 attempts, 2 seconds each = 30 seconds total
            page_text = await page.inner_text('body')
            if '00:00:' in page_text or 'transcript' in page_text.lower():
                timestamp_found = True
                logger.info("timestamp_pattern_found", attempt=attempt)
                break
            await page.wait_for_timeout(2000)

        if not timestamp_found:
            await page.screenshot(path=str(screenshots_dir / "04_error_no_transcript.png"))
            logger.error("no_transcript_element_found")
            return None, {}

        await page.screenshot(path=str(screenshots_dir / "04_transcript_found.png"))

        # Extract metadata
        logger.info("extracting_metadata")
        metadata = await self._extract_metadata(page)

        # Extract transcript - try multiple strategies
        logger.info("extracting_transcript_text")

        # Strategy 1: Look for a div/section containing the transcript
        transcript_containers = await page.query_selector_all('div, section, article')
        for container in transcript_containers:
            text = await container.inner_text()
            # If it contains multiple timestamp patterns, it's likely the transcript
            if text.count('00:00:') > 3 or text.count('00:01:') > 1:
                cleaned_text = self._clean_transcript(text)
                logger.info("transcript_extracted_from_container", length=len(cleaned_text))
                return cleaned_text, metadata

        # Strategy 2: Get all text and filter for transcript-like content
        all_text = await page.inner_text('body')
        cleaned_text = self._clean_transcript(all_text)

        if cleaned_text:
            logger.info("transcript_extracted_from_body", length=len(cleaned_text))
            return cleaned_text, metadata

        logger.warning("transcript_element_not_found")
        return None, metadata

    def _clean_transcript(self, raw_text: str) -> str:
        lines = raw_text.split('\n')
        transcript_lines = []
        in_transcript = False

        for line in lines:
            stripped = line.strip()

            # Start collecting when we see the first timestamp
            if not in_transcript and stripped.startswith('00:'):
                in_transcript = True

            # Stop at footer text
            if '©' in stripped or 'Made with' in stripped or 'All rights reserved' in stripped:
                break

            # Collect transcript lines
            if in_transcript:
                # Skip empty lines and navigation text
                if stripped and not any(skip in stripped for skip in [
                    'Get started for FREE',
                    'Copy',
                    'Download',
                    'Upload the transcript',
                    'Learn more'
                ]):
                    transcript_lines.append(stripped)

        return '\n'.join(transcript_lines)

    async def _extract_metadata(self, page: Page) -> dict:
        metadata = {}

        try:
            # Try to extract video title from YouTube iframe or page title
            page_title = await page.title()
            if page_title and page_title != "YouTube Transcript Generator":
                metadata['title'] = page_title

            # Try to find YouTube iframe and extract video ID
            iframe = await page.query_selector('iframe[src*="youtube.com"]')
            video_id = None
            if iframe:
                src = await iframe.get_attribute('src')
                if src:
                    logger.info("youtube_iframe_found", src=src)
                    # Extract video ID from iframe src
                    import re
                    match = re.search(r'/embed/([a-zA-Z0-9_-]+)', src)
                    if match:
                        video_id = match.group(1)
                        logger.info("video_id_extracted", video_id=video_id)

            # If we have video ID, fetch metadata from YouTube using yt-dlp
            if video_id:
                try:
                    from yt_dlp import YoutubeDL
                    ydl_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': True,
                    }
                    with YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
                        if info:
                            metadata['title'] = info.get('title')
                            metadata['channel'] = info.get('uploader') or info.get('channel')
                            # Format duration from seconds to HH:MM:SS or MM:SS
                            if info.get('duration'):
                                duration_sec = int(info['duration'])
                                hours = duration_sec // 3600
                                minutes = (duration_sec % 3600) // 60
                                seconds = duration_sec % 60
                                if hours > 0:
                                    metadata['duration'] = f"{hours}:{minutes:02d}:{seconds:02d}"
                                else:
                                    metadata['duration'] = f"{minutes}:{seconds:02d}"
                            logger.info("metadata_from_ytdlp", metadata=metadata)
                except ImportError:
                    logger.warning("yt_dlp_not_available")
                except Exception as e:
                    logger.warning("ytdlp_metadata_extraction_failed", error=str(e))

            logger.info("metadata_extracted", metadata=metadata)

        except Exception as e:
            logger.warning("metadata_extraction_failed", error=str(e))

        return metadata
