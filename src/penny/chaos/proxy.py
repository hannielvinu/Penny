import asyncio
import os
from contextlib import asynccontextmanager
from typing import Literal

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict


class Mode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["off", "503", "429", "timeout"]


def create_app(upstream: str | None = None, transport=None, timeout_sleep=asyncio.sleep) -> FastAPI:
    upstream = upstream or os.getenv("CHAOS_UPSTREAM_URL", "")

    @asynccontextmanager
    async def lifespan(app):
        yield

    app = FastAPI(title="Penny chaos harness", lifespan=lifespan)
    app.state.mode = "off"

    @app.get("/admin/mode")
    async def status():
        return {"mode": app.state.mode, "harness": True}

    @app.post("/admin/mode")
    async def mode(value: Mode):
        app.state.mode = value.mode
        return {"mode": app.state.mode}

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def forward(path: str, request: Request):
        if app.state.mode == "503":
            return JSONResponse(
                {"error": {"message": "Penny chaos: upstream unavailable"}}, status_code=503
            )
        if app.state.mode == "429":
            return JSONResponse(
                {"error": {"message": "Penny chaos: rate limited"}},
                status_code=429,
                headers={"Retry-After": "1"},
            )
        if app.state.mode == "timeout":
            await timeout_sleep(90)
            return JSONResponse({"error": {"message": "Penny chaos: timeout"}}, status_code=504)
        if not upstream:
            return JSONResponse({"error": "CHAOS_UPSTREAM_URL not configured"}, status_code=503)
        # Forward only data-plane headers, never log credentials. Fixed upstream;
        # incoming paths cannot override the host or address the admin API upstream.
        headers = {
            k: v
            for k, v in request.headers.items()
            if k.lower()
            in {"authorization", "content-type", "accept", "anthropic-version", "x-api-key"}
        }
        url = upstream.rstrip("/") + "/" + path.lstrip("/")
        try:
            async with httpx.AsyncClient(
                timeout=65, transport=transport, follow_redirects=False
            ) as client:
                response = await client.request(
                    request.method,
                    url,
                    params=request.query_params,
                    headers=headers,
                    content=await request.body(),
                )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers={
                    k: v
                    for k, v in response.headers.items()
                    if k.lower() in {"content-type", "retry-after"}
                },
            )
        except httpx.HTTPError:
            return JSONResponse({"error": "Chaos upstream request failed"}, status_code=502)

    return app


app = create_app()
