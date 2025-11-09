# YouTube Transcriber PoC

Proof of concept for YouTube transcript extraction using tactiq.io web scraping.

## Setup

```bash
# Install playwright
uv add --dev playwright

# Install browser binaries
uv run playwright install chromium
```

## Usage

```bash
# Test with a YouTube URL
uv run python experiments/youtube_transcriber/test_transcriber.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Save to file
uv run python experiments/youtube_transcriber/test_transcriber.py "https://www.youtube.com/watch?v=VIDEO_ID" --output transcript.txt
```

## How It Works

1. Opens tactiq.io transcript tool in headless browser
2. Inputs YouTube URL into the form
3. Waits for transcript to load
4. Extracts transcript text
5. Returns structured result

## Limitations

- Depends on tactiq.io web interface (may break if they change it)
- Slower than direct API access
- Requires browser automation overhead
- Rate limiting unknown (use responsibly)
