const { makeDeck } = require("./lib");
const fs = require("fs");
const out = process.argv[2];
const ROOT = process.argv[3] || "/home/user/penny";
const S = JSON.parse(fs.readFileSync(ROOT + "/benchmark/SUMMARY.json", "utf8"));
const LIVE = JSON.parse(fs.readFileSync(ROOT + "/docs/live/SCENARIOS.json", "utf8"));
const IMG = ROOT + "/docs/screenshots/REAL-receipt-crop.png";
const fmt = (n) => n.toLocaleString("en-US");

const d = makeDeck({
  bg: "F7F5F0", dark: "15233B", primary: "1F3A5F", accent: "C26A1B", ink: "171A1F", muted: "6A7180",
  card: "FFFFFF", line: "DCD7CC", footer: "Penny · Global AI Hackathon 2026 · Coding agent on the fewest tokens (Bifrost)",
});
const { pptx, T } = d;

// 1 Title
{
  const s = d.slide({ dark: true });
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 0.25, h: 7.5, fill: { color: "D9893A" }, line: { color: "D9893A" } });
  s.addText("GLOBAL AI HACKATHON 2026 · CODING AGENT ON THE FEWEST TOKENS · BIFROST", { x: 0.8, y: 0.8, w: 12, h: 0.4, fontFace: "Inter", fontSize: 13, bold: true, color: "D9893A", charSpacing: 2 });
  s.addText("Penny", { x: 0.8, y: 1.6, w: 11, h: 1.5, fontFace: "Poppins", fontSize: 72, bold: true, color: "FFFFFF" });
  s.addText("The coding agent that does the job on fewer tokens, and hands you the receipt.", { x: 0.8, y: 3.1, w: 11.8, h: 0.9, fontFace: "Poppins", fontSize: 26, color: "D6E0EE" });
  s.addText("Quote before it starts. Your approval before any file write, command or Git action. An itemised receipt after. Every model call through the Bifrost gateway, with outages, budgets and private code handled for real.", { x: 0.8, y: 4.1, w: 11.5, h: 1.0, fontFace: "Inter", fontSize: 17, color: "FFFFFF" });
  [[`${S.step_reduction_pct}% fewer steps`, `${S.penny_steps_both} vs ${S.baseline_steps_both} on the ${S.both_passed} tasks both agents solved`], [`${S.token_reduction_pct}% fewer tokens`, `${(S.penny_tokens_both/1000).toFixed(1)}k vs ${(S.baseline_tokens_both/1000).toFixed(1)}k, same model, same tasks`], ["Outage + budget", "real Groq outage survived; real gateway spending stop"]].forEach(([a, b], i) => {
    const x = 0.8 + i * 4.0;
    s.addShape(pptx.ShapeType.roundRect, { x, y: 5.45, w: 3.7, h: 1.35, rectRadius: 0.1, fill: { color: "1F3050" }, line: { color: "34496B" } });
    s.addText(a, { x: x + 0.2, y: 5.52, w: 3.3, h: 0.6, fontFace: "Poppins", fontSize: 22, bold: true, color: "F0A65A", fit: "shrink" });
    s.addText(b, { x: x + 0.2, y: 6.15, w: 3.3, h: 0.55, fontFace: "Inter", fontSize: 13, color: "FFFFFF" });
  });
}

// 2 Problem
{
  const s = d.slide({ n: 2 });
  d.heading(s, "The problem", "Coding agents burn tokens, money and trust");
  d.bullets(s, [
    "Typical agents explore by listing folders and reading whole files, then resend the growing history on every step.",
    "Tokens are the bill: every wasted read is paid for, and on free tiers it stalls the agent (Groq's free tier allows 8,000 tokens per minute).",
    "Providers go down mid-task; a single-provider agent just stops.",
    "Spending is a surprise after the fact; no per-developer cap.",
    "Confidential code gets sent to whichever cloud model is configured.",
    "Agents write files, run commands and touch Git without asking.",
  ], 0.6, 1.9, 7.2, 4.9, 16.5);
  d.card(s, 8.1, 1.9, 4.6, 4.75);
  s.addText("What we saw (same model, same task)", { x: 8.35, y: 2.05, w: 4.2, h: 0.4, fontFace: "Inter", fontSize: 12, bold: true, color: T.accent });
  const p = S.rows[0];
  s.addText("Plain agent", { x: 8.35, y: 2.6, w: 4.1, h: 0.4, fontFace: "Poppins", fontSize: 15, bold: true, color: T.ink });
  s.addText(`list_dir ×4, read_file ×4, write_file, run_tests, finish\n${p.baseline.steps} steps · ${fmt(p.baseline.tokens)} tokens · ${p.baseline.seconds} s`, { x: 8.35, y: 3.0, w: 4.1, h: 1.0, fontFace: "Inter", fontSize: 13, color: T.ink });
  s.addText("Penny", { x: 8.35, y: 4.15, w: 4.1, h: 0.4, fontFace: "Poppins", fontSize: 15, bold: true, color: T.primary });
  s.addText(`read_symbol, apply_patch, run_tests, finish\n${p.penny.steps} steps · ${fmt(p.penny.tokens)} tokens · ${p.penny.seconds} s`, { x: 8.35, y: 4.55, w: 4.1, h: 1.0, fontFace: "Inter", fontSize: 13, color: T.ink });
  s.addText("Task: fix the pagination bug in a 40-module repo. Both passed all 48 tests.", { x: 8.35, y: 5.7, w: 4.1, h: 0.8, fontFace: "Inter", fontSize: 12, color: T.muted });
}

