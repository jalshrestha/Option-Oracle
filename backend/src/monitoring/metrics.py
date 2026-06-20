"""Prometheus metrics for API runtime monitoring."""
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response


REQUEST_COUNT = Counter(
    "option_oracle_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "option_oracle_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)


def record_request(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    REQUEST_COUNT.labels(method=method, path=path, status_code=str(status_code)).inc()
    REQUEST_LATENCY.labels(method=method, path=path).observe(duration_seconds)


def prometheus_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
