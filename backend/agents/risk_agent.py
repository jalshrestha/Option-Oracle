"""
Risk Management Agent
OpenAI Agents SDK v0.3.0 Implementation
"""
from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent
from config.logging import get_agents_logger

logger = get_agents_logger()


class RiskManagementAgent(BaseAgent):
    """AI agent specializing in risk management and strike selection"""
    
    def __init__(self, client):
        super().__init__(client, "Risk Management")
        
    def _get_system_instructions(self) -> str:
        return """
You are a risk management specialist for the Neural Options Oracle++ system.

Your responsibilities:
1. Assess portfolio and position-level risk
2. Recommend appropriate option strikes based on user risk profile
3. Calculate position sizing and risk metrics
4. Provide risk-adjusted recommendations

Risk Profiles:
- CONSERVATIVE: Delta 0.15-0.35, Max loss 2% of account
- MODERATE: Delta 0.25-0.55, Max loss 5% of account  
- AGGRESSIVE: Delta 0.45-0.85, Max loss 10% of account

OUTPUT FORMAT (JSON):
{
    "risk_assessment": {
        "overall_risk": "low|medium|high",
        "risk_score": float_between_0_and_1,
        "key_risks": ["string1", "string2"]
    },
    "position_sizing": {
        "recommended_contracts": int,
        "max_loss_dollar": float,
        "max_loss_percent": float,
        "risk_reward_ratio": float
    },
    "strike_recommendations": [
        {
            "strike": float,
            "option_type": "call|put",
            "expiration": "YYYY-MM-DD",
            "delta": float,
            "probability_profit": float,
            "max_loss": float,
            "max_gain": float,
            "risk_level": "low|medium|high"
        }
    ],
    "risk_mitigation": {
        "stop_loss": float,
        "take_profit": float,
        "time_decay_warning": boolean,
        "volatility_risk": "low|medium|high"
    },
    "portfolio_impact": {
        "correlation_risk": float,
        "concentration_risk": float,
        "diversification_score": float
    }
}
"""
    
    def _get_response_schema(self) -> Dict[str, Any]:
        """Get JSON Schema for risk management response"""
        return {
            "type": "object",
            "properties": {
                "risk_assessment": {
                    "type": "object",
                    "properties": {
                        "overall_risk": {"type": "string", "enum": ["low", "medium", "high"]},
                        "risk_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "key_risks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 5
                        }
                    },
                    "required": ["overall_risk", "risk_score", "key_risks"],
                    "additionalProperties": False
                },
                "position_sizing": {
                    "type": "object",
                    "properties": {
                        "recommended_contracts": {"type": "integer", "minimum": 1},
                        "max_loss_dollar": {"type": "number", "minimum": 0.0},
                        "max_loss_percent": {"type": "number", "minimum": 0.0, "maximum": 100.0},
                        "risk_reward_ratio": {"type": "number", "minimum": 0.0}
                    },
                    "required": ["recommended_contracts", "max_loss_dollar", "max_loss_percent", "risk_reward_ratio"],
                    "additionalProperties": False
                },
                "strike_recommendations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "strike": {"type": "number", "minimum": 0.0},
                            "option_type": {"type": "string", "enum": ["call", "put"]},
                            "expiration": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                            "delta": {"type": "number", "minimum": -1.0, "maximum": 1.0},
                            "probability_profit": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                            "max_loss": {"type": "number", "minimum": 0.0},
                            "max_gain": {"type": "number", "minimum": 0.0},
                            "risk_level": {"type": "string", "enum": ["low", "medium", "high"]}
                        },
                        "required": ["strike", "option_type", "expiration", "delta", "probability_profit", "max_loss", "max_gain", "risk_level"],
                        "additionalProperties": False
                    },
                    "minItems": 1,
                    "maxItems": 5
                },
                "risk_mitigation": {
                    "type": "object",
                    "properties": {
                        "stop_loss": {"type": "number", "minimum": 0.0},
                        "take_profit": {"type": "number", "minimum": 0.0},
                        "time_decay_warning": {"type": "boolean"},
                        "volatility_risk": {"type": "string", "enum": ["low", "medium", "high"]}
                    },
                    "required": ["stop_loss", "take_profit", "time_decay_warning", "volatility_risk"],
                    "additionalProperties": False
                },
                "portfolio_impact": {
                    "type": "object",
                    "properties": {
                        "correlation_risk": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "concentration_risk": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "diversification_score": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                    },
                    "required": ["correlation_risk", "concentration_risk", "diversification_score"],
                    "additionalProperties": False
                }
            },
            "required": ["risk_assessment", "position_sizing", "strike_recommendations", "risk_mitigation", "portfolio_impact"],
            "additionalProperties": False
        }
    
    async def recommend_strikes(
        self, 
        signal: Dict[str, Any], 
        user_risk_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Recommend option strikes from real provider option-chain data only."""
        
        try:
            logger.info(f"Generating strike recommendations for {signal.get('direction', 'UNKNOWN')}")
            if signal.get('direction') == 'HOLD' or float(signal.get('confidence') or 0) < 0.35:
                logger.info("Skipping strike recommendations for neutral or low-confidence signal")
                return []

            try:
                current_price = float(signal.get('current_price') or 0)
            except (TypeError, ValueError):
                current_price = 0.0
            if current_price <= 0:
                logger.warning("Skipping strike recommendations because current price is unavailable")
                return []

            from src.data.market_data_manager import market_data_manager

            symbol = str(signal.get('symbol') or '').upper()
            market_data = await market_data_manager.get_comprehensive_data(symbol)
            options_data = market_data.get('options', {})
            recommendations = self._select_real_option_candidates(
                options_data=options_data,
                signal=signal,
                user_risk_profile=user_risk_profile,
            )
            if not recommendations:
                logger.warning("No real option contracts matched risk filters")
                return []

            logger.info(f"Generated {len(recommendations)} strike recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Strike recommendation failed: {e}")
            return []
    
    async def analyze(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """General risk analysis (not used in main flow but required by base class)"""
        
        return {
            'risk_score': 0.5,
            'confidence': 0.7,
            'risk_level': 'medium',
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'agent': self.name
        }
    
    def _select_real_option_candidates(
        self,
        options_data: Dict[str, Any],
        signal: Dict[str, Any],
        user_risk_profile: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Pick liquid contracts from the real option chain. No synthetic strikes."""
        chain = options_data.get('options_chain') or []
        quality = options_data.get('data_quality') or {}
        if options_data.get('error') or quality.get('source_status') == 'unavailable' or not chain:
            return []

        try:
            current_price = float(options_data.get('current_price') or signal.get('current_price') or 0)
        except (TypeError, ValueError):
            current_price = 0.0
        if current_price <= 0:
            return []

        direction = signal.get('direction', 'HOLD')
        if direction in {'BUY', 'STRONG_BUY'}:
            option_type = 'call'
        elif direction in {'SELL', 'STRONG_SELL'}:
            option_type = 'put'
        else:
            return []

        risk_level = user_risk_profile.get('risk_level') or user_risk_profile.get('risk_tolerance') or 'moderate'
        max_position_percent = float(user_risk_profile.get('max_position_percent') or 5)
        account_size = float(user_risk_profile.get('account_size') or 100000)
        max_contract_cost = account_size * (max_position_percent / 100)
        today = datetime.now().date()

        scored = []
        for contract in chain:
            if contract.get('option_type') != option_type:
                continue

            strike = self._safe_float(contract.get('strike_price'))
            if strike is None or strike <= 0:
                continue

            expiration = str(contract.get('expiration_date') or '')
            try:
                dte = (datetime.strptime(expiration, '%Y-%m-%d').date() - today).days
            except ValueError:
                dte = 999
            if dte < 7 or dte > 75:
                continue

            bid = self._safe_float(contract.get('bid'))
            ask = self._safe_float(contract.get('ask'))
            last_price = self._safe_float(contract.get('last_price'))
            premium = None
            if bid is not None and ask is not None and bid > 0 and ask > 0:
                premium = (bid + ask) / 2
            elif last_price is not None and last_price > 0:
                premium = last_price
            if premium is None or premium <= 0:
                continue

            max_loss = premium * 100
            if max_loss > max_contract_cost:
                continue

            volume = int(contract.get('volume') or 0)
            open_interest = int(contract.get('open_interest') or 0)
            if volume <= 0 and open_interest <= 0:
                continue

            moneyness = strike / current_price - 1
            if option_type == 'put':
                moneyness = 1 - strike / current_price

            target_moneyness = {
                'conservative': 0.03,
                'moderate': 0.015,
                'aggressive': 0.0,
            }.get(str(risk_level).lower(), 0.015)

            liquidity_score = min(volume / 1000, 1.0) + min(open_interest / 5000, 1.0)
            spread = (ask - bid) if bid is not None and ask is not None else None
            spread_penalty = min((spread / premium), 2.0) if spread is not None and premium else 1.0
            score = abs(moneyness - target_moneyness) + abs(dte - 35) / 100 - liquidity_score / 10 + spread_penalty / 10
            scored.append((score, contract, premium, max_loss, dte, volume, open_interest, bid, ask, last_price))

        scored.sort(key=lambda item: item[0])
        recommendations = []
        for _, contract, premium, max_loss, dte, volume, open_interest, bid, ask, last_price in scored[:3]:
            strike = float(contract['strike_price'])
            recommendations.append({
                'strike': strike,
                'option_type': option_type,
                'expiration': contract.get('expiration_date'),
                'days_to_expiration': dte,
                'bid': bid,
                'ask': ask,
                'last_price': last_price,
                'premium': round(premium, 2),
                'contracts': 1,
                'max_loss': round(max_loss, 2),
                'max_gain': None,
                'probability_profit': None,
                'delta': None,
                'risk_level': 'medium' if risk_level == 'moderate' else risk_level,
                'volume': volume,
                'open_interest': open_interest,
                'implied_volatility': contract.get('implied_volatility'),
                'underlying_price': current_price,
                'source': options_data.get('source', 'options_chain'),
                'data_quality': {
                    'source_status': 'real_chain',
                    'source': options_data.get('source', 'options_chain'),
                    'is_fallback': False,
                    'warnings': ['Greeks are unavailable from current options source; contract selected using real price, bid/ask, volume, and open interest'],
                },
            })

        return recommendations

    def _safe_float(self, value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _format_options_chain(self, chain: List[Dict]) -> str:
        """Format real options contracts for logs/debugging."""
        formatted = []
        for opt in chain[:10]:
            strike = opt.get('strike_price', opt.get('strike'))
            option_type = opt.get('option_type', opt.get('type'))
            bid = opt.get('bid')
            ask = opt.get('ask')
            volume = opt.get('volume')
            oi = opt.get('open_interest')
            formatted.append(
                f"{strike} {option_type}: bid={bid}, ask={ask}, volume={volume}, oi={oi}"
            )
        return "\n".join(formatted)

    def _validate_strike_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """Validate real strike recommendation shape without inventing missing fields."""
        validated = []
        for rec in recommendations:
            if not isinstance(rec, dict):
                continue
            strike = self._safe_float(rec.get('strike'))
            premium = self._safe_float(rec.get('premium'))
            if strike is None or premium is None:
                continue
            validated.append(rec)
        return validated[:5]
