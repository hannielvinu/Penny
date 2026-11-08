import base64
import json
from html import escape
from importlib.resources import files

from penny.report.charts import grouped, quote_chart
from penny.report.model import RunRecord
from penny.version import __version__

SCRIPT = """
(()=>{const root=document.documentElement;const b=document.getElementById('theme');
try{const t=localStorage.getItem('penny-theme');if(t)root.dataset.theme=t}catch(e){}
b.addEventListener('click',()=>{const dark=root.dataset.theme==='dark'||(!root.dataset.theme&&matchMedia('(prefers-color-scheme:dark)').matches);root.dataset.theme=dark?'light':'dark';try{localStorage.setItem('penny-theme',root.dataset.theme)}catch(e){}});
const c=document.getElementById('copy');if(c)c.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(document.getElementById('undo').textContent);c.textContent='Copied'}catch(e){c.textContent='Select command to copy'}});
const f=document.getElementById('filter');if(f)f.addEventListener('change',()=>document.querySelectorAll('[data-status]').forEach(r=>r.hidden=!!f.value&&r.dataset.status!==f.value));
addEventListener('beforeprint',()=>document.querySelectorAll('details').forEach(d=>{d.dataset.wasOpen=d.open;d.open=true}));
addEventListener('afterprint',()=>document.querySelectorAll('details').forEach(d=>d.open=d.dataset.wasOpen==='true'));
})();
"""


def e(value) -> str:
    return escape(str(value))


def dump(value) -> str:
    return e(json.dumps(value, indent=2, ensure_ascii=False))


def money(cost) -> str:
    return f"${cost:.6f}" if cost is not None else "price not configured"


def badge(label: str, css: str = "") -> str:
    return f'<span class="badge {e(css)}">● {e(label)}</span>'


def font_css() -> str:
    root = files("penny").joinpath("report/assets/fonts")
    result = ""
    if root.is_dir():
        for asset in root.iterdir():
            if asset.name.endswith(".woff2"):
                name = (
                    "Space Grotesk"
                    if "space-grotesk" in asset.name
                    else "IBM Plex Mono"
                    if "ibm-plex" in asset.name
                    else "Inter"
                )
                weight = (
                    "500"
                    if "-500-" in asset.name
                    else "400"
                    if "ibm-plex" in asset.name
                    else "100 900"
                )
                data = base64.b64encode(asset.read_bytes()).decode()
                result += f"@font-face{{font-family:'{name}';font-style:normal;font-weight:{weight};font-display:swap;src:url(data:font/woff2;base64,{data}) format('woff2')}}"
    return result


def page(title: str, body: str, mock=False) -> str:
    css = files("penny").joinpath("report/assets/style.css").read_text(encoding="utf-8")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><meta name="color-scheme" content="light dark"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; font-src data:; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'"><title>{e(title)} · Penny</title><style>{font_css()}{css}</style></head><body><a class="skip" href="#main">Skip to content</a><header><div class="brand">penny<span>.</span> <span class="edition">WORK ACCOUNTED FOR</span></div><nav aria-label="Receipt controls">{badge("MOCK", "mock") if mock else ""}<button type="button" id="theme" aria-label="Toggle light or dark theme">◐ Theme</button></nav></header><main id="main">{body}</main><footer>Penny {__version__} · Generated locally by Penny. No data was sent to create this page.{" · MOCK: scripted model and synthetic usage." if mock else ""}</footer><script>{SCRIPT}</script></body></html>"""


