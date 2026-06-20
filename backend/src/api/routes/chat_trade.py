"""Trading command route for chat workflows."""
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from config.logging import get_api_logger
from src.api.dependencies import get_current_session, get_orchestrator, get_rate_limiter

logger = get_api_logger()
router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    selectedStock: Optional[str] = None


@router.post("/chat/trade")
async def process_trading_command(
    message_data: ChatMessage,
    session: Dict = Depends(get_current_session),
    _rate: None = Depends(get_rate_limiter(10)),
) -> Dict[str, Any]:
    """Process trading commands from chat interface."""
    try:
        orchestrator = get_orchestrator()
        user_context = {
            "selectedStock": message_data.selectedStock,
            "risk_profile": {
                "risk_level": "moderate",
                "experience": "intermediate",
                "max_position_size": 0.05,
                "account_balance": 100000,
            },
        }
        result = await orchestrator.process_user_query(message_data.message, user_context)
        buy_agent_result = result.get("frontend_data", {}).get("buy_agent", {})
        buy_analysis = buy_agent_result.get("buy_analysis", {})

        return {
            "symbol": result.get("symbol"),
            "query": message_data.message,
            "trading_analysis": {
                "recommendations": buy_analysis.get("recommendations", []),
                "execution_plan": buy_analysis.get("execution_plan", {}),
                "risk_assessment": buy_analysis.get("risk_assessment", {}),
                "confidence": buy_analysis.get("confidence", 0.0),
            },
            "ai_response": result.get("ai_response", "Trading analysis complete."),
            "actions": {
                "showBuyRecommendations": len(buy_analysis.get("recommendations", [])) > 0,
                "enableTrading": True,
                "symbol": result.get("symbol"),
            },
            "suggestions": [
                "Review buy recommendations",
                "Execute trade",
                "Adjust position size",
                "Set stop loss",
            ],
            "agents_triggered": result.get("ai_agents_triggered", []),
            "timestamp": time.time(),
        }
    except Exception as exc:
        logger.error(f"Trading command error: {exc}", exc_info=True)
        raise HTTPException(status_code=502, detail="Trading command processing is temporarily unavailable")
