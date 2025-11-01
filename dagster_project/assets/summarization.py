"""Summarization asset for generating AI summaries of extracted content."""

import json
import time
from pathlib import Path

from dagster import AssetExecutionContext, Backoff, Field, RetryPolicy, asset

from dagster_project.assets.content_extraction import ExtractedContent


def create_summarization_prompt(content: ExtractedContent) -> list[dict[str, str]]:
    """Create prompt messages for summarization.

    Args:
        content: Extracted content to summarize

    Returns:
        List of message dictionaries for LLM API
    """
    system_message = {
        "role": "system",
        "content": (
            "You are a helpful assistant that creates concise, informative summaries "
            "of articles and videos. Focus on key points, main ideas, and actionable insights."
        ),
    }

    content_type = "video transcript" if content.content_type == "youtube" else "article"

    user_message = {
        "role": "user",
        "content": (
            f"Please summarize this {content_type}:\n\n"
            f"Title: {content.title}\n\n"
            f"Content:\n{content.text}\n\n"
            f"Provide a clear, structured summary covering:\n"
            f"1. Main topic and key points\n"
            f"2. Important details and supporting information\n"
            f"3. Key takeaways or conclusions"
        ),
    }

    return [system_message, user_message]


def save_summary(
    url_hash: str,
    summary_data: dict,
    output_dir: Path,
) -> None:
    """Save summary to JSON file.

    Args:
        url_hash: Hash of the URL
        summary_data: Summary data dictionary
        output_dir: Directory to save to (summaries/)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{url_hash}.json"

    with open(output_file, "w") as f:
        json.dump(summary_data, f, indent=2)


@asset(
    name="summarization",
    deps=["content_extraction"],
    retry_policy=RetryPolicy(
        max_retries=3,
        delay=1,  # Initial delay in seconds
        backoff=Backoff.EXPONENTIAL,
    ),
    config_schema={
        "project_root": Field(str, is_required=False),
    },
)
def summarization_asset(
    context: AssetExecutionContext,
    content_extraction: list[ExtractedContent],
) -> dict:
    """Generate AI summaries for extracted content.

    Uses OpenRouter resource to generate summaries via LLM API.
    Saves summaries with metadata to artifacts/summaries/.
    On failure after retries, saves error details with status="failed".

    Config:
        project_root: Path to project root directory (default: auto-detected from __file__)

    Args:
        context: Dagster execution context
        content_extraction: List of extracted content from content_extraction asset

    Returns:
        Summary statistics dictionary
    """
    # Get project root from config or auto-detect
    project_root_str = context.op_config.get("project_root")
    if project_root_str:
        project_root = Path(project_root_str)
    else:
        project_root = Path(__file__).parent.parent.parent
    summaries_dir = project_root / "artifacts" / "summaries"

    # Access OpenRouter resource
    openrouter = context.resources.openrouter

    successful_summaries = 0
    failed_summaries = 0
    total_tokens = 0
    total_latency = 0.0

    for content in content_extraction:
        # Skip content that failed extraction
        if not content.extraction_success:
            context.log.warning(f"Skipping summarization for failed extraction: {content.url}")

            # Save failed status
            summary_data = {
                "url": content.url,
                "url_hash": content.url_hash,
                "status": "failed",
                "error": content.error_message or "Content extraction failed",
                "title": content.title,
                "content_type": content.content_type,
            }
            save_summary(content.url_hash, summary_data, summaries_dir)
            failed_summaries += 1
            continue

        context.log.info(f"Generating summary for: {content.title}")

        try:
            # Create prompt
            messages = create_summarization_prompt(content)

            # Call LLM API with timing
            start_time = time.time()
            response = openrouter.chat_completion(
                context,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )
            latency_ms = (time.time() - start_time) * 1000

            # Extract summary text
            summary_text = openrouter.get_completion_text(response)

            # Extract token usage
            tokens_used = (
                response.usage.total_tokens
                if hasattr(response, "usage") and hasattr(response.usage, "total_tokens")
                else 0
            )

            # Extract model name
            model_used = response.model if hasattr(response, "model") else openrouter.model

            # Log metadata to Dagster
            context.add_output_metadata(
                {
                    f"summary_{content.url_hash}_model": model_used,
                    f"summary_{content.url_hash}_tokens": tokens_used,
                    f"summary_{content.url_hash}_latency_ms": int(latency_ms),
                }
            )

            # Prepare summary data
            summary_data = {
                "url": content.url,
                "url_hash": content.url_hash,
                "status": "success",
                "title": content.title,
                "content_type": content.content_type,
                "summary": summary_text,
                "metadata": {
                    "model": model_used,
                    "tokens": tokens_used,
                    "latency_ms": int(latency_ms),
                    "original_metadata": content.metadata,
                },
            }

            # Save summary
            save_summary(content.url_hash, summary_data, summaries_dir)

            successful_summaries += 1
            total_tokens += tokens_used
            total_latency += latency_ms

            context.log.info(
                f"Summary generated: {content.title} ({tokens_used} tokens, {int(latency_ms)}ms)"
            )

        except Exception as e:
            context.log.error(f"Failed to generate summary for {content.url}: {e}")

            # After all retries, save failed status
            summary_data = {
                "url": content.url,
                "url_hash": content.url_hash,
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "retry_count": 3,  # Max retries from retry_policy
                "title": content.title,
                "content_type": content.content_type,
            }
            save_summary(content.url_hash, summary_data, summaries_dir)
            failed_summaries += 1

    # Log overall metadata
    avg_latency = 0 if successful_summaries == 0 else int(total_latency / successful_summaries)
    context.add_output_metadata(
        {
            "total_processed": len(content_extraction),
            "successful_summaries": successful_summaries,
            "failed_summaries": failed_summaries,
            "total_tokens": total_tokens,
            "avg_latency_ms": avg_latency,
        }
    )

    return {
        "successful": successful_summaries,
        "failed": failed_summaries,
        "total_tokens": total_tokens,
    }
