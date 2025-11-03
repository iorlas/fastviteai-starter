from dagster import AssetSelection, define_asset_job

process_partitions_job = define_asset_job(
    name="process_partitions",
    description="Process URL partitions through pipeline: bronze → silver (skip discovery)",
    selection=AssetSelection.assets(
        "bronze_raw_html",
        "silver_extracted_content",
        "silver_summary",
    ),
)

discovery_only_job = define_asset_job(
    name="discovery_only",
    description="Only run URL discovery (adds new partitions, sensor auto-processes)",
    selection=AssetSelection.assets("discovered_urls"),
)
