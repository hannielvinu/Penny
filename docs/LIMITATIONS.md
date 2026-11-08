# Limitations

- Python AST symbols are first-class; other-language extraction is best-effort.
- Small local models can fail JSON or tasks. Private runs do not degrade to cloud.
- Conservative maps may route a whole run locally; compaction can discard useful context.
- Token and quote estimates are rough. Prices are user-maintained and can go stale.
  Cached-token discounts, aliases and provider retry billing may diverge from the ledger.
- Gateway budgets check accrued usage, rather than reserving every in-flight token.
- Approved commands/tests execute with host permissions. There is no OS, filesystem,
  process or network sandbox for repository code. Environment filtering is limited.
- Regexes can miss secrets. Receipts may retain proprietary code after masking.
- Exact patches require unique matches. No native deletion/rename tool is provided;
  review shell/Git proposals for operations requiring those capabilities.
- Undo refuses later commits/changes and dirty starts; it cannot reverse external effects.
- HTTP 429 retries are bounded; other transport errors stop. Fallback visibility
  depends on metadata. Successful real inference metadata remains to be verified.
- Real provider completion, real fallback, paid budget exhaustion and Ollama inference
  were not run without provider keys/model availability.
- Benchmarks are synthetic and use a simple baseline. Other products were not compared.
  Token-saving results are Not yet run.
- Browser QA covers the supplied MOCK receipt in Chromium, not every possible content
  or browser. The 200% check uses CSS layout zoom rather than browser UI automation.
- Linux through WSL was tested. macOS has CI configuration, not local execution.
  Native Windows is best-effort; use WSL for the whole gateway workflow.
- Abrupt termination, disk errors or hardware failure can interrupt receipt finalization.
