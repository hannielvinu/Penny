import shlex
from enum import StrEnum
from pathlib import Path, PureWindowsPath


class Risk(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCKED = "BLOCKED"


def argv(command: str | list[str]) -> list[str]:
    return shlex.split(command) if isinstance(command, str) else command


def classify(command: str | list[str], root: Path) -> tuple[Risk, str]:
    raw = command if isinstance(command, str) else " ".join(command)
    if any(op in raw for op in (";", "&", "|", ">", "<", "`", "$(", "\n", "\r", "\x00")):
        return Risk.BLOCKED, "Shell operators and substitutions are blocked"
    try:
        args = argv(command)
    except ValueError:
        return Risk.BLOCKED, "Malformed command"
    if not args:
        return Risk.BLOCKED, "Empty command"
    exe = args[0].replace("\\", "/").split("/")[-1].lower().removesuffix(".exe")
    root = root.resolve()
    for item in args:
        value = item.split("=", 1)[-1] if "=" in item else item
        if value.startswith(("~", "file:", "http:", "https:")):
            return Risk.BLOCKED, "External path or URL"
        if value.startswith("-"):
            continue
        if PureWindowsPath(value).drive or "\\" in value:
            return Risk.BLOCKED, "External or ambiguous path"
        if "/" in value or value in {"..", ".git", ".penny"}:
            path = (root / value).resolve()
            if not path.is_relative_to(root) or any(
                p in {".git", ".penny"} for p in path.relative_to(root).parts
            ):
                return Risk.BLOCKED, "Argument escapes the repository or targets metadata"
    if exe in {"sudo", "su", "shutdown", "reboot", "curl", "wget"} or exe.startswith("mkfs"):
        return Risk.BLOCKED, "Forbidden executable"
    if exe == "dd" and any(x.startswith("of=") for x in args):
        return Risk.BLOCKED, "Raw disk write"
    if (
        exe == "git"
        and "push" in args
        and any(x.startswith("--force") or x == "-f" or x.startswith("+") for x in args[2:])
    ):
        return Risk.BLOCKED, "Force push"
    if exe in {"rm", "chmod"} and any(x in {"/", "~", ".", "./"} for x in args[1:]):
        return Risk.BLOCKED, "Root-like target"
    if exe in {"rm", "rmdir", "mv", "cp", "ln", "docker", "chmod"}:
        return Risk.HIGH, "Destructive or broad filesystem capability"
    # Executable paths can conceal a different program with an allow-listed name.
    if args[0] != exe:
        return Risk.HIGH, "Executable path requires review"
    if exe == "git":
        if any(x.startswith("-") for x in args[1:2]):
            return Risk.HIGH, "Git global options require review"
        op = args[1] if len(args) > 1 else ""
        if op in {"status", "diff", "log", "show"} and not any(
            x.startswith(("--ext-diff", "--output", "--exec")) for x in args
        ):
            return Risk.LOW, "Read-only Git"
        if op in {"add", "commit", "branch", "switch", "stash"}:
            return Risk.MEDIUM, "Git state change"
        return Risk.HIGH, "Git operation requires review"
    if exe in {"pytest"} or (exe == "python" and args[1:3] == ["-m", "pytest"]):
        # Pytest executes repository code, even when classified LOW.
        return Risk.LOW, "Test runner executes repository code"
    if (exe, args[1:2]) in [("npm", ["test"]), ("go", ["test"]), ("cargo", ["test"])]:
        return Risk.LOW, "Test runner"
    if exe == "ruff" and args[1:2] == ["check"] and not any(x.startswith("--fix") for x in args):
        return Risk.LOW, "Read-only lint"
    if (
        exe in {"make", "black", "prettier"}
        or (exe == "ruff" and "format" in args)
        or (exe == "npm" and "run" in args)
    ):
        return Risk.MEDIUM, "Build or formatter may write files"
    return Risk.HIGH, "Unknown executable or arbitrary code execution"


def normalized(command: str | list[str]) -> str:
    return shlex.join(argv(command))
