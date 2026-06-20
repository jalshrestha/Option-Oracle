"""Session compatibility routes."""
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request

from config.database import AsyncSessionLocal
from config.logging import get_api_logger
from src.api.dependencies import get_current_session, get_rate_limiter
from src.repositories.sessions import SessionRepository

logger = get_api_logger()
router = APIRouter()


@router.post("/create")
async def create_session(
    request: Request,
    risk_profile: str = "moderate",
    _rate: None = Depends(get_rate_limiter(5)),
) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")
    session_token = str(uuid.uuid4())

    async with AsyncSessionLocal() as db:
        try:
            repo = SessionRepository(db)
            await repo.create({
                "session_token": session_token,
                "ip_address": client_ip,
                "user_agent": user_agent,
                "risk_profile": risk_profile,
                "preferences": {},
                "is_active": True,
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
            })
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    logger.info(f"New session created: {session_token}")
    return {
        "session_token": session_token,
        "risk_profile": risk_profile,
        "expires_in": 86400,
        "created_at": time.time(),
    }


@router.get("/info")
async def get_session_info(session: Dict = Depends(get_current_session)) -> Dict[str, Any]:
    return {
        "session_token": session["session_token"],
        "risk_profile": session.get("risk_profile", "moderate"),
        "preferences": session.get("preferences", {}),
    }
