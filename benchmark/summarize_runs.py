"""Combine real benchmark result files (benchmark/results/*.json) into one summary.

Writes benchmark/SUMMARY.json and prints a Markdown table. Only files whose
runs used real gateway calls are present in benchmark/results/ (misconfigured attempts
live in benchmark/results/attempts/ and are excluded on purpose, see README).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Groq published price for qwen/qwen3.8-27b (console.groq.com/docs/model/qwen/qwen3.8-27b, 2026-11-21).
PRICE_IN, PRICE_OUT = 0.80 / 1e6, 4.00 / 1e6


def main():
    runs, sources = [], []
    for path in sorted((ROOT / "benchmark/results").glob("2026*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        sources.append(path.name)
        for run in data["runs"]:
            totals = run["totals"]
            runs.append(
                dict(
                    task=run["task"],
                    agent=run["agent"],
                    passed=run["acceptance"]["passed"],
                    status=run["status"],
                    tokens=totals.get("tokens_in", 0) + totals.get("tokens_out", 0),
                    tokens_in=totals.get("tokens_in", 0),
                    tokens_out=totals.get("tokens_out", 0),
                    steps=totals.get("steps", 0),
                    seconds=round(totals.get("wall_ms", 0) / 1000, 1),
                    usd=round(
                        totals.get("tokens_in", 0) * PRICE_IN
                        + totals.get("tokens_out", 0) * PRICE_OUT,
                        5,
                    ),
                    raw=run["raw"],
                    models=data["models"],
                )
            )
    tasks = sorted({r["task"] for r in runs}, key=[r["task"] for r in runs].index)
    rows = []
    for task in tasks:
        p = next((r for r in runs if r["task"] == task and r["agent"] == "penny"), None)
        b = next((r for r in runs if r["task"] == task and r["agent"] == "baseline"), None)
        if p and b:
            rows.append(dict(task=task, penny=p, baseline=b))
    both = [r for r in rows if r["penny"]["passed"] and r["baseline"]["passed"]]
    total = lambda agent, key, rs: sum(r[agent][key] for r in rs)  # noqa: E731
    summary = dict(
        sources=sources,
        tasks=len(rows),
        penny_passed=sum(r["penny"]["passed"] for r in rows),
        baseline_passed=sum(r["baseline"]["passed"] for r in rows),
        both_passed=len(both),
        penny_tokens_both=total("penny", "tokens", both),
        baseline_tokens_both=total("baseline", "tokens", both),
        penny_steps_both=total("penny", "steps", both),
        baseline_steps_both=total("baseline", "steps", both),
        penny_seconds_both=round(total("penny", "seconds", both), 1),
        penny_usd_both=round(total("penny", "usd", both), 4),
        baseline_usd_both=round(total("baseline", "usd", both), 4),
        baseline_seconds_both=round(total("baseline", "seconds", both), 1),
        rows=rows,
    )
    if both:
        summary["token_reduction_pct"] = round(
            100 * (1 - summary["penny_tokens_both"] / summary["baseline_tokens_both"]), 1
        )
        summary["step_reduction_pct"] = round(
            100 * (1 - summary["penny_steps_both"] / summary["baseline_steps_both"]), 1
        )
    (ROOT / "benchmark/SUMMARY.json").write_text(json.dumps(summary, indent=2))
    print(
        "| Task | Penny tokens | Baseline tokens | Penny steps | Baseline steps | Penny time | Baseline time | Tests pass (P / B) |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        p, b = r["penny"], r["baseline"]
        print(
            f"| {r['task']} | **{p['tokens']:,}** | {b['tokens']:,} | **{p['steps']}** | {b['steps']} | "
            f"{p['seconds']} s | {b['seconds']} s | {'✅' if p['passed'] else '❌'} / {'✅' if b['passed'] else '❌'} |"
        )
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=1))


if __name__ == "__main__":
    main()
