import json

import httpx
import pytest

from penny.agent.guard import Chunk
from penny.gateway.client import BifrostClient, retry_delay
from penny.gateway.errors import (
    AllProvidersFailed,
    AuthError,
    BadRequest,
    GatewayBudgetExceeded,
    GatewayUnreachable,
    RateLimited,
    Timeout,
)
from penny.gateway.routing import Route, select


def payload(
    content='{"thought":"ok","action":"finish","args":{"status":"cannot_complete","summary":"done"}}',
    usage=True,
    provider="test",
):
    value = {
        "choices": [{"message": {"content": content}}],
        "model": "model",
        "extra_fields": {"provider": provider},
    }
    if usage:
        value["usage"] = {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "prompt_tokens_details": {"cached_tokens": 3},
        }
    return value


def client_for(handler):
    return BifrostClient(
        "http://gateway.invalid", transport=httpx.MockTransport(handler), sleep=lambda _: None
    )


def test_completion_usage_headers_and_fallbacks():
    def handler(request):
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["x-bf-vk"] == "test-key"
        body = json.loads(request.content)
        assert body["fallbacks"] == ["other/model"]
        return httpx.Response(200, json=payload())

    client = client_for(handler)
    response = client.complete(
        [dict(role="user", content="hello")],
        Route("cloud", "test/model", "test-key", ["other/model"]),
        100,
        [Chunk("hello")],
    )
    assert (response.tokens_in, response.tokens_out, response.cached_tokens) == (10, 5, 3)
    assert response.provider_used == "test" and response.tokens_source == "provider"
    client.close()


@pytest.mark.parametrize(
    "code,body,error",
    [
        (403, "not allowed", AuthError),
        (401, "unauthorized", AuthError),
        (400, "invalid", BadRequest),
        (503, "down", AllProvidersFailed),
        (429, "rate limit", RateLimited),
        (403, "virtual key budget exceeded", GatewayBudgetExceeded),
        (429, "budget limit exceeded", GatewayBudgetExceeded),
    ],
)
def test_errors(code, body, error):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(code, text=body, headers={"Retry-After": "0"})

    client = client_for(handler)
    with pytest.raises(error):
        client.complete([], Route("cloud", "test/model", "key", []), 100, [])
    assert len(calls) == (3 if error == RateLimited else 1)
    client.close()


def test_missing_usage_and_guard():
    client = client_for(lambda _: httpx.Response(200, json=payload("hello", False)))
    response = client.complete(
        [],
        Route("local", "ollama/model", "key", []),
        100,
        [Chunk("private", sensitivity="confidential")],
    )
    assert response.tokens_source == "estimate"
    with pytest.raises(ValueError, match="Confidential"):
        client.complete(
            [],
            Route("cloud", "test/model", "key", []),
            100,
            [Chunk("private", sensitivity="confidential")],
        )
    with pytest.raises(AuthError):
        client.complete([], Route("cloud", "test/model", "", []), 100, [])
    client.close()


@pytest.mark.parametrize(
    "exception,expected",
    [(httpx.ConnectError("down"), GatewayUnreachable), (httpx.ReadTimeout("timeout"), Timeout)],
)
def test_transport_errors(exception, expected):
    def handler(request):
        raise exception

    with pytest.raises(expected):
        client_for(handler).complete([], Route("cloud", "test/model", "key", []), 10, [])


def test_invalid_response_and_retry_date():
    with pytest.raises(BadRequest):
        client_for(lambda _: httpx.Response(200, json={})).complete(
            [], Route("cloud", "test/model", "key", []), 10, []
        )
    assert retry_delay("bad") == 1
    assert retry_delay("-1") == 0
    assert retry_delay("Thu, 01 Jan 1970 00:00:00 GMT") == 0


def test_routes(policy, mock_settings):
    policy.models.fallbacks = ["another/model"]
    assert select(policy, mock_settings, "cloud", "cheap").fallbacks == ["another/model"]
    assert select(policy, mock_settings, "local", "strong").fallbacks == []
    policy.models.fallbacks = ["ollama/model"]
    with pytest.raises(ValueError):
        select(policy, mock_settings, "cloud", "cheap")
    policy.models.local = "cloud/model"
    with pytest.raises(ValueError):
        select(policy, mock_settings, "local", "cheap")
