from dagster import ScheduleDefinition

from dagster_project.jobs.pipelines import watchers_pipeline

monitoring_schedule = ScheduleDefinition(
    name="monitoring_schedule",
    cron_schedule="0 */6 * * *",
    job=watchers_pipeline,
    description="Run watchers pipeline every 6 hours (discovery → download → extract → summarize)",
)
