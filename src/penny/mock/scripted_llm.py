import json

from penny.gateway.client import Completion

DEMO_ACTIONS = [
    {"action": "search", "args": {"query": "paginate"}},
    {
        "action": "read_symbol",
        "args": {"path": "shopkit/utils/pagination.py", "symbol": "paginate"},
    },
    {
        "action": "apply_patch",
        "args": {
            "path": "shopkit/utils/pagination.py",
            "edits": [
                {"search": "start = page * page_size", "replace": "start = (page - 1) * page_size"}
            ],
        },
    },
    {"action": "run_tests", "args": {}},
    {
        "action": "finish",
        "args": {
            "summary": "Corrected pagination and ran the tests (MOCK scripted model).",
            "status": "done",
        },
    },
]


class ScriptedLLM:
    """Test/UI development double; no real model outputs or performance measurements."""

    def __init__(self, actions=None):
        self.actions = iter(DEMO_ACTIONS if actions is None else actions)

    def complete(self, messages, route, max_output, chunks):
        action = next(
            self.actions,
            {
                "action": "finish",
                "args": {"summary": "Script exhausted", "status": "cannot_complete"},
            },
        )
        content = (
            action
            if isinstance(action, str)
            else json.dumps({"thought": "MOCK scripted action", **action})
        )
        return Completion(
            content, 100, 30, "mock", provider_used="mock", model_used="mock/scripted"
        )

    def close(self):
        pass
