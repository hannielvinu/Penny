# Submission copy kit

Theme: **Build a Coding Agent That Gets the Job Done on the Fewest Tokens** (Bifrost).

One-liner: Penny quotes a coding task, asks before risky changes, and does the job on fewer tokens through the Bifrost gateway, with a receipt for every run.

Measured (21 Nov 2026, same model for both agents): on the 4 tasks both solved, 13.2% fewer tokens and 58.5% fewer steps than a plain agent; real outage failover, real gateway budget stop, local-only confidential route.

AI usage: LLMs (Groq Qwen 3.8 27B, NVIDIA Nemotron 3.5 Lightning, local qwen2.5-coder via Ollama) plan, read and edit code inside Penny through Bifrost. An AI coding assistant helped build and test the code.

Technologies: Python 3.11+, Typer, Rich, Pydantic v2, httpx, PyYAML, FastAPI (chaos proxy), Bifrost v2.4.0, Groq, NVIDIA API catalog, Ollama, Docker Compose, pytest, Ruff.
