import importlib.util
import time
from pathlib import Path

import httpx
import pytest

from penny.agent.context import Techniques
from penny.agent.loop import run
from penny.exec.gitops import undo
from penny.gateway.client import BifrostClient
from penny.gateway.errors import BadRequest, Timeout
from penny.gateway.routing import Route
from penny.mock.scripted_llm import ScriptedLLM
from penny.pricing import Pricing
from penny.repo.grep import search_text
from penny.repo.repomap import RepoMap
from penny.safety.approvals import ScriptedApprover
from penny.safety.risk import Risk, classify


def test_both_grep_backends(repo, monkeypatch):
    (repo / "notes.txt").write_text("a unique phrase\nnot a signature\n")
    repo_map = RepoMap(repo).build()
    assert search_text(repo_map, "unique phrase")[0]["path"] == "notes.txt"
    monkeypatch.setattr("penny.repo.grep.shutil.which", lambda _: None)
    assert search_text(repo_map, "unique phrase")[0]["start_line"] == 1


def test_force_push_combined_flags(repo):
    assert classify("git push -uf origin main", repo)[0] == Risk.BLOCKED


def test_budget_token_cap_receipt(repo, policy, mock_settings):
    policy.limits.token_cap = 1
    record = run("Task", repo, policy, Pricing(), mock_settings, ScriptedApprover([True, True]))
    assert record.status == "budget_stopped" and not record.steps
    assert record.budget_events[0]["layer"] == "agent"


def test_ablation_whole_file_write_and_undo_safety(repo, policy, mock_settings):
    actions = [
        dict(action="write_file", args=dict(path="new.py", content="print(1)\n")),
        dict(action="finish", args=dict(summary="manual review", status="cannot_complete")),
    ]
    record = run(
        "Task",
        repo,
        policy,
        Pricing(),
        mock_settings,
        ScriptedApprover([True] * 10),
        client=ScriptedLLM(actions),
        techniques=Techniques(patch_edits=False),
    )
    assert (repo / "new.py").read_text() == "print(1)\n"
    assert "new.py" in record.created_file_hashes
    (repo / "new.py").write_text("user's subsequent change\n")
    with pytest.raises(ValueError, match="created file changed"):
        undo(repo, record.model_dump())


def test_deadline_and_negative_usage():
    client = BifrostClient(
        "http://gateway.invalid",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "x"}}],
                    "usage": {"prompt_tokens": -10, "completion_tokens": 1},
                },
            )
        ),
    )
    route = Route("cloud", "test/model", "key", [])
    with pytest.raises(BadRequest):
        client.complete([], route, 10, [])
    client.deadline = time.monotonic() - 1
    with pytest.raises(Timeout):
        client.complete([], route, 10, [])
    client.close()


def test_benchmark_refuses_mock_and_summarizes_without_claims(repo, mock_settings):
    spec = importlib.util.spec_from_file_location(
        "benchmark_runner", Path("benchmark/run_benchmark.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(ValueError, match="MOCK"):
        module.run_benchmark(repo)
    rows = module.summarize(
        [
            dict(
                task="fixture",
                agent="penny",
                acceptance=dict(passed=True),
                totals=dict(tokens_in=10, tokens_out=2, cost_usd=None, steps=1, wall_ms=1),
            ),
            dict(
                task="fixture",
                agent="penny",
                acceptance=dict(passed=False),
                totals=dict(tokens_in=20, tokens_out=4, cost_usd=None, steps=2, wall_ms=2),
            ),
        ]
    )
    assert rows[0]["tokens"] == 18 and rows[0]["tokens_range"] == [12, 24]
    assert rows[0]["cost_usd"] is None and rows[0]["passed"] == 1
