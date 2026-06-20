"""Technical indicator and trading signal routes."""
import asyncio
import time
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path

from config.logging import get_api_logger
from src.api.dependencies import get_current_session, get_orchestrator, get_rate_limiter

logger = get_api_logger()
router = APIRouter()


@router.get("/technical/{symbol}")
async def get_technical_indicators(
    symbol: str = Path(..., min_length=1, max_length=5, pattern=r"^[A-Za-z]+$"),
    session: Dict = Depends(get_current_session),
    _rate: None = Depends(get_rate_limiter(30)),
) -> Dict[str, Any]:
    """Get technical indicators for a symbol."""
    try:
        from src.data.alpaca_client import AlpacaMarketDataClient

        client = AlpacaMarketDataClient()
        quote, indicators = await asyncio.gather(
            client.get_current_quote(symbol),
            client.get_technical_indicators(symbol),
        )

        candles = []
        try:
            df = await client.get_historical_data(symbol, period="3mo", interval="1d")
            if not df.empty:
                for idx, row in df.tail(90).iterrows():
                    candles.append({
                        "date": str(idx.date()) if hasattr(idx, "date") else str(idx),
                        "open": float(row.get("Open", row.get("open", 0))),
                        "high": float(row.get("High", row.get("high", 0))),
                        "low": float(row.get("Low", row.get("low", 0))),
                        "close": float(row.get("Close", row.get("close", 0))),
                        "volume": int(row.get("Volume", row.get("volume", 0))),
                    })
        except Exception as candle_err:
            logger.warning(f"Could not fetch candles for {symbol}: {candle_err}")

        return {
            "symbol": symbol,
            "price": quote.get("price", indicators.get("current_price", 0)),
            "change": quote.get("change", 0),
            "change_percent": quote.get("change_percent", indicators.get("change_percent", 0)),
            "bid": quote.get("bid", 0),
            "ask": quote.get("ask", 0),
            "volume": quote.get("volume", indicators.get("volume", 0)),
            "avg_volume": int(indicators.get("avg_volume", indicators.get("volume", 1_000_000))),
            "indicators": indicators,
            "candles": candles,
            "last_updated": quote.get("timestamp", datetime.utcnow().isoformat()),
        }
    except Exception as exc:
        logger.error(f"Technical indicators error for {symbol}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/signals/{symbol}")
async def get_trading_signals(
    symbol: str = Path(..., min_length=1, max_length=5, pattern=r"^[A-Za-z]+$"),
    session: Dict = Depends(get_current_session),
    _rate: None = Depends(get_rate_limiter(30)),
) -> Dict[str, Any]:
    """Get trading signals for a symbol."""
    try:
        orchestrator = get_orchestrator()
        analysis_result = await orchestrator.process_user_query(
            f"trading signals for {symbol}",
            {
                "selectedStock": symbol,
                "risk_profile": {"risk_level": "moderate", "experience": "intermediate"},
            },
        )
        trading_signals = analysis_result.get("frontend_data", {}).get("trading_signals", [])
        return {
            "signals": trading_signals,
            "symbol": symbol,
            "timestamp": time.time(),
            "total_signals": len(trading_signals),
            "data_source": "ai_agent_analysis",
        }
    except Exception as exc:
        logger.error(f"Trading signals API error for {symbol}: {exc}", exc_info=True)
        raise HTTPException(status_code=502, detail="Trading signals are temporarily unavailable")
