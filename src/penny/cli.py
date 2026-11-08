import json
import re
import shutil
import sys
import webbrowser
from pathlib import Path

import httpx
import typer
from rich.table import Table

from penny.agent.loop import run as agent_run
from penny.config import Settings
from penny.cost.estimate import tokens
from penny.cost.quote import quote as make_quote
from penny.exec.gitops import undo as undo_run
from penny.exec.tests_runner import detect
from penny.policy import example_policy, load_policy
from penny.pricing import load_pricing
from penny.repo.repomap import RepoMap
from penny.report.html import benchmark as benchmark_page
from penny.report.html import index
from penny.report.html import receipt as render_receipt
from penny.report.model import RunRecord
from penny.safety.approvals import Approval, DenyAllApprover, InteractiveApprover
from penny.safety.risk import Risk
from penny.ui.term import Terminal
from penny.version import __version__

app = typer.Typer(no_args_is_help=True, help="Penny — quote, approve, receipt.")
pricing_app = typer.Typer(help="Check user-maintained pricing.")
app.add_typer(pricing_app, name="pricing")
EXIT = dict(success=0, failed=1, gateway_error=3, budget_stopped=4, aborted=5, denied=5)


def fail(exc):
    typer.echo(f"Penny: {exc}", err=True)
    raise typer.Exit(2)


def root_path(repo: Path) -> Path:
    root = repo.resolve()
    if (root / ".penny").is_symlink():
        raise ValueError(".penny must not be a symlink")
    return root


def read_records(root: Path) -> list[RunRecord]:
    records = []
    for path in (root / ".penny/runs").glob("*/run.json"):
        records.append(RunRecord.model_validate_json(path.read_text(encoding="utf-8")))
    return records


def get_record(root: Path, run_id: str | None) -> RunRecord:
    if run_id and not re.fullmatch(r"[\w-]+", run_id):
        raise ValueError("Invalid run ID")
    records = read_records(root)
    matching = [r for r in records if run_id is None or r.id == run_id]
    if not matching:
        raise ValueError("No run found. Start with penny run.")
    return sorted(matching, key=lambda r: r.started_at)[-1]


@app.command()
def version():
    """Show the installed version."""
    typer.echo(f"Penny {__version__}")


@app.command()
def init(repo: Path = typer.Option(Path("."), help="Git repository root")):
    """Create a policy and ignore run metadata. Does not overwrite existing config."""
    try:
        root = root_path(repo)
        folder = root / ".penny"
        folder.mkdir(exist_ok=True)
        policy_path = folder / "policy.yaml"
        if not policy_path.exists():
            policy_path.write_text(example_policy(), encoding="utf-8")
        ignore = root / ".gitignore"
        text = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
        missing = [p for p in (".penny/", ".env", "pricing.yaml") if p not in text.splitlines()]
        if missing:
            ignore.write_text(text.rstrip() + "\n" + "\n".join(missing) + "\n", encoding="utf-8")
        load_policy(root)
        typer.echo(
            "Initialized .penny/policy.yaml. Set models, test command and budgets; commit .gitignore before running."
        )
    except (ValueError, OSError) as exc:
        fail(exc)


