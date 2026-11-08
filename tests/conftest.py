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


def pytest_addoption(parser):
    parser.addoption("--real", action="store_true", help="Enable explicit live-gateway tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--real"):
        for item in items:
            if "real" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="Live tests require --real"))


@pytest.fixture(autouse=True)
def no_network(monkeypatch, request):
    """Tests must use in-process transports. No accidental provider spend."""
    import socket

    if request.node.get_closest_marker("real") and request.config.getoption("--real"):
        return

    def blocked(*args, **kwargs):
        raise AssertionError("Network access is disabled in the offline suite")

    monkeypatch.setattr(socket, "create_connection", blocked)
