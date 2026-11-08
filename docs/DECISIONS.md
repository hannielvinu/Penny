# Decisions

Date: 2026-11-08. The repository was empty; no existing user work was removed.
Adjacent build milestones were combined into logical vertical-slice commits rather
than forty artificial intermediate commits.

1. Model proposals are strict data. Path checks, risk and approvals are independent.
2. Ship null prices. Require both prices plus source/date to account cost; unknown
   calls keep totals unknown. Independently enforce token caps.
3. Default token estimation is deterministic characters/4, labelled approximate.
   Optional tokenizer packaging is reserved for cached-tokenizer environments;
   the current estimator uses the offline fallback. Provider usage is authoritative.
4. Conservatively mark a map confidential when any mapped path matches a private
   glob. Search results preserve provenance. Local context pins derived conversation.
   Separate task/map chunks prevent withholding a map from losing a public task.
5. Official Bifrost docs establish `x-bf-vk`, `/v1/chat/completions`, string `fallbacks`,
   `env.NAME`, budgets arrays and provider `key_ids: ["*"]`. Omitted/empty key IDs
   deny keys. Bootstrap uses the management API to avoid tracked key secrets.
6. Live Bifrost returned `virtual_keys: null` on an empty store. Bootstrap now
   normalizes it and preserves existing names on rerun.
7. Compose pins v2.4.0 from the official setup guide. Live startup and official Go
   schema showed Ollama requires per-key `ollama_key_config.url`; network base_url
   alone was insufficient. Fixed to the environment URL and restarted successfully.
8. Real cloud probe with `penny-local` returned HTTP 403, `provider_blocked`, with
   `error_type: policy_provider_blocked`. Doctor requires this specific rejection.
9. **Outstanding ASSUMPTION:** verify successful inference exposes actual answering
   provider in `extra_fields.provider` on the deployed gateway. No successful real
   LLM response was available without credentials. The client preserves available
   metadata and otherwise reports failover unverified. No successful failover is claimed.
10. OpenAI's custom base URL points at a fixed-upstream chaos proxy. Fault/header
    behavior is tested; actual provider recovery still requires real credentials.
11. Semantic caching is off: no extra cache infrastructure or caching claim. Stable
    prefix is implemented without claiming a provider actually reused cached tokens.
12. Preview all exact-match edits, recheck after approval, then atomic replace.
    Whole-file write is offered only when disabling patch_edits for ablation.
13. Undo compares base/current branch/diff/created-file hashes and refuses ambiguous
    state. Dirty starts disable automatic undo; external side effects need review.
14. Requested Fontsource Latin WOFF2 assets and OFL licenses were fetched; actual
    versions are stored beside fonts. Reports embed them and need no network.
15. Benchmark tasks/baseline were committed before real measurement. Offline fixes
    did not use real results. Acceptance checks the initial commit, not just HEAD.
16. Human review cannot be inferred from automated commits. Disclosure states review
    is pending instead of claiming the author already reviewed every change.
17. WebProNews was retrieved. Supplied Verdict/Waxell URLs were unavailable; they
    remain labelled references without asserting their specific anecdote numbers.
18. Linux/WSL Python 3.12 and Windows Python 3.11 were exercised. macOS is in CI,
    not locally verified. No native Windows support claim is made.

## Official sources consulted

- [Index](https://docs.getbifrost.ai/llms.txt)
- [Setup / image pin / auth](https://docs.getbifrost.ai/quickstart/gateway/setting-up)
- [Provider config](https://docs.getbifrost.ai/quickstart/gateway/provider-configuration)
- [Virtual keys](https://docs.getbifrost.ai/features/governance/virtual-keys)
- [Budgets](https://docs.getbifrost.ai/features/governance/budget-and-limits)
- [Retries / fallbacks](https://docs.getbifrost.ai/features/retries-and-fallbacks)
- [Ollama](https://docs.getbifrost.ai/providers/supported-providers/ollama)
- [Create-key response](https://docs.getbifrost.ai/api-reference/governance/create-virtual-key)
- [Observability](https://docs.getbifrost.ai/features/observability/default)
- [Official per-key config schema](https://github.com/maximhq/bifrost/blob/main/core/schemas/account.go)
