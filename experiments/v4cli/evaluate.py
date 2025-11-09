#!/usr/bin/env python3
"""
CLI script for URL content extraction and summarization.

Usage:
    ./evaluate.py --url <url> [--model <model>] [--schema <schema>]

Examples:
    ./evaluate.py --url https://example.com/article
    ./evaluate.py --url https://youtube.com/watch?v=xyz --model "anthropic/claude-3.5-sonnet"
    ./evaluate.py --url https://example.com --schema simple --system-prompt "Be concise"
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RUNS_DIR = Path(__file__).parent / "runs"
RUNS_DIR.mkdir(exist_ok=True)

from dagster_project.config import settings
from dagster_project.core.content_types.generic_html import GenericHTMLExtractor
from dagster_project.core.content_types.youtube import YouTubeExtractor
from dagster_project.core.summary.schema import KnowledgeGraphSummary, RawTextSummary, SimpleSummary
from dagster_project.core.summary.summarizer import SummaryGenerator, SummaryInput
from openai import OpenAI

SYSTEM_PROMPT_PATH = PROJECT_ROOT / "experiments/v3/prompts/baseline/system.txt"
USER_PROMPT_PATH = PROJECT_ROOT / "experiments/v3/prompts/baseline/user.txt"

DEFAULT_SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text() if SYSTEM_PROMPT_PATH.exists() else ""
DEFAULT_USER_PROMPT = USER_PROMPT_PATH.read_text() if USER_PROMPT_PATH.exists() else ""

SCHEMAS = {
    "knowledge-graph": KnowledgeGraphSummary,
    "simple": SimpleSummary,
    "raw-text": RawTextSummary,
}


def save_execution_log(
    url: str,
    schema_name: str,
    model: str,
    result: dict | None = None,
    error: str | None = None,
) -> Path:
    """Save execution details to timestamped JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"{timestamp}.json"
    filepath = RUNS_DIR / filename

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "schema": schema_name,
        "model": model,
        "success": error is None,
    }

    if result:
        log_data["result"] = result

    if error:
        log_data["error"] = error

    filepath.write_text(json.dumps(log_data, indent=2))
    return filepath


async def extract_content(url: str) -> tuple[str, str, str]:
    """Extract content from URL (HTML or YouTube)."""
    is_youtube = "youtube.com" in url or "youtu.be" in url

    if is_youtube:
        extractor = YouTubeExtractor()
        result = await extractor.extract(url)
    else:
        extractor = GenericHTMLExtractor()
        result = await extractor.extract(url)

    if not result.success:
        raise ValueError(f"Extraction failed: {result.error}")

    return result.title, result.content, result.content_type


async def generate_summary_async(
    url: str,
    system_prompt: str,
    user_prompt_template: str,
    model: str,
    response_schema: type,
) -> dict:
    """Extract content and generate summary."""
    title, content, content_type = await extract_content(url)

    summary_input = SummaryInput(
        content=content,
        title=title,
        content_type=content_type,
        url=url,
        discussions=None,
    )

    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        max_retries=3,
        timeout=30.0,
    )

    generator = SummaryGenerator(
        openai_client=client,
        model=model,
        system_prompt=system_prompt,
        user_prompt_template=user_prompt_template,
        response_schema=response_schema,
    )

    result = generator.generate(summary_input)

    return {
        "url": url,
        "summary": result.structured_summary.model_dump(),
        "model": result.model,
        "tokens_used": result.tokens_used,
        "latency_ms": result.latency_ms,
    }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract and summarize content from URLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --url https://example.com/article
  %(prog)s --url https://youtube.com/watch?v=xyz --model "openai/gpt-4o"
  %(prog)s --url https://example.com --schema simple
        """,
    )

    parser.add_argument(
        "--url",
        required=True,
        help="URL to extract and summarize",
    )

    parser.add_argument(
        "--model",
        default=settings.openai_model,
        help=f"OpenRouter model ID (default: {settings.openai_model})",
    )

    parser.add_argument(
        "--system-prompt",
        default=DEFAULT_SYSTEM_PROMPT,
        help="System prompt inline string (default: baseline prompt)",
    )

    parser.add_argument(
        "--user-prompt",
        default=DEFAULT_USER_PROMPT,
        help="User prompt template inline string (default: baseline prompt)",
    )

    parser.add_argument(
        "--schema",
        choices=list(SCHEMAS.keys()),
        default="knowledge-graph",
        help="Response schema type (default: knowledge-graph)",
    )

    args = parser.parse_args()

    selected_schema = SCHEMAS[args.schema]

    try:
        result = asyncio.run(
            generate_summary_async(
                url=args.url,
                system_prompt=args.system_prompt,
                user_prompt_template=args.user_prompt,
                model=args.model,
                response_schema=selected_schema,
            )
        )

        # Log execution
        save_execution_log(
            url=args.url,
            schema_name=args.schema,
            model=args.model,
            result=result,
        )

        # Output to stdout
        print(json.dumps(result, indent=2))
        sys.exit(0)

    except Exception as e:
        # Log error
        save_execution_log(
            url=args.url,
            schema_name=args.schema,
            model=args.model,
            error=str(e),
        )

        # Output error to stderr
        error_output = {
            "error": str(e),
            "url": args.url,
        }
        print(json.dumps(error_output, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
