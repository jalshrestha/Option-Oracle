"""
RequestIDMiddleware — injects a UUID4 request ID into every request/response.

The ID is stored on ``request.state.request_id`` so that error handlers and
service code can include it in structured log entries and JSON error responses.
"""
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from config.settings import settings


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request for tracing.

    The ID is always available on ``request.state.request_id``.
    The ``X-Request-ID`` response header is only sent in debug mode
    to avoid leaking internal trace IDs to production clients.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        if settings.app_debug:
            response.headers["X-Request-ID"] = request_id
        return response
