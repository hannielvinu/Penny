const { deck } = require("./lib2");
const fs = require("fs");
const A = "/tmp/claude-0/-home-user/e323aa61-8f0e-5334-831c-29839f98ed72/scratchpad/deck2/";
const S = JSON.parse(fs.readFileSync("/home/user/penny/benchmark/SUMMARY.json", "utf8"));
const fmt = (n) => n.toLocaleString("en-US");
const X = deck({
  bg: "F6F4EF", dark: "111C30", primary: "1F3A5F", accent: "E08A2E", accent2: "F3B26B", ink: "141A24", muted: "6A7180",
  card: "FFFFFF", line: "DCD7CC", red: "C2410C", soft: "E9EEF5",
  footer: "Penny · Global AI Hackathon 2026 · Coding agent on the fewest tokens · Bifrost",
});
const { pptx, T } = X;
const P = S.rows[0];

// 1. Title
{
  const s = X.slide(true);
  s.addShape(pptx.ShapeType.ellipse, { x: 8.6, y: -2.4, w: 7.5, h: 7.5, fill: { color: "1A2A47" }, line: { color: "1A2A47" } });
  X.t(s, "GLOBAL AI HACKATHON 2026", 0.7, 0.7, 6, 0.35, { size: 12, bold: true, color: T.accent2, cs: 3 });
  X.t(s, "Penny", 0.7, 1.25, 7, 1.3, { font: X.H, size: 66, bold: true, color: "FFFFFF" });
  X.t(s, "The coding agent that does the job on fewer tokens, and hands you the receipt.", 0.7, 2.6, 6.7, 1.2, { font: X.H, size: 24, color: "D2DCEB" });
  X.t(s, "Quote before it starts. Your approval before any write, command or Git action. A receipt after. Every call through Bifrost, with outages, budgets and private code handled for real.", 0.7, 3.85, 6.4, 1.25, { size: 15, color: "FFFFFF", ls: 1.15 });
  let x = 0.7;
  for (const [t, f] of [["Fewest-Tokens Coding Agent", T.accent], ["Bifrost", "2C4C78"], ["Groq · NVIDIA · Ollama", "2C4C78"]]) x += X.pill(s, t, x, 5.3, { fill: f, color: f === T.accent ? "111C30" : "FFFFFF" }) + 0.12;
  X.t(s, "github.com/hannielvinu/Penny", 0.7, 6.55, 6, 0.35, { size: 12, color: "9DB0CC" });
  X.browser(s, A + "pn-receipt.png", 7.6, 1.2, 5.25, 4.9, { url: "penny receipt · real benchmark run" });
}

// 2. Hook
{
  const s = X.slide();
  X.head(s, "The problem", "Same bug. Same model. 11 steps vs 4.");
  const lanes = [
    ["Plain agent", ["list_dir", "list_dir", "list_dir", "read_file", "read_file", "list_dir", "read_file", "read_file", "write_file", "run_tests", "finish"], "A8AFB8", `${P.baseline.steps} steps · ${fmt(P.baseline.tokens)} tokens\n${Math.round(P.baseline.seconds)} seconds`],
    ["Penny", ["read_symbol", "apply_patch", "run_tests", "finish"], T.primary, `${P.penny.steps} steps · ${fmt(P.penny.tokens)} tokens\n${Math.round(P.penny.seconds)} seconds`],
  ];
  lanes.forEach(([name, acts, c, stat], li) => {
    const y = 1.95 + li * 1.75;
    X.t(s, name, 0.55, y, 2.0, 0.4, { font: X.H, size: 18, bold: true, color: li ? T.primary : T.ink });
    X.t(s, stat, 0.55, y + 0.42, 2.4, 0.6, { size: 12, color: T.muted });
    let x = 2.9;
    acts.forEach((a) => {
      const w = li ? 0.45 + a.length * 0.1 : 0.2 + a.length * 0.068;
      X.box(s, x, y + 0.12, w, 0.5, { fill: li ? T.primary : "EEF0F2", line: li ? T.primary : "C9CED6", r: 0.12 });
      X.t(s, a, x, y + 0.12, w, 0.5, { size: li ? 12 : 9.5, bold: true, color: li ? "FFFFFF" : "3A4250", align: "center", valign: "middle" });
      x += w + 0.06;
    });
  });
  X.t(s, "Real benchmark run (pagination bug, 40-module repo). Both passed all 48 tests.", 2.9, 5.35, 9.5, 0.35, { size: 11.5, color: T.muted });
  const pains = [["Tokens are the bill", "and, on free tiers, the speed limit (8,000 tokens/min on Groq)."], ["Outages stop work", "a single-provider agent just halts."], ["Bills arrive after", "no per-developer spending cap."], ["Private code leaks", "to whichever cloud model is set."]];
  pains.forEach(([h, b], i) => {
    const x = 0.55 + i * 3.1;
    X.box(s, x, 5.85, 2.95, 1.0, { fill: i ? T.card : "FFF3E6", line: i ? T.line : "F1CFA6" });
    X.t(s, [{ text: h + " ", options: { bold: true } }, { text: b }], x + 0.15, 5.92, 2.7, 0.88, { size: 11.5, valign: "middle" });
  });
}

