import json
from pathlib import Path

from dagster import ConfigurableResource

from dagster_project.utils.tables import BronzeTable, SilverTable


class Storage(ConfigurableResource):
    base_dir: str

    def save(self, partition: BronzeTable | SilverTable, id: str, data: dict, sub_partition: str | None = None) -> None:
        if sub_partition:
            path = Path(self.base_dir) / partition / sub_partition / f"{id}.json"
        else:
            path = Path(self.base_dir) / partition / f"{id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str))

    def load(self, partition: BronzeTable | SilverTable, id: str, sub_partition: str | None = None) -> dict:
        if sub_partition:
            path = Path(self.base_dir) / partition / sub_partition / f"{id}.json"
        else:
            path = Path(self.base_dir) / partition / f"{id}.json"
        return json.loads(path.read_text())

    def exists(self, partition: BronzeTable | SilverTable, id: str, sub_partition: str | None = None) -> bool:
        if sub_partition:
            path = Path(self.base_dir) / partition / sub_partition / f"{id}.json"
        else:
            path = Path(self.base_dir) / partition / f"{id}.json"
        return path.exists()
