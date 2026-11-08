# Submission copy kit

## One-liner (limit 140 characters)

Penny quotes coding tasks, asks before changes, and gives an itemized receipt through the Bifrost gateway.

Verified length: 106 characters using the bundled counter.

## Problem (two sentences)

Solo developers need to understand agent spending before a task and review changes
before they happen. Reported billing-transparency complaints motivate clearer
estimates, explicit decisions and an inspectable audit trail.

## Solution (two sentences)

Penny is a CLI coding agent with local quotes, approved tools and offline receipts.
It combines compact repository context with Bifrost virtual-key budgets, configured
fallbacks and a separate Ollama-only route for confidential model context.

## AI usage

An AI coding assistant helped write and test this implementation. Commits use the
repository owner's configured identity; human review before submission is pending.

## Technologies

Python 3.11+, Typer, Rich, Pydantic v2, pydantic-settings, httpx, PyYAML, pathspec,
FastAPI, uvicorn, Bifrost, Docker Compose, Git, pytest/coverage, Ruff, mypy, optional
Ollama and Playwright; offline HTML/CSS/JavaScript/SVG and Fontsource WOFF2 fonts.

## Character counting

```bash
python scripts/count_chars.py docs/submission-one-liner.txt --limit 140
# Description limit is an input, not an invented form requirement:
python scripts/count_chars.py your-description.txt --limit YOUR_FORM_LIMIT
```

The counter counts Unicode code points after stripping final newline characters;
the actual form's counting rules may differ.

## Truthful checklist

- [x] Runnable source, package, CLI, MIT license and detailed README.
- [x] Offline mock vertical slice with real edits/tests and labelled synthetic usage.
- [x] Unit/integration/adversarial tests and CI configuration.
- [x] Responsive offline receipts with labelled MOCK screenshots.
- [x] Bifrost Compose startup, key creation and local-key cloud rejection exercised.
- [x] Eight-task synthetic preregistration, simple baseline and real-only runner.
- [ ] Human source review and final form-specific copy editing.
- [ ] Real model task completion with supported model IDs and credentials.
- [ ] Real provider outage recovery, paid cap stop and Ollama inference evidence.
- [ ] Real repeated benchmark and real screenshots/recording.
- [ ] Build the presentation deck from PITCH.md and fill the submission form.

Do not claim an official integration, approval, real saving percentage or unrun
provider outcome. Present all included scripted UI materials as MOCK.
