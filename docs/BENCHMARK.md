# Benchmark

## Pre-registration

Commit `1007664` contains tasks, generator, template and simple baseline before any
real measurement. Later implementation fixes before the first real run are visible
in history. No real result was used to tune tasks. The runner fingerprints the
registration and refuses to combine results after a protocol change.

Synthetic shopkit has 40 business modules across eight domains and roughly 3–5k
lines. Shared mapping utilities provide intentionally repetitive context, not a
claim of realism for every repository. The clean suite passes; all eight injections
fail acceptance: pagination, tax rounding, cross-module rename, empty report, unique
helper, cross-module shipping cause, address extraction and CLI flag.

## Method

Penny uses its compact map, slices, patches, deterministic compaction, tiers and
output trimming. The baseline is a simple strong-model ReAct loop with whole-file
reads/writes, full test output and no map/compaction/tiers. Both use Bifrost, the same
synthetic tasks, fresh Git copies, configured limits and route guard. Baseline has
a 4,000-token output cap for file rewrites; Penny defaults to 800. This is a relevant
method difference. Other products were **not compared**.

Default N=3 gives 48 runs. Order is task → agent → repetition, not randomized.
Acceptance re-runs the complete suite, checks allowed files against the initial
commit (including agent commits), and protects tests except the prescribed rename.
Passing tests do not prove all task semantics or code quality.

`SandboxAutoApprover` is restricted to marked temporary benchmark copies, refuses
HIGH/BLOCKED actions and budget extensions, and is not exposed in normal CLI runs.

## Reproduce

```bash
python -m pip install -e '.[dev]'
python benchmark/generate_sandbox.py
(cd benchmark/sandbox_template && python -m pytest -q)
# Configure actual models, gateway keys and optional pricing first.
PENNY_MOCK=0 penny bench --n 3
PENNY_MOCK=0 penny bench --n 1 --task pagination  # labelled SMALL SAMPLE
PENNY_MOCK=0 penny bench --n 3 --ablate dedupe   # optional single toggle
```

Raw runs and independent acceptance output are under `benchmark/results/<timestamp>/`.
Aggregate JSON records date, commit, model IDs, registration hashes, N, pass/fail,
tokens, nullable costs, steps, wall time and raw links. Means include failures and
show min–max ranges. Unknown costs remain unknown. The runner updates marked result
blocks in README/this file and generates self-contained HTML. Partial results save
incrementally. N<3 or fewer than eight tasks is SMALL SAMPLE. Mock mode is refused.

Do not modify tasks or baseline after inspecting results. Version protocols
separately, document why and rerun both agents.

## Results

<!-- RESULTS:START -->

**Not yet run.** Real inference credentials and supported live models were not
supplied. No comparative savings percentage is claimed.

<!-- RESULTS:END -->

## Caveats

This is a bounded synthetic Python sample and a deliberately simple baseline.
Provider load, randomness, caching and quota state affect observations. Three
repetitions are descriptive. Prices may be stale; local hardware, energy and taxes
are not priced. Do not extrapolate to other products, languages or workloads.
