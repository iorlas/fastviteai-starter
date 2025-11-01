from dagster import ScheduleDefinition

from dagster_project.jobs.monitoring_pipeline import monitoring_pipeline_job

# Schedule to run monitoring pipeline every 6 hours
# Cron format: minute hour day month day_of_week
# "0 */6 * * *" = at minute 0 of every 6th hour
monitoring_schedule = ScheduleDefinition(
    name="monitoring_schedule",
    cron_schedule="0 */6 * * *",
    job=monitoring_pipeline_job,
    description="Run monitoring pipeline every 6 hours to process monitoring_list.txt",
)
