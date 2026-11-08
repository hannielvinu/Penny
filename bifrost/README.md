# Local Bifrost setup

From the repository root, install Penny, run `python scripts/bootstrap_bifrost.py
--prepare`, fill provider keys in untracked `.env`, then `make up` and `make bootstrap`.
Put the printed virtual-key values into `.env` privately. Rerunning bootstrap leaves
existing names unchanged. With dashboard auth enabled, use BIFROST_MANAGEMENT_TOKEN.

`config.json` references provider secrets via documented `env.NAME` syntax, disables
content logging and enforces virtual keys on inference. The database lives in a
Compose volume. Keys are API-created rather than committed into this file:

- penny-dev: OpenAI/Anthropic, 0.50 USD/day budget.
- penny-local: Ollama only; no cloud provider config.
- penny-demo-tiny: OpenAI/Anthropic, 0.001 USD/day budget.
- All: 60 requests/minute, 150k tokens/hour; key_ids wildcard explicitly present.

Inference uses `x-bf-vk`, `/v1/chat/completions` and a request-body `fallbacks` array.
Set cloud fallback IDs in the target repo's policy; examples intentionally ship an
empty chain because provider access/model availability must be configured first.
Local requests send no fallbacks and use a separately restricted key.

OpenAI's network base URL is `http://chaos:8099/v1`; healthy chaos forwards to the
real upstream. Anthropic is the separately configured alternative. Ollama requires
`ollama_key_config.url: env.OLLAMA_BASE_URL`, default host Docker access. Ensure the
host Ollama interface is reachable from the container. Never expose it publicly.

Budgets are accrued-usage checks and can overshoot by an in-flight request. They are
independent from Penny's approximate pre-call budget check. Semantic caching is off.

Live evidence on v2.4.0: both containers started, three keys created, idempotent
bootstrap preserved keys, local-key cloud request returned HTTP 403 provider_blocked.
No successful provider completion, fallback recovery, paid exhaustion or local
inference is claimed. See [verification](../docs/VERIFICATION.md).

Official references: [setup](https://docs.getbifrost.ai/quickstart/gateway/setting-up),
[virtual keys](https://docs.getbifrost.ai/features/governance/virtual-keys),
[fallbacks](https://docs.getbifrost.ai/features/retries-and-fallbacks),
[key schema](https://github.com/maximhq/bifrost/blob/main/core/schemas/account.go).
