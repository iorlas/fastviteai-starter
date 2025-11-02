import hashlib
import time
from datetime import UTC, datetime

import structlog
from dagster import AssetExecutionContext, Backoff, RetryPolicy, asset
from openai import OpenAI

logger = structlog.get_logger()


def create_summarization_prompt(content_data: dict) -> list[dict[str, str]]:
    system_message = {
        "role": "system",
        "content": (
            "You are a helpful assistant that creates concise, informative summaries "
            "of articles and videos. Focus on key points, main ideas, and actionable insights."
        ),
    }

    content_type = "video transcript" if content_data["type"] == "youtube" else "article"

    user_message = {
        "role": "user",
        "content": (
            f"Please summarize this {content_type}:\n\n"
            f"Title: {content_data['title']}\n\n"
            f"Content:\n{content_data['content']}\n\n"
            f"Provide a clear, structured summary covering:\n"
            f"1. Main topic and key points\n"
            f"2. Important details and supporting information\n"
            f"3. Key takeaways or conclusions"
        ),
    }

    return [system_message, user_message]


@asset(
    io_manager_key="silver_io_manager",
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "source": "summarization"},
    retry_policy=RetryPolicy(
        max_retries=3,
        delay=1,
        backoff=Backoff.EXPONENTIAL,
    ),
)
def silver_summaries(
    context: AssetExecutionContext,
    silver_extracted_content: list,
    openai_client: OpenAI,
) -> list:
    results = []
    successful_summaries = 0
    failed_summaries = 0
    total_tokens = 0
    total_latency = 0.0

    logger.info(
        "silver_layer.summarization.started",
        content_count=len(silver_extracted_content),
    )

    for content_data in silver_extracted_content:
        url = content_data["url"]
        url_hash = hashlib.sha256(url.encode()).hexdigest()

        logger.info(
            "silver_layer.summarization.processing",
            url=url,
            title=content_data.get("title", "Unknown"),
        )

        try:
            messages = create_summarization_prompt(content_data)

            start_time = time.time()
            response = openai_client.chat.completions.create(
                model="openai/gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )
            latency_ms = int((time.time() - start_time) * 1000)

            summary_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            model_used = response.model

            summary_data = {
                "url": url,
                "title": content_data.get("title", url),
                "status": "success",
                "summary": summary_text,
                "model": model_used,
                "tokens_used": tokens_used,
                "latency_ms": latency_ms,
                "lineage": {
                    "source_asset": "silver_extracted_content",
                    "source_hash": url_hash,
                    "transformation_timestamp": datetime.now(UTC).isoformat(),
                },
            }

            results.append(summary_data)
            successful_summaries += 1
            total_tokens += tokens_used
            total_latency += latency_ms

            logger.info(
                "silver_layer.summarization.success",
                url=url,
                tokens=tokens_used,
                latency_ms=latency_ms,
            )

        except Exception as e:
            logger.error(
                "silver_layer.summarization.failed",
                url=url,
                error=str(e),
                error_type=type(e).__name__,
            )

            summary_data = {
                "url": url,
                "title": content_data.get("title", url),
                "status": "failed",
                "summary": None,
                "model": None,
                "tokens_used": None,
                "latency_ms": None,
                "error": str(e),
                "error_type": type(e).__name__,
                "lineage": {
                    "source_asset": "silver_extracted_content",
                    "source_hash": url_hash,
                    "transformation_timestamp": datetime.now(UTC).isoformat(),
                },
            }

            results.append(summary_data)
            failed_summaries += 1

    avg_latency = 0 if successful_summaries == 0 else int(total_latency / successful_summaries)

    logger.info(
        "silver_layer.summarization.complete",
        total_processed=len(silver_extracted_content),
        successful=successful_summaries,
        failed=failed_summaries,
        total_tokens=total_tokens,
        avg_latency_ms=avg_latency,
    )

    context.add_output_metadata(
        {
            "total_processed": len(silver_extracted_content),
            "successful_summaries": successful_summaries,
            "failed_summaries": failed_summaries,
            "total_tokens": total_tokens,
            "avg_latency_ms": avg_latency,
        }
    )

    return results
