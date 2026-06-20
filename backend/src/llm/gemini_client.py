"""
Google Gemini implementation of LLMClient.
Wraps google.generativeai with the provider-agnostic interface.

Message format conversion:
  OpenAI:  [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
  Gemini:  system_instruction + contents=[{"role": "user"|"model", "parts": [...]}]

Tool format conversion:
  OpenAI:  {"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}
  Gemini:  genai.protos.Tool(function_declarations=[genai.protos.FunctionDeclaration(...)])
"""
import asyncio
from typing import Any, Dict, List, Optional, Tuple

from src.llm.base import LLMClient, ToolCall, ToolCallResult


# ---------------------------------------------------------------------------
# Message format conversion helpers
# ---------------------------------------------------------------------------

def _split_messages(
    messages: List[Dict[str, str]],
) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    """
    Split OpenAI messages into (system_instruction, gemini_contents).

    Gemini treats the system message separately from the conversation.
    All assistant messages become role="model".
    """
    system_instruction: Optional[str] = None
    contents: List[Dict[str, Any]] = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            # Gemini takes system prompt as model-level instruction, not a turn
            system_instruction = content
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
        else:
            contents.append({"role": "user", "parts": [{"text": content}]})

    # Gemini requires the last turn to be "user" — if not, append a dummy
    if contents and contents[-1]["role"] != "user":
        contents.append({"role": "user", "parts": [{"text": "Continue."}]})

    # If only system message exists with no turns, add a placeholder user turn
    if not contents:
        contents.append({"role": "user", "parts": [{"text": "Begin."}]})

    return system_instruction, contents


def _openai_tools_to_gemini(tools: List[Dict[str, Any]]) -> List[Any]:
    """
    Translate OpenAI function-calling tool definitions → Gemini FunctionDeclarations.

    OpenAI format:
      {"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}

    Gemini format:
      genai.protos.Tool(function_declarations=[FunctionDeclaration(...)])
    """
    import google.generativeai.protos as protos

    declarations = []
    for tool in tools:
        fn = tool.get("function", tool)  # handle both formats
        declarations.append(
            protos.FunctionDeclaration(
                name=fn["name"],
                description=fn.get("description", ""),
                parameters=_json_schema_to_gemini_schema(fn.get("parameters", {})),
            )
        )
    return [protos.Tool(function_declarations=declarations)]


def _json_schema_to_gemini_schema(schema: Dict[str, Any]) -> Any:
    """Convert a JSON Schema dict to a Gemini Schema proto."""
    import google.generativeai.protos as protos

    type_map = {
        "string": protos.Type.STRING,
        "number": protos.Type.NUMBER,
        "integer": protos.Type.INTEGER,
        "boolean": protos.Type.BOOLEAN,
        "array": protos.Type.ARRAY,
        "object": protos.Type.OBJECT,
    }

    schema_type = type_map.get(schema.get("type", "object"), protos.Type.OBJECT)
    properties = {}
    for prop_name, prop_schema in schema.get("properties", {}).items():
        properties[prop_name] = _json_schema_to_gemini_schema(prop_schema)

    return protos.Schema(
        type=schema_type,
        description=schema.get("description", ""),
        properties=properties if properties else None,
        required=schema.get("required", []),
        items=_json_schema_to_gemini_schema(schema["items"]) if "items" in schema else None,
    )


def _parse_gemini_tool_response(response: Any) -> ToolCallResult:
    """Parse Gemini function-call response into ToolCallResult."""
    tool_calls = []
    text_parts = []

    for candidate in response.candidates:
        for part in candidate.content.parts:
            if hasattr(part, "function_call") and part.function_call.name:
                fc = part.function_call
                # Gemini returns arguments as a Struct — convert to plain dict
                args = dict(fc.args) if fc.args else {}
                tool_calls.append(ToolCall(name=fc.name, arguments=args))
            elif hasattr(part, "text") and part.text:
                text_parts.append(part.text)

    return ToolCallResult(
        content=" ".join(text_parts) if text_parts else None,
        tool_calls=tool_calls,
    )


# ---------------------------------------------------------------------------
# GeminiLLMClient
# ---------------------------------------------------------------------------

class GeminiLLMClient(LLMClient):
    """
    LLMClient backed by Google Gemini (gemini-2.0-flash, gemini-2.0-flash-lite, etc.).

    Uses asyncio.to_thread() since the google-generativeai SDK is synchronous.
    """

    def __init__(self, api_key: str, model: str) -> None:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self._model_name = model
        self._genai = genai

    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        json_mode: bool = False,
    ) -> str:
        from google.generativeai.types import GenerationConfig

        system_instruction, contents = _split_messages(messages)

        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json" if json_mode else "text/plain",
        )

        model = self._genai.GenerativeModel(
            self._model_name,
            system_instruction=system_instruction,
            generation_config=generation_config,
        )

        response = await asyncio.to_thread(model.generate_content, contents)
        return response.text or ""

    async def complete_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.1,
    ) -> ToolCallResult:
        from google.generativeai.types import GenerationConfig

        system_instruction, contents = _split_messages(messages)
        gemini_tools = _openai_tools_to_gemini(tools)

        model = self._genai.GenerativeModel(
            self._model_name,
            system_instruction=system_instruction,
            tools=gemini_tools,
            generation_config=GenerationConfig(temperature=temperature),
        )

        response = await asyncio.to_thread(model.generate_content, contents)
        return _parse_gemini_tool_response(response)

    @property
    def provider(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name
