"""Integration tests for system routes."""
import pytest
from httpx import ASGITransport, AsyncClient

from config.settings import settings
from src.api.dependencies import get_current_session


def _mock_session():
    return {"session_token": "test-token", "risk_profile": "moderate", "preferences": {}}


@pytest.mark.asyncio
async def test_update_system_config_requires_admin_token(monkeypatch):
    from src.api.main import create_app

    monkeypatch.setattr(settings, "admin_api_token", "test-admin-token")
    app = create_app()
    app.dependency_overrides[get_current_session] = lambda: _mock_session()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/system/config",
            params={"key": "paper_trading_balance", "value": 100000},
        )

    assert resp.status_code == 403
    assert resp.json()["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_update_system_config_fails_closed_when_admin_token_unset(monkeypatch):
    from src.api.main import create_app

    monkeypatch.setattr(settings, "admin_api_token", None)
    app = create_app()
    app.dependency_overrides[get_current_session] = lambda: _mock_session()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/system/config",
            params={"key": "paper_trading_balance", "value": 100000},
            headers={"X-Admin-Token": "anything"},
        )

    assert resp.status_code == 403
    assert "not configured" in resp.json()["error"]


@pytest.mark.asyncio
async def test_ingestion_status_disabled_by_default(monkeypatch):
    from src.api.main import create_app

    monkeypatch.setattr(settings, "ingestion_kafka_enabled", False)
    monkeypatch.setattr(settings, "ingestion_dask_enabled", False)
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/system/ingestion/status")

    assert resp.status_code == 200
    ingestion = resp.json()["ingestion_layer"]
    assert ingestion["status"] == "disabled"
    assert ingestion["kafka"]["enabled"] is False
    assert ingestion["dask"]["enabled"] is False


@pytest.mark.asyncio
async def test_ingestion_health_enabled_reports_degraded_contract(monkeypatch):
    from src.api.main import create_app

    monkeypatch.setattr(settings, "ingestion_kafka_enabled", True)
    monkeypatch.setattr(settings, "ingestion_dask_enabled", True)
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/system/ingestion/health")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["healthy"] is False
    assert payload["status"] == "degraded"
    assert payload["components"]["kafka_producer"] == "pending"
    assert payload["components"]["dask_cluster"] == "pending"


@pytest.mark.asyncio
async def test_detailed_health_does_not_mock_external_services_as_healthy(monkeypatch):
    from src.api.main import create_app
    import src.api.routes.system as system_routes

    async def fake_db_health():
        return {"status": "healthy", "connection": "active", "backend": "postgresql"}

    async def fake_redis_health():
        return {"status": "disabled", "enabled": False}

    monkeypatch.setattr(system_routes, "db_health_check", fake_db_health)
    monkeypatch.setattr(system_routes, "redis_health_check", fake_redis_health)
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "alpaca_api_key", None)
    monkeypatch.setattr(settings, "alpaca_secret_key", None)
    monkeypatch.setattr(settings, "jigsawstack_api_key", None)

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/system/health")

    assert resp.status_code == 200
    services = resp.json()["components"]["external_services"]
    assert services["openai"]["status"] == "unconfigured"
    assert services["alpaca"]["status"] == "unconfigured"
    assert services["jigsawstack"]["status"] == "unconfigured"


def test_create_app_registers_legacy_frontend_routes():
    from src.api.main import create_app

    app = create_app()
    paths = set(app.openapi()["paths"])

    assert "/api/v1/stocks/hot-stocks" in paths
    assert "/api/v1/agents/{symbol}" in paths
    assert "/api/v1/technical/{symbol}" in paths
    assert "/api/v1/signals/{symbol}" in paths
    assert "/api/v1/options/{symbol}" in paths
    assert "/api/v1/options/execute" in paths
    assert "/api/v1/chat/trade" in paths
    assert "/api/v1/session/create" in paths
    assert "/api/v1/session/info" in paths
