"""Options chain and legacy options execution routes."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import JSONResponse

from config.logging import get_api_logger
from src.api.dependencies import get_current_session, get_rate_limiter

logger = get_api_logger()
router = APIRouter()


@router.get("/options/{symbol}")
async def get_options_chain(
    symbol: str = Path(..., min_length=1, max_length=5, pattern=r"^[A-Za-z]+$"),
    expiry: str = None,
    session: Dict = Depends(get_current_session),
    _rate: None = Depends(get_rate_limiter(30)),
) -> Dict[str, Any]:
    """Get options chain data for a symbol."""
    try:
        from src.data.alpaca_client import AlpacaMarketDataClient

        client = AlpacaMarketDataClient()
        data = await client.get_options_data(symbol)
        options = data.get("options_chain", [])
        expirations = data.get("expirations", [])
        selected_expiry = expiry or (expirations[0] if expirations else None)

        if selected_expiry:
            options = [o for o in options if o.get("expiration_date") == selected_expiry]

        calls = [o for o in options if o.get("option_type") == "call"]
        puts = [o for o in options if o.get("option_type") == "put"]

        def _row(o: Dict[str, Any], otype: str) -> Dict[str, Any]:
            return {
                "strike": o["strike_price"],
                "type": otype,
                "last": o["last_price"],
                "bid": o["bid"],
                "ask": o["ask"],
                "volume": o["volume"],
                "open_interest": o["open_interest"],
                "iv": o["implied_volatility"],
                "delta": 0.0,
                "itm": o.get("in_the_money", False),
            }

        return {
            "symbol": symbol,
            "expiry": selected_expiry,
            "calls": [_row(o, "call") for o in calls],
            "puts": [_row(o, "put") for o in puts],
            "put_call_ratio": data.get("put_call_ratio", 1.0),
            "total_call_volume": data.get("total_call_volume", 0),
            "total_put_volume": data.get("total_put_volume", 0),
        }
    except Exception as exc:
        logger.error(f"Options chain error for {symbol}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/options/execute")
async def execute_options_purchase(
    request: Dict[str, Any],
    session: Dict = Depends(get_current_session),
    _rate: None = Depends(get_rate_limiter(10)),
):
    """Execute options purchase after user confirmation."""
    try:
        purchase_type = request.get("type")
        analysis = request.get("analysis", {})
        confirmed = request.get("confirmed", False)

        if not confirmed:
            return JSONResponse(status_code=400, content={"error": "User confirmation required"})

        if purchase_type == "single_option":
            from src.agents.buy_agent import execute_option_buy

            result = await execute_option_buy(analysis, confirmed=True)
        elif purchase_type == "multi_options":
            from src.agents.multi_options_buy_agent import execute_multi_options_buy

            portfolio_data = {"recommended_portfolio": analysis.get("recommended_portfolio", [])}
            result = await execute_multi_options_buy(portfolio_data, confirmed=True)
        else:
            return JSONResponse(
                status_code=400,
                content={"error": f"Unknown purchase type: {purchase_type}"},
            )

        if result.get("status") == "executed" or result.get("portfolio_status") == "executed":
            logger.info(f"Options purchase executed successfully: {result}")
        else:
            logger.warning(f"Options purchase failed: {result}")

        return result
    except Exception as exc:
        logger.error(f"Options execution error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "An internal error occurred. Please try again.", "status": "failed"},
        )
