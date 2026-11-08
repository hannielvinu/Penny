import json
import os

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme


class Terminal:
    def __init__(self, plain=False, json_mode=False):
        self.json_mode = json_mode
        self.console = Console(
            no_color=plain or bool(os.getenv("NO_COLOR")),
            theme=Theme(
                {"accent": "#B4440D", "good": "#166534", "bad": "#B42318", "local": "#1E40AF"}
            ),
            stderr=json_mode,
        )

    def emit(self, event):
        if self.json_mode:
            print(json.dumps(event, ensure_ascii=True))
            return
        kind = event["event"]
        if kind == "quote":
            q = event["quote"]
            self.console.print(
                Panel(
                    f"Estimate: {q['low']:,}–{q['high']:,} tokens\n{q['assumptions']}\nRoute: {event['route'].upper()} · cap {event['budget']} USD\n"
                    + (
                        f"Estimated cost: ${q['cost_low']:.6f}–${q['cost_high']:.6f}"
                        if q["cost_low"] is not None
                        else "price not configured; token cap applies"
                    ),
                    title="Penny · Quote",
                )
            )
        elif kind == "step":
            self.console.print(
                f"Step {event['step']}/{event['max_steps']} · {event['model']} · {event['route'].upper()} · {event['tokens']:,} tokens",
                style="accent",
            )
        elif kind == "finished":
            self.console.print(
                Panel(
                    Text(
                        f"Status: {event['status'].upper()}\nTokens: {event['totals']['tokens_in']:,} in / {event['totals']['tokens_out']:,} out\nReceipt: {event['receipt']}\n{event.get('error') or ''}\nUndo: {event['undo']}\nBrowse all receipts: penny report"
                    ),
                    title="MOCK receipt" if event["mock"] else "Penny · Receipt",
                )
            )