def receipt(record: RunRecord) -> str:
    r = record
    t = r.totals
    total_tokens = t.get("tokens_in", 0) + t.get("tokens_out", 0)
    mock = bool(r.flags.get("mock"))
    total = (
        money(t.get("cost_usd")) if t.get("cost_usd") is not None else f"{total_tokens:,} tokens"
    )
    approved = sum(bool(a["decision"]) for a in r.approvals)
    routes = sorted({s.get("route", "unknown").upper() for s in r.steps})
    hero = f'<div class="hero"><p class="edition">RECEIPT / {e(r.id)}</p><h1>{e(r.task)}</h1><div class="total">{e(total)}</div><p>{badge(r.status.upper(), r.status)} {" ".join(badge(v, v.lower()) for v in routes)}</p><p class="muted">{e("MOCK synthetic usage. " if mock else "")}{e(money(t.get("cost_usd")) if t.get("cost_usd") is None else "Configured prices applied to reported usage")} · {e(r.summary or r.error or "Run ended")}</p></div>'
    cards = [
        ("Tokens in / out", f"{t.get('tokens_in', 0):,} / {t.get('tokens_out', 0):,}"),
        ("Steps / wall time", f"{t.get('steps', 0)} / {t.get('wall_ms', 0) / 1000:.1f}s"),
        ("Approvals: approved / denied", f"{approved} / {len(r.approvals) - approved}"),
        (
            "Models requested",
            ", ".join(sorted({s.get("requested_model", "") for s in r.steps})) or "No model calls",
        ),
        (
            "Tier escalations",
            str(sum(bool(s.get("escalation")) or s.get("action") == "escalate" for s in r.steps)),
        ),
        (
            "Failover evidence",
            f"{sum(bool(v.get('verified')) for v in r.failover_events)} verified / {sum(not v.get('verified') for v in r.failover_events)} unverified",
        ),
    ]
    body = (
        hero
        + '<div class="grid">'
        + "".join(
            f'<div class="card"><span class="label">{e(label)}</span><span class="value">{e(value)}</span></div>'
            for label, value in cards
        )
        + "</div>"
    )
    q = r.quote
    low, high = q.get("low", 0), q.get("high", 0)
    error = (total_tokens - (low + high) / 2) / ((low + high) / 2) * 100 if high + low else 0
    body += f'<section class="panel"><h2>Estimate, meet reality.</h2><p>Estimate was {low:,}–{high:,} tokens. Actual: {total_tokens:,}. Error versus midpoint: {error:+.1f}%.</p><p class="muted">{e(q.get("assumptions", "No quote available"))}</p>{quote_chart(low, high, total_tokens)}</section>'
    body += '<section class="panel"><h2>The work, step by step.</h2><ol class="timeline">'
    for s in r.steps:
        body += f'<li><div class="stephead"><strong><span class="stepnum">{s["number"]:02d}</span> {e(s.get("action", "call"))}</strong>{badge(s.get("route", "unknown").upper(), s.get("route", "").lower())}<span class="mono">{s.get("tokens_in", 0):,} in / {s.get("tokens_out", 0):,} out · {e(money(s.get("cost_usd")))}</span></div><p class="muted">{e(s.get("tier"))} · {s.get("wall_ms", 0)} ms · usage: {e(s.get("tokens_source"))}</p><details><summary>Arguments, result and accounting</summary><pre>{dump(s)}</pre></details></li>'
    body += '</ol></section><section class="panel"><h2>Safety log</h2><table class="safety-table"><thead><tr><th>Operation</th><th>Decision</th><th>What was approved</th></tr></thead><tbody>'
    for a in r.approvals:
        body += f'<tr><td>{e(a["kind"])}<br>{badge(a["risk"])}</td><td>{badge("APPROVED" if a["decision"] else "DENIED", "success" if a["decision"] else "denied")}<p class="muted">{e(a["timestamp"])}</p></td><td><details><summary>Review exact operation</summary><pre>{e(a["content"])}</pre></details></td></tr>'
    body += "</tbody></table></section>"
    body += f'<section class="panel"><h2>Resilience</h2><p>{"Failover events recorded below." if r.failover_events else "No failover verified in this run."}</p><pre>{dump(r.failover_events)}</pre><h3>Withheld context</h3><p>{e(", ".join(r.withheld_files) or "None")}</p></section>'
    body += f'<section class="panel"><h2>Budget</h2><p>Agent cap: {e(r.policy.get("limits", {}).get("budget_usd", "unknown"))} USD. Gateway cap is configured independently.</p><pre>{dump(r.budget_events) if r.budget_events else "No budget block recorded."}</pre></section>'
    diff = "\n".join(
        f'<span class="{"diff-add" if line.startswith("+") else "diff-del" if line.startswith("-") else ""}">{e(line)}</span>'
        for line in r.final_diff.splitlines()
    )
    body += f'<section class="panel"><h2>Files changed</h2><p>{e(", ".join(r.files_changed) or "None recorded")}</p><pre>{diff or "No tracked diff."}</pre></section>'
    body += '<section class="panel"><h2>Tests</h2>'
    for test in r.tests:
        body += f"<h3>{e(test['command'])}</h3><p>{badge('PASSED' if test['returncode'] == 0 else 'FAILED', 'success' if test['returncode'] == 0 else 'failed')}</p><pre>{e(test['output'])}</pre>"
    if not r.tests:
        body += "<p>No tests executed.</p>"
    body += f'</section><section class="panel"><h2>Undo this run</h2><p>Review the recorded branch and changes before undoing. Penny refuses automatic undo when subsequent changes are detected.</p><pre id="undo">{e(r.undo_command)}</pre><button id="copy" type="button" aria-label="Copy undo command">Copy command</button></section>'
    return page(f"Receipt {r.id}", body, mock)


