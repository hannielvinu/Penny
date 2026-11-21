# Penny

**The coding agent that does the job on fewer tokens, and hands you the receipt.**

Penny is a CLI coding agent for solo developers, students and freelancers. It quotes a task before spending anything, asks before any file write, shell command or Git action, and finishes with an itemised receipt. Every model call goes through the **Bifrost AI gateway**, which enforces per-developer budgets, fails over between providers and keeps confidential code on a local model.

> **Live and measured (21 Nov 2026).** Real Bifrost v2.4.0 gateway, real Groq / NVIDIA / Ollama models. On the 4 tasks both agents solved, Penny used **13.2% fewer tokens** (52,901 vs 60,971) and **58.5% fewer steps** (17 vs 41) than a plain agent on the same model, and cost $0.0454 vs $0.0638. A real provider outage, a real gateway budget stop and a local-only confidential run are recorded in [`docs/live/`](docs/live/). [Results](#benchmark).

![Real Penny receipt from the benchmark: 12,214 tokens, 4 steps, tests passing](docs/screenshots/REAL-receipt-crop.png)

*Real receipt (pagination task, Groq Qwen 3.8 27B through Bifrost): 4 steps, read the one function, patch, run all 48 tests, finish.*

## Why fewer tokens matter

Typical agents explore by listing folders and reading whole files, then resend the growing history every step. Tokens are the bill, and on free tiers they are also the speed limit: Groq's free tier allows 8,000 tokens per minute, so a wasteful agent literally stalls. Penny finds the right symbol with a repository map and BM25 search, reads a bounded slice, applies an exact patch, compacts history and keeps outputs short.

## What it does, and the evidence

| Theme requirement | How Penny does it | Real evidence (21 Nov 2026) |
|---|---|---|
| Complete tasks on fewer tokens | Symbol map + BM25, bounded slices, exact patches, history compaction, cheap/strong tiers, short outputs | 4/5 tasks solved; 13.2% fewer tokens and 58.5% fewer steps on the 4 tasks both agents solved ([table](#benchmark)) |
| Keep working through provider outages | Bifrost request-level fallbacks; receipt records which provider answered | Groq forced to HTTP 503 → every step served by NVIDIA, task finished in 5 steps ([run](docs/live/failover/)) |
| Individual spending limits | Penny's own budget preflight **and** a per-developer Bifrost virtual-key budget | $0.001/day key exhausted → gateway refused the call, run `budget_stopped` at layer *gateway* ([run](docs/live/budget/)) |
| Protect confidential repositories with local models | `confidential: true` or confidential globs force the local route; local key can reach only Ollama | All calls went to local `qwen2.5-coder:3b`; gateway refuses cloud models for that key (`penny doctor` PASS). The 3B CPU model could not finish the task ([run](docs/live/confidential/)) |
| Approval before risky operations | Exact diffs and commands with risk labels, branch per run, blocked patterns, guarded undo | 161 tests incl. adversarial commands; benchmark sandboxes auto-approve only LOW/MEDIUM risk |
| Correctness | Test-before-finish; independent acceptance check in the benchmark | Acceptance re-runs the full suite and checks which files changed |

## Quick start without keys

Requirements: Python 3.11+, Git, and a POSIX shell. Linux through WSL was tested; macOS is configured in CI but was not run locally. Native Windows is best-effort.

```bash
git clone https://github.com/hannielvinu/Penny.git
cd Penny
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python scripts/record_demo.py --mock --output .penny/demo
```

The demo creates a synthetic shopkit Git repository in the OS temp directory, injects a pagination bug, and performs search → symbol read → patch → tests → receipt. Only this MOCK development harness uses scripted approvals. Open `.penny/demo/MOCK-receipt.html`. The terminal also prints the retained sandbox path for inspection and undo. Mock token counts are synthetic and excluded from history and benchmarks. The default mock sequence is specifically for the pagination fixture; it cannot solve arbitrary tasks.

## Real gateway setup

Run these commands from the checkout in one shell environment. On Windows, use WSL for the entire workflow so Python, Docker, Git and `localhost` refer to the same environment.

1. Install Penny as above, Docker with Compose, and optionally host Ollama.
2. Prepare an untracked environment file and a random gateway setup token:

   ```bash
   python scripts/bootstrap_bifrost.py --prepare
   ```

   Existing `.env` is not overwritten. Copy missing settings from [`.env.example`](.env.example). Fill `GROQ_API_KEY` and `NVIDIA_API_KEY` (both have free tiers; this is the measured setup). OpenAI/Anthropic keys are optional extra providers. Provider credentials are consumed by the gateway; Penny's client uses virtual keys.

3. Start Bifrost and the outage harness:

   ```bash
   make up
   # Equivalent: docker compose up --build -d --wait
   ```

   Published ports are loopback-only: gateway `8080`, chaos `8099`. Bifrost is pinned to `maximhq/bifrost:v2.4.0`. Groq goes through the initially healthy chaos proxy (so `penny chaos on --mode 503` simulates a Groq outage); NVIDIA is the fallback provider; Ollama serves the local route. The Compose volume retains configuration/log state. `make down` stops services without deleting the volume.

4. Create virtual keys:

   ```bash
   python scripts/bootstrap_bifrost.py
   ```

   This intentionally prints newly created key values: put them in the matching `.env` variables privately. Rerunning preserves existing keys. If gateway dashboard authentication is enabled, set `BIFROST_MANAGEMENT_TOKEN` instead of using the setup token. Finish first-admin setup in Bifrost's UI before exposing it beyond this local configuration.

   | Key | Providers | Gateway budget | Rate limit |
   |---|---|---|---|
   | `penny-dev` | `PENNY_CLOUD_PROVIDERS` (default here: Groq, NVIDIA) | 0.50 USD / rolling day | 60 requests/min, 150k tokens/hour |
   | `penny-local` | Ollama only | Local compute unpriced | Same request/token limits |
   | `penny-demo-tiny` | Same as `penny-dev` | 0.001 USD / rolling day | Same request/token limits |

   These are configured **limits**, not model prices. Gateway accounting can overshoot by an in-flight request; a budget is not a prepaid reservation for every generated token. [Gateway details](bifrost/README.md).

5. Pull a local coding model when using private mode:

   ```bash
   ollama pull qwen2.5-coder:3b   # 7b+ recommended if your machine can run it
   ```

   `OLLAMA_BASE_URL` is seen from the container, default `http://host.docker.internal:11434`. On Linux, Ollama must listen on a host interface reachable from Docker. Restrict host access; do not expose Ollama publicly. Restart Bifrost after changing its environment.

6. Configure the target repository and prices:

   ```bash
   cp pricing.example.yaml pricing.yaml
   penny init --repo /path/to/your/git/repository
   ```

   Start from [`examples/groq-bifrost.policy.yaml`](examples/groq-bifrost.policy.yaml) (the measured setup) or [`examples/groq-bifrost.failover.policy.yaml`](examples/groq-bifrost.failover.policy.yaml) for NVIDIA fallback; copy [`examples/pricing.groq.yaml`](examples/pricing.groq.yaml) to `pricing.yaml`. Place a filled `pricing.yaml` in the target too, with provider-page URLs and checked dates. Keep prices untracked. Commit the `.gitignore` changes made by `init`; start with a clean tree and at least one Git commit.

7. Check, estimate and run:

   ```bash
   penny doctor --repo /path/to/repository
   penny pricing check --repo /path/to/repository
   penny quote "Fix pagination" --repo /path/to/repository
   penny run "Fix pagination" --repo /path/to/repository
   penny report --repo /path/to/repository --open
   ```

   Environment variables come from the current directory's `.env` or the shell. `doctor` sends a tiny cloud-model probe with the local key to check rejection. A misconfigured key could permit that request; the result is reported explicitly.

## Commands

| Command | Purpose |
|---|---|
| `penny init [--repo PATH]` | Create policy and metadata ignore rules |
| `penny doctor [--repo PATH] [--plain]` | Check environment, prices, gateway, model listing and key isolation |
| `penny quote TASK [--private] [--json]` | Local estimate without a model call |
| `penny run TASK` | Quote, approve, act, test, receipt |
| `penny receipt [RUN_ID] [--open]` | Regenerate/open a stored receipt; latest by default |
| `penny report [--open]` | Generate local run ledger and benchmark page |
| `penny undo [RUN_ID]` | Approve restoring base state; refuse subsequent changes |
| `penny chaos on --mode 503` | Simulate an outage; also `429` and `timeout` |
| `penny chaos off` / `status` | Restore/check proxy |
| `penny pricing check` | Report configured-model prices and missing entries |
| `penny bench --n 3 [--task ID] [--ablate TOGGLE]` | Real-only benchmark from this source checkout |
| `penny version` | Installed version |

`run` flags: `--repo`, `--budget`, `--private`, `--tier cheap|strong|auto`, `--max-steps`, `--yes-quote`, `--non-interactive`, `--allow-dirty`, `--plain`, `--json`.

`--yes-quote` approves only the quote. Noninteractive and JSON runs deny writes, Git changes and non-allowlisted commands. JSON mode emits JSON Lines on stdout; notices go to stderr. There is no broad automatic-approval flag. Interactive options are `y` yes, `n` no, `a` subsequent non-delete writes, `d` full diff, `q` quit. Shell/Git approval remains separate.

Exit codes: **0** success, **1** task failed, **2** usage/configuration error, **3** gateway error, **4** budget stop, **5** abort or initial approval denied. Later denials are sent back to the model so it can adapt.

## Policy and pricing

Full examples: [`policy.example.yaml`](policy.example.yaml), [`pricing.example.yaml`](pricing.example.yaml). Unknown fields are rejected.

```yaml
# .penny/policy.yaml excerpt; retain the other generated fields
confidential: false
confidential_globs: ["internal/**", "config/prod/**"]
on_confidential: go_local  # go_local | withhold | block
test_command: "python -m pytest -q"
limits:
  budget_usd: 0.50
  max_steps: 25
  max_prompt_tokens: 12000
  max_output_tokens: 800
  max_wall_seconds: 900
  token_cap: 150000
```

The secret-path denylist excludes `.env*`, private keys, `.aws`, `.ssh` and `.git` regardless of policy. Maps, search results, slices and tool output carry sensitivity. Once confidential context uses a local route, derived conversation stays local. `withhold` substitutes a file-withheld notice; `block` stops.

```yaml
# pricing.yaml — user-maintained and untracked
models:
  openai/gpt-4o-mini:
    input_per_1m_usd: null
    output_per_1m_usd: null
    source_url: ""
    checked_on: ""
```

Set both prices, an HTTPS source URL and an ISO date to enable cost accounting. Null prices show **price not configured**. Ollama compute is **not priced**, rather than assumed free. Unknown prices or uncertain fallback identity keep total cost unknown; the token cap applies. Estimates are approximate; provider-reported usage is authoritative.

## Architecture and Bifrost

```mermaid
flowchart LR
  U[Developer task] --> Q[Local quote + Git preflight]
  Q --> A[Approval gate]
  A --> L[Bounded agent loop]
  R[AST / BM25 / slices] --> L
  L --> G[Provenance and route guard]
  G --> B[Bifrost gateway]
  B --> C[Cloud providers + configured fallbacks]
  B --> O[Ollama / local-only key]
  L --> T[Approved patches / commands / Git]
  T --> V[Tests]
  V --> L
  L --> E[Usage ledger + events]
  E --> H[Offline HTML receipt]
```

- Inference: `POST /v1/chat/completions`, `x-bf-vk` and documented `fallbacks` array.
- Governance: API-created provider-restricted keys with budgets and rate limits.
- Local inference: `ollama_key_config.url` from the gateway environment.
- Outage demo: OpenAI's gateway base URL points at the fixed-upstream chaos proxy.
- Observability: reported usage and available metadata are recorded. Only metadata-evidenced failover is claimed; missing metadata is marked unverified. Semantic caching is not enabled or claimed.

[Architecture](docs/ARCHITECTURE.md) · [Security](docs/SECURITY.md) · [Decisions](docs/DECISIONS.md).

## Benchmark

<!-- RESULTS:START -->

**Run on 21 Nov 2026** · both agents on `groq/qwen/qwen3.8-27b` through Bifrost · one run per task (small sample) · raw logs in [`benchmark/results/`](benchmark/results/), summary in [`benchmark/SUMMARY.json`](benchmark/SUMMARY.json) (`python benchmark/summarize_runs.py`).

| Task | Penny tokens | Baseline tokens | Penny steps | Baseline steps | Penny time | Baseline time | Tests pass (P / B) |
|---|---|---|---|---|---|---|---|
| pagination | **12,214** | 17,991 | **4** | 11 | 29.4 s | 144.1 s | ✅ / ✅ |
| tax_rounding | **12,307** | 16,579 | **4** | 10 | 84.5 s | 131.3 s | ✅ / ✅ |
| empty_sales | **12,408** | 13,016 | **4** | 10 | 85.2 s | 101.2 s | ✅ / ✅ |
| ordered_unique | **15,972** | 13,385 | **5** | 10 | 133.3 s | 109.5 s | ✅ / ✅ |
| rename_discount | **55,486** | 29,384 | **13** | 25 | 376.0 s | 247.0 s | ❌ / ❌ |

On the 4 tasks both solved: **52,901 vs 60,971 tokens (13.2% fewer)**, 17 vs 41 steps, 332 s vs 486 s, $0.0454 vs $0.0638 at Groq's published price ($0.80 / $4.00 per 1M input/output tokens).

**Where Penny was worse, honestly.** On `ordered_unique` (write a new function) Penny used more tokens than the baseline, though half the steps. On `rename_discount` (rename across five files) both agents failed acceptance: Penny renamed the function in all four source files and all tests passed, but it did not update the test import the task asked for, and it spent 1.9× the baseline's tokens reading slices. Multi-file edits are the next thing to fix. Excluded harness failures (and why) are listed in [`benchmark/results/attempts/`](benchmark/results/attempts/README.md).

<!-- RESULTS:END -->

Eight tasks and the simple whole-file baseline were pre-registered in commit `1007664` before real measurements. Deterministic synthetic shopkit contains 40 business modules; its clean suite passes and each injected task fails. After setting real keys/models, run `make bench`. Default sample: 8 tasks × 2 agents × 3 repetitions = 48 fresh-copy runs.

Raw usage, failures, acceptance results, model IDs, commit, task fingerprints and means with min–max ranges are saved. Independent acceptance re-runs the full suite and checks changed-file restrictions. Mock mode is refused. Small samples are labelled. Other products were not compared. [Method](docs/BENCHMARK.md).

## Development and reports

```bash
make lint
make test
make build
mypy src/penny
python -m pytest tests/test_real_gateway.py --real -q
# Optional browser verification:
python -m pip install -e '.[browser]'
python -m playwright install chromium
python scripts/screenshots.py .penny/demo/MOCK-receipt.html --mock
```

Default tests use scripted models/in-process transports and block accidental network connections. CI is configured for Python 3.11–3.13 on Linux/macOS; [verification](docs/VERIFICATION.md) distinguishes observed runs. Fontsource Latin WOFF2 assets and OFL licenses are vendored, then embedded into HTML. Refresh with `bash scripts/vendor_fonts.sh`.

`make install` installs the tested `requirements-dev.lock` snapshot before the editable package. The six Linux/macOS CI jobs passed on the final implementation commit, covering Python 3.11, 3.12 and 3.13. Local WSL verification passed 160 tests; the explicit live-gateway isolation test passed separately. Safety, route-guard, cost and patch coverage exceeded 99% in aggregate; each requested area exceeded 90%.

Records: `.penny/runs/<id>/run.json`, `events.jsonl`, redacted full command output in `raw/`, `receipt.html`. Index: `.penny/index.html`. Receipts show quote error, steps, approvals, diffs, tests, budgets, failover evidence and undo instructions. Runtime records can contain proprietary code even after masking: treat them as private.

## Limits

Python is first-class; other-language extraction is best-effort. Passing tests do not establish complete correctness. Approved tests/commands execute repository code with host permissions: Penny is **not an operating-system sandbox**. Pattern scanning can miss secrets. Concurrent filesystem changes remain a risk. Use disposable copies and restricted permissions for unfamiliar code.

Quotes are rough, prices can become stale, and in-flight requests can overshoot limits. Private routing does not isolate a compromised gateway, a network-capable local service, or approved shell programs. Undo refuses ambiguous state and cannot reverse external side effects. Local model quality varies. [Full limitations](docs/LIMITATIONS.md).

## Submission kit

Demo video (76 s, real receipts from the benchmark, outage and budget runs): [`docs/demo/Penny_demo.mp4`](docs/demo/Penny_demo.mp4)

Pitch deck: [PDF](deck/Penny_Pitch.pdf) · [PPTX](deck/Penny_Pitch.pptx) (all numbers generated from `benchmark/SUMMARY.json` and `docs/live/SCENARIOS.json`).


[Demo script](docs/DEMO_SCRIPT.md) · [Pitch and Q&A](docs/PITCH.md) · [Submission copy](docs/SUBMISSION.md) · [Progress](docs/PROGRESS.md) · [Verification](docs/VERIFICATION.md).

Stack: Python, Typer, Rich, Pydantic, pydantic-settings, httpx, PyYAML, pathspec, FastAPI, uvicorn, pytest, Ruff, mypy, Docker Compose, Bifrost, optional Ollama and Playwright. No provider SDK or frontend build.

**AI usage:** LLMs plan, read and edit code inside Penny (through Bifrost). An AI coding assistant helped write and test this implementation.

MIT License · Copyright (c) 2026 Hanniel Vinu.
