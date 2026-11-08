import json

import pytest

from penny.exec.gitops import branch_name, git, preflight, undo
from penny.exec.patch import PatchError, atomic_write, preview
from penny.exec.shell import execute
from penny.exec.trim import trim
from penny.repo.bm25 import rank
from penny.repo.repomap import RepoMap
from penny.repo.slices import Slices


def test_map_cache_and_search(repo):
    (repo / "client.ts").write_text("export function request() {\n return 1;\n}\n")
    (repo / ".env").write_text("secret")
    (repo / "binary.bin").write_bytes(b"\x00\xff")
    (repo / "huge.txt").write_text("x" * 300001)
    m = RepoMap(repo).build()
    assert {f["path"] for f in m.files} == {".gitignore", "example.py", "client.ts"}
    assert m.search("add")[0]["name"] == "add"
    assert m.search("request")[0]["path"] == "client.ts"
    before = json.dumps(m.files)
    assert json.dumps(m.build().files) == before
    assert "def add" in m.compact("add", 100)
    slices = Slices(m)
    assert "return a + b" in slices.symbol("example.py", "add", 1)
    assert "already provided" in slices.symbol("example.py", "add", 2)
    (repo / "example.py").write_text("def add(a, b):\n    return a - b\n")
    assert "a - b" in slices.symbol("example.py", "add", 3)
    with pytest.raises(ValueError):
        slices.lines("example.py", 1, 200)
    with pytest.raises(ValueError):
        m.read(".env")
    assert rank("tax", ["shipping parcel", "calculate tax total"])[0][0] == 1


def test_patch_unique_atomic(repo):
    path, new, diff = preview(repo, "example.py", [{"search": "a + b", "replace": "a - b"}])
    assert "+    return a - b" in diff
    atomic_write(path, new)
    assert "a - b" in path.read_text()
    with pytest.raises(PatchError):
        preview(repo, "example.py", [{"search": "missing", "replace": "x"}])
    with pytest.raises(PatchError):
        preview(repo, "example.py", [{"search": "a", "replace": "x"}])
    with pytest.raises(PatchError):
        preview(repo, "example.py", content="overwrite")
    with pytest.raises(PatchError):
        preview(repo, ".env", content="secret")


def test_atomic_replace_failure_preserves_original(repo, monkeypatch):
    path = repo / "example.py"
    original = path.read_text()

    def failed(*args):
        raise OSError("simulated filesystem refusal")

    monkeypatch.setattr("penny.exec.patch.os.replace", failed)
    with pytest.raises(OSError):
        atomic_write(path, "new contents")
    assert path.read_text() == original
    assert not list(repo.glob(".penny-write-*"))


def test_trim_and_shell(repo):
    output = (
        "noise\n" * 2000 + "FAILED test_tax - AssertionError\nE assert 1 == 2\n=== 1 failed ==="
    )
    result = trim(output)
    assert "FAILED test_tax" in result and "1 failed" in result and len(result) <= 4800
    assert trim("small") == "small"
    with pytest.raises(ValueError, match="BLOCKED"):
        execute(repo, "curl example.com")
    assert execute(repo, ["python", "-c", "print(42)"])["output"].strip() == "42"


def test_git_preflight_undo(repo):
    base, branch = preflight(repo)
    name = branch_name("Test task", "20260101-010101", "penny/")
    git(repo, "switch", "-c", name)
    (repo / "example.py").write_text("fixed\n")
    record = dict(
        base_commit=base,
        base_branch=branch,
        branch=name,
        final_diff=git(repo, "diff", "HEAD", "--no-ext-diff"),
        created_files=[],
    )
    undo(repo, record)
    assert git(repo, "branch", "--show-current") == "main"
    assert "return a + b" in (repo / "example.py").read_text()
    with pytest.raises(ValueError):
        undo(repo, {**record, "allow_dirty": True})
    (repo / "new").touch()
    with pytest.raises(ValueError, match="dirty"):
        preflight(repo)
