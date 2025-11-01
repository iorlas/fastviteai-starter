# DeepRock

Content processing pipeline that ingests links from various sources, extracts content, and generates AI-powered summaries.

## Features

- **Link Ingestion**: Process links from manual input or automated monitoring sources
- **RSS Feed Monitoring**: Automatically discover new content from RSS/Atom feeds
- **Content Extraction**: Extract article text from HTML pages and YouTube videos
- **AI Summarization**: Generate concise summaries using OpenRouter LLM models
- **Automated Scheduling**: Background monitoring of RSS feeds every 6 hours
- **Extensible Architecture**: Pluggable watcher protocol for future content sources

## Requirements

- Python 3.12+
- OpenRouter API key

## Installation

```bash
uv sync
```

## Usage

### Dagster Pipeline (Link Processing)

```bash
# Start Dagster development server
uv run dagster dev

# Access Dagster UI at http://localhost:3000
```

**Adding links to process:**

```bash
# Manual links (processed on-demand)
echo "https://example.com/article" >> manual_links.txt

# Monitoring links - supports both direct URLs and RSS feeds
echo "https://news.ycombinator.com/rss" >> monitoring_list.txt
echo "https://example.com/feed.xml" >> monitoring_list.txt

# RSS feeds are automatically detected and processed by RSSWatcher
# Direct article URLs can also be added to monitoring_list.txt
```

**Note:** Create input files from templates if they don't exist:
```bash
cp manual_links.txt.template manual_links.txt
cp monitoring_list.txt.template monitoring_list.txt
```

#### Known Limitations

**YouTube Transcript Extraction:** The YouTube extractor currently does not download actual video transcripts. Instead, it falls back to using the video description for summarization. This is a known limitation in the current implementation.

- **Workaround:** Video descriptions are used for summarization when transcripts are unavailable
- **Future Enhancement:** Full transcript extraction using yt-dlp subtitle download capabilities

If you need actual transcript extraction, the implementation can be found in `dagster_project/ops/youtube_extractor.py` (see `_extract_transcript()` function).

### Other Usage

```bash
# Classify an email via CLI
echo "Your email text here" | uv run python src/cli/classify.py

# Start Streamlit UI
uv run streamlit run src/ui/app.py
```

## Development

```bash
# Run tests
uv run pytest

# Run quality checks
make check
```
