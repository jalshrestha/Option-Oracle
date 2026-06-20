"""Integration tests for chat route contracts."""
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_chat_message_accepts_frontend_selected_stock(monkeypatch):
    from src.api.main import create_app
    from src.api import chat_router

    mock_route = AsyncMock(return_value={
        "response": "AAPL analysis is ready.",
        "intent": "STOCK_ANALYSIS",
        "symbol": "AAPL",
        "tools_called": ["analyze_stock"],
        "tool_results": [{"tool": "analyze_stock", "symbol": "AAPL"}],
        "confidence": 0.9,
        "timestamp": "2026-01-01T00:00:00",
    })
    monkeypatch.setattr(chat_router, "route_with_ai", mock_route)

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/chat/message",
            json={"message": "analyze this", "selectedStock": "AAPL"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["actions"]["analyzeStock"] == "AAPL"
    assert data["agents_triggered"] == ["technical", "sentiment", "flow", "history", "risk"]
    mock_route.assert_awaited_once()
    assert mock_route.await_args.args[1]["selectedStock"] == "AAPL"


@pytest.mark.asyncio
async def test_chat_message_includes_thread_memory_context(monkeypatch):
    from src.api.main import create_app
    from src.api import chat_router

    class FakeHistoryService:
        def __init__(self, db):
            pass

        async def ensure_thread(self, session_id, thread_id, first_message):
            return {"id": thread_id or "thread-1"}

        async def get_memory_context(self, session_id, thread_id):
            return [
                {"role": "user", "content": "Analyze AAPL"},
                {"role": "assistant", "content": "AAPL is a watchlist candidate."},
            ]

        async def append_message(self, *args, **kwargs):
            return None

    mock_route = AsyncMock(return_value={
        "response": "Still discussing AAPL.",
        "intent": "GENERAL_CHAT",
        "tools_called": [],
        "tool_results": [],
        "confidence": 0.7,
        "timestamp": "2026-01-01T00:00:00",
    })
    monkeypatch.setattr(chat_router, "ChatHistoryService", FakeHistoryService)
    monkeypatch.setattr(chat_router, "route_with_ai", mock_route)

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/chat/message",
            json={"message": "what about calls?", "session_id": "session-1", "thread_id": "thread-1"},
        )

    assert resp.status_code == 200
    assert resp.json()["thread_id"] == "thread-1"
    context = mock_route.await_args.args[1]
    assert context["thread_id"] == "thread-1"
    assert context["conversation_history"][0]["content"] == "Analyze AAPL"


@pytest.mark.asyncio
async def test_chat_route_endpoint_uses_existing_ai_router(monkeypatch):
    from src.api.main import create_app
    from src.api import chat_router

    monkeypatch.setattr(
        chat_router,
        "route_with_ai",
        AsyncMock(return_value={
            "response": "ok",
            "intent": "GENERAL_CHAT",
            "tools_called": [],
            "tool_results": [],
            "confidence": 0.7,
            "timestamp": "2026-01-01T00:00:00",
        }),
    )

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/chat/route", json={"message": "hello"})

    assert resp.status_code == 200
    assert resp.json()["routing_plan"]["intent"] == "GENERAL_CHAT"
