# Pitch outline

1. **Problem:** a solo developer wants predictable agent spending and reviewable changes.
2. **Evidence:** reported billing-transparency complaints; clearly labelled source
   limitations. No unsupported incident timing or comparative product claim.
3. **Solution:** quote before model usage, approvals before mutations, receipt after
   success/failure. One developer persona and one CLI workflow.
4. **Architecture:** compact repo context and bounded actions, with Bifrost as the
   shared transport/governance layer; separate cloud and Ollama-only keys.
5. **Demo:** actual quote/patch/test/receipt. Live key rejection is verified. Introduce
   any scripted demonstration as MOCK and show what still needs real credentials.
6. **Benchmark:** pre-registered eight-task synthetic comparison. Not yet run; show
   the method/empty state instead of invented savings.
7. **Limits:** no OS sandbox, imperfect secrets/estimates/local models, in-flight
   budget overshoot, synthetic benchmark and incomplete real-model evidence.
8. **Next 30 days:** real repeated benchmark; successful inference metadata checks;
   provider outage/private inference demonstrations; subprocess container isolation;
   broader task/language evaluation and signed provenance for receipts.

## Judge Q&A

1. **How does Penny save tokens?** It retrieves symbols/slices, patches instead of
   rewrites, deduplicates reads, trims output and compacts without another model.
   These mechanisms are implemented; measured savings are not yet established.
2. **Why a gateway?** One transport for cloud/local inference plus centrally enforced
   provider restrictions, budgets, rate limits and configured fallbacks.
3. **What is real versus mocked?** Filesystem edits, tests, reports, container startup,
   key creation and cloud rejection were run. The bundled task-completing model is
   scripted and its usage synthetic. Real completion/failover/benchmark remain unrun.
4. **What if prices are wrong?** Costs are only as current as user-supplied prices.
   Sources/dates are required; unknowns stay null. Cross-check gateway accounting.
5. **What if a local model is weak?** Repair JSON, escalate locally if configured or
   stop with a receipt. There is no automatic cloud fallback for private context.
6. **How do approvals work?** Exact diff/command plus risk, with separate Git and
   shell decisions. Blocked operations cannot execute through a yes flag.
7. **Why not another agent?** This prototype focuses on the contractor workflow and
   auditable cost/routing. Other products were not compared.
8. **What did not work initially?** Live Bifrost revealed null empty-key lists and a
   required per-key Ollama URL. Real testing caught and corrected both.
9. **Can it stop every leak?** No. Regexes and paths cover specific cases. Approved
   repository code can use host capabilities; private routing only governs model calls.
10. **Is a budget a strict final-bill ceiling?** No. Agent estimates are approximate;
    gateway accrued usage can overshoot with in-flight requests.
11. **Can it prove failover?** Only when gateway metadata identifies the answering
    provider. Otherwise the receipt says unverified.
12. **What counts as success?** The agent requires tests after edits, and the benchmark
    independently reruns full acceptance with allowed-path/test-integrity checks.
13. **Can I undo everything?** No. Guarded Git restoration refuses later changes;
    shell effects outside tracked source cannot be reconstructed.
14. **How does it scale?** Hash-cached maps and BM25 keep retrieval local. Context,
    usage and wall-clock caps bound each run. Large-repo evaluation remains future work.
15. **What is submission-ready now?** Source, tests, infrastructure, demo, reports,
    methods and documentation. User credentials, real measurements, human review,
    presentation recording and the submission form remain manual.
