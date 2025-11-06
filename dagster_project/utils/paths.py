import os
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).parent.parent.parent))

MANUAL_LINKS_FILE = PROJECT_ROOT / "manual_links.txt"
MONITORING_LINKS_FILE = PROJECT_ROOT / "monitoring_list.txt"
