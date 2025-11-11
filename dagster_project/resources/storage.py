import json
from pathlib import Path

from dagster import ConfigurableResource

from dagster_project.utils.tables import BronzeTable, SilverTable


class Storage(ConfigurableResource):
    base_dir: str

    def get_path(
        self,
        partition: BronzeTable | SilverTable,
        id: str,
        sub_partition: str | None = None,
        extension: str = ".json",
        create_dirs: bool = True,
    ) -> Path:
        filename = f"{id}{extension}"
        if sub_partition:
            path = Path(self.base_dir) / partition / sub_partition / filename
        else:
            path = Path(self.base_dir) / partition / filename

        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)

        return path

    def get_cache_path(self, cache_type: str, id: str, extension: str = ".txt") -> Path:
        """Get path for cache files outside bronze/silver layers"""
        cache_dir = Path(self.base_dir).parent / "cache" / cache_type
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"{id}{extension}"

    def save(self, partition: BronzeTable | SilverTable, id: str, data: dict, sub_partition: str | None = None) -> None:
        path = self.get_path(partition, id, sub_partition)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str))

    def load(self, partition: BronzeTable | SilverTable, id: str, sub_partition: str | None = None) -> dict:
        path = self.get_path(partition, id, sub_partition)
        return json.loads(path.read_text())

    def exists(self, partition: BronzeTable | SilverTable, id: str, sub_partition: str | None = None) -> bool:
        path = self.get_path(partition, id, sub_partition)
        return path.exists()
