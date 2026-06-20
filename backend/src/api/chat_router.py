"""
Chat Router API - Intelligent text routing for user queries
"""
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal
from src.core.ai_intent_router import ai_intent_router, route_with_ai
from src.api.dependencies import get_db
from config.logging import get_agents_logger
from src.services.chat_history_service import ChatHistoryService

logger = get_agents_logger()

router = APIRouter(prefix="/api/v1/chat", tags=["Chat Router"])


class ChatMessage(BaseModel):
    """Chat message model"""
    message: str
    selectedStock: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    intent: str
    symbol: Optional[str]
    confidence: float
    data: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    agents_triggered: Optional[List[str]] = None
    thread_id: Optional[str] = None
    timestamp: str


class ChatHistoryMessage(BaseModel):
    id: str
    role: str
    content: str
    metadata: Dict[str, Any] = {}
    created_at: str


class ChatThreadSummary(BaseModel):
    id: str
    title: str
    last_message_preview: Optional[str] = None
    created_at: str
    updated_at: str


class ChatThreadDetail(ChatThreadSummary):
    messages: List[ChatHistoryMessage]


def _build_frontend_actions(symbol: Optional[str], message: str) -> Optional[Dict[str, Any]]:
    if not symbol:
        return None

    actions: Dict[str, Any] = {
        "analyzeStock": symbol,
        "showAnalysis": True,
    }
    lower_message = message.lower()
    if "buy" in lower_message or "execute" in lower_message:
        actions["showBuyRecommendations"] = True
        actions["enableTrading"] = True
    return actions


