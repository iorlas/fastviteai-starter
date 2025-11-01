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

# Monitoring links (processed every 6 hours automatically)
echo "https://news.ycombinator.com/rss" >> monitoring_list.txt
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
