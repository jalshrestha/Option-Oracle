"""
Neural Options Oracle++ FastAPI Main Application
"""
import time
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

from config.settings import settings
from config.logging import setup_logging, log_api_access, get_api_logger
from config.database import health_check as db_health_check, engine, create_tables
from src.api.dependencies import set_orchestrator
from src.api.middleware.request_id import RequestIDMiddleware
from src.api.routes import (
    analysis,
    auth as auth_routes,
    chat_trade,
    education,
    market,
    options,
    portfolio,
    sessions,
    system,
    technical,
    trading,
)
from src.api.chat_router import router as chat_router
from src.api.intelligent_orchestrator import IntelligentOrchestrator
from src.data.redis_cache import close_redis_client
from src.monitoring.metrics import prometheus_response, record_request

logger = get_api_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Neural Options Oracle++ API Server")

    # Setup logging
    setup_logging()

    # Create tables (dev mode); in production Alembic runs migrations
    if settings.env != "production":
        await create_tables()

    # Verify database connection
    db_health = await db_health_check()
    if db_health["status"] != "healthy":
        logger.error(f"Database connection failed: {db_health}")
        raise Exception("Database connection failed")

    # Initialize shared orchestrator once
    set_orchestrator(IntelligentOrchestrator())
    logger.info("IntelligentOrchestrator singleton initialized")

    logger.info("Database connection established")
    logger.info("Neural Options Oracle++ API Server started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Neural Options Oracle++ API Server")
    await close_redis_client()
    await engine.dispose()


# ---------------------------------------------------------------------------
# App factory helpers
# ---------------------------------------------------------------------------

def _register_middleware(app: FastAPI) -> None:
    """Register all middleware in reverse call-stack order (last = outermost)."""
    # TrustedHost: production + staging; "0.0.0.0" is not a valid hostname
    if settings.env in ("production", "staging"):
        allowed = getattr(settings, "allowed_hosts", ["localhost", "127.0.0.1"])
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "X-Session-Token", "X-Request-ID", "Accept", "Authorization"],
    )

    # RequestIDMiddleware runs outermost — every handler has request.state.request_id
    app.add_middleware(RequestIDMiddleware)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            metric_path = getattr(request.scope.get("route"), "path", request.url.path)
            record_request(request.method, metric_path, response.status_code, process_time)
            log_api_access(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                response_time=process_time,
                user_agent=user_agent,
                ip_address=client_ip,
            )
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-API-Version"] = "1.0.0"
            return response
        except Exception as e:
            process_time = time.time() - start_time
            metric_path = getattr(request.scope.get("route"), "path", request.url.path)
            record_request(request.method, metric_path, 500, process_time)
            logger.error(f"Request failed: {request.method} {request.url.path} - {e}")
            log_api_access(
                method=request.method,
                path=request.url.path,
                status_code=500,
                response_time=process_time,
                user_agent=user_agent,
                ip_address=client_ip,
            )
            raise HTTPException(status_code=500, detail="Internal server error")


def _register_error_handlers(app: FastAPI) -> None:
    """Register centralised exception → JSON response handlers."""
    from src.exceptions import OracleError
    from src.api.error_handlers import (
        oracle_error_handler,
        http_exception_handler as oracle_http_handler,
        unhandled_exception_handler,
    )
    app.add_exception_handler(OracleError, oracle_error_handler)
    app.add_exception_handler(HTTPException, oracle_http_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


def _register_routers(app: FastAPI) -> None:
    """Mount all API routers and register core endpoints."""
    app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
    app.include_router(trading.router, prefix="/api/v1/trading", tags=["Trading"])
    app.include_router(education.router, prefix="/api/v1/education", tags=["Education"])
    app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
    app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
    app.include_router(chat_router, tags=["Chat Router"])
    app.include_router(sessions.router, prefix="/api/v1/session", tags=["Session"])
    app.include_router(market.router, prefix="/api/v1", tags=["Market"])
    app.include_router(technical.router, prefix="/api/v1", tags=["Technical"])
    app.include_router(options.router, prefix="/api/v1", tags=["Options"])
    app.include_router(chat_trade.router, prefix="/api/v1", tags=["Chat Trading"])

    @app.get("/")
    async def root() -> Dict[str, Any]:
        return {
            "name": "Neural Options Oracle++ API",
            "version": "1.0.0",
            "status": "active",
            "timestamp": time.time(),
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "analysis": "/api/v1/analysis",
                "trading": "/api/v1/trading",
                "education": "/api/v1/education",
                "portfolio": "/api/v1/portfolio",
                "system": "/api/v1/system",
            },
        }

    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        db_health = await db_health_check()
        overall = "healthy" if db_health["status"] == "healthy" else "unhealthy"
        return {
            "status": overall,
            "components": {"api": "healthy", "database": db_health["status"]},
            "database_details": db_health,
            "timestamp": time.time(),
        }

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return prometheus_response()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    _app = FastAPI(
        title="Neural Options Oracle++ API",
        description="AI-Driven Options Trading Intelligence Platform",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    _register_middleware(_app)
    _register_error_handlers(_app)
    _register_routers(_app)
    return _app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        log_level=settings.log_level.lower()
    )