// 3. Solution
{
  const s = X.slide();
  X.head(s, "The solution", "Quote → Approve → Receipt, on a lean context");
  const flow = [["Quote", "Local token and $ estimate before any model call; stops at your budget."], ["Approve", "Exact diffs and commands with risk labels; branch per run; undo."], ["Receipt", "Every step's model, provider, tokens, cost, approvals and tests."]];
  flow.forEach(([h, b], i) => {
    const x = 0.85 + i * 4.2;
    s.addShape(pptx.ShapeType.ellipse, { x, y: 1.9, w: 1.25, h: 1.25, fill: { color: i === 1 ? T.accent : T.primary }, line: { color: i === 1 ? T.accent : T.primary } });
    X.t(s, String(i + 1), x, 1.9, 1.25, 1.25, { font: X.H, size: 34, bold: true, color: i === 1 ? "111C30" : "FFFFFF", align: "center", valign: "middle" });
    X.t(s, h, x + 1.45, 1.95, 2.5, 0.5, { font: X.H, size: 22, bold: true });
    X.t(s, b, x + 1.45, 2.45, 2.5, 1.1, { size: 12.5, color: "3A4250" });
    if (i < 2) X.arrow(s, x + 3.95, 2.52, x + 4.15, 2.52, { w: 2.5 });
  });
  X.t(s, "HOW PENNY SPENDS FEWER TOKENS", 0.55, 3.95, 8, 0.3, { size: 11, bold: true, color: T.primary, cs: 3 });
  const tech = ["Symbol map", "BM25 search", "Bounded line slices", "Exact patches", "History compaction", "Cheap / strong tiers", "Short outputs", "Deduplicated reads"];
  let x = 0.55, y = 4.4;
  tech.forEach((t) => {
    const w = 0.4 + t.length * 0.115;
    if (x + w > 12.8) { x = 0.55; y += 0.62; }
    X.box(s, x, y, w, 0.48, { fill: T.soft, line: "C8D3E3", r: 0.24 });
    X.t(s, t, x, y, w, 0.48, { size: 13, bold: true, color: T.primary, align: "center", valign: "middle" });
    x += w + 0.14;
  });
  X.box(s, 0.55, 5.85, 12.25, 0.95, { fill: T.dark, line: T.dark });
  X.t(s, [{ text: "Result: ", options: { bold: true, color: T.accent2 } }, { text: "find the one function, read only those lines, patch, test, done. Fewer tokens per step also means more steps per minute on rate-limited free tiers.", options: { color: "FFFFFF" } }], 0.8, 5.85, 11.8, 0.95, { size: 14, valign: "middle" });
}

