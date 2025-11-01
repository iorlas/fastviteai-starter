"""Dagster assets for the link processing pipeline."""

from dagster_project.assets.content_extraction import content_extraction_asset
from dagster_project.assets.link_ingestion import link_ingestion_asset
from dagster_project.assets.summarization import summarization_asset

__all__ = [
    "link_ingestion_asset",
    "content_extraction_asset",
    "summarization_asset",
]
