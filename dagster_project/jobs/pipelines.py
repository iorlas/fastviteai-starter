from dagster import AssetSelection, RunConfig, define_asset_job

manual_urls_pipeline = define_asset_job(
    name="manual_urls_pipeline",
    description="Process URLs from manual_links.txt: discovery → bronze → silver → summary",
    selection=AssetSelection.assets(
        "discovered_urls",
        "bronze_html",
        "bronze_youtube_download",
        "bronze_youtube_transcription",
        "bronze_discussions",
        "silver_article_summary",
        "silver_discussion_summary",
        "silver_summary",
    ),
    config=RunConfig(
        ops={
            "discovered_urls": {
                "config": {
                    "source_type": "manual",
                }
            }
        }
    ),
    tags={"pipeline": "manual"},
)

watchers_pipeline = define_asset_job(
    name="watchers_pipeline",
    description="Process URLs from monitoring_list.txt via watchers: discovery → bronze → silver → summary",
    selection=AssetSelection.assets(
        "discovered_urls",
        "bronze_html",
        "bronze_youtube_download",
        "bronze_youtube_transcription",
        "bronze_discussions",
        "silver_article_summary",
        "silver_discussion_summary",
        "silver_summary",
    ),
    config=RunConfig(
        ops={
            "discovered_urls": {
                "config": {
                    "source_type": "watchers",
                }
            }
        }
    ),
    tags={"pipeline": "watchers"},
)