// 3 Solution
{
  const s = d.slide({ n: 3 });
  d.heading(s, "The solution", "Quote → Approve → Receipt, built around a lean context");
  const items = [
    ["Fewer tokens by design", "Symbol map + BM25 search find the right function; bounded line slices instead of whole files; exact patches; history compaction; short outputs; cheap/strong model tiers."],
    ["Quote before it starts", "A local token and dollar estimate with no model call; the run stops at your budget, and the gateway key has its own cap."],
    ["You approve every risky step", "Exact diffs and commands with risk labels; a branch per run; blocked dangerous patterns; one-command undo."],
    ["Receipt after", "Every step's model, provider, tokens, cost, approvals, failovers and test results, offline in HTML and JSON."],
  ];
  items.forEach(([h, b], i) => {
    const x = 0.6 + (i % 2) * 6.2, y = 1.95 + Math.floor(i / 2) * 2.45;
    d.card(s, x, y, 5.95, 2.2);
    s.addShape(pptx.ShapeType.rect, { x, y: y + 0.25, w: 0.09, h: 1.7, fill: { color: i === 0 ? T.accent : T.primary }, line: { color: i === 0 ? T.accent : T.primary } });
    s.addText(h, { x: x + 0.3, y: y + 0.2, w: 5.45, h: 0.55, fontFace: "Poppins", fontSize: 17, bold: true, color: T.ink, fit: "shrink" });
    s.addText(b, { x: x + 0.3, y: y + 0.8, w: 5.45, h: 1.3, fontFace: "Inter", fontSize: 13.5, color: T.ink, fit: "shrink" });
  });
}

// 4 Architecture
{
  const s = d.slide({ n: 4 });
  d.heading(s, "Technical architecture", "Every model call goes through Bifrost virtual keys");
  d.flow(s, [
    { tag: "PENNY CLI", title: "Quote + context", sub: "Repo map, BM25, slices, compaction; local estimate before any call" },
    { tag: "SAFETY", title: "Route guard", sub: "Confidential files force the local route; approvals for writes, shell, Git" },
    { tag: "BIFROST", title: "Virtual keys", sub: "penny-dev ($0.50/day), penny-local (Ollama only), penny-demo-tiny ($0.001/day)" },
    { tag: "BIFROST", title: "Routing + fallback", sub: "Primary Groq; on 5xx/429 falls back to NVIDIA; budgets and rate limits enforced" },
    { tag: "PROVIDERS", title: "Groq · NVIDIA · Ollama", sub: "Qwen 3.8 27B (Groq), Nemotron 3.5 (NVIDIA), qwen2.5-coder (local)" },
  ], 0.6, 1.95, 12.1, 2.55);
  d.card(s, 0.6, 4.8, 12.1, 1.95);
  s.addText("Why Bifrost is the backbone", { x: 0.85, y: 4.9, w: 11.6, h: 0.4, fontFace: "Poppins", fontSize: 15, bold: true, color: T.primary });
  d.bullets(s, [
    "Spending limits live in the gateway (virtual-key budgets), so a buggy or hostile agent still cannot overspend.",
    "Outage recovery is a request-level fallback list; Penny records which provider actually answered.",
    "A local-only key cannot reach any cloud model: the gateway refuses it (checked by `penny doctor`).",
  ], 0.85, 5.3, 11.6, 1.4, 13.5);
}

