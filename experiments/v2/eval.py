import json
import sys
from pathlib import Path

import structlog

log = structlog.get_logger()


def append_evaluation(run_file: Path) -> None:
    if not run_file.exists():
        log.error("file_not_found", path=str(run_file))
        sys.exit(1)

    with open(run_file) as f:
        data = json.load(f)

    if data.get("evaluation") is not None:
        log.warning("evaluation_exists", path=str(run_file))

    log.info("paste_evaluation", instruction="Paste evaluation JSON (Ctrl+D when done):")
    eval_text = sys.stdin.read()

    try:
        evaluation = json.loads(eval_text)
    except json.JSONDecodeError as e:
        log.error("invalid_json", error=str(e))
        sys.exit(1)

    data["evaluation"] = evaluation

    with open(run_file, "w") as f:
        json.dump(data, f, indent=2)

    log.info("evaluation_appended", path=str(run_file))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        log.error("usage", command="python eval.py <run_file>")
        sys.exit(1)

    append_evaluation(Path(sys.argv[1]))
