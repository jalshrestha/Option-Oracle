"""Chat persistence and memory-window service."""
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.redis_cache import delete_json, get_json, set_json
from src.repositories.chat import ChatRepository

MEMORY_LIMIT = 12
MEMORY_TTL_SECONDS = 60 * 60 * 6


def _make_title(message: str) -> str:
    compact = " ".join(message.strip().split())
    if not compact:
        return "New chat"
    return compact[:60]


def _memory_key(session_id: str, thread_id: str) -> str:
    return f"chat:memory:{session_id}:{thread_id}"


class ChatHistoryService:
    """Durable chat history with Redis-backed recent memory cache."""

    def __init__(self, db: AsyncSession):
        self.repo = ChatRepository(db)

    async def list_threads(self, session_id: str) -> List[Dict[str, Any]]:
        return await self.repo.list_threads(session_id)

    async def get_thread(self, session_id: str, thread_id: str) -> Optional[Dict[str, Any]]:
        return await self.repo.get_thread(session_id, thread_id)

    async def ensure_thread(
        self,
        session_id: Optional[str],
        thread_id: Optional[str],
        first_message: str,
    ) -> Optional[Dict[str, Any]]:
        if not session_id:
            return None
        if thread_id:
            existing = await self.repo.get_thread(session_id, thread_id)
            if existing:
                return existing
        return await self.repo.create_thread(session_id, _make_title(first_message))

    async def append_message(
        self,
        session_id: Optional[str],
        thread_id: Optional[str],
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not session_id or not thread_id:
            return None
        message = await self.repo.add_message(thread_id, role, content, metadata)
        await delete_json(_memory_key(session_id, thread_id))
        return message

    async def get_memory_context(
        self,
        session_id: Optional[str],
        thread_id: Optional[str],
    ) -> List[Dict[str, str]]:
        if not session_id or not thread_id:
            return []
        key = _memory_key(session_id, thread_id)
        cached = await get_json(key)
        if isinstance(cached, list):
            return cached
        rows = await self.repo.recent_messages(session_id, thread_id, MEMORY_LIMIT)
        memory = [
            {"role": row["role"], "content": row["content"]}
            for row in rows
            if row.get("role") in {"user", "assistant"} and row.get("content")
        ]
        await set_json(key, memory, MEMORY_TTL_SECONDS)
        return memory