// 4. Architecture
{
  const s = X.slide();
  X.head(s, "Technical architecture", "Every model call goes through Bifrost virtual keys");
  // left: Penny
  X.box(s, 0.55, 1.95, 3.1, 4.75, { fill: T.dark, line: T.dark, shadow: true });
  X.t(s, "PENNY CLI", 0.8, 2.1, 2.6, 0.35, { size: 11, bold: true, color: T.accent2, cs: 2 });
  ["Quote + lean context", "Route guard (confidential → local)", "Approvals: writes, shell, Git", "Tests + receipt"].forEach((t, i) => {
    X.box(s, 0.8, 2.6 + i * 0.98, 2.6, 0.78, { fill: "1D2C48", line: "2E4268" });
    X.t(s, t, 0.9, 2.6 + i * 0.98, 2.4, 0.78, { size: 12.5, bold: true, color: "FFFFFF", valign: "middle" });
  });
  // middle: Bifrost
  X.box(s, 4.45, 1.95, 4.15, 4.75, { fill: T.card, line: T.primary, lw: 2, shadow: true });
  X.t(s, "BIFROST GATEWAY v2.4.0", 4.7, 2.1, 3.7, 0.35, { size: 11, bold: true, color: T.primary, cs: 2 });
  [["penny-dev", "$0.50/day · token + request limits"], ["penny-local", "Ollama only · cloud refused"], ["penny-demo-tiny", "$0.001/day · cap demo"]].forEach(([k, d], i) => {
    X.box(s, 4.7, 2.6 + i * 0.86, 3.65, 0.7, { fill: T.soft, line: "C8D3E3" });
    X.t(s, [{ text: k + "\n", options: { bold: true, fontFace: "Poppins", fontSize: 12.5 } }, { text: d, options: { fontSize: 11, color: "4A5466" } }], 4.85, 2.6 + i * 0.86, 3.4, 0.7, { valign: "middle" });
  });
  X.box(s, 4.7, 5.25, 3.65, 1.2, { fill: "FFF3E6", line: "F1CFA6" });
  X.t(s, [{ text: "Routing + fallback\n", options: { bold: true, fontFace: "Poppins" } }, { text: "Groq first; on 5xx/429 → NVIDIA. Budgets and rate limits enforced in the gateway.", options: { fontSize: 11 } }], 4.85, 5.28, 3.4, 1.15, { size: 12.5, valign: "middle" });
  X.arrow(s, 3.7, 4.3, 4.4, 4.3, { w: 3 });
  // right: providers
  [["Groq", "Qwen 3.8 27B (primary)", "via chaos proxy for outage tests"], ["NVIDIA", "Nemotron 3.5 Lightning", "fallback provider"], ["Ollama (local)", "qwen2.5-coder", "confidential repos only"]].forEach(([h, m, d], i) => {
    const y = 1.95 + i * 1.62;
    X.box(s, 9.4, y, 3.4, 1.4, { shadow: true });
    X.t(s, h, 9.6, y + 0.12, 3.0, 0.4, { font: X.H, size: 15, bold: true, color: i === 2 ? T.accent : T.primary });
    X.t(s, m, 9.6, y + 0.52, 3.0, 0.35, { size: 12, bold: true });
    X.t(s, d, 9.6, y + 0.88, 3.0, 0.4, { size: 11, color: T.muted });
    X.arrow(s, 8.65, 4.3, 9.35, y + 0.7, { w: 1.75, dash: i === 1 ? "dash" : "solid", color: i === 2 ? T.accent : T.primary });
  });
}

