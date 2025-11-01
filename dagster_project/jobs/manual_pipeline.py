"""Manual pipeline job for processing manual_links.txt."""

from dagster import AssetSelection, define_asset_job

# Define job that processes all pipeline assets
# This will be triggered manually via Dagster UI
# Configured to only process manual_links.txt
manual_pipeline_job = define_asset_job(
    name="manual_pipeline",
    description="Process links from manual_links.txt only through extraction and summarization",
    selection=AssetSelection.assets(
        "link_ingestion",
        "content_extraction",
        "summarization",
    ),
    config={"ops": {"link_ingestion": {"config": {"source_filter": "manual"}}}},
)