def index(records: list[RunRecord]) -> str:
    body = '<div class="hero"><p class="edition">YOUR WORK LEDGER</p><h1>Every run. Accounted for.</h1><p class="muted">Quotes, decisions and receipts, kept on your machine.</p></div><label for="filter">Filter by status </label><select id="filter"><option value="">All statuses</option>'
    body += (
        "".join(
            f'<option value="{s}">{s}</option>'
            for s in ("success", "failed", "budget_stopped", "denied", "aborted", "gateway_error")
        )
        + "</select>"
    )
    if not records:
        body += '<section class="panel"><h2>Your first receipt starts here.</h2><p>Run <code>penny run "your task"</code> in an initialized Git repository.</p></section>'
    for r in sorted(records, key=lambda r: r.started_at, reverse=True):
        body += f'<article class="panel card" data-status="{e(r.status)}"><h2><a class="runlink" href="runs/{e(r.id)}/receipt.html">{e(r.task)}</a></h2><p>{badge(r.status.upper(), r.status)} {badge("MOCK", "mock") if r.flags.get("mock") else ""}</p><p>{r.totals.get("tokens_in", 0) + r.totals.get("tokens_out", 0):,} tokens · {e(money(r.totals.get("cost_usd")))}</p></article>'
    return page("Run ledger", body, any(r.flags.get("mock") for r in records))


def benchmark(result: dict | None = None) -> str:
    body = '<div class="hero"><p class="edition">MEASURED, NOT PROMISED</p><h1>Tokens spent. Work finished.</h1></div>'
    if not result:
        body += '<section class="panel"><h2>Not yet run</h2><p>A real Bifrost gateway, configured models and credentials are required. Mock benchmarking is refused.</p></section>'
    else:
        body += f'<section class="panel"><h2>Observed results</h2>{badge("SMALL SAMPLE") if result.get("small_sample") else ""}<p>Repetitions: {result["n"]} · Commit: {e(result["commit"])}</p><pre>{dump(result["summary"])}</pre></section>'
        for metric in ("tokens", "cost_usd", "steps"):
            body += f'<section class="panel"><h2>{e(metric)}</h2>{grouped(result["summary"], metric)}</section>'
    body += '<aside class="notice"><h2>Caveats</h2><p>Synthetic tasks, a simple baseline, and a small sample do not establish performance on other repositories. Other coding products were not compared. Unconfigured prices remain unknown.</p></aside>'
    return page("Benchmark", body)
