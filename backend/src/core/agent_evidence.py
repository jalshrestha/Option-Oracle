"""
Public-facing evidence contract for stock analysis responses.

Agents can keep internal diagnostics, but the final chat writer should receive
only trade evidence, source coverage, and user-facing caveats.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List


INTERNAL_TERMS = (
    "llm",
    "formatter",
    "deterministic",
    "fallback",
    "confidence cap",
    "confidence_cap",
    "professional indicator library",
    "matched-pattern database",
    "matched pattern database",
    "backend",
    "failed",
    "api limitation",
)


def build_agent_evidence(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Build the normalized evidence packet consumed by the final writer."""
    agent_results = analysis.get("agent_results", {}) or {}
    technical = agent_results.get("technical", {}) or {}
    flow = agent_results.get("flow", {}) or {}
    sentiment = agent_results.get("sentiment", {}) or {}
    history = agent_results.get("history", {}) or {}
    signal = analysis.get("signal", {}) or {}
    trade_decision = analysis.get("trade_decision", {}) or {}

    technical_snapshot = technical.get("market_data_snapshot", {}) or {}
    flow_metrics = flow.get("metrics", {}) or {}

    return {
        "symbol": analysis.get("symbol") or signal.get("symbol"),
        "decision": {
            "action": trade_decision.get("decision", "NO_TRADE"),
            "direction": trade_decision.get("direction") or _bias_from_signal(signal.get("direction")),
            "signal": signal.get("direction", "HOLD"),
            "confidence": trade_decision.get("confidence", signal.get("confidence", 0.0)),
            "decision_score": analysis.get("decision_score"),
            "current_price": signal.get("current_price") or technical_snapshot.get("current_price"),
            "entry_trigger": trade_decision.get("entry_trigger"),
            "invalidation": trade_decision.get("invalidation"),
            "target": trade_decision.get("target"),
            "rationale": _clean_list(trade_decision.get("rationale", [])),
        },
        "source_coverage": _source_coverage(analysis.get("data_quality", {}) or {}),
        "technical": {
            "scenario": technical.get("scenario") or analysis.get("market_scenario"),
            "score": technical.get("weighted_score"),
            "confidence": technical.get("confidence"),
            "support": (technical.get("support_resistance", {}) or {}).get("support"),
            "resistance": (technical.get("support_resistance", {}) or {}).get("resistance"),
            "volume": technical.get("volume_analysis"),
            "indicators": _technical_indicator_snapshot(technical),
            "evidence": _clean_list(technical.get("key_insights", [])),
        },
        "options_flow": {
            "score": flow.get("flow_score"),
            "confidence": flow.get("confidence"),
            "sentiment": flow.get("flow_sentiment"),
            "unusual_activity": bool(flow.get("unusual_activity", False)),
            "put_call_ratio": flow_metrics.get("put_call_ratio"),
            "call_volume": flow_metrics.get("call_volume"),
            "put_volume": flow_metrics.get("put_volume"),
            "total_volume": flow_metrics.get("total_volume"),
            "evidence": _clean_list(flow.get("key_insights", [])),
        },
        "sentiment": {
            "score": sentiment.get("aggregate_score"),
            "confidence": sentiment.get("confidence"),
            "trend": sentiment.get("sentiment_trend"),
            "evidence": _clean_list(sentiment.get("key_factors", [])),
            "risks": _clean_list(sentiment.get("risk_factors", [])),
        },
        "history": {
            "score": history.get("pattern_score"),
            "confidence": history.get("confidence"),
            "pattern": history.get("dominant_pattern"),
            "levels": history.get("key_levels"),
            "evidence": _clean_list(history.get("pattern_insights", [])),
        },
        "risk": {
            "strike_recommendations": analysis.get("strike_recommendations", [])[:3],
            "max_loss": trade_decision.get("max_loss"),
            "reward_risk": trade_decision.get("reward_risk"),
            "position_size": trade_decision.get("position_size"),
        },
    }


def _bias_from_signal(direction: Any) -> str:
    if direction in {"BUY", "STRONG_BUY"}:
        return "bullish"
    if direction in {"SELL", "STRONG_SELL"}:
        return "bearish"
    return "neutral"


def _technical_indicator_snapshot(technical: Dict[str, Any]) -> Dict[str, Any]:
    snapshot = technical.get("market_data_snapshot", {}) or {}
    indicators = technical.get("indicators", {}) or {}
    return {
        "rsi": snapshot.get("rsi"),
        "macd": snapshot.get("macd"),
        "macd_signal": snapshot.get("macd_signal"),
        "vwap": snapshot.get("vwap"),
        "ma20": snapshot.get("ma20"),
        "ma50": snapshot.get("ma50"),
        "relative_volume": (technical.get("volume_analysis", {}) or {}).get("relative_volume"),
        "ma_signal": (indicators.get("ma", {}) or {}).get("signal"),
        "rsi_signal": (indicators.get("rsi", {}) or {}).get("signal"),
        "macd_signal_score": (indicators.get("macd", {}) or {}).get("signal"),
    }


def _source_coverage(data_quality: Dict[str, Any]) -> Dict[str, str]:
    agents = data_quality.get("agents", {}) if isinstance(data_quality, dict) else {}
    return {
        "overall": _overall_source_text(data_quality.get("overall", "unknown") if isinstance(data_quality, dict) else "unknown"),
        "technical": _source_note("technical", agents.get("technical", {})),
        "options_flow": _source_note("flow", agents.get("flow", {})),
        "sentiment": _source_note("sentiment", agents.get("sentiment", {})),
        "history": _source_note("history", agents.get("history", {})),
    }


def _overall_source_text(status: str) -> str:
    return {
        "usable": "usable source coverage",
        "partial": "partial source coverage",
        "weak": "weak source coverage",
    }.get(str(status), "source coverage unknown")


def _source_note(agent: str, quality: Dict[str, Any]) -> str:
    if not isinstance(quality, dict):
        return "source coverage unknown"
    status = quality.get("source_status", "unknown")
    if status in {"fallback", "unavailable"} or quality.get("is_fallback"):
        return "data unavailable"
    if agent == "technical":
        return "daily price and volume candles"
    if agent == "flow":
        return "public options chain volume/open interest only"
    if agent == "sentiment":
        return "news, StockTwits, and market proxy sources"
    if agent == "history":
        return "historical daily candle statistics"
    return "available market data"


def _clean_list(items: Iterable[Any]) -> List[str]:
    cleaned = []
    for item in items or []:
        text = str(item).strip()
        if not text:
            continue
        lower = text.lower()
        if any(term in lower for term in INTERNAL_TERMS):
            continue
        cleaned.append(text)
    return cleaned
