"""
UserRepository — CRUD operations for the users table.
"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_email(self, email: str) -> Optional[User]:
        try:
            result = await self._session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
        except Exception as exc:
            self._handle_db_error(exc, "get_by_email")

    async def get_by_username(self, username: str) -> Optional[User]:
        try:
            result = await self._session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except Exception as exc:
            self._handle_db_error(exc, "get_by_username")

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        try:
            result = await self._session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as exc:
            self._handle_db_error(exc, "get_by_id")

    async def create(
        self, email: str, username: str, hashed_password: str
    ) -> User:
        try:
            user = User(email=email, username=username, hashed_password=hashed_password)
            self._session.add(user)
            await self._session.flush()
            await self._session.refresh(user)
            return user
        except Exception as exc:
            self._handle_db_error(exc, "create")
