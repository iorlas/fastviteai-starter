"""Monitoring pipeline job for processing monitoring_list.txt."""

from dagster import AssetSelection, define_asset_job

# Define job that processes all pipeline assets
# This will be triggered by the monitoring schedule
# Configured to only process monitoring_list.txt
monitoring_pipeline_job = define_asset_job(
    name="monitoring_pipeline",
    description="Process links from monitoring_list.txt only through extraction and summarization",
    selection=AssetSelection.assets(
        "link_ingestion",
        "content_extraction",
        "summarization",
    ),
    config={"ops": {"link_ingestion": {"config": {"source_filter": "monitoring"}}}},
)
