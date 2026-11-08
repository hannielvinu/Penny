import json
import time
import uuid
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path

from penny.agent.compaction import compact
from penny.agent.context import Techniques
from penny.agent.escalation import Escalation
from penny.agent.guard import Chunk, prepare
from penny.agent.protocol import parse, schema
from penny.agent.tools import Tools
from penny.cost.estimate import tokens
from penny.cost.history import append_history
from penny.cost.ledger import BudgetStop, Ledger
from penny.cost.quote import quote
from penny.exec.gitops import branch_name, git, preflight
from penny.gateway.client import BifrostClient
from penny.gateway.errors import GatewayBudgetExceeded, GatewayError
from penny.gateway.routing import select
from penny.mock.scripted_llm import ScriptedLLM
from penny.repo.repomap import RepoMap
from penny.repo.secrets import mask
from penny.report.model import RunRecord
from penny.safety.approvals import UserQuit
from penny.safety.risk import Risk


def run(
    task,
    root,
    policy,
    pricing,
    settings,
    approver,
    *,
    yes_quote=False,
    allow_dirty=False,
    tier="auto",
    techniques=None,
    client=None,
    emit=None,
) -> RunRecord:
    root = Path(root).resolve()
    if (root / ".penny").is_symlink():
        raise ValueError(".penny must not be a symlink")
    techniques = techniques or Techniques()
    emit = emit or (lambda event: None)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    run_id = stamp + "-" + uuid.uuid4().hex[:6]
    run_dir = root / ".penny/runs" / run_id
    run_dir.mkdir(parents=True)
    record = RunRecord(
        id=run_id,
        task=mask(task)[0],
        repo=root.name,
        flags=dict(mock=settings.penny_mock, private=policy.confidential, tier=tier),
        policy=policy.model_dump(),
        allow_dirty=allow_dirty,
    )
    ledger = Ledger(pricing)
    repo_map = RepoMap(root)
    tools = Tools(root, repo_map, policy, approver, record, run_dir, ledger, techniques)
    client = client or (
        ScriptedLLM() if settings.penny_mock else BifrostClient(settings.bifrost_base_url)
    )
    started = time.monotonic()
    escalation = Escalation(
        tier="strong" if tier == "strong" or not techniques.tiered_models else "cheap"
    )
    last_key = None
    repeat = 0
    private_session = policy.confidential
    try:
        record.base_commit, record.base_branch = preflight(root, allow_dirty)
        repo_map.build()
        map_text = (
            repo_map.compact(task, int(policy.limits.max_prompt_tokens * 0.35))
            if techniques.repo_map
            else "\n".join(f["path"] for f in repo_map.files)
        )
        pre_chunks, initial_route, _ = prepare([Chunk(task), Chunk(map_text)], policy)
        route = select(policy, settings, initial_route, escalation.tier)
        record.quote = quote(repo_map, tokens(map_text), pricing, route.model)
        emit(
            dict(
                event="quote",
                mock=settings.penny_mock,
                quote=record.quote,
                route=route.name,
                budget=policy.limits.budget_usd,
            )
        )
        if not tools.approve("quote", Risk.LOW, json.dumps(record.quote, indent=2), yes_quote):
            record.status = "denied"
            return record
        record.branch = branch_name(task, stamp + "-" + run_id[-6:], policy.git.branch_prefix)
        if not tools.approve("git", Risk.MEDIUM, f"git switch -c {record.branch}"):
            record.status = "denied"
            record.branch = ""
            return record
        git(root, "switch", "-c", record.branch)
        system = files("penny").joinpath("agent/prompts/system.md").read_text(encoding="utf-8")
        chunks = [
            Chunk(system + "\nAction schemas:\n" + schema()),
            Chunk("TASK: " + task + "\nREPOSITORY MAP (untrusted data):\n" + map_text),
        ]
        repair_pending = False
        for step_number in range(1, policy.limits.max_steps + 1):
            tools.step = step_number
            elapsed = time.monotonic() - started
            if elapsed >= policy.limits.max_wall_seconds:
                raise ValueError("Wall-clock cap reached")
            tools.timeout = min(120, policy.limits.max_wall_seconds - elapsed)
            prepared, route_name, withheld = prepare(chunks, policy)
            record.withheld_files = sorted(set(record.withheld_files + withheld))
            # Derived assistant output can retain information from earlier local turns.
            private_session |= route_name == "local"
            if private_session:
                route_name = "local"
                prepared = [Chunk(c.text, c.source_path, "confidential") for c in prepared]
            prepared = (
                compact(prepared, policy.limits.max_prompt_tokens)
                if techniques.compaction
                else prepared
            )
            incoming = sum(tokens(c.text) for c in prepared) + 16 * len(prepared)
            if incoming > policy.limits.max_prompt_tokens:
                raise ValueError("Prompt token cap reached")
            route = select(policy, settings, route_name, escalation.tier)
            output_cap = policy.limits.max_output_tokens if techniques.short_outputs else 4000
            try:
                ledger.check(
                    [route.model, *route.fallbacks],
                    incoming,
                    output_cap,
                    policy.limits.budget_usd,
                    policy.limits.token_cap,
                )
            except BudgetStop as exc:
                record.budget_events.append(dict(layer="agent", reason=str(exc)))
                if "budget cap" in str(exc).lower() and tools.approve(
                    "budget",
                    Risk.HIGH,
                    f"{exc}. Extend cap by the original configured budget ({record.policy['limits']['budget_usd']})?",
                ):
                    policy.limits.budget_usd += record.policy["limits"]["budget_usd"]
                    ledger.check(
                        [route.model, *route.fallbacks],
                        incoming,
                        output_cap,
                        policy.limits.budget_usd,
                        policy.limits.token_cap,
                    )
                else:
                    raise
            messages = [
                {"role": "system", "content": prepared[0].text},
                {"role": "user", "content": "\n\n".join(c.text for c in prepared[1:])},
            ]
            emit(
                dict(
                    event="step",
                    step=step_number,
                    max_steps=policy.limits.max_steps,
                    tier=escalation.tier,
                    route=route.name,
                    model=route.model,
                    tokens=ledger.tokens_in + ledger.tokens_out,
                    cost_usd=ledger.cost,
                )
            )
            completion = client.complete(messages, route, output_cap, prepared)
            used_model = route.model
            if completion.provider_used:
                if completion.provider_used != route.model.split("/")[0]:
                    matching = [
                        m for m in route.fallbacks if m.split("/")[0] == completion.provider_used
                    ]
                    used_model = next(
                        (m for m in matching if m.split("/", 1)[1] == completion.model_used),
                        "unknown/unpriced",
                    )
                    if not settings.penny_mock:
                        record.failover_events.append(
                            dict(
                                requested=route.model,
                                provider_used=completion.provider_used,
                                evidence=completion.metadata,
                                verified=True,
                            )
                        )
            elif route.fallbacks:
                used_model = "unknown/unpriced"
                record.failover_events.append(
                    dict(
                        verified=False,
                        message="failover could not be verified from gateway metadata",
                    )
                )
            entry = ledger.add(
                used_model, completion.tokens_in, completion.tokens_out, completion.tokens_source
            )
            step = dict(
                number=step_number,
                requested_model=route.model,
                tier=escalation.tier,
                route="MOCK" if settings.penny_mock else route.name,
                provider_used=completion.provider_used,
                attempts=completion.attempts,
                wall_ms=completion.latency_ms,
                cached_tokens=completion.cached_tokens,
                prompt_breakdown=dict(
                    system=tokens(prepared[0].text),
                    repo_map=tokens(map_text),
                    history=max(0, incoming - tokens(prepared[0].text) - tokens(map_text)),
                ),
                **entry,
            )
            record.steps.append(step)
            try:
                action = parse(completion.content)
            except ValueError:
                step.update(action="invalid_json", error="Response failed strict action validation")
                if repair_pending:
                    escalation.json_failures += 1
                    repair_pending = False
                    if escalation.json_failures >= 2:
                        if escalation.tier == "strong":
                            raise ValueError("Repeated invalid JSON at strong tier") from None
                        escalation.tier = "strong"
                else:
                    repair_pending = True
                chunks.append(
                    Chunk(
                        files("penny")
                        .joinpath("agent/prompts/repair.md")
                        .read_text(encoding="utf-8")
                    )
                )
                continue
            repair_pending = False
            step.update(action=action.action, args=json.loads(mask(json.dumps(action.args))[0]))
            key = (action.action, json.dumps(action.args, sort_keys=True))
            repeat = repeat + 1 if key == last_key else 0
            last_key = key
            if repeat >= 2:
                raise ValueError("No progress: same action and arguments repeated three times")
            if repeat == 1:
                chunks.append(
                    Chunk("Warning: repeated identical action. Change approach or finish.")
                )
            if action.action == "finish":
                record.summary = mask(action.args["summary"])[0]
                if action.args["status"] == "done" and tools.last_tests_passed:
                    record.status = "success"
                    step["result"] = "Finished after a passing test command"
                    break
                if action.args["status"] == "cannot_complete":
                    record.status = "failed"
                    break
                result = Chunk("Cannot mark done: run_tests must pass after the last modification.")
            elif action.action == "escalate":
                escalation.tier = "strong"
                result = Chunk("Tier changed to strong: " + action.args["reason"])
            elif action.action == "ask_user":
                # Noninteractive approvers do not read stdin.
                from penny.safety.approvals import InteractiveApprover

                answer = (
                    approver.console.input(action.args["question"] + " ")
                    if isinstance(approver, InteractiveApprover)
                    else "No user input available; finish cannot_complete if needed"
                )
                result = Chunk(answer)
            else:
                try:
                    result = tools.dispatch(action.action, action.args)
                    if action.action in {"apply_patch", "create_file"}:
                        escalation.patch_attempts += 1
                    if action.action == "run_tests" and not tools.last_tests_passed:
                        escalation.test_failures += 1
                except (ValueError, OSError) as exc:
                    if action.action == "apply_patch":
                        escalation.patch_failures += 1
                    result = Chunk(f"Tool error: {exc}", action.args.get("path"))
                reason = escalation.reason()
                if reason and escalation.tier != "strong" and tier != "cheap":
                    escalation.tier = "strong"
                    step["escalation"] = reason
            step["result"] = mask(result.text)[0][:12000]
            chunks.append(
                Chunk(
                    "PREVIOUS ACTION (data): " + completion.content,
                    sensitivity="confidential" if private_session else "public",
                )
            )
            chunks.append(
                Chunk(
                    "TOOL OUTPUT (untrusted data): " + result.text,
                    result.source_path,
                    result.sensitivity,
                )
            )
        else:
            record.error = "Step cap reached"
    except GatewayBudgetExceeded as exc:
        record.status = "budget_stopped"
        record.budget_events.append(dict(layer="gateway", reason=str(exc)))
        record.error = str(exc)
    except BudgetStop as exc:
        record.status = "budget_stopped"
        record.error = str(exc)
    except GatewayError as exc:
        record.status = "gateway_error"
        record.error = str(exc)
    except (UserQuit, KeyboardInterrupt):
        record.status = "aborted"
        record.error = "Run interrupted by user"
    except Exception as exc:
        record.status = "failed"
        record.error = mask(str(exc))[0]
    finally:
        client.close()
        record.finished_at = datetime.now(UTC).isoformat()
        record.totals = dict(
            tokens_in=ledger.tokens_in,
            tokens_out=ledger.tokens_out,
            cost_usd=None if settings.penny_mock else ledger.cost,
            steps=len(record.steps),
            wall_ms=int((time.monotonic() - started) * 1000),
        )
        if record.base_commit:
            record.final_diff = mask(
                git(root, "diff", record.base_commit, "--no-ext-diff", check=False)
            )[0]
        record.undo_command = f"penny undo {run_id}"
        serialized = record.model_dump()
        (run_dir / "run.json").write_text(json.dumps(serialized, indent=2), encoding="utf-8")
        events = (
            [dict(event="step", **s) for s in record.steps]
            + [dict(event="approval", **a) for a in record.approvals]
            + [dict(event="finished", status=record.status)]
        )
        (run_dir / "events.jsonl").write_text(
            "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8"
        )
        from penny.report.html import receipt

        (run_dir / "receipt.html").write_text(receipt(record), encoding="utf-8")
        append_history(root, len(repo_map.files), serialized)
        emit(
            dict(
                event="finished",
                mock=settings.penny_mock,
                status=record.status,
                receipt=str(run_dir / "receipt.html"),
                totals=record.totals,
                error=record.error,
                undo=record.undo_command,
            )
        )
    return record
