import difflib
import os
import tempfile
from pathlib import Path

from penny.repo.secrets import secret_path
from penny.safety.paths import safe_path


class PatchError(ValueError):
    pass


def preview(
    root: Path, path: str, edits: list[dict] | None = None, content: str | None = None
) -> tuple[Path, str, str]:
    target = safe_path(root, path, write=True)
    if secret_path(path):
        raise PatchError("Writes to secret paths are refused")
    if content is not None:
        if target.exists():
            raise PatchError("create_file refuses to overwrite existing files")
        old, new = "", content
    else:
        old = target.read_text(encoding="utf-8")
        new = old
        for edit in edits or []:
            search = edit["search"]
            if not search or new.count(search) != 1:
                near = difflib.get_close_matches(search, new.splitlines(), n=15, cutoff=0.2)
                raise PatchError(
                    "SEARCH must match exactly once. Nearby lines:\n" + "\n".join(near)
                )
            new = new.replace(search, edit["replace"], 1)
    diff = "".join(
        difflib.unified_diff(
            old.splitlines(True), new.splitlines(True), fromfile=f"a/{path}", tofile=f"b/{path}"
        )
    )
    return target, new, diff


def atomic_write(target: Path, text: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = target.stat().st_mode if target.exists() else None
    fd, name = tempfile.mkstemp(prefix=".penny-write-", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        if mode is not None:
            os.chmod(name, mode)
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)