// 5. Benchmark
{
  const s = X.slide();
  X.head(s, "Measured on real runs", "Penny vs a plain agent: same model, same tests");
  X.big(s, `${Math.round(S.step_reduction_pct)}%`, `fewer steps (${S.penny_steps_both} vs ${S.baseline_steps_both}) on the ${S.both_passed} tasks both solved`, 0.55, 1.7, 3.0, { size: 48, h: 0.9 });
  X.big(s, `${Math.round(S.token_reduction_pct)}%`, `fewer tokens (${(S.penny_tokens_both / 1000).toFixed(1)}k vs ${(S.baseline_tokens_both / 1000).toFixed(1)}k)`, 3.75, 1.7, 2.9, { size: 48, h: 0.9 });
  X.big(s, `${Math.round(100 * (1 - S.penny_usd_both / S.baseline_usd_both))}%`, `cheaper at Groq's price ($${S.penny_usd_both} vs $${S.baseline_usd_both})`, 6.85, 1.7, 2.9, { size: 48, h: 0.9 });
  X.big(s, `${Math.round(100 * (1 - S.penny_seconds_both / S.baseline_seconds_both))}%`, `faster (${Math.round(S.penny_seconds_both)} s vs ${Math.round(S.baseline_seconds_both)} s)`, 9.95, 1.7, 2.9, { size: 48, h: 0.9, color: T.accent });
  const max = Math.max(...S.rows.map((r) => Math.max(r.penny.tokens, r.baseline.tokens)));
  X.bars(s, S.rows.map((r) => ({ label: r.task.replace(/_/g, " ") + (!r.penny.passed && !r.baseline.passed ? " (both failed)" : ""), a: r.penny.tokens, b: r.baseline.tokens, max, fa: fmt(r.penny.tokens), fb: fmt(r.baseline.tokens) })), 0.55, 4.0, 8.4, 0.6, ["Penny tokens", "Plain agent tokens"]);
  X.box(s, 9.3, 3.7, 3.55, 3.05, { fill: "FFF3E6", line: "F1CFA6" });
  X.t(s, "Honest about losses", 9.5, 3.8, 3.2, 0.4, { font: X.H, size: 14, bold: true, color: "9A5612" });
  X.t(s, "Ordered-unique: Penny used more tokens (but half the steps). Five-file rename: both agents failed acceptance and Penny used 1.9× the tokens. Multi-file edits are next.\n\nModel: Groq Qwen 3.8 27B for both, via Bifrost. One run per task; raw logs in the repo.", 9.5, 4.2, 3.2, 2.5, { size: 11, ls: 1.1 });
}

// 6. Reliability
{
  const s = X.slide();
  X.head(s, "Reliability, run for real", "Outage, spending cap, private code: all live");
  const sc = [
    [A + "pn-failover.png", "Provider outage", "Groq forced to HTTP 503 on every request. Bifrost failed over to NVIDIA on every step; Penny still finished (5 steps).", T.primary],
    [A + "pn-budget.png", "Spending limit", "Key with a $0.001/day budget, already spent. Bifrost refused the first call; Penny stopped: budget_stopped, layer gateway, 0 tokens.", T.accent],
    [null, "Confidential code", "confidential: true → every call went to local Ollama, none to the cloud; the gateway refuses cloud models for that key. (The 3B CPU model couldn't finish: needs 7B+.)", T.primary],
  ];
  sc.forEach(([img, h, b, c], i) => {
    const x = 0.55 + i * 4.15;
    X.box(s, x, 1.85, 3.95, 4.95, { shadow: true });
    s.addShape(pptx.ShapeType.rect, { x, y: 1.85, w: 3.95, h: 0.09, fill: { color: c }, line: { color: c } });
    if (img) X.browser(s, img, x + 0.2, 2.1, 3.55, 2.35, {});
    else {
      X.box(s, x + 0.2, 2.1, 3.55, 2.35, { fill: T.dark, line: T.dark });
      X.t(s, "LOCAL ONLY", x + 0.2, 2.35, 3.55, 0.4, { size: 12, bold: true, color: T.accent2, align: "center", cs: 3 });
      X.t(s, "100%", x + 0.2, 2.75, 3.55, 0.9, { font: X.H, size: 48, bold: true, color: "FFFFFF", align: "center" });
      X.t(s, "of calls stayed on the machine", x + 0.2, 3.7, 3.55, 0.4, { size: 12, color: "C8D3E3", align: "center" });
    }
    X.t(s, h, x + 0.25, 4.6, 3.5, 0.45, { font: X.H, size: 17, bold: true, color: c === T.accent ? "9A5612" : T.primary });
    X.t(s, b, x + 0.25, 5.05, 3.5, 1.65, { size: 12, color: "3A4250", ls: 1.1 });
  });
}

