import pytest

from src.api.intelligent_orchestrator import IntelligentOrchestrator


def test_empty_query_scores_default_to_core_analysis_agents():
    orchestrator = IntelligentOrchestrator.__new__(IntelligentOrchestrator)

    agents = orchestrator._determine_agents_to_trigger({})

    assert agents == ["technical", "sentiment", "flow", "history"]


@pytest.mark.asyncio
async def test_empty_query_scores_generate_comprehensive_response():
    orchestrator = IntelligentOrchestrator.__new__(IntelligentOrchestrator)

    response = await orchestrator._generate_intelligent_response(
        query="trading signals for AAPL",
        symbol="AAPL",
        query_scores={},
        analysis_result={"market_data": {"quote": {"price": 123.45}}},
    )

    assert response["query_type"] == "comprehensive_analysis"
    assert response["symbol"] == "AAPL"
    assert response["analysis_complete"] is True
    assert "frontend_data" in response
    assert "ai_response" in response
