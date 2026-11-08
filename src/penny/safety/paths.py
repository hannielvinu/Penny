from pathlib import Path, PureWindowsPath


class PathViolation(ValueError):
    pass


def safe_path(root: Path, value: str, *, write: bool = False) -> Path:
    root = root.resolve()
    candidate = Path(value)
    if candidate.is_absolute() or PureWindowsPath(value).is_absolute() or "\\" in value:
        raise PathViolation("Use a repository-relative path with forward slashes")
    target = (root / candidate).resolve()
    if not target.is_relative_to(root):
        raise PathViolation("Path escapes repository (including symlinks)")
    parts = target.relative_to(root).parts
    if any(p.lower() in {".git", ".penny"} for p in parts):
        raise PathViolation("Repository metadata is not available to model tools")
    return target
