import subprocess

from penny.exec.gitops import git


def test_git_survives_env_config_triplets(tmp_path, monkeypatch):
    """GIT_CONFIG_COUNT without its KEY_n entries makes git exit; Penny must drop all three."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.autocrlf")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "false")
    assert git(tmp_path, "rev-parse", "--is-inside-work-tree") == "true"
