"""
FastAPI dependency providers — DB session, services, session validation, and rate limiting.
"""
import math
import time
from threading import Lock
from typing import Any, AsyncGenerator, Dict, Optional

from cachetools import TTLCache
from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal
from config.logging import get_api_logger
from config.settings import settings
from src.exceptions import RateLimitError
from src.repositories.positions import PositionRepository
from src.repositories.sessions import SessionRepository
from src.repositories.signals import TradingSignalRepository
from src.services.analysis_service import AnalysisService
from src.services.portfolio_service import PortfolioService
from src.services.trading_service import TradingService

logger = get_api_logger()

# ---------------------------------------------------------------------------
# Rate limiting — per-IP, fixed 1-minute window via TTLCache
# ---------------------------------------------------------------------------
_rate_cache: TTLCache = TTLCache(maxsize=10_000, ttl=60)
_rate_lock = Lock()


def _check_rate_limit(client_ip: str, max_requests: int) -> None:
    bucket = math.floor(time.time() / 60)
    key = f"{client_ip}:{bucket}"
    with _rate_lock:
        count = _rate_cache.get(key, 0) + 1
        if count > max_requests:
            raise RateLimitError(f"Rate limit exceeded — max {max_requests} req/min")
        _rate_cache[key] = count


def get_rate_limiter(max_requests: int = 60):
    """Return a FastAPI ``Depends``-compatible function enforcing per-IP rate limits."""
    def _dependency(request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        client_ip = request.client.host if request.client else "unknown"
        _check_rate_limit(client_ip, max_requests)
    return _dependency


# ---------------------------------------------------------------------------
# Database session — one AsyncSession per request, auto-committed on success
# ---------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an AsyncSession scoped to a single HTTP request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Session dependency
# ---------------------------------------------------------------------------

async def get_current_session(
    x_session_token: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Resolve and validate the caller's browser session.

    Returns a minimal temp session when no token is provided (demo / dev mode).
    """
    if not x_session_token:
        return {
            "session_token": "temp",
            "risk_profile": "moderate",
            "preferences": {},
        }

    session_repo = SessionRepository(db)
    session = await session_repo.get(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    await session_repo.touch(x_session_token)
    return session


# ---------------------------------------------------------------------------
# Service provider functions
# ---------------------------------------------------------------------------

def get_analysis_service(db: AsyncSession = Depends(get_db)) -> AnalysisService:
    # Lazy import avoids circular dependency: main → dependencies → main
    from src.api.main import get_orchestrator
    signal_repo = TradingSignalRepository(db)
    return AnalysisService(get_orchestrator(), signal_repo)


def get_trading_service(db: AsyncSession = Depends(get_db)) -> TradingService:
    return TradingService(PositionRepository(db))


def get_portfolio_service(db: AsyncSession = Depends(get_db)) -> PortfolioService:
    return PortfolioService(PositionRepository(db))
