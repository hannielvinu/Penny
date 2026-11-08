# Security boundaries

Penny is a local developer tool with approval controls, not an OS sandbox or a
proof of code safety. Use a disposable copy and restricted host account for
untrusted repositories.

| Threat | Enforced control | Boundary |
|---|---|---|
| Prompt injection in files | Data-only system instruction, strict actions, independent tool approvals | Models can still be influenced; review proposals |
| Command injection | shlex argv, forbidden operators, blocked downloads/force push, no shell=True | Approved tests/interpreters/builds can execute arbitrary repo code |
| Traversal / symlinks | Real-path containment, metadata/secret-path protection, patch snapshot recheck | Concurrent filesystem races are not eliminated |
| Secret leakage | Regex masking, sensitivity tags, denied paths, subprocess credential env filtering | Regexes can miss secrets; approved code can read other credentials |
| Confidential data to cloud | Maximum-sensitivity route guard; local session pin; no local cloud fallback | Gateway/local model host are trusted; admins can change restrictions |
| Gateway route escape | Ollama-only provider config on penny-local | Real cloud-request rejection verified; compromised gateway not covered |
| Runaway spending | Agent cost/token/step/prompt/wall/progress limits; gateway budgets/rate limits | Estimates, stale prices, retries and in-flight requests can overshoot |
| Destructive Git / undo | Branch approvals, push policy, force block, base/diff/created-file-hash checks | Shell/network side effects are not reversible |
| Receipt HTML injection | Escape all untrusted data, no raw HTML insertion, restrictive CSP | Reports contain code and should remain private |

## Trust assumptions

The operator, policy, host filesystem, Git executable, Bifrost administrator and
chosen local/provider model infrastructure are trusted within their roles. Private
routing protects model-call destinations; it does not stop network access by an
approved test, package, script or local model service.

LOW is a review classification, not a claim of harmlessness. `python -m pytest -q`
executes repository code. Remove automatic command approvals for unfamiliar repos.
Penny strips key/token/secret/password environment variables from subprocesses, but
credentials stored in files, Git configuration or other services can remain reachable.

Model tools cannot directly read/write `.git` or `.penny`; Git is a separate approved
capability. Init deliberately writes policy/ignore files at the operator's request.
Benchmark auto approval requires a temp-root marker and refuses HIGH/BLOCKED actions
and budget extensions. The marker prevents accidental misuse, not malicious code
running as the same user.

## Gateway and chaos exposure

Compose publishes ports on loopback. Bootstrap creates a random untracked setup
token; after dashboard authentication is enabled, use a management credential.
Do not publish `.env`, bootstrap stdout, gateway databases or runtime receipts.
Content logging is disabled in the shipped gateway config and generated keys.

Chaos admin has no authentication: it is a local test harness. It forwards only to
its fixed configured upstream, does not log Authorization/body content, and disables
HTTP access logs in Compose. Other clients on its Docker network may reach it.

## Reporting

Use a synthetic reproduction without credentials or proprietary receipts in public
issues. Include Penny/Bifrost versions. Rotate credentials that may have been exposed.
