import pytest

from penny.config import Settings
from penny.exec.gitops import git
from penny.policy import load_policy


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Test Developer")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    (tmp_path / ".gitignore").write_text(
        ".penny/\n__pycache__/\n.pytest_cache/\n.env\npricing.yaml\n", encoding="utf-8"
    )
    (tmp_path / "example.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "initial fixture")
    return tmp_path


@pytest.fixture
def policy(repo):
    return load_policy(repo)


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("PENNY_MOCK", "1")
    return Settings(_env_file=None)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Tests must use in-process transports. No accidental provider spend."""
    import socket

    def blocked(*args, **kwargs):
        raise AssertionError("Network access is disabled in the offline suite")

    monkeypatch.setattr(socket, "create_connection", blocked)
