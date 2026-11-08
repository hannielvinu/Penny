from pathlib import Path


def detect(root: Path) -> str | None:
    if any(
        (root / item).exists() for item in ("pytest.ini", "pyproject.toml", "tests", "setup.py")
    ):
        return "python -m pytest -q"
    if (root / "package.json").is_file():
        return "npm test"
    if (root / "go.mod").is_file():
        return "go test ./..."
    if (root / "Cargo.toml").is_file():
        return "cargo test"
    return None