// 7. Impact
{
  const s = X.slide();
  X.head(s, "Impact and scale", "Agents teams can actually trust, and budget for");
  const who = [["Solo devs & students", "Free-tier quotas go further when every step is small; the quote tells you the cost up front."], ["Teams", "One Bifrost key per developer with its own daily budget; receipts become an audit trail."], ["Platform owners", "Swap providers in policy.yaml; Bifrost handles routing, keys and failover."]];
  who.forEach(([h, b], i) => {
    const x = 0.55 + i * 4.15;
    X.box(s, x, 1.85, 3.95, 2.25, { fill: i === 1 ? T.dark : T.card, line: i === 1 ? T.dark : T.line, shadow: true });
    X.t(s, h, x + 0.3, 2.0, 3.4, 0.5, { font: X.H, size: 18, bold: true, color: i === 1 ? "FFFFFF" : T.ink });
    X.t(s, b, x + 0.3, 2.55, 3.4, 1.45, { size: 13.5, color: i === 1 ? "D2DCEB" : "3A4250", ls: 1.12 });
  });
  X.t(s, "ROADMAP", 0.55, 4.45, 3, 0.3, { size: 11, bold: true, color: T.primary, cs: 3 });
  s.addShape(pptx.ShapeType.line, { x: 0.9, y: 5.35, w: 11.6, h: 0, line: { color: T.line, width: 3 } });
  [["Now", "CLI agent, receipts, Bifrost keys, live benchmark"], ["Next", "Multi-file edit planning (our weak spot)"], ["Then", "Real-repo benchmark at N=3 + IDE plugin"], ["Later", "Team receipt dashboard and budgets per project"]].forEach(([h, b], i) => {
    const x = 0.9 + i * 3.05;
    X.dot(s, "", x - 0.16, 5.19, 0.32, { fill: i === 0 ? T.accent : T.primary });
    X.t(s, h, x - 0.16, 5.6, 2.8, 0.35, { font: X.H, size: 14, bold: true });
    X.t(s, b, x - 0.16, 5.95, 2.8, 0.8, { size: 12, color: "3A4250" });
  });
}

// 8. Close
{
  const s = X.slide(true);
  X.t(s, "Your coding agent,", 0.8, 1.7, 11.5, 0.9, { font: X.H, size: 36, color: "D2DCEB" });
  X.t(s, "on a budget you control.", 0.8, 2.55, 11.5, 1.2, { font: X.H, size: 54, bold: true, color: "FFFFFF" });
  [[`${S.penny_steps_both} vs ${S.baseline_steps_both}`, "steps on the same tasks"], ["5 / 5", "steps answered by NVIDIA in a Groq outage"], ["0", "tokens over a gateway budget"]].forEach(([a, b], i) => {
    const x = 0.8 + i * 4.0;
    X.t(s, a, x, 4.15, 3.6, 0.8, { font: X.H, size: 38, bold: true, color: T.accent2 });
    X.t(s, b, x, 4.95, 3.6, 0.5, { size: 14, color: "FFFFFF" });
  });
  X.t(s, "github.com/hannielvinu/Penny  ·  Bifrost v2.4.0  ·  Groq · NVIDIA · Ollama  ·  MIT", 0.8, 6.3, 11.5, 0.4, { size: 13, color: "9DB0CC" });
  X.t(s, "AI use: LLMs plan, read and edit code inside Penny through Bifrost; an AI coding assistant helped build Penny.", 0.8, 6.75, 11.5, 0.35, { size: 10, color: "6F82A0" });
}

X.save(process.argv[2]).then(() => console.log("saved"));
