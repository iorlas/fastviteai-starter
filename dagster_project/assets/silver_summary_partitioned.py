import structlog
from dagster import AssetExecutionContext, Backoff, RetryPolicy, asset

from dagster_project.core.summarizer import SummaryGenerator, SummaryRequest
from dagster_project.partitions import url_partitions
from dagster_project.url_metadata import URLMetadataStore

logger = structlog.get_logger()


@asset(
    partitions_def=url_partitions,
    io_manager_key="silver_io_manager",
    required_resource_keys={"openai"},
    retry_policy=RetryPolicy(
        max_retries=3,
        delay=1,
        backoff=Backoff.EXPONENTIAL,
    ),
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "operation": "summarization"},
)
def silver_summary(
    context: AssetExecutionContext,
    silver_extracted_content: dict,
) -> dict:
    url_hash = context.partition_key
    metadata_store = URLMetadataStore()
    url_metadata = metadata_store.get_metadata(url_hash)

    if not url_metadata:
        msg = f"No metadata found for URL hash: {url_hash}"
        logger.error("silver.summary.no_metadata", url_hash=url_hash)
        raise ValueError(msg)

    canonical_url = url_metadata["canonical_url"]

    if not silver_extracted_content.get("extraction_success"):
        logger.warning(
            "silver.summary.skip_failed_extraction",
            url_hash=url_hash,
            canonical_url=canonical_url,
        )

        result = {
            "url": canonical_url,
            "url_hash": url_hash,
            "title": silver_extracted_content.get("title", "Unknown"),
            "status": "failed",
            "error": silver_extracted_content.get("error_message", "Content extraction failed"),
            "error_type": "ExtractionError",
            "content_type": silver_extracted_content.get("content_type", "unknown"),
            "lineage": {
                "silver_extracted_content": {
                    "extraction_success": False,
                    "error": silver_extracted_content.get("error_message"),
                },
            },
        }

        context.add_output_metadata(
            {
                "url": canonical_url,
                "status": "failed",
                "reason": "extraction_failed",
            }
        )

        return result

    openai_resource = context.resources.openai
    title = silver_extracted_content.get("title", canonical_url)

    logger.info(
        "silver.summary.started",
        url_hash=url_hash,
        canonical_url=canonical_url,
        title=title,
    )

    try:
        generator = SummaryGenerator(
            openai_client=openai_resource.client, model=openai_resource.model
        )

        result = generator.generate(
            SummaryRequest(
                content=silver_extracted_content.get("content", ""),
                title=title,
                content_type=silver_extracted_content.get("content_type", "unknown"),
                url=canonical_url,
            )
        )

        context.add_output_metadata(
            {
                "url": canonical_url,
                "status": "success",
                "model": result.model,
                "tokens_used": result.tokens_used,
                "latency_ms": result.latency_ms,
            }
        )

        return {
            "url": canonical_url,
            "url_hash": url_hash,
            "title": title,
            "status": "success",
            "content_type": silver_extracted_content.get("content_type", "unknown"),
            "summary": result.summary,
            "model": result.model,
            "tokens_used": result.tokens_used,
            "latency_ms": result.latency_ms,
            "lineage": {
                "silver_extracted_content": {
                    "extraction_success": True,
                    "content_length": len(silver_extracted_content.get("content", "")),
                },
            },
        }

    except Exception as e:
        logger.error(
            "silver.summary.failed",
            url_hash=url_hash,
            canonical_url=canonical_url,
            error=str(e),
            error_type=type(e).__name__,
        )

        result = {
            "url": canonical_url,
            "url_hash": url_hash,
            "title": title,
            "status": "failed",
            "error": str(e),
            "error_type": type(e).__name__,
            "retry_count": 3,
            "content_type": silver_extracted_content.get("content_type", "unknown"),
            "lineage": {
                "silver_extracted_content": {
                    "extraction_success": True,
                },
            },
        }

        context.add_output_metadata(
            {
                "url": canonical_url,
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
            }
        )

        return result