def _iso(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _serialize_thread_summary(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "last_message_preview": row.get("last_message_preview"),
        "created_at": _iso(row["created_at"]),
        "updated_at": _iso(row["updated_at"]),
    }


def _serialize_message(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "role": row["role"],
        "content": row["content"],
        "metadata": row.get("metadata") or {},
        "created_at": _iso(row["created_at"]),
    }


def _to_chat_response_payload(
    message_data: ChatMessage,
    result: Dict[str, Any],
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:
    intent = result.get("intent", "GENERAL_CHAT")
    confidence = result.get("confidence", 0.5)
    response_text = result.get("response", "I'm here to help.")
    tools_called = result.get("tools_called", [])

    symbol = result.get("symbol")
    data: Dict[str, Any] = {}
    for tool_result in result.get("tool_results", []):
        if tool_result.get("tool") == "analyze_stock":
            symbol = tool_result.get("symbol") or symbol
            if "analysis_result" in tool_result:
                data["analysis_result"] = tool_result["analysis_result"]
                data["stock_data"] = _extract_stock_data(tool_result["analysis_result"])
        elif tool_result.get("tool") == "get_quote":
            symbol = tool_result.get("symbol") or symbol
            data["quote"] = tool_result.get("quote", {})

    agent_mapping = {
        "analyze_stock": ["technical", "sentiment", "flow", "history", "risk"],
        "buy_option": ["buy", "technical", "risk"],
        "buy_multiple_options": ["buy", "technical", "sentiment", "flow", "risk"],
        "explain_concept": ["education"],
        "get_quote": [],
        "get_market_trends": ["sentiment", "flow"],
        "portfolio_analysis": ["risk"],
        "generate_quiz": ["education"],
        "casual_response": [],
    }
    agents_triggered = []
    for tool in tools_called:
        agents_triggered.extend(agent_mapping.get(tool, []))

    return ChatResponse(
        response=response_text,
        intent=intent,
        symbol=symbol,
        confidence=confidence,
        data=data,
        actions=_build_frontend_actions(symbol or message_data.selectedStock, message_data.message),
        suggestions=_generate_ai_suggestions(intent, symbol, tools_called),
        agents_triggered=list(dict.fromkeys(agents_triggered)),
        thread_id=thread_id or message_data.thread_id,
        timestamp=datetime.now().isoformat(),
    ).model_dump()


async def _route_user_message(message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    result = await route_with_ai(message, context or {})
    tools_called = result.get("tools_called", [])
    symbols = []
    for tool_result in result.get("tool_results", []):
        if tool_result.get("symbol"):
            symbols.append(tool_result["symbol"])

    return {
        "intent": result.get("intent", "GENERAL_CHAT"),
        "confidence": result.get("confidence", 0.0),
        "agents_to_call": tools_called,
        "extracted_data": {
            "symbols": symbols,
            "keywords": message.split(),
        },
        "response_type": "tool_call" if tools_called else "chat",
        "timestamp": result.get("timestamp", datetime.now().isoformat()),
    }




@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    message_data: ChatMessage,
    db: AsyncSession = Depends(get_db),
):
    """
    Send chat message and get intelligent response using AI-powered routing with tool calling
    """
    try:
        logger.info(f"💬 Processing chat message: '{message_data.message}'")
        
        history = ChatHistoryService(db)
        thread = await history.ensure_thread(
            message_data.session_id,
            message_data.thread_id,
            message_data.message,
        )
        thread_id = thread["id"] if thread else None
        conversation_history = await history.get_memory_context(message_data.session_id, thread_id)
        await history.append_message(message_data.session_id, thread_id, "user", message_data.message)

        # Use AI Intent Router with tool calling
        context = {
            "user_id": message_data.user_id,
            "session_id": message_data.session_id,
            "thread_id": thread_id,
            "conversation_history": conversation_history,
            "selectedStock": message_data.selectedStock,
            **(message_data.context or {})
        }
        
        # Route and process with AI
        result = await route_with_ai(message_data.message, context)
        
        # Extract info from AI result
        intent = result.get("intent", "GENERAL_CHAT")
        confidence = result.get("confidence", 0.5)
        response_text = result.get("response", "I'm here to help!")
        tools_called = result.get("tools_called", [])
        
        # Determine symbol from tools called
        symbol = None
        data = {}
        
        # Check if any analysis was performed
        for tool_result in result.get("tool_results", []):
            if tool_result.get("tool") == "analyze_stock":
                symbol = tool_result.get("symbol")
                if "analysis_result" in tool_result:
                    data["analysis_result"] = tool_result["analysis_result"]
                    data["stock_data"] = _extract_stock_data(tool_result["analysis_result"])
            elif tool_result.get("tool") == "get_quote":
                symbol = tool_result.get("symbol")
                data["quote"] = tool_result.get("quote", {})
        
        # Generate suggestions based on intent and tools used
        suggestions = _generate_ai_suggestions(intent, symbol, tools_called)
        
        logger.info(f"🎯 AI Intent: {intent} ({confidence:.2f}) -> Tools: {tools_called}")
        
        # Map tools to agent names for frontend display
        agent_mapping = {
            "analyze_stock": ["technical", "sentiment", "flow", "history", "risk"],
            "buy_option": ["buy", "technical", "risk"],
            "buy_multiple_options": ["buy", "technical", "sentiment", "flow", "risk"],
            "explain_concept": ["education"],
            "get_quote": [],
            "get_market_trends": ["sentiment", "flow"],
            "portfolio_analysis": ["risk"],
            "generate_quiz": ["education"],
            "casual_response": []
        }
        
        agents_triggered = []
        for tool in tools_called:
            agents_triggered.extend(agent_mapping.get(tool, []))
        
        # Remove duplicates while preserving order
        agents_triggered = list(dict.fromkeys(agents_triggered))
        
        response = ChatResponse(
            response=response_text,
            intent=intent,
            symbol=symbol,
            confidence=confidence,
            data=data,
            actions=_build_frontend_actions(symbol or message_data.selectedStock, message_data.message),
            suggestions=suggestions,
            agents_triggered=agents_triggered,
            thread_id=thread_id,
            timestamp=datetime.now().isoformat()
        )
        await history.append_message(
            message_data.session_id,
            thread_id,
            "assistant",
            response.response,
            response.model_dump(exclude={"response"}),
        )
        return response

    except Exception as e:
        logger.error(f"❌ AI Chat routing error: {e}")
        # Fallback response
        return ChatResponse(
            response="I apologize, but I encountered an issue processing your request. Please try asking about a specific stock symbol or trading concept, and I'll do my best to help!",
            intent="ERROR",
            symbol=None,
            confidence=0.0,
            data={},
            actions=_build_frontend_actions(message_data.selectedStock, message_data.message),
            suggestions=[
                "Analyze AAPL stock",
                "What is delta in options?", 
                "Show trending stocks",
                "Portfolio overview"
            ],
            agents_triggered=[],
            timestamp=datetime.now().isoformat()
        )


@router.post("/stream")
async def stream_chat_message(message_data: ChatMessage):
    """Stream real LangGraph/tool progress events, ending with a final response payload."""

    async def _events():
        async with AsyncSessionLocal() as db:
            history = ChatHistoryService(db)
            thread = await history.ensure_thread(
                message_data.session_id,
                message_data.thread_id,
                message_data.message,
            )
            thread_id = thread["id"] if thread else None
            conversation_history = await history.get_memory_context(message_data.session_id, thread_id)
            await history.append_message(message_data.session_id, thread_id, "user", message_data.message)
            await db.commit()

            context = {
                "user_id": message_data.user_id,
                "session_id": message_data.session_id,
                "thread_id": thread_id,
                "conversation_history": conversation_history,
                "selectedStock": message_data.selectedStock,
                **(message_data.context or {}),
            }
            async for event in ai_intent_router.route_and_process_events(message_data.message, context):
                if event.get("event") in {"final", "error"} and event.get("data"):
                    event["data"] = _to_chat_response_payload(message_data, event["data"], thread_id)
                    await history.append_message(
                        message_data.session_id,
                        thread_id,
                        "assistant",
                        event["data"]["response"],
                        {key: value for key, value in event["data"].items() if key != "response"},
                    )
                    await db.commit()
                yield f"data: {json.dumps(event, default=str)}\n\n"

    return StreamingResponse(
        _events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/threads", response_model=List[ChatThreadSummary])
async def list_chat_threads(
    session_id: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    rows = await ChatHistoryService(db).list_threads(session_id)
    return [_serialize_thread_summary(row) for row in rows]


@router.get("/threads/{thread_id}", response_model=ChatThreadDetail)
async def get_chat_thread(
    thread_id: str,
    session_id: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    row = await ChatHistoryService(db).get_thread(session_id, thread_id)
    if not row:
        raise HTTPException(status_code=404, detail="Chat thread not found")
    return {
        **_serialize_thread_summary(row),
        "messages": [_serialize_message(message) for message in row.get("messages", [])],
    }


@router.post("/route")
async def route_user_message_detailed(message_data: ChatMessage):
    """
    Analyze user message intent and provide detailed routing information
    """
    try:
        logger.info(f"🔄 Analyzing message routing: '{message_data.message}'")
        
        # Get routing plan
        routing_plan = await _route_user_message(
            message_data.message,
            {
                "user_id": message_data.user_id,
                "session_id": message_data.session_id,
                "selectedStock": message_data.selectedStock,
                **(message_data.context or {}),
            },
        )
        
        return {
            "routing_plan": routing_plan,
            "processing_time": datetime.now().isoformat(),
            "message_analysis": {
                "original_message": message_data.message,
                "detected_intent": routing_plan['intent'],
                "confidence_score": routing_plan['confidence'],
                "agents_required": routing_plan['agents_to_call'],
                "extracted_entities": routing_plan['extracted_data']
            },
            "recommendations": {
                "should_process": len(routing_plan['agents_to_call']) > 0 or routing_plan['intent'] != 'GENERAL_CHAT',
                "response_strategy": routing_plan['response_type'],
                "suggested_followups": _generate_intent_suggestions(
                    routing_plan['intent'], 
                    routing_plan['extracted_data']['symbols']
                )
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Message routing analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


# Duplicate route removed - using AI Intent Router above


@router.get("/intent/{text}")
async def analyze_intent(text: str):
    """
    Analyze intent of text without processing
    """
    try:
        routing_plan = await _route_user_message(text)
        
        return {
            'intent': routing_plan['intent'],
            'confidence': routing_plan['confidence'],
            'agents_to_call': routing_plan['agents_to_call'],
            'extracted_symbols': routing_plan['extracted_data']['symbols'],
            'extracted_keywords': routing_plan['extracted_data']['keywords'],
            'response_type': routing_plan['response_type'],
            'timestamp': routing_plan['timestamp']
        }
        
    except Exception as e:
        logger.error(f"❌ Intent analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


# Helper functions for AI-powered routing

def _generate_ai_suggestions(intent: str, symbol: Optional[str], tools_called: List[str]) -> List[str]:
    """Generate contextual suggestions based on AI analysis"""
    base_suggestions = []
    
    if "get_quote" in tools_called and symbol:
        base_suggestions.extend([
            f"Analyze {symbol}",
            f"Check {symbol} options flow",
            f"Give me a risk-managed {symbol} setup",
        ])
    elif "analyze_stock" in tools_called and symbol:
        base_suggestions.extend([
            f"Technical analysis for {symbol}",
            f"Options strategies for {symbol}",
            f"Risk assessment for {symbol}",
            f"Compare {symbol} to sector"
        ])
    elif intent == "OPTIONS_EDUCATION":
        base_suggestions.extend([
            "What is delta?",
            "Explain call options",
            "How do puts work?",
            "Options Greeks overview"
        ])
    elif intent == "MARKET_TRENDS":
        base_suggestions.extend([
            "Sector performance",
            "Top gainers today",
            "Options flow analysis",
            "Market sentiment overview"
        ])
    else:
        base_suggestions.extend([
            "Analyze AAPL stock",
            "What are options?",
            "Show trending stocks", 
            "Portfolio overview"
        ])
    
    return base_suggestions[:4]  # Return max 4 suggestions


def _generate_intent_suggestions(intent: str, symbols: List[str]) -> List[str]:
    symbol = symbols[0] if symbols else None
    if intent == "STOCK_ANALYSIS" and symbol:
        return [
            f"Open technical indicators for {symbol}",
            f"Review options chain for {symbol}",
            f"Check latest signals for {symbol}",
        ]
    if intent in {"OPTIONS_BUYING", "PORTFOLIO_BUYING"}:
        return [
            "Review risk assessment",
            "Compare option expirations",
            "Confirm position size",
        ]
    if intent == "OPTIONS_EDUCATION":
        return [
            "Explain options Greeks",
            "Show beginner examples",
            "Generate a short quiz",
        ]
    return ["Analyze AAPL stock", "Show trending stocks", "Explain call options"]


def _extract_stock_data(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract stock data for frontend"""
    return {
        "symbol": analysis_result.get('symbol'),
        "signal": analysis_result.get('signal', {}),
        "confidence": analysis_result.get('confidence', 0),
        "scenario": analysis_result.get('market_scenario'),
        "timestamp": analysis_result.get('timestamp')
    }
















# Helper functions moved to AI Intent Router