// 5 Benchmark
{
  const s = d.slide({ n: 5 });
  d.heading(s, "Measured on real runs", "Penny vs a plain agent: same model, same tasks");
  const rows = S.rows.map((r) => ({ label: r.task.replace(/_/g, " ") + (!r.penny.passed && !r.baseline.passed ? " (both failed)" : ""), a: r.penny.tokens, b: r.baseline.tokens, max: Math.max(...S.rows.map((x) => Math.max(x.penny.tokens, x.baseline.tokens))), fmt: (v) => fmt(v) }));
  d.bars(s, rows, 0.6, 2.35, 7.7, ["Penny tokens", "Plain agent tokens"], { rowH: Math.min(0.95, 4.4 / rows.length), labelW: 2.3 });
  d.card(s, 8.6, 1.95, 4.1, 4.85);
  s.addText(`The ${S.both_passed} tasks both solved`, { x: 8.85, y: 2.05, w: 3.7, h: 0.4, fontFace: "Poppins", fontSize: 15, bold: true, color: T.primary });
  d.bullets(s, [
    { text: `Tokens: ${fmt(S.penny_tokens_both)} vs ${fmt(S.baseline_tokens_both)} (${S.token_reduction_pct}% fewer)`, bold: true },
    `Steps: ${S.penny_steps_both} vs ${S.baseline_steps_both} (${S.step_reduction_pct}% fewer)`,
    `Time: ${Math.round(S.penny_seconds_both)} s vs ${Math.round(S.baseline_seconds_both)} s`,
    `Cost at Groq's price: $${S.penny_usd_both} vs $${S.baseline_usd_both}`,
    `Solved: ${S.penny_passed}/${S.tasks} vs ${S.baseline_passed}/${S.tasks}; on the multi-file rename both failed and Penny used 1.9x the tokens (our weak spot)`,
    "Model: groq/qwen/qwen3.8-27b for both, through Bifrost. One run per task: a small sample, raw logs in the repo.",
  ], 8.85, 2.5, 3.7, 4.2, 12.5);
}

// 6 Reliability scenarios
{
  const s = d.slide({ n: 6 });
  d.heading(s, "Reliability, run for real", "Outage, spending cap, private code: live");
  LIVE.forEach((sc, i) => {
    const x = 0.6 + i * 4.07;
    d.card(s, x, 1.95, 3.85, 4.8);
    s.addText(sc.tag, { x: x + 0.25, y: 2.05, w: 3.4, h: 0.35, fontFace: "Inter", fontSize: 11, bold: true, color: T.accent });
    s.addText(sc.title, { x: x + 0.25, y: 2.4, w: 3.4, h: 0.6, fontFace: "Poppins", fontSize: 17, bold: true, color: T.ink, fit: "shrink" });
    s.addText(sc.how, { x: x + 0.25, y: 3.05, w: 3.4, h: 1.3, fontFace: "Inter", fontSize: 12.5, color: T.muted, fit: "shrink" });
    s.addText(sc.result, { x: x + 0.25, y: 4.4, w: 3.4, h: 2.2, fontFace: "Inter", fontSize: 13.5, color: T.ink, fit: "shrink" });
  });
}

// 7 Receipt + impact
{
  const s = d.slide({ n: 7 });
  d.heading(s, "The receipt, and why it scales", "Every run accounted for, so teams can trust agents");
  s.addImage({ path: IMG, x: 0.6, y: 1.85, w: 4.6, h: 4.6 * 0.9375 });
  d.bullets(s, [
    "Real receipt from the benchmark: 12,214 tokens, 4 steps, 29.4 s, 4 approvals, all tests passing, estimate vs actual shown.",
    "Solo developers and students: free-tier quotas go further when each step is small.",
    "Teams: one Bifrost key per developer with its own daily budget; receipts become an audit trail.",
    "Model-agnostic: change providers in policy.yaml; Bifrost handles routing, keys and fallbacks.",
    "Next: real-repo benchmark at N=3, IDE plugin, team receipt dashboard.",
  ], 5.6, 1.95, 7.1, 4.9, 15);
}

// 8 Try it
{
  const s = d.slide({ n: 8 });
  d.heading(s, "Try it", "Open source, reproducible, built during the hackathon");
  d.bullets(s, [
    "Code, setup, benchmark and receipts: github.com/hannielvinu/Penny",
    "Run: pip install -e .; copy .env.example; add free Groq and NVIDIA keys; docker compose up; python scripts/bootstrap_bifrost.py; penny doctor.",
    "Reproduce: penny bench --n 1 --task pagination (results in benchmark/results/, summary via benchmark/summarize_runs.py).",
    "Scenarios: python scripts/live_scenarios.py failover | budget | confidential (receipts in docs/live/).",
    "Tech: Bifrost v2.4.0 (virtual keys, budgets, fallbacks), Groq, NVIDIA API catalog, Ollama, Python, Typer, Pydantic, httpx, pytest.",
    "AI use: LLMs plan and edit code inside Penny; an AI coding assistant helped build and test Penny.",
  ], 0.6, 1.95, 12.1, 4.6, 17);
}

d.save(out).then(() => console.log("saved", out));
