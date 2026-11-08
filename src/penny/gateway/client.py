import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx

from penny.agent.guard import Chunk, RouteGuard
from penny.cost.estimate import tokens
from penny.gateway.errors import (
    AllProvidersFailed,
    AuthError,
    BadRequest,
    GatewayBudgetExceeded,
    GatewayUnreachable,
    RateLimited,
    Timeout,
)
from penny.gateway.routing import Route


@dataclass
class Completion:
    content: str
    tokens_in: int
    tokens_out: int
    tokens_source: str
    cached_tokens: int = 0
    provider_used: str | None = None
    model_used: str | None = None
    attempts: int = 1
    latency_ms: int = 0
    metadata: dict | None = None


def retry_delay(value: str) -> float:
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            return max(0, (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds())
        except (ValueError, TypeError):
            return 1.0


class BifrostClient:
    def __init__(self, base_url: str, transport=None, sleep=time.sleep):
        self.http = httpx.Client(
            base_url=base_url.rstrip("/") + "/",
            timeout=httpx.Timeout(60, connect=5),
            transport=transport,
            follow_redirects=False,
        )
        self.sleep = sleep

    def close(self):
        self.http.close()

    def complete(
        self, messages: list[dict], route: Route, max_output: int, chunks: list[Chunk]
    ) -> Completion:
        RouteGuard.assert_allowed(chunks, route.name)
        if not route.key:
            raise AuthError(f"Missing BIFROST_VK_{'LOCAL' if route.name == 'local' else 'DEV'}")
        payload = dict(
            model=route.model,
            messages=messages,
            max_tokens=max_output,
            temperature=0,
            fallbacks=route.fallbacks,
        )
        started = time.monotonic()
        for attempt in range(1, 4):
            try:
                response = self.http.post(
                    "v1/chat/completions", json=payload, headers={"x-bf-vk": route.key}
                )
            except httpx.TimeoutException as exc:
                raise Timeout(
                    "Gateway timed out; stopped to avoid duplicate billed requests"
                ) from exc
            except httpx.RequestError as exc:
                raise GatewayUnreachable("Gateway not reachable. Start it with `make up`.") from exc
            if response.is_error:
                # Bifrost governance budget errors carry budget wording. Preserve no raw
                # upstream text because error bodies may echo credentials or prompts.
                body = response.text.lower()
                if "budget" in body and any(
                    w in body for w in ("exceeded", "exhausted", "limit", "blocked")
                ):
                    raise GatewayBudgetExceeded("Budget enforced by the gateway virtual key")
                if response.status_code == 429:
                    delay = retry_delay(response.headers.get("Retry-After", "1"))
                    if attempt < 3 and delay <= 60:
                        self.sleep(delay)
                        continue
                    raise RateLimited("Gateway rate limit; retry later")
                if response.status_code in {401, 403}:
                    raise AuthError("Gateway rejected virtual key or provider/model access")
                if response.status_code >= 500:
                    raise AllProvidersFailed(
                        f"Gateway upstream failure HTTP {response.status_code}"
                    )
                raise BadRequest(f"Gateway rejected request HTTP {response.status_code}")
            try:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                if not isinstance(content, str):
                    raise ValueError("Non-text completion")
                usage = data.get("usage") or {}
                authoritative = "prompt_tokens" in usage and "completion_tokens" in usage
                metadata = data.get("extra_fields") or {}
                provider = metadata.get("provider")
                if provider is not None and not isinstance(provider, str):
                    raise ValueError("Invalid provider metadata")
                return Completion(
                    content=content,
                    tokens_in=int(usage["prompt_tokens"])
                    if authoritative
                    else tokens(json.dumps(messages)),
                    tokens_out=int(usage["completion_tokens"])
                    if authoritative
                    else tokens(content),
                    tokens_source="provider" if authoritative else "estimate",
                    cached_tokens=int(
                        (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
                    ),
                    provider_used=provider,
                    model_used=data.get("model"),
                    attempts=attempt,
                    latency_ms=int((time.monotonic() - started) * 1000),
                    metadata={
                        k: metadata[k]
                        for k in ("provider", "model_requested", "model", "latency", "request_id")
                        if k in metadata
                    },
                )
            except (KeyError, IndexError, ValueError, TypeError) as exc:
                raise BadRequest("Gateway returned an invalid completion response") from exc
        raise RateLimited("Gateway rate limit")
