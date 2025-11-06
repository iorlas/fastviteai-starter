import json
from pathlib import Path

from dagster import ConfigurableResource


class Storage(ConfigurableResource):
    base_dir: str

    def save(self, partition: str, id: str, data: dict) -> None:
        path = Path(self.base_dir) / partition / f"{id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str))

    def load(self, partition: str, id: str) -> dict:
        path = Path(self.base_dir) / partition / f"{id}.json"
        return json.loads(path.read_text())

    def exists(self, partition: str, id: str) -> bool:
        return (Path(self.base_dir) / partition / f"{id}.json").exists()
