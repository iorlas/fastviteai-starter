from dagster import Definitions, load_assets_from_modules

from dagster_project import assets  # noqa: TID252
from dagster_project.resources import openrouter_resource

all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
    resources={
        "openrouter": openrouter_resource,
    },
)
