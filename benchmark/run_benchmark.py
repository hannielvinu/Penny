"""Real-only, fresh-sandbox comparison runner with raw results and acceptance checks."""

import argparse
import fnmatch
import hashlib
import importlib.util
import json
import re
import shutil
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

import yaml

from penny.agent.context import Techniques
from penny.agent.loop import run
from penny.config import Settings
from penny.exec.gitops import git
from penny.exec.shell import execute
from penny.policy import load_policy
from penny.pricing import load_pricing
from penny.report.html import benchmark
from penny.safety.approvals import SandboxAutoApprover


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def fingerprints(root: Path) -> dict:
    paths = [
        root / "benchmark/tasks.yaml",
        root / "benchmark/baseline_agent.py",
        root / "benchmark/generate_sandbox.py",
    ]
    paths.extend(
        p
        for p in (root / "benchmark/sandbox_template").rglob("*")
        if p.is_file() and not any(x in {"__pycache__", ".pytest_cache"} for x in p.parts)
    )
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(paths)
    }


def inject(root: Path, task: dict):
    for patch in task["setup"]:
        path = root / patch["path"]
        text = path.read_text(encoding="utf-8")
        if patch["search"] not in text:
            raise ValueError(f"Setup no longer matches: {task['id']} / {patch['path']}")
        path.write_text(
            text.replace(patch["search"], patch["replace"], -1 if patch.get("all") else 1),
            encoding="utf-8",
        )


def initialize(root: Path):
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Hanniel Vinu")
    git(root, "config", "user.email", "hannielvinu@gmail.com")
    git(root, "add", ".")
    git(root, "commit", "-m", "test: prepare synthetic task")


def acceptance(root: Path, task: dict, before: dict) -> dict:
    changed = (
        git(root, "diff", "--name-only", before["_base_commit"]).splitlines()
        + git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    )
    allowed = task["allowed_files"]
    violations = [p for p in changed if not any(fnmatch.fnmatch(p, pattern) for pattern in allowed)]
    # Preserve acceptance tests except the specifically requested symbol rename.
    test_path = root / "tests/test_shopkit.py"
    if task["id"] == "rename_discount":
        original = (
            before["tests/test_shopkit.py"]
            .replace(
                "from shopkit.pricing.discounts import discounted_total as discount_total",
                "from shopkit.pricing.discounts import discounted_total",
            )
            .replace("discount_total", "discounted_total")
        )
        if test_path.read_text(encoding="utf-8") != original:
            violations.append("Acceptance test change differs from prescribed rename")
        for path in allowed:
            if re.search(r"\bdiscount_total\b", (root / path).read_text(encoding="utf-8")):
                violations.append("Old discount_total name remains in " + path)
    elif test_path.read_text(encoding="utf-8") != before["tests/test_shopkit.py"]:
        violations.append("Acceptance tests modified")
    result = execute(root, ["python", "-m", "pytest", "-q"])
    return dict(
        passed=result["returncode"] == 0 and not violations, violations=violations, test=result
    )


def summarize(runs: list[dict]) -> list[dict]:
    rows = []
    for task, agent in sorted({(r["task"], r["agent"]) for r in runs}):
        selected = [r for r in runs if (r["task"], r["agent"]) == (task, agent)]
        row = dict(
            task=task,
            agent=agent,
            n=len(selected),
            passed=sum(r["acceptance"]["passed"] for r in selected),
        )
        for key in ("tokens", "cost_usd", "steps", "wall_ms"):
            values = [
                (r["totals"]["tokens_in"] + r["totals"]["tokens_out"])
                if key == "tokens"
                else r["totals"].get(key)
                for r in selected
            ]
            if any(v is None for v in values):
                row[key] = None
                row[key + "_range"] = None
            else:
                row[key] = mean(values)
                row[key + "_range"] = [min(values), max(values)]
        rows.append(row)
    return rows


