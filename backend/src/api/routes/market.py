"""Market and agent-analysis routes."""
import asyncio
import time
from typing import Any, Dict

from fastapi import APIRouter, Depends, Path

from config.logging import get_api_logger
from config.settings import settings
from src.api.dependencies import get_current_session, get_orchestrator, get_rate_limiter

logger = get_api_logger()
router = APIRouter()


@router.get("/stocks/hot-stocks")
async def get_hot_stocks(
    session: Dict = Depends(get_current_session),
    _rate: None = Depends(get_rate_limiter(20)),
) -> Dict[str, Any]:
    """Get hot stocks with StockTwits trending data and market data."""
    try:
        logger.info("Getting trending stocks from StockTwits")

        from openai import OpenAI
        from src.agents.web_scraper_agent import get_web_scraper_agent

        orchestrator = get_orchestrator()
        openai_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        web_scraper = get_web_scraper_agent(openai_client)

        trending_stocks_data = await web_scraper.get_trending_stocks(limit=5)

        if not trending_stocks_data:
            logger.warning("No trending stocks found from StockTwits - using fallback symbols")
            symbols = ["NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NFLX"]
        else:
            symbols = [stock["symbol"] for stock in trending_stocks_data]

        for idx_sym in ["SPY", "QQQ", "IWM"]:
            if idx_sym not in symbols:
                symbols.append(idx_sym)

        async def _process_one_stock(symbol: str, trending_data: dict | None) -> dict | None:
            try:
                market_data = await orchestrator.market_data_manager.get_comprehensive_data(symbol)
                quote = market_data.get("quote", {})
                current_price = float(quote.get("price", 0))
                volume = float(quote.get("volume", 0))
                change = float(quote.get("change", 0))
                change_percent = float(quote.get("change_percent", 0))

                if change == 0 and change_percent == 0:
                    previous_close = float(quote.get("previous_close", current_price))
                    change = current_price - previous_close
                    change_percent = (change / previous_close) * 100 if previous_close > 0 else 0

                if abs(change_percent) > 50:
                    logger.warning(f"Extreme change detected for {symbol}: {change_percent:.1f}% - using 0%")
                    change = 0
                    change_percent = 0

                historical = market_data.get("historical", [])
                if historical:
                    sparkline_data = [
                        {"value": float(bar.get("close", current_price))}
                        for bar in historical[-20:]
                    ]
                else:
                    sparkline_data = [{"value": current_price} for _ in range(20)]

                ai_signals = []
                ai_score = 50

                if trending_data:
                    sentiment = trending_data.get("sentiment", "Neutral")
                    mentions = trending_data.get("mentions", 0)
                    ai_signals.append(f"StockTwits: {sentiment}")
                    if isinstance(mentions, str):
                        try:
                            mentions = int(mentions)
                        except ValueError:
                            mentions = 0
                    if mentions > 0:
                        ai_signals.append(f"{mentions} mentions")
                    sentiment_score = trending_data.get("sentiment_score", 0.5)
                    if sentiment_score is not None:
                        ai_score = max(ai_score, int(sentiment_score * 100))

                if change > 0:
                    ai_signals.append("Price Up")
                    ai_score += 10
                elif change < 0:
                    ai_signals.append("Price Down")
                    ai_score -= 5

                if volume > 1_000_000:
                    ai_signals.append("High Volume")
                    ai_score += 5

                ai_score = max(0, min(100, ai_score))
                return {
                    "symbol": symbol,
                    "name": (trending_data.get("name") if trending_data else None)
                    or market_data.get("company_name", f"{symbol} Inc"),
                    "price": current_price,
                    "change": change,
                    "changePercent": change_percent,
                    "volume": volume,
                    "sparklineData": sparkline_data,
                    "aiScore": ai_score,
                    "signals": ai_signals or ["Market Data"],
                    "trending": (trending_data and trending_data.get("trending", False)) or ai_score > 75,
                }
            except Exception as exc:
                logger.error(f"Error processing {symbol}: {exc}")
                return None

        paired = [
            (symbols[i], trending_stocks_data[i] if trending_stocks_data and i < len(trending_stocks_data) else None)
            for i in range(len(symbols))
        ]
        results = await asyncio.gather(*[_process_one_stock(sym, td) for sym, td in paired])
        hot_stocks = [result for result in results if result is not None]

        return {
            "stocks": hot_stocks,
            "timestamp": time.time(),
            "total_count": len(hot_stocks),
            "data_source": "stocktwits_trending_with_ai_analysis",
            "trending_source": "stocktwits.com/sentiment/most-active",
            "symbols_found": symbols,
        }
    except Exception as exc:
        logger.error(f"Hot stocks API error: {exc}", exc_info=True)
        return {
            "stocks": [],
            "timestamp": time.time(),
            "total_count": 0,
            "data_source": "error",
        }


@router.get("/agents/{symbol}")
async def get_agent_analysis(
    symbol: str = Path(..., min_length=1, max_length=5, pattern=r"^[A-Za-z]+$"),
    session: Dict = Depends(get_current_session),
    _rate: None = Depends(get_rate_limiter(30)),
) -> Dict[str, Any]:
    """Get AI agent analysis for a symbol."""
    try:
        orchestrator = get_orchestrator()
        result = await orchestrator.process_user_query(
            f"agent analysis for {symbol}",
            {"selectedStock": symbol},
        )
        agent_data = result.get("frontend_data", {}).get("agent_analysis", [])
        signals = result.get("frontend_data", {}).get("trading_signals") or []
        return {
            "symbol": symbol,
            "agents": agent_data,
            "overall_signal": signals[0].get("direction", "HOLD") if signals else "HOLD",
            "timestamp": time.time(),
        }
    except Exception as exc:
        logger.error(f"Agent analysis error for {symbol}: {exc}", exc_info=True)
        return {
            "symbol": symbol,
            "agents": [],
            "overall_signal": "HOLD",
            "timestamp": time.time(),
        }
