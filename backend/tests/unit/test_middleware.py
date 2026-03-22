"""
Unit tests for src/api/middleware/request_id.py — 100% coverage required.
"""
import re
import uuid

import pytest
from httpx import AsyncClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from src.api.middleware.request_id import RequestIDMiddleware


# ---------------------------------------------------------------------------
# Minimal test app
# ---------------------------------------------------------------------------

async def _homepage(request: Request):
    """Echo the request_id stored on request.state back in the body."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse({"request_id": request_id})


def _make_app() -> Starlette:
    app = Starlette(routes=[Route("/", _homepage)])
    app.add_middleware(RequestIDMiddleware)
    return app


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_response_has_x_request_id_header():
    client = TestClient(_make_app())
    resp = client.get("/")
    assert "X-Request-ID" in resp.headers


def test_x_request_id_is_valid_uuid4():
    client = TestClient(_make_app())
    resp = client.get("/")
    request_id = resp.headers["X-Request-ID"]
    parsed = uuid.UUID(request_id)
    assert parsed.version == 4


def test_request_id_set_on_request_state():
    client = TestClient(_make_app())
    resp = client.get("/")
    body_id = resp.json()["request_id"]
    header_id = resp.headers["X-Request-ID"]
    # The same ID should appear in both the response header and request.state
    assert body_id == header_id


def test_each_request_gets_unique_id():
    client = TestClient(_make_app())
    ids = {client.get("/").headers["X-Request-ID"] for _ in range(5)}
    assert len(ids) == 5


def test_existing_response_headers_preserved():
    async def _with_extra_header(request: Request):
        return JSONResponse({"ok": True}, headers={"X-Custom": "value"})

    app = Starlette(routes=[Route("/", _with_extra_header)])
    app.add_middleware(RequestIDMiddleware)
    client = TestClient(app)
    resp = client.get("/")
    assert resp.headers["X-Custom"] == "value"
    assert "X-Request-ID" in resp.headers


@pytest.mark.asyncio
async def test_request_id_present_on_async_client():
    app = _make_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/")
    assert "X-Request-ID" in resp.headers
    assert uuid.UUID(resp.headers["X-Request-ID"]).version == 4
