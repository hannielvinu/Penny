# Three-minute demo

Use a real provider recording only after running the commands and inspecting the
receipt evidence. The bundled screenshots and offline demo are MOCK and must be
introduced with that label. Keep a recorded fallback when presenting live.

| Time | Action | What to say / show |
|---|---|---|
| 0:00–0:20 | Problem | Reported incidents and billing-transparency complaints motivate a contractor workflow: quote, approval, receipt. Do not assert unavailable-source timings. |
| 0:20–0:55 | `penny quote` then `penny run` | Show approximate range, configured cap, branch approval and exact patch. If prices are null, say price not configured. |
| 0:55–1:25 | `penny chaos on --mode 503` | Run with a configured working cloud fallback. Show answering-provider metadata in the receipt. If absent, say failover unverified. End with `penny chaos off`. |
| 1:25–1:50 | Tiny-budget key | In a separate demo shell use penny-demo-tiny as BIFROST_VK_DEV. Show the actual gateway budget rejection and receipt layer. Do not promise the first call is blocked: the gateway can overshoot by one request. |
| 1:50–2:20 | `penny doctor`; `penny run TASK --private` | Show actual local-key cloud rejection; then a local-model task if Ollama is running. Explain approved shell programs remain outside route isolation. |
| 2:20–2:50 | `penny receipt --open` | Timeline, approvals, tests, diff, quote error, budget events and undo. Open the real benchmark only if it has real measurements. |
| 2:50–3:00 | Close | State observed limits and the next tests to run. |

## Preparation

1. `make up`, bootstrap, configure actual supported cheap/strong/fallback models.
2. Fill pricing with source/date or present token-only estimates.
3. Pull and verify the Ollama model before the private-inference segment.
4. `python scripts/record_demo.py` for an interactive real-model synthetic task.
5. `make bench` for real comparison data; inspect failures as well as successes.
6. Capture real receipts/screenshots and record the demonstration externally.

For development or an explicitly labelled fallback:

```bash
python scripts/record_demo.py --mock --output .penny/demo
python scripts/screenshots.py .penny/demo/MOCK-receipt.html --mock
```

This script runs the real patch/test/receipt workflow using a scripted model and
scripted approvals. It does not simulate evidence of real provider recovery or paid
usage. Introduce it as MOCK before showing the result. The included screenshot
files have MOCK in their names.

Do not change the gateway config during the demo without rechecking isolation.
Restore chaos to off and restore the normal virtual key after the cap segment.
