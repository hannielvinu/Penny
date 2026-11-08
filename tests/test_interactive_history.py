import io

import pytest
from rich.console import Console

from penny.cost.estimate import estimate_label
from penny.cost.history import append_history, read_history
from penny.cost.quote import quote
from penny.pricing import Pricing
from penny.repo.repomap import RepoMap
from penny.safety.approvals import Approval, InteractiveApprover, UserQuit
from penny.safety.risk import Risk
from penny.ui.term import Terminal


def test_interactive_choices_and_blocked():
    output = io.StringIO()
    console = Console(file=output, width=80, force_terminal=False)
    approver = InteractiveApprover(console)
    decisions = iter(["d", "y", "a", "q"])
    console.input = lambda _: next(decisions)
    request = Approval("write", Risk.MEDIUM, "diff with [brackets]")
    assert not approver.approve(Approval("shell", Risk.BLOCKED, "blocked"))
    assert approver.approve(request)
    assert "diff with [brackets]" in output.getvalue()
    assert approver.approve(request)
    assert approver.approve(request)  # All subsequent non-delete writes for this task.
    with pytest.raises(UserQuit):
        approver.approve(Approval("git", Risk.HIGH, "danger"))
    console.input = lambda _: "n"
    assert not approver.approve(Approval("shell", Risk.HIGH, "unknown"))


def test_real_history_quote_and_mock_exclusion(repo):
    (repo / ".penny").mkdir()
    mock = dict(flags={"mock": True}, totals={"tokens_in": 1, "tokens_out": 1})
    append_history(repo, 2, mock)
    assert not (repo / ".penny/history.jsonl").exists()
    for value in [100, 200, 300]:
        append_history(
            repo, 2, dict(flags={"mock": False}, totals={"tokens_in": value, "tokens_out": 100})
        )
    assert len(read_history(repo, 2)) == 3
    m = RepoMap(repo).build()
    q = quote(m, 10, Pricing(), "test/model")
    assert q["low"] == 180 and q["high"] == 540
    assert "median" in q["assumptions"]
    assert "approx" in estimate_label()


def test_terminal_receipt_and_json():
    terminal = Terminal(plain=True)
    output = io.StringIO()
    terminal.console = Console(file=output, width=80)
    terminal.emit(
        dict(
            event="finished",
            mock=True,
            status="success",
            totals=dict(tokens_in=10, tokens_out=20),
            receipt="receipt.html",
            undo="penny undo run",
        )
    )
    assert "MOCK receipt" in output.getvalue()
