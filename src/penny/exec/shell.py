import os
import subprocess
import sys
import time
from pathlib import Path

from penny.safety.risk import Risk, argv, classify


def execute(root: Path, command: str | list[str], timeout: float = 120) -> dict:
    risk, reason = classify(command, root)
    if risk == Risk.BLOCKED:
        raise ValueError(f"BLOCKED: {reason}")
    args = argv(command)
    if args[0] == "python":
        args[0] = sys.executable
    started = time.monotonic()
    # Do not pass gateway/provider credentials to repository tests or subprocesses.
    env = {
        k: v
        for k, v in os.environ.items()
        if not any(s in k.upper() for s in ("KEY", "TOKEN", "SECRET", "PASSWORD", "BIFROST"))
    }
    try:
        result = subprocess.run(
            args,
            cwd=root,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(0.1, timeout),
            shell=False,
        )
        code, output = result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired as exc:
        code = 124
        output = "Command timed out\n" + (
            exc.stdout.decode(errors="replace")
            if isinstance(exc.stdout, bytes)
            else exc.stdout or ""
        )
    return dict(
        command=command,
        returncode=code,
        output=output,
        wall_ms=int((time.monotonic() - started) * 1000),
    )
