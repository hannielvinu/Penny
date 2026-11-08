import json
from pathlib import Path


def bucket(files: int) -> str:
    return "small" if files < 20 else "medium" if files < 100 else "large"


def read_history(root: Path, files: int) -> list[dict]:
    try:
        values = [
            json.loads(s)
            for s in (root / ".penny/history.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        return [v for v in values if v.get("bucket") == bucket(files) and not v.get("mock")]
    except (OSError, ValueError):
        return []


def append_history(root: Path, files: int, record: dict):
    if record["flags"]["mock"]:
        return
    with (root / ".penny/history.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(bucket=bucket(files), **record["totals"])) + "\n")
