"""
Option Oracle — Custom Exception Hierarchy

Every exception the application can raise deliberately maps to a specific
HTTP status code and a machine-readable `code` string. The centralized
error handler in src/api/error_handlers.py converts these to JSON responses.

Usage:
    from src.exceptions import NotFoundError, RateLimitError
    raise NotFoundError("Position abc123 not found")
"""


class OracleError(Exception):
    """
    Base class for all application exceptions.

    Attributes:
        status_code  HTTP status code to return to the client.
        code         Machine-readable error identifier (uppercase_snake_case).
        message      Human-readable description (set via constructor).
    """

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = "An unexpected error occurred."):
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


# ---------------------------------------------------------------------------
# Client errors (4xx)
# ---------------------------------------------------------------------------

class NotFoundError(OracleError):
    """Resource does not exist (404)."""

    status_code = 404
    code = "NOT_FOUND"

    def __init__(self, message: str = "The requested resource was not found."):
        super().__init__(message)


class ValidationError(OracleError):
    """Input failed schema or business-rule validation (422)."""

    status_code = 422
    code = "VALIDATION_ERROR"

    def __init__(self, message: str = "Request validation failed."):
        super().__init__(message)


class RateLimitError(OracleError):
    """Too many requests from this client (429)."""

    status_code = 429
    code = "RATE_LIMIT_EXCEEDED"

    def __init__(self, message: str = "Too many requests. Please slow down."):
        super().__init__(message)


# ---------------------------------------------------------------------------
# Server / dependency errors (5xx)
# ---------------------------------------------------------------------------

class ExternalAPIError(OracleError):
    """An upstream service (OpenAI, Alpaca, Supabase) returned an error (502)."""

    status_code = 502
    code = "EXTERNAL_API_ERROR"

    def __init__(self, message: str = "An upstream service is unavailable."):
        super().__init__(message)


class DatabaseError(OracleError):
    """Database operation failed (503)."""

    status_code = 503
    code = "DATABASE_ERROR"

    def __init__(self, message: str = "Database operation failed."):
        super().__init__(message)


class AnalysisTimeoutError(OracleError):
    """Agent analysis exceeded the configured timeout (504)."""

    status_code = 504
    code = "ANALYSIS_TIMEOUT"

    def __init__(self, message: str = "Analysis timed out. Try again."):
        super().__init__(message)
