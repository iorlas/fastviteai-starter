from dagster import AssetSelection, define_asset_job

manual_pipeline_job = define_asset_job(
    name="manual_pipeline",
    description="Process links from manual_links.txt through medallion: bronze → silver",
    selection=AssetSelection.assets(
        "bronze_raw_links",
        "bronze_raw_html",
        "silver_extracted_content",
        "silver_summaries",
    ),
    config={"ops": {"bronze_raw_links": {"config": {"source_filter": "manual"}}}},
)
