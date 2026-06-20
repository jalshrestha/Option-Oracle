"""Repository for persisted chat threads and messages."""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from src.models.chat import ChatMessage, ChatThread
from src.repositories.base import BaseRepository


def _thread_to_dict(row: ChatThread) -> Dict[str, Any]:
    return {
        "id": str(row.id),
        "session_id": row.session_id,
        "title": row.title,
        "last_message_preview": row.last_message_preview,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _message_to_dict(row: ChatMessage) -> Dict[str, Any]:
    return {
        "id": str(row.id),
        "thread_id": str(row.thread_id),
        "role": row.role,
        "content": row.content,
        "metadata": row.message_metadata or {},
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


class ChatRepository(BaseRepository):
    """Data access for chat history."""

    async def list_threads(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            result = await self._session.execute(
                select(ChatThread)
                .where(ChatThread.session_id == session_id)
                .order_by(desc(ChatThread.updated_at), desc(ChatThread.created_at))
                .limit(limit)
            )
            return [_thread_to_dict(row) for row in result.scalars().all()]
        except Exception as exc:
            self._handle_db_error(exc, "list_chat_threads")

    async def get_thread(self, session_id: str, thread_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = await self._session.execute(
                select(ChatThread)
                .options(selectinload(ChatThread.messages))
                .where(
                    ChatThread.id == uuid.UUID(thread_id),
                    ChatThread.session_id == session_id,
                )
            )
            row = result.scalar_one_or_none()
            if not row:
                return None
            thread = _thread_to_dict(row)
            thread["messages"] = [_message_to_dict(message) for message in row.messages]
            return thread
        except ValueError:
            return None
        except Exception as exc:
            self._handle_db_error(exc, "get_chat_thread")

    async def create_thread(self, session_id: str, title: str) -> Dict[str, Any]:
        try:
            row = ChatThread(session_id=session_id, title=title, last_message_preview=None)
            self._session.add(row)
            await self._session.flush()
            return _thread_to_dict(row)
        except Exception as exc:
            self._handle_db_error(exc, "create_chat_thread")

    async def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            thread_uuid = uuid.UUID(thread_id)
            row = ChatMessage(
                thread_id=thread_uuid,
                role=role,
                content=content,
                message_metadata=metadata or {},
            )
            self._session.add(row)
            thread = await self._session.get(ChatThread, thread_uuid)
            if thread:
                thread.last_message_preview = content.strip().replace("\n", " ")[:240]
                thread.updated_at = datetime.now(timezone.utc)
            await self._session.flush()
            return _message_to_dict(row)
        except Exception as exc:
            self._handle_db_error(exc, "add_chat_message")

    async def recent_messages(
        self,
        session_id: str,
        thread_id: str,
        limit: int = 12,
    ) -> List[Dict[str, Any]]:
        thread = await self.get_thread(session_id, thread_id)
        if not thread:
            return []
        messages = thread.get("messages", [])
        return messages[-limit:]
