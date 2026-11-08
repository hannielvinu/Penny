"""Literal search fallback for matches absent from symbol signatures."""

import json
import shutil
import subprocess

from penny.safety.paths import safe_path


def search_text(repo_map, query: str, limit: int = 8) -> list[dict]:
    paths = [f["path"] for f in repo_map.files]
    for path in paths:
        safe_path(repo_map.root, path)
    if not paths:
        return []
    if shutil.which("rg") and len(" ".join(paths)) < 16000:
        result = subprocess.run(
            [
                "rg",
                "--json",
                "--ignore-case",
                "--fixed-strings",
                "--max-count",
                str(limit),
                "--",
                query,
                *paths,
            ],
            cwd=repo_map.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            shell=False,
        )
        hits = []
        if result.returncode in {0, 1}:
            for line in result.stdout.splitlines():
                event = json.loads(line)
                if event["type"] == "match":
                    data = event["data"]
                    hits.append(
                        dict(
                            path=data["path"]["text"],
                            start_line=data["line_number"],
                            end_line=data["line_number"],
                            signature=data["lines"]["text"].strip()[:200],
                            name="text match",
                        )
                    )
                    if len(hits) >= limit:
                        break
            return hits
    hits = []
    for path in paths:
        for number, line in enumerate(repo_map.read(path).splitlines(), 1):
            if query.lower() in line.lower():
                hits.append(
                    dict(
                        path=path,
                        start_line=number,
                        end_line=number,
                        signature=line.strip()[:200],
                        name="text match",
                    )
                )
                if len(hits) >= limit:
                    return hits
    return hits
