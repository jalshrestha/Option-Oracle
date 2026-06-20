"""
LLM Provider Abstraction — base interface.

All LLM clients implement this interface so agents and orchestrators
are completely provider-agnostic.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolCall:
    """A single tool/function call requested by the LLM."""
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolCallResult:
    """The full response from complete_with_tools()."""
    content: Optional[str]          # Any text the model included alongside tool calls
    tool_calls: List[ToolCall] = field(default_factory=list)

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class LLMClient(ABC):
    """
    Provider-agnostic LLM client interface.

    All implementations must support:
    - complete()             — standard chat completion, returns text
    - complete_with_tools()  — chat completion with function/tool calling
    """

    @abstractmethod
    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        json_mode: bool = False,
    ) -> str:
        """
        Send a chat completion request and return the assistant reply as a plain string.

        Args:
            messages:    List of {"role": "system"|"user"|"assistant", "content": str}
            temperature: Sampling temperature (0.0–1.0)
            max_tokens:  Maximum tokens to generate
            json_mode:   If True, instruct the model to respond with valid JSON only
        """

    @abstractmethod
    async def complete_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.1,
    ) -> ToolCallResult:
        """
        Send a chat completion request with tool/function calling.

        Args:
            messages:    Conversation history in OpenAI message format
            tools:       Tool definitions in OpenAI function-calling format
            temperature: Sampling temperature
        """

    @property
    @abstractmethod
    def provider(self) -> str:
        """Return the provider name: 'openai', 'gemini', or 'deepseek'."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the specific model being used (e.g. 'gpt-4o', 'gemini-2.0-flash')."""
