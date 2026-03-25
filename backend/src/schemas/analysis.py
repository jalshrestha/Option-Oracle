"""
Schemas for the analysis / signals domain.
"""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecentSignalItem(BaseModel):
    """A compact signal item for the recent-signals-across-all-symbols endpoint."""

    id: str
    symbol: str
    direction: Literal["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"]
    strength: Optional[Literal["strong", "moderate", "weak"]] = None
    confidence_score: float
    market_scenario: str
    created_at: Optional[str] = None


class AnalysisRequest(BaseModel):
    """Request body / path parameter for a stock analysis."""

    model_config = ConfigDict(frozen=True)

    symbol: str = Field(..., description="Stock ticker symbol (e.g. AAPL)")

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        v = v.strip().upper()
        if not v.isalpha():
            raise ValueError(f"Symbol must contain only letters, got: {v!r}")
        if not (1 <= len(v) <= 5):
            raise ValueError(f"Symbol must be 1–5 characters, got: {v!r} ({len(v)} chars)")
        return v


class SignalSchema(BaseModel):
    """The core directional signal output."""

    direction: Literal["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"]
    strength: Literal["strong", "moderate", "weak"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    decision_score: float = Field(..., ge=-1.0, le=1.0)
    strategy_type: str
    market_scenario: str
    reasoning: str


class StrikeRecommendation(BaseModel):
    """A single options strike recommendation."""

    option_type: Literal["call", "put"]
    strike: float
    expiry: str
    delta: Optional[float] = None
    premium: Optional[float] = None
    risk_reward: Optional[float] = None
    rationale: str = ""


class AnalysisResponse(BaseModel):
    """Full analysis result returned to the client."""

    symbol: str
    signal: SignalSchema
    agent_results: Dict[str, Any] = {}
    strike_recommendations: List[StrikeRecommendation] = []
    educational_content: str = ""
    confidence: float = Field(..., ge=0.0, le=1.0)
    market_scenario: str
    agent_weights: Dict[str, float] = {}
    analysis_time_seconds: float = 0.0
    timestamp: str