def write_reports(root: Path, result: dict):
    rows = [
        "| Task | Agent | Passed / N | Tokens mean (min–max) | Cost mean | Steps mean |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in result["summary"]:
        bounds = r["tokens_range"]
        cost = f"${r['cost_usd']:.6f}" if r["cost_usd"] is not None else "price not configured"
        rows.append(
            f"| {r['task']} | {r['agent']} | {r['passed']} / {r['n']} | {r['tokens']:.0f} ({bounds[0]}–{bounds[1]}) | {cost} | {r['steps']:.1f} |"
        )
    content = "\n".join(rows)
    doc = root / "docs/BENCHMARK.md"
    original = doc.read_text(encoding="utf-8") if doc.exists() else "# Benchmark\n\n"
    start, end = "<!-- RESULTS:START -->", "<!-- RESULTS:END -->"
    block = f"{start}\n\n{'SMALL SAMPLE' if result['small_sample'] else 'Registered sample'} · {result['date']} · commit `{result['commit']}`\n\n{content}\n\n{end}"
    if start in original and end in original:
        original = (
            original[: original.index(start)] + block + original[original.index(end) + len(end) :]
        )
    else:
        original += "\n" + block + "\n"
    doc.write_text(original, encoding="utf-8")
    readme = root / "README.md"
    text = readme.read_text(encoding="utf-8")
    if start in text and end in text:
        text = text[: text.index(start)] + block + text[text.index(end) + len(end) :]
        readme.write_text(text, encoding="utf-8")
    (root / "benchmark/results" / f"{result['id']}.html").write_text(
        benchmark(result), encoding="utf-8"
    )


def run_benchmark(root: Path, n=3, task_filter=None, ablate=None):
    settings = Settings()
    if settings.penny_mock:
        raise ValueError("Benchmark refuses MOCK MODE")
    if n < 1:
        raise ValueError("N must be positive")
    policy, pricing = load_policy(root), load_pricing(root)
    if not settings.bifrost_vk_dev.get_secret_value():
        raise ValueError("Configure BIFROST_VK_DEV before a real benchmark")
    tasks = yaml.safe_load((root / "benchmark/tasks.yaml").read_text(encoding="utf-8"))["tasks"]
    if task_filter:
        tasks = [t for t in tasks if t["id"] == task_filter]
        if not tasks:
            raise ValueError("Unknown task ID")
    result_dir = root / "benchmark/results"
    result_dir.mkdir(exist_ok=True)
    registration = fingerprints(root)
    for previous in result_dir.glob("*.json"):
        if json.loads(previous.read_text(encoding="utf-8"))["registration"] != registration:
            raise ValueError(
                "Pre-registration changed since a real run; document the change and move old results into a separate version before rerunning"
            )
    baseline = module(root / "benchmark/baseline_agent.py", "penny_baseline")
    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    raw_dir = result_dir / run_id
    raw_dir.mkdir()
    result = dict(
        id=run_id,
        date=datetime.now(UTC).isoformat(),
        commit=git(root, "rev-parse", "HEAD"),
        n=n,
        small_sample=n < 3 or len(tasks) < 8,
        models=policy.models.model_dump(),
        registration=registration,
        runs=[],
        summary=[],
    )
    techniques = Techniques()
    if ablate:
        if ablate not in asdict(techniques):
            raise ValueError("Unknown technique toggle")
        setattr(techniques, ablate, False)
    result["techniques"] = asdict(techniques)
    for task in tasks:
        for agent in ("penny", "baseline"):
            for repetition in range(n):
                with tempfile.TemporaryDirectory(prefix="penny-benchmark-") as folder:
                    sandbox = Path(folder)
                    shutil.copytree(
                        root / "benchmark/sandbox_template",
                        sandbox,
                        dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
                    )
                    (sandbox / ".penny-benchmark-sandbox").touch()
                    inject(sandbox, task)
                    initialize(sandbox)
                    before = {
                        "_base_commit": git(sandbox, "rev-parse", "HEAD"),
                        "tests/test_shopkit.py": (sandbox / "tests/test_shopkit.py").read_text(
                            encoding="utf-8"
                        ),
                    }
                    print(f"{task['id']} / {agent} / {repetition + 1}/{n}", flush=True)
                    if agent == "penny":
                        record = run(
                            task["prompt"],
                            sandbox,
                            policy.model_copy(deep=True),
                            pricing,
                            settings,
                            SandboxAutoApprover(sandbox),
                            techniques=techniques,
                        )
                        raw = record.model_dump()
                    else:
                        raw = baseline.run_baseline(
                            sandbox, task["prompt"], policy, pricing, settings
                        )
                    checked = acceptance(sandbox, task, before)
                    filename = f"{task['id']}-{agent}-{repetition + 1}.json"
                    (raw_dir / filename).write_text(
                        json.dumps(dict(run=raw, acceptance=checked), indent=2), encoding="utf-8"
                    )
                    item = dict(
                        task=task["id"],
                        agent=agent,
                        repetition=repetition + 1,
                        totals=raw["totals"],
                        status=raw["status"],
                        acceptance=checked,
                        raw=f"{run_id}/{filename}",
                    )
                    result["runs"].append(item)
                    result["summary"] = summarize(result["runs"])
                    (result_dir / f"{run_id}.json").write_text(
                        json.dumps(result, indent=2), encoding="utf-8"
                    )
    write_reports(root, result)
    print(f"Results: {result_dir / (run_id + '.json')}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--task")
    parser.add_argument("--ablate")
    args = parser.parse_args()
    run_benchmark(Path(__file__).resolve().parents[1], args.n, args.task, args.ablate)
