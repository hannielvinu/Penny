import hashlib
import json
import os
from pathlib import Path

from penny.cost.estimate import tokens
from penny.repo import symbols_generic, symbols_py
from penny.repo.bm25 import rank
from penny.repo.ignore import Ignore
from penny.safety.paths import safe_path


class RepoMap:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.ignore = Ignore(self.root)
        self.files: list[dict] = []

    def build(self):
        cache_path = self.root / ".penny/cache/repomap.json"
        try:
            cached = {f["path"]: f for f in json.loads(cache_path.read_text(encoding="utf-8"))}
        except (OSError, ValueError, TypeError):
            cached = {}
        self.files = []
        for directory, dirs, names in os.walk(self.root, followlinks=False):
            dirs[:] = sorted(
                d
                for d in dirs
                if not self.ignore.excluded(
                    (Path(directory) / d).relative_to(self.root).as_posix() + "/"
                )
                and not (Path(directory) / d).is_symlink()
            )
            for name in sorted(names):
                path = Path(directory) / name
                relative = path.relative_to(self.root).as_posix()
                if self.ignore.excluded(relative) or path.is_symlink():
                    continue
                try:
                    if path.stat().st_size > 300000:
                        continue
                    data = path.read_bytes()
                    if b"\x00" in data:
                        continue
                    text = data.decode("utf-8")
                except (OSError, UnicodeError):
                    continue
                digest = hashlib.sha1(data).hexdigest()
                if relative in cached and cached[relative]["sha1"] == digest:
                    self.files.append(cached[relative])
                    continue
                language = path.suffix.lstrip(".") or "text"
                extractor = symbols_py.extract if language == "py" else symbols_generic.extract
                self.files.append(
                    dict(path=relative, language=language, sha1=digest, symbols=extractor(text))
                )
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(self.files), encoding="utf-8")
        return self

    def search(self, query: str, limit: int = 8) -> list[dict]:
        entries = []
        for file in self.files:
            for symbol in file["symbols"] or [
                dict(name="(file)", signature="", start_line=1, end_line=1, docstring_first_line="")
            ]:
                entries.append(dict(path=file["path"], **symbol))
        documents = [" ".join(str(v) for v in entry.values()) for entry in entries]
        return [entries[i] for i, score in rank(query, documents)[:limit] if score > 0]

    def compact(self, query: str, cap: int) -> str:
        documents = [
            f["path"] + " " + " ".join(s["signature"] for s in f["symbols"]) for f in self.files
        ]
        selected = []
        for i, _ in rank(query, documents):
            line = documents[i]
            if tokens("\n".join(selected + [line])) <= cap:
                selected.append(line)
        return "\n".join(selected)

    def read(self, relative: str) -> str:
        if self.ignore.excluded(relative):
            raise ValueError("File is ignored or on the secret denylist")
        path = safe_path(self.root, relative)
        if path.stat().st_size > 300000:
            raise ValueError("File exceeds 300 KB")
        data = path.read_bytes()
        if b"\x00" in data:
            raise ValueError("Binary file")
        return data.decode("utf-8")
