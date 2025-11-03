import structlog
from dagster import (
    AssetKey,
    DefaultSensorStatus,
    RunRequest,
    SensorEvaluationContext,
    SkipReason,
    sensor,
)

from dagster_project.partitions import url_partitions

logger = structlog.get_logger()


@sensor(
    name="auto_process_new_urls",
    description="Auto-process unmaterialized URL partitions",
    minimum_interval_seconds=30,
    default_status=DefaultSensorStatus.RUNNING,
)
def discover_and_process_sensor(context: SensorEvaluationContext):
    """Sensor that processes unmaterialized URL partitions.

    Checks for partitions that haven't been materialized yet and submits runs.
    """
    all_partitions = context.instance.get_dynamic_partitions(url_partitions.name)

    if not all_partitions:
        return SkipReason("No URL partitions exist yet")

    asset_keys = [
        AssetKey("bronze_raw_html"),
        AssetKey("silver_extracted_content"),
        AssetKey("silver_summary"),
    ]

    records = context.instance.fetch_materializations(
        AssetKey("silver_summary"),
        limit=1000,
    )

    materialized_partitions = {
        r.event_log_entry.dagster_event.partition
        for r in records.records
        if r.event_log_entry.dagster_event and r.event_log_entry.dagster_event.partition
    }

    unmaterialized = [p for p in all_partitions if p not in materialized_partitions]

    if not unmaterialized:
        return SkipReason(f"All {len(all_partitions)} partitions already processed")

    run_requests = []
    for partition_key in unmaterialized:
        run_requests.append(
            RunRequest(
                run_key=f"process_{partition_key}",
                partition_key=partition_key,
                asset_selection=asset_keys,
                tags={
                    "sensor": "auto_process_new_urls",
                    "url_hash": partition_key,
                },
            )
        )

    logger.info(
        "sensor.processing_unmaterialized",
        unmaterialized_count=len(unmaterialized),
        total_partitions=len(all_partitions),
    )

    return run_requests
