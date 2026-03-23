"""
OpenAI implementation of LLMClient.
Wraps openai.OpenAI with the provider-agnostic interface.
"""
import asyncio
import json
from typing import Any, Dict, List

from src.llm.base import LLMClient, ToolCall, ToolCallResult


class OpenAILLMClient(LLMClient):
    """
    LLMClient backed by OpenAI (gpt-4o, gpt-4o-mini, etc.).

    Uses asyncio.to_thread() so the synchronous openai SDK doesn't block
    the event loop.
    """

    def __init__(self, api_key: str, model: str) -> None:
        import openai
        self._client = openai.OpenAI(api_key=api_key, timeout=60)
        self._model = model

    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        json_mode: bool = False,
    ) -> str:
        kwargs: Dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await asyncio.to_thread(
            self._client.chat.completions.create, **kwargs
        )
        return response.choices[0].message.content or ""

    async def complete_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.1,
    ) -> ToolCallResult:
        response = await asyncio.to_thread(
            self._client.chat.completions.create,
            model=self._model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=temperature,
        )
        msg = response.choices[0].message
        tool_calls = []
        for tc in msg.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(ToolCall(name=tc.function.name, arguments=args))
        return ToolCallResult(content=msg.content, tool_calls=tool_calls)

    @property
    def provider(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model
