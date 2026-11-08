"""Run the pagination vertical slice in a disposable synthetic repository.

--mock uses scripted approvals and fake LLM usage for reproducible UI development.
Without --mock a real Bifrost model and interactive approvals are required.
The repository is retained in the OS temporary directory for inspection/undo.
"""

import argparse
import shutil
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from penny.agent.loop import run
from penny.config import Settings
from penny.exec.gitops import git
from penny.policy import load_policy
from penny.pricing import load_pricing
from penny.safety.approvals import InteractiveApprover, ScriptedApprover
from penny.ui.term import Terminal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")
    sandbox = Path(tempfile.mkdtemp(prefix="penny-demo-"))
    shutil.copytree(
        root / "benchmark/sandbox_template",
        sandbox,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
    )
    path = sandbox / "shopkit/utils/pagination.py"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "start = (page - 1) * page_size", "start = page * page_size"
        ),
        encoding="utf-8",
    )
    for command in [
        ("init", "-b", "main"),
        ("config", "user.name", "Hanniel Vinu"),
        ("config", "user.email", "hannielvinu@gmail.com"),
        ("add", "."),
        ("commit", "-m", "test: prepare synthetic pagination task"),
    ]:
        git(sandbox, *command)
    settings = Settings(penny_mock=args.mock)
    terminal = Terminal()
    if args.mock:
        terminal.console.print(
            "MOCK MODE — scripted actions and approvals; synthetic model usage.",
            style="bold magenta",
        )
    record = run(
        "Fix the one-based pagination bug; run all tests.",
        sandbox,
        load_policy(root),
        load_pricing(root),
        settings,
        ScriptedApprover([True, True, True])
        if args.mock
        else InteractiveApprover(terminal.console),
        emit=terminal.emit,
    )
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        label = "MOCK" if args.mock else "REAL"
        for name in ("run.json", "receipt.html"):
            shutil.copyfile(
                sandbox / ".penny/runs" / record.id / name, args.output / f"{label}-{name}"
            )
    print(f"Synthetic demo repository retained at: {sandbox}")
    raise SystemExit(0 if record.status == "success" else 1)


if __name__ == "__main__":
    main()
