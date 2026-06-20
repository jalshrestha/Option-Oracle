"""
Technical Analysis Agent
OpenAI Agents SDK v0.3.0 Implementation
"""
from typing import Dict, Any
from datetime import datetime
from .base_agent import BaseAgent
from config.logging import get_agents_logger

logger = get_agents_logger()


class TechnicalAnalysisAgent(BaseAgent):
    """AI agent specializing in technical analysis for options trading"""
    
    def __init__(self, client):
        super().__init__(client, "Technical Analysis")
        
    def _get_system_instructions(self) -> str:
        """Get system instructions for technical analysis"""
        return """
You are an expert technical analyst specializing in options trading for the Neural Options Oracle++ system.

Your core responsibilities:
1. Analyze stock price movements, trends, and technical indicators
2. Detect current market scenarios and recommend dynamic weight adjustments
3. Provide actionable insights for options trading strategies
4. Calculate confidence scores based on technical signal strength

DYNAMIC SCENARIO DETECTION & WEIGHTS:
You must identify one of these market scenarios and apply the specified indicator weights:

1. STRONG_UPTREND: Clear upward momentum
   - MA(30%), RSI(15%), BB(10%), MACD(25%), VWAP(20%)

2. STRONG_DOWNTREND: Clear downward momentum  
   - MA(30%), RSI(15%), BB(10%), MACD(25%), VWAP(20%)

3. RANGE_BOUND: Sideways movement, low volatility
   - MA(15%), RSI(25%), BB(30%), MACD(15%), VWAP(15%)

4. BREAKOUT: Price breaking key levels, high volume
   - MA(20%), RSI(15%), BB(30%), MACD(20%), VWAP(15%)

5. POTENTIAL_REVERSAL: Signs of trend change
   - MA(15%), RSI(25%), BB(20%), MACD(30%), VWAP(10%)

6. HIGH_VOLATILITY: Elevated volatility environment
   - Increase BB weight by +10%, reduce others proportionally

KEY TECHNICAL INDICATORS TO ANALYZE:
- Moving Averages (5, 10, 20, 50, 200 day)
- RSI (14-period)
- Bollinger Bands (20, 2)
- MACD (12, 26, 9)
- VWAP (Volume Weighted Average Price)
- Volume analysis
- Support/Resistance levels
- Chart patterns

CRITICAL: You must respond with valid JSON format only. Always return a JSON object with this exact structure:
{
    "scenario": "scenario_name",
    "weighted_score": float_between_-1_and_1,
    "confidence": float_between_0_and_1,
    "indicators": {
        "ma": {"signal": float, "weight": float, "details": "string"},
        "rsi": {"signal": float, "weight": float, "details": "string"},
        "bb": {"signal": float, "weight": float, "details": "string"},
        "macd": {"signal": float, "weight": float, "details": "string"},
        "vwap": {"signal": float, "weight": float, "details": "string"}
    },
    "support_resistance": {
        "support": [float, float],
        "resistance": [float, float]
    },
    "volatility": {
        "current": float,
        "percentile": float,
        "trend": "increasing|decreasing|stable"
    },
    "volume_analysis": {
        "relative_volume": float,
        "volume_trend": "string",
        "volume_score": float
    },
    "key_insights": ["string1", "string2", "string3"],
    "options_strategy_suggestion": "string"
}

IMPORTANT CALCULATION RULES:
- weighted_score = sum of (indicator_signal * indicator_weight) for all indicators
- All signals must be between -1 (strong bearish) and +1 (strong bullish)  
- Confidence reflects how aligned indicators are (high when most agree)
- Adjust weights dynamically based on detected scenario
- Consider volatility environment for strategy suggestions

Remember: You are the primary decision driver with 60% weight in the final system decision.
"""
    
    def _get_response_schema(self) -> Dict[str, Any]:
        """Get JSON Schema for technical analysis response"""
        return {
            "type": "object",
            "properties": {
                "scenario": {
                    "type": "string",
                    "enum": ["STRONG_UPTREND", "STRONG_DOWNTREND", "RANGE_BOUND", "BREAKOUT", "POTENTIAL_REVERSAL", "HIGH_VOLATILITY"]
                },
                "weighted_score": {
                    "type": "number",
                    "minimum": -1.0,
                    "maximum": 1.0
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "indicators": {
                    "type": "object",
                    "properties": {
                        "ma": {
                            "type": "object",
                            "properties": {
                                "signal": {"type": "number", "minimum": -1.0, "maximum": 1.0},
                                "weight": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                                "details": {"type": "string"}
                            },
                            "required": ["signal", "weight", "details"],
                            "additionalProperties": False
                        },
                        "rsi": {
                            "type": "object",
                            "properties": {
                                "signal": {"type": "number", "minimum": -1.0, "maximum": 1.0},
                                "weight": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                                "details": {"type": "string"}
                            },
                            "required": ["signal", "weight", "details"],
                            "additionalProperties": False
                        },
                        "bb": {
                            "type": "object",
                            "properties": {
                                "signal": {"type": "number", "minimum": -1.0, "maximum": 1.0},
                                "weight": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                                "details": {"type": "string"}
                            },
                            "required": ["signal", "weight", "details"],
                            "additionalProperties": False
                        },
                        "macd": {
                            "type": "object",
                            "properties": {
                                "signal": {"type": "number", "minimum": -1.0, "maximum": 1.0},
                                "weight": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                                "details": {"type": "string"}
                            },
                            "required": ["signal", "weight", "details"],
                            "additionalProperties": False
                        },
                        "vwap": {
                            "type": "object",
                            "properties": {
                                "signal": {"type": "number", "minimum": -1.0, "maximum": 1.0},
                                "weight": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                                "details": {"type": "string"}
                            },
                            "required": ["signal", "weight", "details"],
                            "additionalProperties": False
                        }
                    },
                    "required": ["ma", "rsi", "bb", "macd", "vwap"],
                    "additionalProperties": False
                },
                "support_resistance": {
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
                "volatility": {
                    "type": "object",
                    "properties": {
                        "current": {"type": "number", "minimum": 0.0},
                        "percentile": {"type": "number", "minimum": 0.0, "maximum": 100.0},
                        "trend": {"type": "string", "enum": ["increasing", "decreasing", "stable"]}
                    },
                    "required": ["current", "percentile", "trend"],
                    "additionalProperties": False
                },
                "volume_analysis": {
                    "type": "object",
                    "properties": {
                        "relative_volume": {"type": "number", "minimum": 0.0},
                        "volume_trend": {"type": "string"},
                        "volume_score": {"type": "number", "minimum": -1.0, "maximum": 1.0}
                    },
                    "required": ["relative_volume", "volume_trend", "volume_score"],
                    "additionalProperties": False
                },
                "key_insights": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 5
                },
                "options_strategy_suggestion": {"type": "string"}
            },
            "required": ["scenario", "weighted_score", "confidence", "indicators", "support_resistance", "volatility", "volume_analysis", "key_insights", "options_strategy_suggestion"],
            "additionalProperties": False
        }

    async def analyze(self, symbol: str, timeframe: str = "1d", **kwargs) -> Dict[str, Any]:
        """Analyze technical indicators for the given symbol"""
        
        try:
            logger.info(f"Starting technical analysis for {symbol}")
            
            # Get real market data
            from src.data.market_data_manager import market_data_manager
            market_data = await market_data_manager.get_comprehensive_data(symbol)
            
            # Extract technical indicators
            tech_data = market_data.get('technical', {})
            quote_data = market_data.get('quote', {})
            market_conditions = market_data.get('market_conditions', {})
            tech_data = self._reconcile_technical_with_quote(tech_data, quote_data)
            data_quality = self._assess_technical_data_quality(tech_data, quote_data)

            if data_quality["source_status"] in {"unavailable", "fallback"}:
                logger.warning(f"Technical indicators unavailable for {symbol}; returning no-signal result")
                return self._get_unavailable_analysis(symbol, tech_data, data_quality)
            
            # Prepare the analysis prompt with real market data
            messages = [
                {"role": "system", "content": self.system_instructions},
                {"role": "user", "content": f"""
Analyze the technical indicators for {symbol} using the following REAL MARKET DATA:

PRICE DATA:
- Current Price: {self._money(tech_data.get('current_price'))}
- Daily Change: {self._pct(tech_data.get('change_percent'))}
- Volume: {self._number(tech_data.get('current_volume'))} (Avg: {self._number(tech_data.get('avg_volume'))})
- Volume Ratio: {self._ratio(tech_data.get('volume_ratio'))}

TECHNICAL INDICATORS:
- RSI(14): {self._number(tech_data.get('rsi'), decimals=1)}
- MACD: {self._number(tech_data.get('macd'), decimals=3)} (Signal: {self._number(tech_data.get('macd_signal'), decimals=3)})
- MACD Histogram: {self._number(tech_data.get('macd_histogram'), decimals=3)}
- BB Position: {self._number(tech_data.get('bb_position'), decimals=2)} (0=lower, 0.5=middle, 1=upper)
- VWAP: {self._money(tech_data.get('vwap'))}

MOVING AVERAGES:
- MA5: {self._money(tech_data.get('ma5'))}
- MA20: {self._money(tech_data.get('ma20'))}
- MA50: {self._money(tech_data.get('ma50'))}
- MA200: {self._money(tech_data.get('ma200'))}

BOLLINGER BANDS:
- Upper: {self._money(tech_data.get('bb_upper'))}
- Middle: {self._money(tech_data.get('bb_middle'))}
- Lower: {self._money(tech_data.get('bb_lower'))}

VOLATILITY & MARKET CONDITIONS:
- 30-day HV: {self._pct(tech_data.get('volatility'))}
- Market VIX: {self._number(market_conditions.get('vix'), decimals=1)}
- Market Trend: {market_conditions.get('market_trend', 'neutral')}
- Volatility Regime: {market_conditions.get('volatility_regime', 'medium')}

SUPPORT/RESISTANCE:
- Resistance: {self._money(tech_data.get('resistance'))}
- Support: {self._money(tech_data.get('support'))}

Data Source: {tech_data.get('source', 'unknown')}
Data Quality: {data_quality['source_status']}

Please provide a comprehensive technical analysis with scenario detection and weighted scoring using this REAL market data.
                """}
            ]
            
            # Get analysis from GPT-4 with structured outputs
            response = await self._make_completion(
                messages, 
                temperature=0.3,
                response_schema=self._get_response_schema()
            )
            
            # Parse the response
            analysis = self._parse_json_response(response['content'])
            if analysis.get('fallback') and not data_quality.get('is_fallback'):
                logger.warning("Technical LLM response was not usable; using deterministic candle-based analysis")
                analysis = self._build_deterministic_analysis(tech_data, data_quality)
            
            # Validate and enhance the analysis
            analysis = self._validate_analysis(analysis, symbol, tech_data, data_quality)
            
            logger.info(f"Technical analysis completed for {symbol}: {analysis.get('scenario', 'unknown')} scenario")
            return analysis
            
        except Exception as e:
            logger.error(f"Technical analysis failed for {symbol}: {e}")
            return self._get_fallback_analysis(symbol)

    def _money(self, value: Any) -> str:
        try:
            if value is None:
                return "unavailable"
            return f"${float(value):.2f}"
        except (TypeError, ValueError):
            return "unavailable"

    def _pct(self, value: Any) -> str:
        try:
            if value is None:
                return "unavailable"
            return f"{float(value):.2f}%"
        except (TypeError, ValueError):
            return "unavailable"

    def _number(self, value: Any, decimals: int = 0) -> str:
        try:
            if value is None:
                return "unavailable"
            return f"{float(value):,.{decimals}f}"
        except (TypeError, ValueError):
            return "unavailable"

    def _ratio(self, value: Any) -> str:
        try:
            if value is None:
                return "unavailable"
            return f"{float(value):.2f}x"
        except (TypeError, ValueError):
            return "unavailable"

    def _reconcile_technical_with_quote(
        self,
        tech_data: Dict[str, Any],
        quote_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prevent placeholder technical prices from being mixed with live quotes."""
        reconciled = dict(tech_data or {})

        try:
            quote_price = float(quote_data.get('price') or 0)
            tech_price = float(reconciled.get('current_price') or 0)
        except (TypeError, ValueError):
            return reconciled

        if quote_price <= 0:
            return reconciled

        source = str(reconciled.get('source', '')).lower()
        has_placeholder_source = 'fallback' in source or 'unavailable' in source
        has_large_dislocation = tech_price <= 0 or abs(tech_price - quote_price) / quote_price > 0.2

        if not has_placeholder_source and not has_large_dislocation:
            return reconciled

        if has_placeholder_source:
            reconciled.update({
                'current_price': quote_price,
                'change_percent': quote_data.get('change_percent'),
                'current_volume': quote_data.get('volume'),
                'source': 'quote_only_no_technical_indicators',
                'data_quality': {
                    'source_status': 'unavailable',
                    'source': 'quote_only',
                    'confidence_cap': 0.0,
                    'is_fallback': True,
                    'warnings': ['Live quote available, but historical candles/technical indicators unavailable'],
                },
            })
            return reconciled

        change_percent = float(quote_data.get('change_percent') or reconciled.get('change_percent') or 0)
        volume = float(quote_data.get('volume') or reconciled.get('current_volume') or 1_000_000)
        avg_volume = float(reconciled.get('avg_volume') or max(volume, 1))

        reconciled.update({
            'current_price': quote_price,
            'change_percent': change_percent,
            'ma5': quote_price,
            'ma20': quote_price,
            'ma50': quote_price,
            'ma200': quote_price,
            'vwap': quote_price,
            'bb_upper': quote_price * 1.03,
            'bb_middle': quote_price,
            'bb_lower': quote_price * 0.97,
            'bb_position': 0.5,
            'current_volume': volume,
            'avg_volume': avg_volume,
            'volume_ratio': volume / avg_volume if avg_volume else 1.0,
            'resistance': quote_price * 1.05,
            'support': quote_price * 0.95,
            'source': 'quote_reconciled_real_price',
            'data_quality': {
                'source_status': 'limited',
                'source': 'quote_reconciled',
                'confidence_cap': 0.35,
                'is_fallback': False,
                'warnings': ['Technical price was reconciled against the live quote'],
            },
        })
        return reconciled

    def _assess_technical_data_quality(
        self,
        tech_data: Dict[str, Any],
        quote_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        explicit = tech_data.get('data_quality')
        if isinstance(explicit, dict):
            return {
                'source_status': explicit.get('source_status', 'unknown'),
                'source': explicit.get('source', tech_data.get('source', 'unknown')),
                'confidence_cap': float(explicit.get('confidence_cap', 0.0)),
                'is_fallback': bool(explicit.get('is_fallback', False)),
                'warnings': explicit.get('warnings', []),
            }

        source = str(tech_data.get('source') or 'unknown')
        required = ['current_price', 'ma20', 'ma50', 'rsi', 'macd', 'support', 'resistance']
        missing = [key for key in required if tech_data.get(key) is None]
        if 'fallback' in source.lower() or 'unavailable' in source.lower() or missing:
            warnings = ['Missing required technical fields: ' + ', '.join(missing)] if missing else []
            if quote_data.get('price'):
                warnings.append('Quote is available, but technical indicators are incomplete')
            return {
                'source_status': 'unavailable',
                'source': source,
                'confidence_cap': 0.0,
                'is_fallback': True,
                'warnings': warnings or ['Technical indicators unavailable'],
            }

        data_points = int(tech_data.get('data_points') or 0)
        if data_points and data_points < 50:
            return {
                'source_status': 'limited',
                'source': source,
                'confidence_cap': 0.45,
                'is_fallback': False,
                'warnings': [f'Only {data_points} historical bars available'],
            }

        return {
            'source_status': 'usable',
            'source': source,
            'confidence_cap': 0.8,
            'is_fallback': False,
            'warnings': [],
        }

    def _build_deterministic_analysis(
        self,
        market_data: Dict[str, Any],
        data_quality: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build a real-data technical read when the LLM JSON response is unusable."""
        def num(key: str) -> float | None:
            try:
                value = market_data.get(key)
                return float(value) if value is not None else None
            except (TypeError, ValueError):
                return None

        price = num('current_price')
        ma20 = num('ma20')
        ma50 = num('ma50')
        rsi = num('rsi')
        macd = num('macd')
        macd_signal = num('macd_signal')
        bb_position = num('bb_position')
        vwap = num('vwap')
        volume_ratio = num('volume_ratio')
        volatility = num('volatility')
        support = num('support')
        resistance = num('resistance')

        def clamp(value: float) -> float:
            return max(-1.0, min(1.0, value))

        ma_signal = 0.0
        if price and ma20 and ma50:
            ma_signal = clamp(((price - ma20) / ma20 + (price - ma50) / ma50) * 5)

        rsi_signal = 0.0
        if rsi is not None:
            if rsi < 30:
                rsi_signal = 0.45
            elif rsi > 70:
                rsi_signal = -0.45
            else:
                rsi_signal = clamp((rsi - 50) / 50)

        macd_signal_value = 0.0
        if macd is not None and macd_signal is not None and price:
            macd_signal_value = clamp((macd - macd_signal) / max(price * 0.01, 1))

        bb_signal = 0.0
        if bb_position is not None:
            bb_signal = clamp((bb_position - 0.5) * 2)

        vwap_signal = 0.0
        if price and vwap:
            vwap_signal = clamp((price - vwap) / vwap * 10)

        weights = {'ma': 0.30, 'rsi': 0.15, 'bb': 0.10, 'macd': 0.25, 'vwap': 0.20}
        weighted_score = (
            ma_signal * weights['ma']
            + rsi_signal * weights['rsi']
            + bb_signal * weights['bb']
            + macd_signal_value * weights['macd']
            + vwap_signal * weights['vwap']
        )
        weighted_score = clamp(weighted_score)

        if volatility and volatility > 45:
            scenario = 'high_volatility'
        elif weighted_score > 0.35:
            scenario = 'strong_uptrend'
        elif weighted_score < -0.35:
            scenario = 'strong_downtrend'
        else:
            scenario = 'range_bound'

        signal_values = [ma_signal, rsi_signal, bb_signal, macd_signal_value, vwap_signal]
        confidence = min(
            sum(abs(value) for value in signal_values) / len(signal_values),
            float(data_quality.get('confidence_cap', 0.55)),
        )

        insights = []
        if price and ma20:
            relation = 'above' if price > ma20 else 'below'
            insights.append(f"Price is {relation} the 20-day moving average.")
        if rsi is not None:
            insights.append(f"RSI is {rsi:.1f}, indicating {'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral-to-moderate'} momentum.")
        if volume_ratio is not None:
            insights.append(f"Volume is {volume_ratio:.2f}x its recent average.")
        if not insights:
            insights.append("Technical indicators were calculated from real candles, but signals are limited.")

        return {
            'scenario': scenario,
            'weighted_score': weighted_score,
            'confidence': confidence,
            'indicators': {
                'ma': {'signal': ma_signal, 'weight': weights['ma'], 'details': f"Price {self._money(price)} vs MA20 {self._money(ma20)} and MA50 {self._money(ma50)}."},
                'rsi': {'signal': rsi_signal, 'weight': weights['rsi'], 'details': f"RSI {self._number(rsi, 1)}."},
                'bb': {'signal': bb_signal, 'weight': weights['bb'], 'details': f"BB position {self._number(bb_position, 2)}."},
                'macd': {'signal': macd_signal_value, 'weight': weights['macd'], 'details': f"MACD {self._number(macd, 3)} vs signal {self._number(macd_signal, 3)}."},
                'vwap': {'signal': vwap_signal, 'weight': weights['vwap'], 'details': f"Price {self._money(price)} vs VWAP {self._money(vwap)}."},
            },
            'support_resistance': {
                'support': [support] if support else [],
                'resistance': [resistance] if resistance else [],
            },
            'volatility': {
                'current': volatility,
                'percentile': None,
                'trend': 'stable',
            },
            'volume_analysis': {
                'relative_volume': volume_ratio,
                'volume_trend': 'above average' if volume_ratio and volume_ratio > 1.2 else 'normal',
                'volume_score': clamp((volume_ratio - 1) if volume_ratio is not None else 0.0),
            },
            'key_insights': insights[:5],
            'options_strategy_suggestion': 'Wait for a confirmed directional trigger before choosing an options strategy.' if abs(weighted_score) < 0.25 else 'Use defined-risk options structures; verify liquidity before entry.',
        }
    
    def _validate_analysis(
        self,
        analysis: Dict,
        symbol: str,
        market_data: Dict,
        data_quality: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Validate and enhance the analysis response"""
        data_quality = data_quality or self._assess_technical_data_quality(market_data, {})

        # Ensure required fields exist
        self._ensure_fields(analysis, {
            'scenario': 'range_bound',
            'weighted_score': 0.0,
            'confidence': 0.5,
        })
        
        # Validate numeric ranges
        analysis['weighted_score'] = max(-1.0, min(1.0, analysis['weighted_score']))
        analysis['confidence'] = min(
            self._validate_confidence(analysis['confidence']),
            float(data_quality.get('confidence_cap', 0.8)),
        )
        
        # Add metadata
        analysis['timestamp'] = datetime.now().isoformat()
        analysis['symbol'] = symbol
        analysis['agent'] = self.name
        analysis['market_data_snapshot'] = market_data
        analysis['data_quality'] = data_quality
        analysis['source'] = data_quality.get('source', market_data.get('source', 'unknown'))
        analysis['is_fallback'] = bool(data_quality.get('is_fallback', False))
        analysis['fallback'] = bool(data_quality.get('is_fallback', False))
        
        # Ensure indicators structure exists
        if 'indicators' not in analysis:
            analysis['indicators'] = {
                'ma': {'signal': 0.0, 'weight': 0.3, 'details': 'Analysis failed'},
                'rsi': {'signal': 0.0, 'weight': 0.15, 'details': 'Analysis failed'},
                'bb': {'signal': 0.0, 'weight': 0.1, 'details': 'Analysis failed'},
                'macd': {'signal': 0.0, 'weight': 0.25, 'details': 'Analysis failed'},
                'vwap': {'signal': 0.0, 'weight': 0.2, 'details': 'Analysis failed'}
            }
        
        return analysis

    def _get_unavailable_analysis(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        data_quality: Dict[str, Any],
    ) -> Dict[str, Any]:
        current_price = market_data.get('current_price')
        return {
            'scenario': 'DATA_UNAVAILABLE',
            'weighted_score': 0.0,
            'confidence': 0.0,
            'indicators': {
                'ma': {'signal': 0.0, 'weight': 0.0, 'details': 'Moving averages unavailable'},
                'rsi': {'signal': 0.0, 'weight': 0.0, 'details': 'RSI unavailable'},
                'bb': {'signal': 0.0, 'weight': 0.0, 'details': 'Bollinger Bands unavailable'},
                'macd': {'signal': 0.0, 'weight': 0.0, 'details': 'MACD unavailable'},
                'vwap': {'signal': 0.0, 'weight': 0.0, 'details': 'VWAP unavailable'},
            },
            'support_resistance': {
                'support': [],
                'resistance': [],
            },
            'volatility': {
                'current': None,
                'percentile': None,
                'trend': 'stable',
            },
            'volume_analysis': {
                'relative_volume': None,
                'volume_trend': 'unavailable',
                'volume_score': 0.0,
            },
            'key_insights': ['Technical analysis unavailable because historical candle data is missing'],
            'options_strategy_suggestion': 'Do not place a trade from technicals until price history is available',
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'agent': self.name,
            'market_data_snapshot': market_data,
            'current_price': current_price,
            'data_quality': data_quality,
            'source': data_quality.get('source', market_data.get('source', 'unknown')),
            'is_fallback': True,
            'fallback': True,
            'error': 'Technical data unavailable',
        }
    
    def _get_fallback_analysis(self, symbol: str) -> Dict[str, Any]:
        """Provide fallback analysis when main analysis fails"""
        
        return {
            'scenario': 'range_bound',
            'weighted_score': 0.0,
            'confidence': 0.0,
            'indicators': {
                'ma': {'signal': 0.0, 'weight': 0.15, 'details': 'Analysis unavailable'},
                'rsi': {'signal': 0.0, 'weight': 0.25, 'details': 'Analysis unavailable'},
                'bb': {'signal': 0.0, 'weight': 0.3, 'details': 'Analysis unavailable'},
                'macd': {'signal': 0.0, 'weight': 0.15, 'details': 'Analysis unavailable'},
                'vwap': {'signal': 0.0, 'weight': 0.15, 'details': 'Analysis unavailable'}
            },
            'support_resistance': {
                'support': [],
                'resistance': []
            },
            'volatility': {
                'current': None,
                'percentile': None,
                'trend': 'stable'
            },
            'volume_analysis': {
                'relative_volume': None,
                'volume_trend': 'unavailable',
                'volume_score': 0.0
            },
            'key_insights': ['Technical analysis temporarily unavailable'],
            'options_strategy_suggestion': 'Wait for better signal',
            'error': 'Fallback analysis due to system error',
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'agent': self.name,
            'data_quality': {
                'source_status': 'unavailable',
                'source': 'technical_agent',
                'confidence_cap': 0.0,
                'is_fallback': True,
                'warnings': ['Technical analysis failed'],
            },
            'source': 'technical_agent',
            'is_fallback': True,
            'fallback': True,
        }
