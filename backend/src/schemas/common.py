"""
Shared Pydantic schemas used across multiple feature domains.
"""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    """Uniform error envelope returned by all error handlers."""

    model_config = ConfigDict(frozen=True)

    error: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code (UPPER_SNAKE_CASE)")
    request_id: str = Field(..., description="UUID4 from X-Request-ID header")
    timestamp: str = Field(..., description="UTC ISO-8601 timestamp")


class PaginationParams(BaseModel):
    """Common query parameters for paginated endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")


class HealthStatus(BaseModel):
    """Response schema for /health endpoint."""

    status: str
    database: dict[str, Any]
    api_version: str
    timestamp: str
