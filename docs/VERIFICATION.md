# Verification evidence

Date: 2026-11-08. This file distinguishes executed checks from work needing external
credentials. No real model output, price or comparative token result is fabricated.

## Executed

- Clone empty origin, configure repo-local Hanniel Vinu identity, commit and push main.
- Install package/development dependencies on Windows Python 3.11 and WSL Python 3.12.
- Run offline pytest on both environments. Linux includes the symlink escape check;
  Windows skips that check when symlink privileges are absent.
- Run Ruff lint/format, mypy, package build, CLI help/version/init/quote/report and
  noninteractive denial checks. Final counts are recorded below after hardening.
- Run `python scripts/record_demo.py --mock --output .penny/demo`: SUCCESS,
  pagination patch applied, full synthetic suite passed, JSON/events/raw/HTML emitted.
  Model actions and usage are synthetic; filesystem edits and pytest are real.
- Run all eight deterministic task injections: clean sandbox passes, injected suites
  fail as expected. No real benchmark was run.
- Fetch/vendor requested fonts and OFL licenses via `scripts/vendor_fonts.sh`.
- Run Chromium receipt QA at 360, 390, 768, 1024, 1280 and 1536 pixels, light/dark,
  keyboard navigation, reduced motion, no external requests and no horizontal page
  overflow; also 200% CSS layout zoom at 1280. Screenshots are labelled MOCK.
- In WSL: `docker compose config --quiet`, `docker compose up --build -d --wait`:
  chaos healthy and real `maximhq/bifrost:v2.4.0` running.
- Bootstrap real gateway: three virtual keys created; secret values kept only in
  untracked `.env`/private runtime state. Rerunning preserves existing keys.
- `penny doctor --plain`: gateway/key checks PASS; pricing/local-model availability
  WARN; local-key isolation PASS. No provider credentials were supplied.
- `pytest tests/test_real_gateway.py --real -q`: actual Bifrost returns HTTP 403,
  `type: provider_blocked`, `extra_fields.error_type: policy_provider_blocked` for
  a cloud request carrying the Ollama-only key.

## Written, but not run with a real model

| Scenario | Missing prerequisite |
|---|---|
| Real model completes a coding task | Provider credential and available model ID |
| Outage followed by successful cloud fallback | Two accessible models/providers and configured fallbacks |
| Paid virtual-key budget exhaustion | Live billed provider use and gateway accounting |
| Private task completes via Ollama | Running host Ollama and downloaded coding model |
| Successful-response failover metadata inspection | A successful real inference response |
| Real comparative benchmark | Working real inference setup; default 48 calls/runs may spend money |
| Real demo/screenshots | Successful real task execution |
| macOS local execution | No macOS host in this session; CI matrix configured |

The setup has no known real model prices, so pricing stays null. Browser QA uses a
MOCK receipt and does not establish model quality, latency, savings or failover.
No other coding product was compared.

## Final hardening results

| Command | Observed result |
|---|---|
| `python -m pytest -q --cov=penny --cov-report=term-missing` — Windows 3.11 | 159 passed, 2 skipped; overall coverage 86% |
| Same command — WSL/Linux 3.12 | 160 passed, 1 skipped (explicit live opt-in); overall coverage 87% |
| `coverage report --include='*/penny/safety/*,*/penny/agent/guard.py,*/penny/cost/*,*/penny/exec/patch.py' --fail-under=90` | PASS, 295/296 statements on Linux (99% displayed); guard/cost/patch 100%, paths 97% |
| `python -m pytest tests/test_real_gateway.py --real -q` — WSL | 1 passed, actual gateway rejection |
| `ruff check .` / `ruff format --check .` | PASS, 71 Python files formatted (generated sandbox excluded) |
| `mypy src/penny` | PASS, 53 source files |
| `python -m build` | PASS, sdist and wheel |
| Isolated import from built wheel | PASS; defaults, prompts, CSS, fonts and HTML renderer available |
| `python scripts/record_demo.py --mock --output .penny/demo` | SUCCESS; real patch and 48 passing sandbox tests; synthetic model usage |
| `python scripts/screenshots.py .penny/demo/MOCK-receipt.html --mock` | PASS, 12 width/theme layouts plus 200% layout zoom |
| `python scripts/count_chars.py docs/submission-one-liner.txt --limit 140` | PASS, 106 characters |
| `docker compose config --quiet` and `docker compose up --build -d --wait` — WSL | PASS; Bifrost/chaos started and healthy |
| `python scripts/bootstrap_bifrost.py` — WSL | Three keys created; rerun left all unchanged |
| `penny doctor --plain` — WSL | Gateway/keys/isolation PASS; pricing and absent local model WARN |

[GitHub Actions run 42499871191](https://github.com/hannielvinu/Penny/actions/runs/42499871191)
passed all six jobs on implementation commit `6d3bec3`: Ubuntu and macOS, each with
Python 3.11, 3.12 and 3.13. Every job ran lint, format, offline tests, targeted coverage,
and build. Mypy also passed locally (CI keeps it nonblocking as requested).

One upstream Starlette/AnyIO deprecation warning remains; it does not fail checks.
Coverage files were separated by platform to prevent Windows/WSL path collisions.
Runtime logs, keys, downloaded schema and build products remain untracked.

Git history uses only Hanniel Vinu / hannielvinu@gmail.com for author and committer.
Commit-message attribution-pattern scan returned clean. Tracked file/history scans
checked credential patterns and the actual generated local key/setup-token values
without printing those values. No `.env`, runtime state or pricing secrets are tracked.
