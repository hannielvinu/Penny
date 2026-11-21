# ruff: noqa: I001  (sys.path must be extended before importing the benchmark module)
"""Run Penny's three reliability scenarios against a REAL Bifrost gateway.

  failover      chaos proxy returns 503 for the primary provider -> Bifrost falls back
  budget        a virtual key with a $0.001/day budget -> the gateway itself stops the run
  confidential  policy.confidential=true -> every model call goes to local Ollama only

Each scenario works on a throwaway sandbox copy of the synthetic shopkit repo with the
pagination bug injected, auto-approves only LOW/MEDIUM actions (SandboxAutoApprover), and
saves run.json + receipt.html under docs/live/<scenario>/. Nothing here is mocked: if a
scenario fails, the failure is what gets recorded.

Usage: python scripts/live_scenarios.py failover|budget|confidential
Requires .env with BIFROST_BASE_URL, BIFROST_VK_DEV, BIFROST_VK_LOCAL, BIFROST_VK_DEMO_TINY.
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv
from pydantic import SecretStr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmark"))

from penny.agent.loop import run  # noqa: E402
from penny.config import Settings  # noqa: E402
from penny.policy import Policy  # noqa: E402
from penny.pricing import load_pricing  # noqa: E402
from penny.report.html import receipt  # noqa: E402
from penny.safety.approvals import SandboxAutoApprover  # noqa: E402
from run_benchmark import initialize, inject  # noqa: E402

TASK_ID = "pagination"


def sandbox(folder: Path) -> Path:
    shutil.copytree(
        ROOT / "benchmark/sandbox_template",
        folder,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
    )
    (folder / ".penny-benchmark-sandbox").touch()
    tasks = yaml.safe_load((ROOT / "benchmark/tasks.yaml").read_text(encoding="utf-8"))["tasks"]
    task = next(t for t in tasks if t["id"] == TASK_ID)
    inject(folder, task)
    initialize(folder)
    return folder, task


def chaos(mode: str, settings: Settings):
    with httpx.Client(base_url=settings.chaos_proxy_url, timeout=5, trust_env=False) as client:
        client.post("/admin/mode", json={"mode": mode}).raise_for_status()


def main(scenario: str):
    load_dotenv(ROOT / ".env")
    settings = Settings()
    policy_file = {
        "failover": "examples/groq-bifrost.failover.policy.yaml",
        "budget": "examples/groq-bifrost.policy.yaml",
        "confidential": "examples/groq-bifrost.policy.yaml",
    }[scenario]
    policy = Policy.model_validate(yaml.safe_load((ROOT / policy_file).read_text()))
    if scenario == "budget":
        tiny = os.environ.get("BIFROST_VK_DEMO_TINY", "")
        if not tiny:
            raise SystemExit("BIFROST_VK_DEMO_TINY missing")
        settings.bifrost_vk_dev = SecretStr(tiny)
        policy.limits.budget_usd = 1.0  # Penny's own cap is generous: the gateway must stop it.
    if scenario == "confidential":
        policy.confidential = True
    out = ROOT / "docs/live" / scenario
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="penny-live-") as tmp:
        folder, task = sandbox(Path(tmp))
        if scenario == "failover":
            chaos("503", settings)
        try:
            record = run(
                task["prompt"],
                folder,
                policy,
                load_pricing(ROOT),
                settings,
                SandboxAutoApprover(folder),
            )
        finally:
            if scenario == "failover":
                chaos("off", settings)
        data = record.model_dump()
        (out / "run.json").write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        (out / "receipt.html").write_text(receipt(record), encoding="utf-8")
        steps = [(s.get("provider_used"), s.get("model"), s.get("action")) for s in data["steps"]]
        print(
            json.dumps(
                {
                    "scenario": scenario,
                    "status": data["status"],
                    "error": data["error"],
                    "totals": data["totals"],
                    "failover_events": data["failover_events"],
                    "budget_events": data["budget_events"],
                    "steps": steps,
                },
                indent=1,
                default=str,
            )
        )


if __name__ == "__main__":
    main(sys.argv[1])
