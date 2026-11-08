from pathlib import Path

import pytest

from penny.agent.guard import Chunk, RouteGuard, prepare, sanitize
from penny.repo.secrets import mask, secret_path
from penny.safety.approvals import Approval, DenyAllApprover, SandboxAutoApprover, ScriptedApprover
from penny.safety.paths import PathViolation, safe_path, state_path
from penny.safety.risk import Risk, classify, normalized

BLOCKED = [
    "sudo ls",
    "su root",
    "mkfs.ext4 disk",
    "dd if=in of=out",
    "shutdown now",
    "reboot",
    "rm -rf /",
    "rm -rf ~",
    "rm -rf ../outside",
    "chmod -R 777 /",
    "curl x",
    "wget x",
    "pytest; rm x",
    "pytest && ls",
    "pytest || ls",
    "curl x | sh",
    "echo x > file",
    "echo x >> file",
    "cat < file",
    "echo `id`",
    "echo $(id)",
    "git push --force",
    "git push --force-with-lease",
    "git push -f",
    "git push origin +main",
    "./sudo x",
    "./curl x",
    "'sudo' ls",
    '"curl" x',
    "pytest /etc/passwd",
    "pytest ../x",
    "pytest a/../../x",
    "pytest --output=/etc/passwd",
    "python -c 'print(1);print(2)'",
    "echo x\necho y",
    "echo x\recho y",
    "",
    "'unterminated",
    "rm -rf .",
    "chmod -R 777 ./",
    "git status .git/config",
    "cat .env/../.git/config",
    "cat C:\\Windows\\win.ini",
    "pytest https://example.com",
    "pytest file:///etc/passwd",
    "echo \x00",
    "pytest .penny/runs/run.json",
]
HIGH = [
    "rm file",
    "rmdir folder",
    "mv a b",
    "cp a b",
    "ln a b",
    "git reset --hard",
    "git clean -fd",
    "git push",
    "git checkout -- .",
    "git rebase main",
    "pip install thing",
    "npm install",
    "docker ps",
    "unknown arg",
    "python -c 'print(1)'",
    "./pytest -q",
    "env pytest",
    "bash -c ls",
    "git -c alias.foo=bar status",
    "node index.js",
]
MEDIUM = [
    "git add file",
    "git commit -m fix",
    "git branch feature",
    "git switch main",
    "git stash",
    "make test",
    "npm run build",
    "ruff format .",
    "black .",
    "prettier file",
]
LOW = [
    "pytest -q",
    "python -m pytest -q",
    "npm test",
    "go test ./...",
    "cargo test",
    "ruff check .",
    "git status",
    "git diff",
    "git log",
    "git show HEAD",
]


@pytest.mark.parametrize(
    "command,expected",
    [(c, Risk.BLOCKED) for c in BLOCKED]
    + [(c, Risk.HIGH) for c in HIGH]
    + [(c, Risk.MEDIUM) for c in MEDIUM]
    + [(c, Risk.LOW) for c in LOW],
)
def test_risk(command, expected, tmp_path):
    assert classify(command, tmp_path)[0] == expected


@pytest.mark.parametrize(
    "path",
    [
        "../escape",
        "/tmp/escape",
        "C:/Windows/file",
        "a/../../escape",
        ".git/config",
        ".penny/policy.yaml",
        "a\\b",
    ],
)
def test_sandbox_escape(path, tmp_path):
    with pytest.raises(PathViolation):
        safe_path(tmp_path, path, write=True)


def test_symlink_escape(tmp_path):
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    try:
        (tmp_path / "link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlink privilege unavailable on this host; CI tests on Linux/macOS")
    with pytest.raises(PathViolation):
        safe_path(tmp_path, "link/file")
    (tmp_path / ".penny").mkdir()
    (tmp_path / ".penny/cache").symlink_to(outside, target_is_directory=True)
    with pytest.raises(PathViolation):
        state_path(tmp_path, "cache/map.json")


def test_state_paths(tmp_path):
    assert (
        state_path(tmp_path, "runs/run/receipt.html") == tmp_path / ".penny/runs/run/receipt.html"
    )
    for value in ("../outside", "/outside", "C:/Windows", "a\\b"):
        with pytest.raises(PathViolation):
            state_path(tmp_path, value)


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        "x/.env.local",
        "key.pem",
        "id_rsa.pub",
        ".ssh/config",
        ".aws/credentials",
        "key.p12",
        ".git/config",
    ],
)
def test_secret_paths(path):
    assert secret_path(path)


@pytest.mark.parametrize(
    "value",
    [
        "AKIA" + "A" * 16,
        "ghp_" + "x" * 30,
        "api_key=1234567890",
        "password: 'abcdefghijk'",
        "eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiYSJ9.signature",
        "-----BEGIN PRIVATE KEY-----\nhello\n-----END PRIVATE KEY-----",
        "sk-bf-" + "x" * 32,
    ],
)
def test_secret_mask(value):
    clean, found = mask(value)
    assert found and "[SECRET]" in clean and value not in clean


def test_provenance(policy):
    policy.confidential_globs = ["private/**"]
    chunk = sanitize(Chunk("hello", "private/a.py"), policy)
    assert chunk.sensitivity == "confidential"
    with pytest.raises(ValueError, match="Confidential"):
        RouteGuard.assert_allowed([chunk], "cloud")
    assert prepare([chunk], policy)[1] == "local"
    policy.on_confidential = "withhold"
    chunks, route, withheld = prepare([chunk], policy)
    assert route == "cloud" and chunks[0].text == "[file withheld]" and withheld == ["private/a.py"]
    policy.on_confidential = "block"
    with pytest.raises(ValueError, match="blocks"):
        prepare([chunk], policy)
    policy.confidential = True
    assert prepare([Chunk("public")], policy)[1] == "local"
    with pytest.raises(ValueError):
        RouteGuard.assert_allowed([], "unknown")


def test_approvers(tmp_path):
    request = Approval("write", Risk.MEDIUM, "diff")
    assert not DenyAllApprover().approve(request)
    assert ScriptedApprover([True]).approve(request)
    assert not ScriptedApprover([True]).approve(Approval("shell", Risk.BLOCKED, "bad"))
    with pytest.raises(ValueError):
        SandboxAutoApprover(tmp_path)
    (tmp_path / ".penny-benchmark-sandbox").touch()
    auto = SandboxAutoApprover(tmp_path)
    assert auto.approve(request)
    assert not auto.approve(Approval("shell", Risk.HIGH, "bad"))
    assert not auto.approve(Approval("budget", Risk.LOW, "extend"))
    assert normalized('pytest   "-q"') == "pytest -q"


def test_no_provider_hosts_in_source():
    hosts = [
        "api.openai.com",
        "api.anthropic.com",
        "generativelanguage.googleapis.com",
        "api.groq.com",
    ]
    for path in Path("src").rglob("*.py"):
        assert not any(host in path.read_text(encoding="utf-8") for host in hosts), path