@app.command()
def doctor(repo: Path = Path("."), plain: bool = False):
    """Inspect environment and gateway, including a tiny local-key cloud isolation probe."""
    terminal = Terminal(plain)
    checks = []

    def add(name, status, detail):
        return checks.append((name, status, detail))

    try:
        root = root_path(repo)
        policy, settings = load_policy(root), Settings()
        add("Python", "PASS" if sys.version_info >= (3, 11) else "FAIL", sys.version.split()[0])
        add("Git", "PASS" if shutil.which("git") else "FAIL", "git executable")
        add(
            "ripgrep",
            "PASS" if shutil.which("rg") else "WARN",
            "BM25 and Python search work without rg",
        )
        add(
            "Tests",
            "PASS" if policy.test_command or detect(root) else "WARN",
            policy.test_command or detect(root) or "Set test_command",
        )
        for name, key in (
            ("Cloud key", settings.bifrost_vk_dev),
            ("Local key", settings.bifrost_vk_local),
        ):
            add(
                name,
                "PASS" if key.get_secret_value() else "WARN",
                "present" if key.get_secret_value() else "Run scripts/bootstrap_bifrost.py",
            )
        pricing = load_pricing(root)
        missing = [
            m for m in (policy.models.cheap, policy.models.strong) if pricing.cost(m, 1, 1) is None
        ]
        add(
            "Pricing",
            "WARN" if missing else "PASS",
            "price not configured: " + ", ".join(missing)
            if missing
            else "Configured with provenance; check dates manually",
        )
        if settings.penny_mock:
            add("Mode", "WARN", "MOCK MODE: gateway probes skipped")
        else:
            with httpx.Client(
                base_url=settings.bifrost_base_url, timeout=10, follow_redirects=False
            ) as client:
                try:
                    key = (
                        settings.bifrost_vk_local.get_secret_value()
                        or settings.bifrost_vk_dev.get_secret_value()
                    )
                    response = client.get("/v1/models", headers={"x-bf-vk": key})
                    add(
                        "Gateway",
                        "PASS" if response.is_success else "FAIL",
                        f"HTTP {response.status_code}",
                    )
                    local_key = settings.bifrost_vk_local.get_secret_value()
                    if response.is_success and local_key:
                        listed = [m["id"] for m in response.json().get("data", [])]
                        local_model = policy.models.local
                        add(
                            "Local model",
                            "PASS"
                            if local_model in listed or local_model.split("/", 1)[-1] in listed
                            else "WARN",
                            "Configured model appears in gateway listing"
                            if local_model in listed
                            else "Check Ollama model and provider reachability",
                        )
                        probe = client.post(
                            "/v1/chat/completions",
                            headers={"x-bf-vk": local_key},
                            json=dict(
                                model=policy.models.cheap,
                                messages=[dict(role="user", content="Reply OK")],
                                max_tokens=1,
                            ),
                        )
                        text = probe.text.lower()
                        rejected = probe.status_code in {400, 403} and any(
                            s in text
                            for s in ("not allowed", "not permitted", "access", "provider", "model")
                        )
                        add(
                            "Local key isolation",
                            "PASS" if rejected else "FAIL",
                            "Cloud model refused by gateway"
                            if rejected
                            else f"Isolation NOT proven (HTTP {probe.status_code}); inspect gateway configuration",
                        )
                    else:
                        add("Local key isolation", "WARN", "Not run: gateway/key unavailable")
                except (httpx.HTTPError, ValueError) as exc:
                    add(
                        "Gateway",
                        "FAIL",
                        f"{type(exc).__name__}: start `make up`; verify BIFROST_BASE_URL",
                    )
        table = Table("Check", "Result", "Detail")
        for row in checks:
            table.add_row(*row)
        terminal.console.print(table)
        if any(status == "FAIL" for _, status, _ in checks):
            raise typer.Exit(3)
    except (ValueError, OSError) as exc:
        fail(exc)


@app.command()
def quote(
    task: str,
    repo: Path = Path("."),
    private: bool = False,
    plain: bool = False,
    json_output: bool = typer.Option(False, "--json"),
):
    """Estimate a task without calling a model."""
    try:
        root = root_path(repo)
        policy, pricing = load_policy(root), load_pricing(root)
        repo_map = RepoMap(root).build()
        text = repo_map.compact(task, int(policy.limits.max_prompt_tokens * 0.35))
        model = policy.models.local if private or policy.confidential else policy.models.cheap
        Terminal(plain, json_output).emit(
            dict(
                event="quote",
                mock=Settings().penny_mock,
                quote=make_quote(repo_map, tokens(text), pricing, model),
                route="local" if private or policy.confidential else "cloud",
                budget=policy.limits.budget_usd,
            )
        )
    except (ValueError, OSError) as exc:
        fail(exc)


@app.command()
def run(
    task: str,
    repo: Path = Path("."),
    budget: float | None = None,
    private: bool = False,
    tier: str = "auto",
    max_steps: int | None = None,
    yes_quote: bool = False,
    non_interactive: bool = False,
    allow_dirty: bool = False,
    plain: bool = False,
    json_output: bool = typer.Option(False, "--json"),
):
    """Run a coding task; writes, shell and Git changes require approval."""
    terminal = Terminal(plain, json_output)
    try:
        root = root_path(repo)
        policy, pricing, settings = load_policy(root), load_pricing(root), Settings()
        if tier not in {"cheap", "strong", "auto"}:
            raise ValueError("--tier must be cheap, strong or auto")
        if budget is not None:
            policy.limits.budget_usd = budget
        if max_steps is not None:
            policy.limits.max_steps = max_steps
        policy.confidential |= private
        policy = type(policy).model_validate(policy.model_dump())
        if settings.penny_mock:
            terminal.console.print(
                "MOCK MODE — scripted test double; usage numbers are synthetic.",
                style="bold magenta",
            )
        if allow_dirty:
            terminal.console.print("WARNING: --allow-dirty enabled. Automatic undo is disabled.")
        approver = (
            DenyAllApprover()
            if non_interactive or json_output
            else InteractiveApprover(terminal.console)
        )
        record = agent_run(
            task,
            root,
            policy,
            pricing,
            settings,
            approver,
            yes_quote=yes_quote,
            allow_dirty=allow_dirty,
            tier=tier,
            emit=terminal.emit,
        )
        raise typer.Exit(EXIT[record.status])
    except (ValueError, OSError) as exc:
        fail(exc)


