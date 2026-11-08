from pathlib import Path, PureWindowsPath


class PathViolation(ValueError):
    pass


def state_path(root: Path, relative: str = "") -> Path:
    """Internal state access: no symlink components or parent traversal."""
    root = root.resolve()
    part = Path(relative)
    if (
        part.is_absolute()
        or relative.startswith("/")
        or PureWindowsPath(relative).drive
        or ".." in part.parts
        or "\\" in relative
    ):
        raise PathViolation("Invalid internal state path")
    target = root / ".penny" / part
    cursor = root
    for name in target.relative_to(root).parts:
        cursor = cursor / name
        if cursor.is_symlink():
            raise PathViolation("Internal state must not contain symlinks")
    if not target.resolve().is_relative_to(root):
        raise PathViolation("Internal state escapes repository")
    return target


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
