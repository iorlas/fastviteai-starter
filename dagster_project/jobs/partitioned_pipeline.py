from dagster import AssetSelection, define_asset_job

discover_and_process_job = define_asset_job(
    name="discover_and_process",
    description="Discover URLs then process all new partitions: discovery → bronze → silver",
    selection=AssetSelection.assets(
        "discovered_urls",
        "bronze_raw_html",
        "silver_extracted_content",
        "silver_summary",
    ),
)

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
    description="Only run URL discovery (adds new partitions without processing)",
    selection=AssetSelection.assets("discovered_urls"),
)
