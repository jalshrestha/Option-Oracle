"""
Auth routes — register, login, logout, refresh, me.
"""
import uuid
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db, get_rate_limiter
from src.auth.jwt import create_access_token, create_refresh_token, decode_token
from src.auth.password import hash_password, verify_password
from src.repositories.users import UserRepository
from src.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse

router = APIRouter()

_401_msg = "Invalid credentials"


def _require_user(authorization: Optional[str], repo: UserRepository):
    """Shared helper: decode bearer token, return User or raise 401."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    payload = decode_token(authorization.removeprefix("Bearer "))
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Access token required")
    return uuid.UUID(payload["sub"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(get_rate_limiter(3)),
) -> TokenResponse:
    repo = UserRepository(db)

    if await repo.get_by_email(body.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    if await repo.get_by_username(body.username):
        raise HTTPException(status_code=409, detail="Username already taken")

    user = await repo.create(
        email=body.email,
        username=body.username,
        hashed_password=hash_password(body.password),
    )

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.email),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(get_rate_limiter(5)),
) -> TokenResponse:
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)

    # Same error for missing user and wrong password — no user enumeration
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail=_401_msg)
    if not user.is_active:
        raise HTTPException(status_code=401, detail=_401_msg)

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.email),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/logout")
async def logout(_rate: None = Depends(get_rate_limiter(20))) -> Dict[str, Any]:
    # Stateless JWT — client discards the token
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(get_rate_limiter(10)),
) -> TokenResponse:
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token required")

    repo = UserRepository(db)
    user = await repo.get_by_id(uuid.UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.email),
        refresh_token=body.refresh_token,  # keep existing refresh token until expiry
    )


@router.get("/me")
async def get_me(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    repo = UserRepository(db)
    user_id = _require_user(authorization, repo)
    user = await repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "risk_profile": user.risk_profile,
        "is_verified": user.is_verified,
    }
