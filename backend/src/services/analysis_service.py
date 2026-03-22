"""
AnalysisService — orchestrates AI agents and persists signals.

Rules:
  - No direct DB access. All persistence goes through repositories.
  - No HTTP concerns. No Request/Response objects.
  - Raises OracleError subclasses; never raises raw exceptions to callers.
"""
import asyncio
from datetime import datetime
from typing import Any, Dict, List

from config.logging import get_api_logger
from config.settings import settings
from src.exceptions import AnalysisTimeoutError, ExternalAPIError
from src.repositories.signals import TradingSignalRepository
from src.schemas.analysis import AnalysisResponse, SignalSchema, StrikeRecommendation

logger = get_api_logger()


class AnalysisService:
    """Business logic for stock analysis requests."""

    def __init__(self, orchestrator, signal_repo: TradingSignalRepository) -> None:
        self._orchestrator = orchestrator
        self._signal_repo = signal_repo

    async def analyze(
        self, symbol: str, risk_profile: Dict[str, Any]
    ) -> AnalysisResponse:
        """
        Run the full agent pipeline for *symbol* and persist the result.

        Raises:
            AnalysisTimeoutError: If agents exceed the configured timeout.
            ExternalAPIError:     If OpenAI / Alpaca calls fail.
        """
        try:
            raw = await asyncio.wait_for(
                self._orchestrator.analyze_stock(symbol, risk_profile),
                timeout=settings.analysis_timeout_seconds,
            )
        except asyncio.TimeoutError:
            raise AnalysisTimeoutError(
                f"Analysis for {symbol} exceeded {settings.analysis_timeout_seconds}s timeout"
            )
        except Exception as e:
            raise ExternalAPIError(f"Agent pipeline failed for {symbol}: {e}") from e

        response = self._build_response(raw)

        # Persist asynchronously (non-blocking); log but don't fail on DB errors
        try:
            signal_data = {
                "symbol": symbol,
                "signal_type": "hybrid",
                "direction": response.signal.direction,
                "strength": response.signal.strength,
                "confidence_score": response.confidence,
                "market_scenario": response.market_scenario,
                "agent_weights": response.agent_weights,
                "technical_analysis": raw.get("agent_results", {}).get("technical", {}),
                "sentiment_analysis": raw.get("agent_results", {}).get("sentiment", {}),
                "flow_analysis": raw.get("agent_results", {}).get("flow", {}),
                "historical_analysis": raw.get("agent_results", {}).get("history", {}),
                "strike_recommendations": raw.get("strike_recommendations", []),
                "educational_content": raw.get("educational_content", ""),
            }
            await self._signal_repo.save(signal_data)
        except Exception as e:
            logger.warning(f"Failed to persist signal for {symbol}: {e}")

        return response

    async def get_history(
        self, symbol: str, limit: int = 10
    ) -> List[SignalSchema]:
        """Return recent signals for *symbol*, newest first."""
        records = await self._signal_repo.get_by_symbol(symbol, limit=limit)
        signals = []
        for r in records:
            try:
                signals.append(
                    SignalSchema(
                        direction=r["direction"],
                        strength=r.get("strength", "moderate"),
                        confidence=r.get("confidence_score", 0.5),
                        decision_score=0.0,
                        strategy_type="hybrid",
                        market_scenario=r.get("market_scenario", "range_bound"),
                        reasoning="",
                    )
                )
            except Exception:
                pass  # Skip malformed historical records
        return signals

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_response(self, raw: Dict[str, Any]) -> AnalysisResponse:
        """Convert raw orchestrator output to a typed AnalysisResponse."""
        raw_signal = raw.get("signal", {})
        signal = SignalSchema(
            direction=raw_signal.get("direction", "HOLD"),
            strength=raw_signal.get("strength", "weak"),
            confidence=raw_signal.get("confidence", 0.5),
            decision_score=raw_signal.get("decision_score", 0.0),
            strategy_type=raw_signal.get("strategy_type", "neutral"),
            market_scenario=raw_signal.get("market_scenario", "range_bound"),
            reasoning=raw_signal.get("reasoning", ""),
        )

        strike_recs = []
        for sr in raw.get("strike_recommendations", []):
            if isinstance(sr, dict):
                try:
                    strike_recs.append(
                        StrikeRecommendation(
                            option_type=sr.get("option_type", "call"),
                            strike=float(sr.get("strike", sr.get("strike_price", 0))),
                            expiry=sr.get("expiry", sr.get("expiry_date", "")),
                            delta=sr.get("delta"),
                            premium=sr.get("premium"),
                            risk_reward=sr.get("risk_reward"),
                            rationale=sr.get("rationale", ""),
                        )
                    )
                except Exception:
                    pass

        return AnalysisResponse(
            symbol=raw.get("symbol", ""),
            signal=signal,
            agent_results=raw.get("agent_results", {}),
            strike_recommendations=strike_recs,
            educational_content=str(raw.get("educational_content", "")),
            confidence=raw.get("confidence", signal.confidence),
            market_scenario=raw.get("market_scenario", signal.market_scenario),
            agent_weights=raw.get("agent_weights", {}),
            analysis_time_seconds=raw.get("analysis_time_seconds", 0.0),
            timestamp=datetime.now().isoformat(),
        )
