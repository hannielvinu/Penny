from pathlib import Path

import pathspec

from penny.repo.secrets import secret_path

DENIED = {
    ".git",
    ".penny",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "htmlcov",
}


class Ignore:
    def __init__(self, root: Path):
        self.root = root
        path = root / ".gitignore"
        self.spec = pathspec.GitIgnoreSpec.from_lines(
            path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
        )

    def excluded(self, relative: str) -> bool:
        return (
            bool(set(Path(relative).parts) & DENIED)
            or secret_path(relative)
            or self.spec.match_file(relative)
        )
