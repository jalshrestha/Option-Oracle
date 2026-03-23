"""
Unit tests for src/api/error_handlers.py and src/exceptions.py
Target: 100% coverage on both modules.
"""
import pytest
from unittest.mock import MagicMock
from fastapi import Request
from fastapi.exceptions import HTTPException

from src.exceptions import (
    OracleError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ExternalAPIError,
    DatabaseError,
    AnalysisTimeoutError,
)
from src.api.error_handlers import (
    oracle_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(path: str = "/test", method: str = "GET", request_id: str = "test-rid-123"):
    """Build a minimal mock Request with state.request_id."""
    req = MagicMock(spec=Request)
    req.method = method
    req.url.path = path
    req.state.request_id = request_id
    return req


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class TestOracleError:
    def test_base_defaults(self):
        err = OracleError()
        assert err.status_code == 500
        assert err.code == "INTERNAL_ERROR"
        assert "unexpected" in err.message.lower()

    def test_custom_message(self):
        err = OracleError("custom msg")
        assert err.message == "custom msg"

    def test_repr(self):
        err = OracleError("msg")
        assert "INTERNAL_ERROR" in repr(err)
        assert "msg" in repr(err)


class TestSubclasses:
    @pytest.mark.parametrize(
        "cls, expected_status, expected_code",
        [
            (NotFoundError, 404, "NOT_FOUND"),
            (ValidationError, 422, "VALIDATION_ERROR"),
            (RateLimitError, 429, "RATE_LIMIT_EXCEEDED"),
            (ExternalAPIError, 502, "EXTERNAL_API_ERROR"),
            (DatabaseError, 503, "DATABASE_ERROR"),
            (AnalysisTimeoutError, 504, "ANALYSIS_TIMEOUT"),
        ],
    )
    def test_status_and_code(self, cls, expected_status, expected_code):
        err = cls()
        assert err.status_code == expected_status
        assert err.code == expected_code

    @pytest.mark.parametrize(
        "cls",
        [NotFoundError, ValidationError, RateLimitError,
         ExternalAPIError, DatabaseError, AnalysisTimeoutError],
    )
    def test_custom_message_propagates(self, cls):
        err = cls("specific detail")
        assert err.message == "specific detail"
        assert str(err) == "specific detail"

    @pytest.mark.parametrize(
        "cls",
        [NotFoundError, ValidationError, RateLimitError,
         ExternalAPIError, DatabaseError, AnalysisTimeoutError],
    )
    def test_is_oracle_error(self, cls):
        assert issubclass(cls, OracleError)


# ---------------------------------------------------------------------------
# oracle_error_handler
# ---------------------------------------------------------------------------

class TestOracleErrorHandler:
    @pytest.mark.asyncio
    async def test_not_found_returns_404(self):
        req = _make_request()
        exc = NotFoundError("Position xyz not found")
        resp = await oracle_error_handler(req, exc)
        assert resp.status_code == 404
        body = resp.body
        import json
        data = json.loads(body)
        assert data["code"] == "NOT_FOUND"
        assert data["error"] == "Position xyz not found"
        assert data["request_id"] == "test-rid-123"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_rate_limit_returns_429(self):
        req = _make_request()
        exc = RateLimitError()
        resp = await oracle_error_handler(req, exc)
        assert resp.status_code == 429
        import json
        data = json.loads(resp.body)
        assert data["code"] == "RATE_LIMIT_EXCEEDED"

    @pytest.mark.asyncio
    async def test_database_error_returns_503(self):
        req = _make_request()
        exc = DatabaseError("Connection pool exhausted")
        resp = await oracle_error_handler(req, exc)
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_request_id_fallback_when_missing(self):
        req = MagicMock(spec=Request)
        req.method = "GET"
        req.url.path = "/test"
        # No state.request_id set
        del req.state
        exc = NotFoundError()
        resp = await oracle_error_handler(req, exc)
        import json
        data = json.loads(resp.body)
        assert data["request_id"] == "unknown"


# ---------------------------------------------------------------------------
# http_exception_handler
# ---------------------------------------------------------------------------

class TestHttpExceptionHandler:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "status_code, expected_code",
        [
            (400, "BAD_REQUEST"),
            (401, "UNAUTHORIZED"),
            (403, "FORBIDDEN"),
            (404, "NOT_FOUND"),
            (405, "METHOD_NOT_ALLOWED"),
            (409, "CONFLICT"),
            (422, "VALIDATION_ERROR"),
            (429, "RATE_LIMIT_EXCEEDED"),
        ],
    )
    async def test_known_status_codes(self, status_code, expected_code):
        req = _make_request()
        exc = HTTPException(status_code=status_code, detail="test detail")
        resp = await http_exception_handler(req, exc)
        import json
        data = json.loads(resp.body)
        assert resp.status_code == status_code
        assert data["code"] == expected_code
        assert data["error"] == "test detail"

    @pytest.mark.asyncio
    async def test_unknown_status_code_falls_back_to_http_error(self):
        req = _make_request()
        exc = HTTPException(status_code=418, detail="I'm a teapot")
        resp = await http_exception_handler(req, exc)
        import json
        data = json.loads(resp.body)
        assert data["code"] == "HTTP_ERROR"
        assert resp.status_code == 418

    @pytest.mark.asyncio
    async def test_non_string_detail_is_stringified(self):
        req = _make_request()
        exc = HTTPException(status_code=422, detail={"msg": "value error"})
        resp = await http_exception_handler(req, exc)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# unhandled_exception_handler
# ---------------------------------------------------------------------------

class TestUnhandledExceptionHandler:
    @pytest.mark.asyncio
    async def test_returns_500(self):
        req = _make_request()
        exc = RuntimeError("something exploded")
        resp = await unhandled_exception_handler(req, exc)
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_response_body_is_generic(self):
        req = _make_request()
        exc = ValueError("internal detail should not leak")
        resp = await unhandled_exception_handler(req, exc)
        import json
        data = json.loads(resp.body)
        assert data["code"] == "INTERNAL_ERROR"
        assert "internal detail should not leak" not in data["error"]

    @pytest.mark.asyncio
    async def test_request_id_included(self):
        req = _make_request(request_id="err-req-456")
        exc = Exception("boom")
        resp = await unhandled_exception_handler(req, exc)
        import json
        data = json.loads(resp.body)
        assert data["request_id"] == "err-req-456"
