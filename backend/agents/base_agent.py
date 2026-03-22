"""
Base Agent Class for Neural Options Oracle++
Provider-agnostic: works with OpenAI or Gemini via the LLMClient abstraction.
"""
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.constants import DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE
from config.logging import get_agents_logger
from src.llm.base import LLMClient

logger = get_agents_logger()


class BaseAgent(ABC):
    """Base class for all AI agents in the system."""

    def __init__(self, client: LLMClient, name: str) -> None:
        self.client = client
        self.name = name
        # Expose model name for logging/status — derived from the client
        self.model = client.model_name
        self.initialized = False
        self.system_instructions = ""

    async def initialize(self) -> bool:
        """Initialize the agent."""
        try:
            self.system_instructions = self._get_system_instructions()
            self.initialized = True
            logger.info(f"{self.name} agent initialized (provider={self.client.provider}, model={self.model})")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {self.name} agent: {e}")
            return False

    @abstractmethod
    def _get_system_instructions(self) -> str:
        """Return the system prompt for this agent."""

    @abstractmethod
    async def analyze(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Main analysis method — must be implemented by subclasses."""

    async def _make_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict]] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        response_schema: Optional[Dict] = None,  # kept for API compat, not used for Gemini
    ) -> Dict[str, Any]:
        """
        Call the LLM and return a normalized response dict.

        Returns dict with keys:
            'content'    — the assistant's text reply (str)
            'tool_calls' — list of {id, function, arguments} dicts (may be empty)
        On failure, returns a fallback response (never raises).
        """
        if not self.client:
            logger.warning(f"{self.name}: no LLM client available, returning fallback")
            return {"content": json.dumps(self._get_fallback_response()), "tool_calls": []}

        try:
            logger.info(f"{self.name}: calling {self.client.provider} ({self.model})")

            if tools:
                result = await self.client.complete_with_tools(
                    messages=messages,
                    tools=tools,
                    temperature=temperature,
                )
                tool_calls = [
                    {"id": f"call_{i}", "function": tc.name, "arguments": tc.arguments}
                    for i, tc in enumerate(result.tool_calls)
                ]
                return {"content": result.content or "", "tool_calls": tool_calls}
            else:
                content = await self.client.complete(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=DEFAULT_MAX_TOKENS,
                    json_mode=True,
                )
                logger.debug(f"{self.name}: response ({len(content)} chars)")
                return {"content": content, "tool_calls": []}

        except Exception as e:
            logger.error(f"{self.name}: completion failed: {e}")
            return {"content": json.dumps(self._get_fallback_response()), "tool_calls": []}

    async def get_status(self) -> Dict[str, Any]:
        """Return agent health status."""
        return {
            "name": self.name,
            "model": self.model,
            "provider": self.client.provider if self.client else "unknown",
            "initialized": self.initialized,
            "healthy": True,
            "last_check": datetime.now().isoformat(),
        }

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse a JSON string from the LLM response, with fallback on failure."""
        try:
            if not content or not content.strip():
                return self._get_fallback_response()

            # Strip markdown code fences if present
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_str = content[start:end].strip()
            elif "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
            else:
                json_str = content

            parsed = json.loads(json_str)
            if not isinstance(parsed, dict):
                return self._get_fallback_response()
            return parsed

        except json.JSONDecodeError as e:
            logger.warning(f"{self.name}: JSON parse failed: {e} | raw[:200]: {repr(content[:200])}")
            return self._get_fallback_response()
        except Exception as e:
            logger.error(f"{self.name}: unexpected parse error: {e}")
            return self._get_fallback_response()

    def _get_fallback_response(self) -> Dict[str, Any]:
        """Fallback when the LLM call or JSON parsing fails."""
        return {
            "summary": f"{self.name} analysis completed with limited data",
            "confidence": 0.3,
            "recommendation": "HOLD",
            "reasoning": "Analysis completed with fallback data due to API limitations",
            "fallback": True,
        }

    def _validate_confidence(self, confidence: float) -> float:
        """Clamp confidence to [0.0, 1.0]."""
        try:
            return max(0.0, min(1.0, float(confidence)))
        except (ValueError, TypeError):
            return 0.5

    def _ensure_fields(self, data: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Fill missing keys in data with values from defaults (in-place)."""
        for key, value in defaults.items():
            if key not in data:
                data[key] = value
        return data


# Reusable JSON Schema fragment for confidence — import in agent schema definitions
CONFIDENCE_SCHEMA = {"type": "number", "minimum": 0.0, "maximum": 1.0}
