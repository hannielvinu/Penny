import re
import subprocess
from pathlib import Path


def git(root: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "--no-pager", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        shell=False,
    )
    if check and result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def preflight(root: Path, allow_dirty: bool = False) -> tuple[str, str]:
    top = Path(git(root, "rev-parse", "--show-toplevel")).resolve()
    if top != root.resolve():
        raise ValueError("--repo must be the Git repository root")
    base = git(root, "rev-parse", "HEAD")
    if git(root, "status", "--porcelain") and not allow_dirty:
        raise ValueError(
            "Working tree is dirty. Commit/stash changes or explicitly use --allow-dirty"
        )
    return base, git(root, "symbolic-ref", "--short", "HEAD", check=False) or base


def branch_name(task: str, stamp: str, prefix: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", task.lower()).strip("-")[:36] or "task"
    value = f"{prefix}{slug}-{stamp}"
    if not re.fullmatch(r"[a-zA-Z0-9/_-]+", value) or ".." in value:
        raise ValueError("Invalid branch prefix")
    return value


def undo(root: Path, record: dict) -> None:
    if record.get("allow_dirty"):
        raise ValueError("Automatic undo is disabled for runs started with --allow-dirty")
    if git(root, "rev-parse", "HEAD") != record["base_commit"]:
        raise ValueError("New commits exist; inspect manually before undo")
    if git(root, "branch", "--show-current") != record["branch"]:
        raise ValueError("Switch to the recorded run branch before undo")
    # Refuse to discard changes made after the recorded run.
    current = git(root, "diff", "HEAD", "--no-ext-diff")
    if current != record.get("final_diff", ""):
        raise ValueError("Working tree changed since run; preserve it before undo")
    untracked = git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    if sorted(untracked) != sorted(record.get("created_files", [])):
        raise ValueError("Untracked files changed since run")
    from penny.safety.paths import safe_path

    for path in untracked:
        safe_path(root, path, write=True).unlink()
    git(root, "reset", "--hard", record["base_commit"])
    git(root, "switch", record["base_branch"])
    git(root, "branch", "-D", record["branch"])
