## Requirements

- Python 3.12+
- OpenRouter API key

## Installation

```bash
uv sync
```

## Usage

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
