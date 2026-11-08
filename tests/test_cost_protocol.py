import json

import pytest

from penny.agent.compaction import compact
from penny.agent.escalation import Escalation
from penny.agent.guard import Chunk
from penny.agent.protocol import parse
from penny.cost.estimate import tokens
from penny.cost.history import bucket
from penny.cost.ledger import BudgetStop, Ledger
from penny.pricing import Price, Pricing


def test_price_ledger():
    price = Price(
        input_per_1m_usd=1,
        output_per_1m_usd=2,
        source_url="https://example.invalid/pricing",
        checked_on="2026-11-08",
    )
    pricing = Pricing(models={"test/model": price})
    ledger = Ledger(pricing)
    assert ledger.cost is None
    ledger.add("test/model", 1000000, 500000, "provider")
    assert ledger.cost == 2
    assert ledger.tokens_in == 1000000
    assert pricing.cost("missing", 1, 1) is None
    assert pricing.cost("ollama/local", 1, 1) is None
    with pytest.raises(BudgetStop, match="budget"):
        ledger.check(["test/model"], 100, 100, 2, 2000000)
    with pytest.raises(BudgetStop, match="token"):
        ledger.check(["test/model"], 100, 100, 20, 10)
    with pytest.raises(ValueError):
        Price(input_per_1m_usd=1)
    unknown = Ledger(Pricing())
    unknown.check(["missing"], 10, 10, 0, 100)
    unknown.add("missing", 1, 1, "estimate")
    assert unknown.cost is None


@pytest.mark.parametrize(
    "text",
    [
        "```json\n{}\n```",
        '{"thought":"x","action":"rm","args":{}}',
        '{"thought":"x","action":"search","args":{"query":"q","extra":1}}',
        '{"thought":"x","action":"read_lines","args":{"path":"a","start":1,"end":121}}',
        '{"thought":"x","action":"run_shell","args":{"command":"ls"}}',
    ],
)
def test_strict_protocol(text):
    with pytest.raises(ValueError):
        parse(text)


def test_protocol_compaction_escalation():
    assert (
        parse(json.dumps(dict(thought="ok", action="search", args=dict(query="tax")))).args[
            "max_results"
        ]
        == 8
    )
    chunks = [
        Chunk("s"),
        Chunk("t"),
        Chunk("x" * 1000, sensitivity="confidential"),
        Chunk("last"),
        Chunk("result"),
    ]
    out = compact(chunks, 100)
    assert out[2].sensitivity == "confidential" and "truncated" in out[2].text
    with pytest.raises(ValueError):
        compact([Chunk("x" * 1000)], 10)
    assert Escalation(patch_failures=2).reason()
    assert Escalation(json_failures=2).reason()
    assert Escalation(patch_attempts=2, test_failures=1).reason()
    assert not Escalation().reason()
    assert tokens("12345") == 2
    assert [bucket(v) for v in (1, 30, 101)] == ["small", "medium", "large"]