@pricing_app.command("check")
def pricing_check(repo: Path = Path(".")):
    """List configured model prices and missing entries."""
    try:
        root = root_path(repo)
        policy, pricing = load_policy(root), load_pricing(root)
        for model in dict.fromkeys(
            [
                policy.models.cheap,
                policy.models.strong,
                policy.models.local,
                *policy.models.fallbacks,
            ]
        ):
            label = (
                "local compute not priced"
                if model.startswith("ollama/")
                else "price not configured"
                if pricing.cost(model, 1, 1) is None
                else "configured; verify source and date"
            )
            typer.echo(f"{model}: {label}")
    except (ValueError, OSError) as exc:
        fail(exc)


@app.command()
def receipt(
    run_id: str | None = None,
    repo: Path = Path("."),
    open_browser: bool = typer.Option(False, "--open"),
):
    """Regenerate or open a stored receipt (latest by default)."""
    try:
        root = root_path(repo)
        record = get_record(root, run_id)
        path = root / ".penny/runs" / record.id / "receipt.html"
        path.write_text(render_receipt(record), encoding="utf-8")
        typer.echo(str(path))
        if open_browser:
            webbrowser.open(path.as_uri())
    except (ValueError, OSError) as exc:
        fail(exc)


@app.command()
def report(repo: Path = Path("."), open_browser: bool = typer.Option(False, "--open")):
    """Generate the local run ledger and benchmark page."""
    try:
        root = root_path(repo)
        folder = root / ".penny"
        folder.mkdir(exist_ok=True)
        path = folder / "index.html"
        path.write_text(index(read_records(root)), encoding="utf-8")
        results = sorted((root / "benchmark/results").glob("*.json"))
        latest = json.loads(results[-1].read_text(encoding="utf-8")) if results else None
        (folder / "benchmark.html").write_text(benchmark_page(latest), encoding="utf-8")
        typer.echo(str(path))
        if open_browser:
            webbrowser.open(path.as_uri())
    except (ValueError, OSError) as exc:
        fail(exc)


@app.command()
def undo(run_id: str | None = None, repo: Path = Path(".")):
    """Approve restoring a run's base branch; refuses subsequent work."""
    try:
        root = root_path(repo)
        record = get_record(root, run_id)
        if not record.branch:
            raise ValueError("This run did not create a branch")
        request = Approval(
            "git",
            Risk.HIGH,
            f"Restore {record.base_commit}, remove recorded new files, switch to {record.base_branch}, and delete {record.branch}.",
        )
        if not InteractiveApprover().approve(request):
            raise typer.Exit(5)
        undo_run(root, record.model_dump())
        typer.echo("Restored the recorded base branch.")
    except (ValueError, OSError) as exc:
        fail(exc)


@app.command()
def chaos(action: str = "status", mode: str = "503"):
    """Control the localhost chaos harness: on, off, status."""
    if action not in {"on", "off", "status"} or mode not in {"503", "429", "timeout"}:
        fail("Use on|off|status with --mode 503|429|timeout")
    try:
        with httpx.Client(base_url=Settings().chaos_proxy_url, timeout=5) as client:
            response = (
                client.get("/admin/mode")
                if action == "status"
                else client.post("/admin/mode", json={"mode": mode if action == "on" else "off"})
            )
            response.raise_for_status()
            typer.echo(json.dumps(response.json()))
    except httpx.HTTPError:
        fail("Chaos harness unavailable. Start it with make up.")


@app.command()
def bench(n: int = 3, repo: Path = Path("."), task: str | None = None):
    """Run the real pre-registered comparison (refuses MOCK)."""
    if Settings().penny_mock:
        fail("Benchmark refuses MOCK MODE. Configure a real Bifrost gateway.")
    script = root_path(repo) / "benchmark/run_benchmark.py"
    if not script.is_file():
        fail("Run penny bench from the Penny source checkout")
    import runpy

    runner = runpy.run_path(str(script))
    try:
        runner["run_benchmark"](root_path(repo), n=n, task_filter=task)
    except (ValueError, OSError) as exc:
        fail(exc)
