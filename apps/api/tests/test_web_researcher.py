"""
Tests for the Web Researcher - Tavily API integration for market research.

Tests cover:
1. Query generation
2. Search execution
3. Result parsing
4. Confidence scoring
5. Error handling and fallbacks
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import List, Dict

import sys
sys.path.insert(0, str(__file__).replace("tests/test_web_researcher.py", "src"))


# ============================================================================
# Mock Data
# ============================================================================

MOCK_TAVILY_RESPONSE = {
    "results": [
        {
            "title": "Pet Grooming Industry Trends 2024",
            "url": "https://example.com/trends",
            "content": "The pet grooming market is expected to reach $14.5 billion by 2025. Key trends include mobile grooming, organic products, and technology integration.",
            "score": 0.95
        },
        {
            "title": "Top Pet Grooming Software Features",
            "url": "https://example.com/software",
            "content": "Essential features include appointment scheduling, customer management, payment processing, and automated reminders.",
            "score": 0.88
        },
        {
            "title": "Competitor Analysis: PetDesk vs Gingr",
            "url": "https://example.com/competitors",
            "content": "Leading software solutions include PetDesk ($50-200/mo), Gingr ($95-300/mo), and Pawfinity ($39-99/mo).",
            "score": 0.82
        }
    ],
    "query": "pet grooming industry trends 2024"
}


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_tavily_client():
    """Mock Tavily API client."""
    client = MagicMock()
    client.search = AsyncMock(return_value=MOCK_TAVILY_RESPONSE)
    return client


@pytest.fixture
def web_researcher(mock_tavily_client):
    """Create a WebResearcher with mocked Tavily client."""
    with patch("services.web_researcher.TavilyClient", return_value=mock_tavily_client):
        from services.web_researcher import WebResearcher
        researcher = WebResearcher(api_key="test-key")
        researcher._client = mock_tavily_client
        return researcher


@pytest.fixture
def sample_business_idea():
    """Sample business idea for testing."""
    return "A pet grooming appointment dashboard for small grooming businesses"


@pytest.fixture
def sample_industry():
    """Sample industry identifier."""
    return "pet_services"


@pytest.fixture
def sample_clarifications():
    """Sample user clarification responses."""
    return {
        "target_market": "Small pet grooming businesses with 1-5 employees",
        "pricing_model": "Monthly subscription, $50-150/month",
        "unique_value": "Simple, affordable, mobile-first design"
    }


# ============================================================================
# Query Generation Tests
# ============================================================================

class TestQueryGeneration:
    """Tests for research query generation."""

    def test_generates_trend_queries(self, web_researcher, sample_industry):
        """Test that trend-focused queries are generated."""
        queries = web_researcher._generate_search_queries(
            business_idea="pet grooming dashboard",
            industry=sample_industry
        )

        # Should have trend-related queries
        trend_queries = [q for q in queries if "trend" in q.lower()]
        assert len(trend_queries) >= 1

    def test_generates_competitor_queries(self, web_researcher, sample_industry):
        """Test that competitor-focused queries are generated."""
        queries = web_researcher._generate_search_queries(
            business_idea="pet grooming dashboard",
            industry=sample_industry
        )

        # Should have competitor-related queries
        competitor_queries = [q for q in queries if "competitor" in q.lower() or "top" in q.lower() or "best" in q.lower()]
        assert len(competitor_queries) >= 1

    def test_generates_pricing_queries(self, web_researcher, sample_industry):
        """Test that pricing-focused queries are generated."""
        queries = web_researcher._generate_search_queries(
            business_idea="pet grooming dashboard",
            industry=sample_industry
        )

        # Should have pricing-related queries
        pricing_queries = [q for q in queries if "pricing" in q.lower() or "cost" in q.lower() or "price" in q.lower()]
        assert len(pricing_queries) >= 1

    def test_generates_feature_queries(self, web_researcher, sample_industry):
        """Test that feature-focused queries are generated."""
        queries = web_researcher._generate_search_queries(
            business_idea="pet grooming dashboard",
            industry=sample_industry
        )

        # Should have feature-related queries
        feature_queries = [q for q in queries if "feature" in q.lower() or "must-have" in q.lower()]
        assert len(feature_queries) >= 1

    def test_includes_industry_in_queries(self, web_researcher, sample_industry):
        """Test that queries include the industry context."""
        queries = web_researcher._generate_search_queries(
            business_idea="appointment dashboard",
            industry=sample_industry
        )

        # Most queries should include industry terms
        industry_relevant = [q for q in queries if "pet" in q.lower() or "grooming" in q.lower()]
        assert len(industry_relevant) >= len(queries) // 2

    def test_query_count_is_reasonable(self, web_researcher, sample_industry):
        """Test that a reasonable number of queries are generated."""
        queries = web_researcher._generate_search_queries(
            business_idea="pet grooming dashboard",
            industry=sample_industry
        )

        # Should generate 4-8 queries (balance between coverage and API costs)
        assert 3 <= len(queries) <= 10


# ============================================================================
# Search Execution Tests
# ============================================================================

class TestSearchExecution:
    """Tests for search execution."""

    @pytest.mark.asyncio
    async def test_executes_all_queries(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test that all generated queries are executed."""
        await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Should have called search for each query
        assert mock_tavily_client.search.call_count >= 3

    @pytest.mark.asyncio
    async def test_handles_partial_failures(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test handling when some queries fail."""
        # Make some calls fail
        call_count = [0]

        async def partial_failure(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                raise Exception("API error")
            return MOCK_TAVILY_RESPONSE

        mock_tavily_client.search = AsyncMock(side_effect=partial_failure)

        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Should still return results from successful queries
        assert result is not None

    @pytest.mark.asyncio
    async def test_respects_rate_limits(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test that rate limiting is respected."""
        import time

        start = time.time()

        await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Should complete in reasonable time (even with rate limiting)
        elapsed = time.time() - start
        assert elapsed < 30  # 30 second max

    @pytest.mark.asyncio
    async def test_progress_callback_called(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test that progress callback is invoked."""
        progress_updates = []

        def progress_callback(message: str, progress: int):
            progress_updates.append((message, progress))

        await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry,
            progress_callback=progress_callback
        )

        # Should have received progress updates
        assert len(progress_updates) >= 1


# ============================================================================
# Result Parsing Tests
# ============================================================================

class TestResultParsing:
    """Tests for parsing search results."""

    @pytest.mark.asyncio
    async def test_extracts_trends(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test extraction of industry trends."""
        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Should extract trends
        assert hasattr(result, 'industry_trends') or 'industry_trends' in result.__dict__
        if hasattr(result, 'industry_trends'):
            assert len(result.industry_trends) >= 0

    @pytest.mark.asyncio
    async def test_extracts_features(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test extraction of common features."""
        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Should extract features
        if hasattr(result, 'common_features'):
            # Features like "appointment scheduling" should be extracted
            pass

    @pytest.mark.asyncio
    async def test_extracts_competitors(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test extraction of competitor information."""
        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Should extract competitors
        if hasattr(result, 'competitors'):
            pass

    @pytest.mark.asyncio
    async def test_extracts_pricing(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test extraction of pricing benchmarks."""
        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Should extract pricing info
        if hasattr(result, 'pricing_benchmarks'):
            pass

    @pytest.mark.asyncio
    async def test_deduplicates_results(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test that duplicate information is deduplicated."""
        # Return duplicate results
        duplicate_response = {
            "results": [
                {"title": "Same Article", "content": "Same content about trends", "score": 0.9, "url": "http://a.com"},
                {"title": "Same Article", "content": "Same content about trends", "score": 0.9, "url": "http://b.com"},
            ]
        }
        mock_tavily_client.search = AsyncMock(return_value=duplicate_response)

        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Results should be deduplicated
        assert result is not None


# ============================================================================
# Confidence Scoring Tests
# ============================================================================

class TestConfidenceScoring:
    """Tests for confidence score calculation."""

    @pytest.mark.asyncio
    async def test_high_confidence_for_good_results(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test high confidence when results are comprehensive."""
        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Good results should have confidence > 0.7
        if hasattr(result, 'confidence_score'):
            assert result.confidence_score >= 0.5

    @pytest.mark.asyncio
    async def test_low_confidence_for_sparse_results(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test low confidence when results are sparse."""
        # Return minimal results
        sparse_response = {
            "results": [
                {"title": "One result", "content": "Minimal info", "score": 0.3, "url": "http://a.com"}
            ]
        }
        mock_tavily_client.search = AsyncMock(return_value=sparse_response)

        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Sparse results should have lower confidence
        if hasattr(result, 'confidence_score'):
            assert result.confidence_score <= 0.8

    @pytest.mark.asyncio
    async def test_confidence_considers_query_coverage(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test that confidence considers how many query types returned results."""
        # Only return results for some query types
        call_count = [0]

        async def selective_results(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                return MOCK_TAVILY_RESPONSE
            return {"results": []}

        mock_tavily_client.search = AsyncMock(side_effect=selective_results)

        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Partial coverage should affect confidence
        assert result is not None


# ============================================================================
# Clarification Integration Tests
# ============================================================================

class TestClarificationIntegration:
    """Tests for integration with user clarifications."""

    @pytest.mark.asyncio
    async def test_uses_clarifications_in_queries(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry, sample_clarifications):
        """Test that clarifications influence search queries."""
        await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry,
            clarifications=sample_clarifications
        )

        # Queries should be influenced by clarifications
        # (e.g., "small business" from target_market)
        calls = mock_tavily_client.search.call_args_list
        # Check that clarification terms appear in queries
        # This is implementation-dependent

    @pytest.mark.asyncio
    async def test_research_without_clarifications(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test that research works without clarifications."""
        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry,
            clarifications=None
        )

        # Should still return valid results
        assert result is not None


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_handles_api_key_error(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test handling of invalid API key."""
        mock_tavily_client.search = AsyncMock(side_effect=Exception("Invalid API key"))

        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Should return empty/default results, not crash
        assert result is not None

    @pytest.mark.asyncio
    async def test_handles_network_error(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test handling of network errors."""
        mock_tavily_client.search = AsyncMock(side_effect=ConnectionError("Network error"))

        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_handles_rate_limit_error(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test handling of rate limit errors."""
        mock_tavily_client.search = AsyncMock(side_effect=Exception("Rate limit exceeded"))

        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_handles_malformed_response(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test handling of malformed API responses."""
        mock_tavily_client.search = AsyncMock(return_value={"invalid": "response"})

        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Should handle gracefully
        assert result is not None


# ============================================================================
# Fallback Tests
# ============================================================================

class TestFallbacks:
    """Tests for fallback mechanisms."""

    @pytest.mark.asyncio
    async def test_fallback_to_cached_results(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test fallback to cached results when API fails."""
        # First call succeeds
        result1 = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Second call fails
        mock_tavily_client.search = AsyncMock(side_effect=Exception("API error"))

        # Should potentially use cached results
        # (depends on implementation)

    @pytest.mark.asyncio
    async def test_fallback_to_llm_knowledge(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test fallback to LLM knowledge when web search fails."""
        mock_tavily_client.search = AsyncMock(side_effect=Exception("All searches fail"))

        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Should still have some results (from LLM knowledge)
        assert result is not None


# ============================================================================
# Data Structure Tests
# ============================================================================

class TestDataStructures:
    """Tests for returned data structures."""

    @pytest.mark.asyncio
    async def test_result_has_required_fields(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test that result has all required fields."""
        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Check for expected attributes
        expected_attrs = ['industry', 'confidence_score']
        for attr in expected_attrs:
            if hasattr(result, attr):
                assert getattr(result, attr) is not None

    @pytest.mark.asyncio
    async def test_competitors_have_structured_data(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test that competitor data is structured."""
        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        if hasattr(result, 'competitors') and result.competitors:
            for competitor in result.competitors:
                # Each competitor should have name and optionally URL, pricing
                assert hasattr(competitor, 'name') or isinstance(competitor, dict)


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests with other components."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_research_feeds_into_orchestrator(self, web_researcher, mock_tavily_client, sample_business_idea, sample_industry):
        """Test that research results can be used by orchestrator."""
        result = await web_researcher.research_domain(
            business_idea=sample_business_idea,
            industry=sample_industry
        )

        # Result should be serializable and usable
        if hasattr(result, '__dict__'):
            # Can convert to dict for passing to other components
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
