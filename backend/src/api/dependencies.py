"""
FastAPI dependency providers — DB session, services, session validation, and rate limiting.
"""
import functools
import math
import time
import uuid
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


@functools.lru_cache(maxsize=None)
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
# JWT-based user dependency
# ---------------------------------------------------------------------------

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Decode the Bearer JWT and return the authenticated User row."""
    from src.auth.jwt import decode_token
    from src.repositories.users import UserRepository

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.removeprefix("Bearer ")
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Access token required")
    user = await UserRepository(db).get_by_id(uuid.UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


# ---------------------------------------------------------------------------
# Session compatibility wrapper — keeps existing route handlers working
# ---------------------------------------------------------------------------

async def get_current_session(
    user=Depends(get_current_user),
) -> Dict[str, Any]:
    """Thin wrapper — returns the same dict shape all existing routes expect."""
    return {
        "session_token": str(user.id),
        "risk_profile": getattr(user, "risk_profile", "moderate"),
        "preferences": {},
    }


# ---------------------------------------------------------------------------
# Service provider functions
# ---------------------------------------------------------------------------

def get_analysis_service(db: AsyncSession = Depends(get_db)) -> AnalysisService:
    # OptionsOracleOrchestrator has analyze_stock() which AnalysisService expects
    from agents.orchestrator import OptionsOracleOrchestrator
    signal_repo = TradingSignalRepository(db)
    return AnalysisService(OptionsOracleOrchestrator(), signal_repo)


def get_trading_service(db: AsyncSession = Depends(get_db)) -> TradingService:
    return TradingService(PositionRepository(db))


def get_portfolio_service(db: AsyncSession = Depends(get_db)) -> PortfolioService:
    return PortfolioService(PositionRepository(db))
