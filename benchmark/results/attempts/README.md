# Excluded attempts (kept for transparency)

These runs are excluded from the summary because the harness, not the agents, failed:

- 20261121-121823, 20261121-121929: Groq's free tier counts max_tokens against 8,000 tokens/min,
  so Bifrost fell back to the NVIDIA reasoning model, which returned empty answers.
- 20261121-1222xx – 1224xx: gpt-oss models emitted native tool calls that Groq rejects
  (`tool_use_failed`, HTTP 400), 0 tokens spent; fixed by switching both agents to Qwen 3.8 27B.
- 20261121-123930 (rename_discount): the penny-dev virtual key's own 150,000 tokens/hour
  gateway limit was reached (152,092 used). Bifrost blocked further calls as configured; the
  hourly limit was raised to 400,000 and the task re-run.
