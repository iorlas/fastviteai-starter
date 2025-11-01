"""Dagster schedules for the link processing pipeline."""

from dagster_project.schedules.monitoring_schedule import monitoring_schedule

__all__ = [
    "monitoring_schedule",
]
