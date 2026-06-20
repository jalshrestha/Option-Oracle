"""
Historical Pattern Analysis Agent
OpenAI Agents SDK v0.3.0 Implementation
"""
from typing import Dict, Any
from datetime import datetime
import asyncio
from .base_agent import BaseAgent
from config.logging import get_agents_logger

logger = get_agents_logger()


class HistoricalPatternAgent(BaseAgent):
    """AI agent specializing in historical pattern analysis"""
    
    def __init__(self, client):
        super().__init__(client, "Historical Pattern")
        
    def _get_system_instructions(self) -> str:
        return """
You are a historical pattern analyst for the Neural Options Oracle++ system.

Your responsibilities:
1. Analyze historical price patterns and seasonality
2. Identify recurring market behaviors and cycles
3. Compare current patterns to historical precedents
4. Provide pattern-based trading insights

Weight in system: 20% of final decision

OUTPUT FORMAT (JSON):
{
    "pattern_score": float_between_-1_and_1,
    "confidence": float_between_0_and_1,
    "dominant_pattern": "uptrend|downtrend|consolidation|breakout|reversal",
    "historical_matches": [
        {"date": "YYYY-MM-DD", "similarity": float, "outcome": "string"}
    ],
    "seasonality": {
        "monthly_bias": "bullish|bearish|neutral",
        "weekly_pattern": "string",
        "earnings_cycle": "pre|post|neutral"
    },
    "pattern_strength": float_between_0_and_1,
    "time_horizon": "short|medium|long",
    "key_levels": {
        "support": [float, float],
        "resistance": [float, float]
    },
    "pattern_insights": ["string1", "string2"]
}
"""
    
    def _get_response_schema(self) -> Dict[str, Any]:
        """Get JSON Schema for historical pattern response"""
        return {
            "type": "object",
            "properties": {
                "pattern_score": {"type": "number", "minimum": -1.0, "maximum": 1.0},
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "dominant_pattern": {"type": "string", "enum": ["uptrend", "downtrend", "consolidation", "breakout", "reversal"]},
                "historical_matches": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                            "similarity": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                            "outcome": {"type": "string"}
                        },
                        "required": ["date", "similarity", "outcome"],
                        "additionalProperties": False
                    },
                    "maxItems": 10
                },
                "seasonality": {
                    "type": "object",
                    "properties": {
                        "monthly_bias": {"type": "string", "enum": ["bullish", "bearish", "neutral"]},
                        "weekly_pattern": {"type": "string"},
                        "earnings_cycle": {"type": "string", "enum": ["pre", "post", "neutral"]}
                    },
                    "required": ["monthly_bias", "weekly_pattern", "earnings_cycle"],
                    "additionalProperties": False
                },
                "pattern_strength": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "time_horizon": {"type": "string", "enum": ["short", "medium", "long"]},
                "key_levels": {
                    "type": "object",
                    "properties": {
                        "support": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 2
                        },
                        "resistance": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 2
                        }
                    },
                    "required": ["support", "resistance"],
                    "additionalProperties": False
                },
                "pattern_insights": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5
                }
            },
            "required": ["pattern_score", "confidence", "dominant_pattern", "historical_matches", "seasonality", "pattern_strength", "time_horizon", "key_levels", "pattern_insights"],
            "additionalProperties": False
        }
    
    async def analyze(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Analyze historical patterns for the symbol"""
        
        try:
            logger.info(f"Starting historical pattern analysis for {symbol}")
            
            history_context = await self._get_real_historical_context(symbol)
            if history_context.get("data_quality", {}).get("source_status") == "unavailable":
                return self._get_unavailable_history(symbol, history_context.get("error"))

            analysis = self._build_real_pattern_analysis(symbol, history_context)
            analysis = self._validate_pattern_analysis(
                analysis,
                symbol,
                float(history_context.get("current_price") or 0),
                history_context.get("data_quality"),
            )
            
            logger.info(f"Historical pattern analysis completed for {symbol}")
            return analysis
            
        except Exception as e:
            logger.error(f"Historical pattern analysis failed for {symbol}: {e}")
            return self._get_unavailable_history(symbol, str(e))
    
    async def _get_real_historical_context(self, symbol: str) -> Dict[str, Any]:
        """Fetch and derive historical context from real daily candles."""
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            history = await asyncio.wait_for(
                asyncio.to_thread(ticker.history, period="1y", interval="1d"),
                timeout=12,
            )
            if history is None or history.empty or "Close" not in history:
                return {
                    "data_quality": {
                        "source_status": "unavailable",
                        "source": "yfinance_history",
                        "confidence_cap": 0.0,
                        "is_fallback": True,
                        "warnings": ["No historical candles returned"],
                    },
                    "error": "Historical candles unavailable",
                }

            history = history.dropna(subset=["Close"])
            if len(history) < 30:
                return {
                    "data_quality": {
                        "source_status": "unavailable",
                        "source": "yfinance_history",
                        "confidence_cap": 0.0,
                        "is_fallback": True,
                        "warnings": ["Not enough historical candles returned"],
                    },
                    "error": "Insufficient historical candles",
                }

            close = history["Close"]
            current_price = float(close.iloc[-1])
            returns = close.pct_change()
            ma20 = float(close.rolling(20).mean().iloc[-1])
            ma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else ma20
            volatility = float(returns.tail(21).std() * (252 ** 0.5) * 100)
            support_window = history.tail(63)

            def period_return(days: int) -> float:
                if len(close) <= days:
                    return 0.0
                base = float(close.iloc[-days - 1])
                if base <= 0:
                    return 0.0
                return ((current_price / base) - 1) * 100

            year_rows = history[history.index.year == history.index[-1].year]
            ytd_base = float(year_rows["Close"].iloc[0]) if not year_rows.empty else float(close.iloc[0])
            ytd_return = ((current_price / ytd_base) - 1) * 100 if ytd_base > 0 else 0.0

            current_month = history.index[-1].month
            monthly_returns = close.resample("ME").last().pct_change().dropna()
            month_avg = float(
                monthly_returns[monthly_returns.index.month == current_month].mean() * 100
            ) if not monthly_returns.empty else 0.0
            if month_avg != month_avg:
                month_avg = 0.0

            return {
                "current_price": current_price,
                "week_return": period_return(5),
                "month_return": period_return(21),
                "quarter_return": period_return(63),
                "ytd_return": ytd_return,
                "ma20": ma20,
                "ma50": ma50,
                "volatility": volatility,
                "support": [
                    float(support_window["Low"].tail(20).min()),
                    float(support_window["Low"].min()),
                ],
                "resistance": [
                    float(support_window["High"].tail(20).max()),
                    float(support_window["High"].max()),
                ],
                "data_points": int(len(history)),
                "month_avg": month_avg,
                "day_of_week": history.index[-1].day_name(),
                "data_quality": {
                    "source_status": "derived",
                    "source": "yfinance_history",
                    "confidence_cap": 0.65,
                    "is_fallback": False,
                    "warnings": ["Historical pattern agent uses derived candle statistics, not a matched-pattern database"],
                },
            }
        except Exception as exc:
            logger.warning(f"Historical price context unavailable for {symbol}: {exc}")
            return {
                "data_quality": {
                    "source_status": "unavailable",
                    "source": "yfinance_history",
                    "confidence_cap": 0.0,
                    "is_fallback": True,
                    "warnings": [str(exc)],
                },
                "error": str(exc),
            }

    def _build_real_pattern_analysis(self, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build pattern output from real historical candles without synthetic matches."""
        month_return = float(context.get("month_return") or 0)
        quarter_return = float(context.get("quarter_return") or 0)
        ytd_return = float(context.get("ytd_return") or 0)
        current_price = float(context.get("current_price") or 0)
        ma20 = float(context.get("ma20") or current_price)
        ma50 = float(context.get("ma50") or ma20)
        volatility = float(context.get("volatility") or 0)

        trend_score = 0.0
        if current_price > ma20:
            trend_score += 0.25
        elif current_price < ma20:
            trend_score -= 0.25
        if ma20 > ma50:
            trend_score += 0.25
        elif ma20 < ma50:
            trend_score -= 0.25
        trend_score += max(-0.35, min(0.35, quarter_return / 30))

        pattern_score = max(-1.0, min(1.0, trend_score))
        if abs(pattern_score) < 0.2:
            dominant_pattern = "consolidation"
        elif month_return * quarter_return < 0:
            dominant_pattern = "reversal"
        elif abs(month_return) > 8 and abs(quarter_return) > 12:
            dominant_pattern = "breakout"
        elif pattern_score > 0:
            dominant_pattern = "uptrend"
        else:
            dominant_pattern = "downtrend"

        monthly_bias = "bullish" if context.get("month_avg", 0) > 1 else "bearish" if context.get("month_avg", 0) < -1 else "neutral"
        volatility_label = "high" if volatility >= 45 else "moderate" if volatility >= 25 else "low"
        confidence = min(0.65, 0.35 + min(abs(pattern_score), 0.4) + min(context.get("data_points", 0) / 500, 0.15))

        return {
            "pattern_score": pattern_score,
            "confidence": confidence,
            "dominant_pattern": dominant_pattern,
            "historical_matches": [],
            "seasonality": {
                "monthly_bias": monthly_bias,
                "weekly_pattern": f"Latest candle is from {context.get('day_of_week', 'unknown')}; no weekday edge inferred",
                "earnings_cycle": "neutral",
            },
            "pattern_strength": min(1.0, abs(pattern_score) + min(volatility / 200, 0.25)),
            "time_horizon": "medium" if abs(quarter_return) > abs(month_return) else "short",
            "key_levels": {
                "support": context.get("support", []),
                "resistance": context.get("resistance", []),
            },
            "pattern_insights": [
                f"1-week return {context.get('week_return', 0):.1f}%, 1-month return {month_return:.1f}%, 3-month return {quarter_return:.1f}%, YTD return {ytd_return:.1f}%.",
                f"Price is {'above' if current_price >= ma20 else 'below'} MA20 and MA20 is {'above' if ma20 >= ma50 else 'below'} MA50.",
                f"Realized volatility is {volatility:.1f}%, a {volatility_label} regime.",
                "No historical match dates are shown because no real matched-pattern database is connected yet.",
            ],
        }

    def _validate_pattern_analysis(
        self,
        analysis: Dict,
        symbol: str,
        current_price: float = 0.0,
        data_quality: Dict[str, Any] | None = None,
    ) -> Dict:
        """Validate pattern analysis"""
        
        if 'pattern_score' not in analysis:
            analysis['pattern_score'] = 0.0
        if 'confidence' not in analysis:
            analysis['confidence'] = 0.5
        if 'dominant_pattern' not in analysis:
            analysis['dominant_pattern'] = 'consolidation'
            
        analysis['pattern_score'] = max(-1.0, min(1.0, analysis['pattern_score']))
        data_quality = data_quality or {
            'source_status': 'unavailable',
            'source': 'unknown',
            'confidence_cap': 0.0,
            'is_fallback': True,
            'warnings': [],
        }
        analysis['confidence'] = min(self._validate_confidence(analysis['confidence']), data_quality.get('confidence_cap', 0.0))
        analysis['timestamp'] = datetime.now().isoformat()
        analysis['symbol'] = symbol
        analysis['agent'] = self.name
        analysis['data_quality'] = data_quality
        analysis['source'] = data_quality.get('source')
        analysis['is_fallback'] = bool(data_quality.get('is_fallback'))
        analysis['fallback'] = bool(data_quality.get('is_fallback'))
        self._reconcile_key_levels(analysis, current_price)
        
        return analysis

    def _reconcile_key_levels(self, analysis: Dict, current_price: float) -> None:
        """Keep historical support/resistance near the live quote."""
        if current_price <= 0:
            return

        key_levels = analysis.setdefault('key_levels', {})
        supports = key_levels.get('support') or []
        resistances = key_levels.get('resistance') or []

        levels = [level for level in supports + resistances if isinstance(level, (int, float))]
        stale = not levels or any(abs(float(level) - current_price) / current_price > 0.4 for level in levels)
        if not stale:
            return

        key_levels['support'] = [round(current_price * 0.95, 2), round(current_price * 0.90, 2)]
        key_levels['resistance'] = [round(current_price * 1.05, 2), round(current_price * 1.10, 2)]
        insights = analysis.setdefault('pattern_insights', [])
        insights.insert(0, "Historical key levels were reconciled to the current quote to avoid stale price context.")
    
    def _get_unavailable_history(self, symbol: str, error: str | None = None) -> Dict:
        """Return no-signal history when real historical candles are unavailable."""
        data_quality = {
            'source_status': 'unavailable',
            'source': 'yfinance_history',
            'confidence_cap': 0.0,
            'is_fallback': True,
            'warnings': [error] if error else ['Historical candles unavailable'],
        }
        return {
            'pattern_score': 0.0,
            'confidence': 0.0,
            'dominant_pattern': 'consolidation',
            'historical_matches': [],
            'seasonality': {
                'monthly_bias': 'neutral',
                'weekly_pattern': 'unavailable',
                'earnings_cycle': 'neutral'
            },
            'pattern_strength': 0.0,
            'time_horizon': 'medium',
            'key_levels': {
                'support': [0.0, 0.0],
                'resistance': [0.0, 0.0]
            },
            'pattern_insights': ['Historical data unavailable'],
            'error': error or 'Historical analysis unavailable',
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'agent': self.name,
            'data_quality': data_quality,
            'source': data_quality['source'],
            'is_fallback': True,
            'fallback': True,
        }

    def _get_fallback_history(self, symbol: str) -> Dict:
        return self._get_unavailable_history(symbol)
