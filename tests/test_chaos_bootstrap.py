import importlib.util
import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from penny.chaos.proxy import create_app


def test_chaos_modes_and_header_forwarding():
    async def no_wait(seconds):
        assert seconds == 90

    def upstream(request):
        assert request.headers["authorization"] == "Bearer private-fixture"
        assert request.url.host == "upstream.invalid"
        return httpx.Response(200, json={"ok": True})

    app = create_app(
        "https://upstream.invalid", transport=httpx.MockTransport(upstream), timeout_sleep=no_wait
    )
    with TestClient(app) as client:
        for mode, code in [("503", 503), ("429", 429), ("timeout", 504)]:
            assert client.post("/admin/mode", json={"mode": mode}).status_code == 200
            assert client.post("/v1/chat/completions").status_code == code
        client.post("/admin/mode", json={"mode": "off"})
        assert client.post(
            "/v1/chat/completions", headers={"authorization": "Bearer private-fixture"}
        ).json()["ok"]
        assert client.get("/admin/mode").json()["mode"] == "off"
        assert client.post("/admin/mode", json={"mode": "invalid"}).status_code == 422


def test_bootstrap_api_payloads():
    spec = importlib.util.spec_from_file_location("bootstrap", Path("scripts/bootstrap_bifrost.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    created = []

    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, json={"virtual_keys": []})
        payload = json.loads(request.content)
        created.append(payload)
        return httpx.Response(200, json={"virtual_key": {"value": "fixture-key"}})

    with httpx.Client(
        base_url="http://gateway.invalid", transport=httpx.MockTransport(handler)
    ) as client:
        module.bootstrap("", {}, client)
    assert len(created) == 3
    local = next(c for c in created if c["name"] == "penny-local")
    assert [p["provider"] for p in local["provider_configs"]] == ["ollama"]
    assert all(c["provider_configs"][0]["key_ids"] == ["*"] for c in created)
    assert created[0]["budgets"][0]["max_limit"] == 0.5
