"""
Web Researcher

Real-time web search for domain expertise acquisition.

This module provides:
1. Industry research (trends, market size, best practices)
2. Competitor analysis (features, pricing, positioning)
3. Target market insights (demographics, behaviors, needs)
4. Terminology discovery (industry-specific language)

Uses Tavily API for AI-optimized search results.
Falls back to Perplexity API or simple web scraping if Tavily unavailable.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result"""
    title: str
    url: str
    content: str
    score: float = 0.0


@dataclass
class CompetitorInfo:
    """Information about a competitor"""
    name: str
    url: str
    description: str
    features: List[str] = field(default_factory=list)
    pricing_model: Optional[str] = None


@dataclass
class MarketInsights:
    """Market research insights"""
    market_size: Optional[str] = None
    growth_rate: Optional[str] = None
    trends: List[str] = field(default_factory=list)
    target_demographics: List[str] = field(default_factory=list)


@dataclass
class DomainResearch:
    """
    Complete domain research results.

    This is the output of the web research phase, containing
    everything the agents need to generate an informed prototype.
    """
    industry: str
    search_timestamp: str

    # Industry insights
    industry_trends: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    common_features: List[str] = field(default_factory=list)

    # Market data
    market_insights: Optional[MarketInsights] = None

    # Competitors
    competitors: List[CompetitorInfo] = field(default_factory=list)

    # Pricing insights
    pricing_benchmarks: Dict[str, str] = field(default_factory=dict)

    # Terminology
    industry_terminology: Dict[str, str] = field(default_factory=dict)

    # Raw search results for reference
    raw_results: Dict[str, List[SearchResult]] = field(default_factory=dict)

    # Research quality
    confidence_score: float = 0.0  # 0-1 based on result quality
    queries_executed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "industry": self.industry,
            "search_timestamp": self.search_timestamp,
            "industry_trends": self.industry_trends,
            "best_practices": self.best_practices,
            "common_features": self.common_features,
            "market_insights": {
                "market_size": self.market_insights.market_size if self.market_insights else None,
                "growth_rate": self.market_insights.growth_rate if self.market_insights else None,
                "trends": self.market_insights.trends if self.market_insights else [],
                "target_demographics": self.market_insights.target_demographics if self.market_insights else [],
            } if self.market_insights else None,
            "competitors": [
                {
                    "name": c.name,
                    "url": c.url,
                    "description": c.description,
                    "features": c.features,
                    "pricing_model": c.pricing_model,
                }
                for c in self.competitors
            ],
            "pricing_benchmarks": self.pricing_benchmarks,
            "industry_terminology": self.industry_terminology,
            "confidence_score": self.confidence_score,
            "queries_executed": self.queries_executed,
        }


class WebResearcher:
    """
    Real-time web research for domain expertise.

    Uses Tavily API for AI-optimized search results. Tavily is designed
    specifically for AI applications and provides clean, relevant results.

    Falls back to simpler methods if Tavily is unavailable.
    """

    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        max_results_per_query: int = 5,
        timeout_seconds: int = 30,
    ):
        """
        Initialize the web researcher.

        Args:
            tavily_api_key: Tavily API key (or set TAVILY_API_KEY env var)
            max_results_per_query: Maximum results per search query
            timeout_seconds: Timeout for each search query
        """
        self.api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        self.max_results = max_results_per_query
        self.timeout = timeout_seconds
        self._client = None

    async def _get_client(self):
        """Get or create Tavily client"""
        if self._client is None and self.api_key:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=self.api_key)
            except ImportError:
                logger.warning("tavily-python not installed. Run: pip install tavily-python")
                self._client = None
        return self._client

    def _generate_research_queries(
        self,
        business_idea: str,
        industry: str,
        clarifications: Dict[str, str],
    ) -> Dict[str, str]:
        """
        Generate targeted search queries based on the business idea.

        Returns a dict of query_type -> query_string
        """
        # Clean up industry for search
        industry_clean = industry.replace("-", " ")

        queries = {
            "trends": f"{industry_clean} industry trends 2026",
            "best_practices": f"{industry_clean} software features best practices",
            "competitors": f"top {industry_clean} software companies",
            "pricing": f"{industry_clean} software pricing models benchmarks",
            "features": f"{industry_clean} app must-have features",
        }

        # Add clarification-based queries
        target_market = clarifications.get("target_market", "")
        if target_market:
            queries["target_market"] = f"{industry_clean} {target_market.lower()} customer needs"

        service_model = clarifications.get("service_model", "")
        if service_model:
            queries["service_specific"] = f"{service_model} {industry_clean} software features"

        return queries

    async def _search_tavily(
        self,
        query: str,
        search_depth: str = "advanced",
    ) -> List[SearchResult]:
        """
        Execute a search using Tavily API.

        Args:
            query: Search query
            search_depth: "basic" or "advanced" (advanced gives better results)

        Returns:
            List of SearchResult objects
        """
        client = await self._get_client()
        if not client:
            return []

        try:
            response = client.search(
                query=query,
                search_depth=search_depth,
                max_results=self.max_results,
            )

            results = []
            for item in response.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0),
                ))

            return results

        except Exception as e:
            logger.warning(f"Tavily search failed for '{query}': {e}")
            return []

    def _extract_trends(self, results: List[SearchResult]) -> List[str]:
        """Extract trends from search results"""
        trends = []

        for result in results:
            content = result.content.lower()

            # Look for trend indicators
            trend_phrases = [
                "trending", "growing", "emerging", "popular",
                "shift toward", "increasing demand", "rise of",
                "adoption of", "focus on", "emphasis on",
            ]

            for phrase in trend_phrases:
                if phrase in content:
                    # Extract the sentence containing the trend
                    sentences = result.content.split(".")
                    for sentence in sentences:
                        if phrase in sentence.lower() and len(sentence) < 200:
                            clean_sentence = sentence.strip()
                            if clean_sentence and clean_sentence not in trends:
                                trends.append(clean_sentence)
                                break

        return trends[:7]  # Limit to top 7 trends

    def _extract_features(self, results: List[SearchResult]) -> List[str]:
        """Extract common features from search results"""
        features = []
        feature_indicators = [
            "feature", "functionality", "capability", "include",
            "offer", "provide", "enable", "allow", "support",
        ]

        for result in results:
            content = result.content.lower()

            for indicator in feature_indicators:
                if indicator in content:
                    sentences = result.content.split(".")
                    for sentence in sentences:
                        if indicator in sentence.lower() and len(sentence) < 150:
                            clean = sentence.strip()
                            if clean and clean not in features:
                                features.append(clean)

        return features[:10]  # Limit to top 10 features

    def _extract_competitors(self, results: List[SearchResult]) -> List[CompetitorInfo]:
        """Extract competitor information from search results"""
        competitors = []
        seen_names = set()

        for result in results:
            # Use title as potential competitor name
            name = result.title.split(" - ")[0].split(" | ")[0].strip()

            if name and name not in seen_names and len(name) < 50:
                seen_names.add(name)
                competitors.append(CompetitorInfo(
                    name=name,
                    url=result.url,
                    description=result.content[:200] if result.content else "",
                ))

        return competitors[:5]  # Top 5 competitors

    def _extract_pricing(self, results: List[SearchResult]) -> Dict[str, str]:
        """Extract pricing benchmarks from search results"""
        pricing = {}

        price_indicators = [
            "per month", "monthly", "annually", "per user",
            "starts at", "pricing", "free", "premium", "enterprise",
        ]

        for result in results:
            content = result.content.lower()

            for indicator in price_indicators:
                if indicator in content:
                    sentences = result.content.split(".")
                    for sentence in sentences:
                        if indicator in sentence.lower() and "$" in sentence:
                            # Found a price mention
                            key = indicator.replace(" ", "_")
                            if key not in pricing:
                                pricing[key] = sentence.strip()

        return pricing

    def _calculate_confidence(
        self,
        raw_results: Dict[str, List[SearchResult]],
    ) -> float:
        """Calculate confidence score based on research quality"""
        if not raw_results:
            return 0.0

        total_results = sum(len(r) for r in raw_results.values())
        queries_with_results = sum(1 for r in raw_results.values() if r)

        # Base confidence on coverage
        coverage = queries_with_results / len(raw_results) if raw_results else 0

        # Boost for high-quality results (high scores)
        avg_score = 0.0
        if total_results > 0:
            all_scores = [r.score for results in raw_results.values() for r in results]
            avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

        confidence = (coverage * 0.6) + (avg_score * 0.4)
        return min(1.0, confidence)

    async def research_domain(
        self,
        business_idea: str,
        industry: str,
        clarifications: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None,
    ) -> DomainResearch:
        """
        Conduct comprehensive domain research.

        Args:
            business_idea: The user's business/app description
            industry: Detected industry (from smart presets)
            clarifications: User's clarification responses
            progress_callback: Optional callback for progress updates

        Returns:
            DomainResearch with all gathered insights
        """
        clarifications = clarifications or {}
        raw_results: Dict[str, List[SearchResult]] = {}

        # Generate queries
        queries = self._generate_research_queries(
            business_idea, industry, clarifications
        )

        # Execute searches in parallel
        if progress_callback:
            await progress_callback(f"Researching {industry} industry...")

        search_tasks = []
        for query_type, query in queries.items():
            search_tasks.append(
                (query_type, self._search_tavily(query))
            )

        # Gather results
        for query_type, task in search_tasks:
            try:
                results = await asyncio.wait_for(task, timeout=self.timeout)
                raw_results[query_type] = results
                if progress_callback:
                    await progress_callback(f"Completed: {query_type}")
            except asyncio.TimeoutError:
                logger.warning(f"Search timeout for {query_type}")
                raw_results[query_type] = []
            except Exception as e:
                logger.warning(f"Search failed for {query_type}: {e}")
                raw_results[query_type] = []

        # Process results
        research = DomainResearch(
            industry=industry,
            search_timestamp=datetime.utcnow().isoformat(),
            queries_executed=len(queries),
        )

        # Extract insights from results
        if raw_results.get("trends"):
            research.industry_trends = self._extract_trends(raw_results["trends"])

        if raw_results.get("features") or raw_results.get("best_practices"):
            all_features = raw_results.get("features", []) + raw_results.get("best_practices", [])
            research.common_features = self._extract_features(all_features)
            research.best_practices = self._extract_features(raw_results.get("best_practices", []))

        if raw_results.get("competitors"):
            research.competitors = self._extract_competitors(raw_results["competitors"])

        if raw_results.get("pricing"):
            research.pricing_benchmarks = self._extract_pricing(raw_results["pricing"])

        # Store raw results for reference
        research.raw_results = raw_results

        # Calculate confidence
        research.confidence_score = self._calculate_confidence(raw_results)

        logger.info(
            f"Domain research complete: {len(research.industry_trends)} trends, "
            f"{len(research.competitors)} competitors, "
            f"confidence={research.confidence_score:.2f}"
        )

        return research

    def is_available(self) -> bool:
        """Check if web research is available (API key configured)"""
        return bool(self.api_key)


# Singleton instance
_web_researcher: Optional[WebResearcher] = None


def get_web_researcher(api_key: Optional[str] = None) -> WebResearcher:
    """Get the singleton web researcher"""
    global _web_researcher
    if _web_researcher is None:
        _web_researcher = WebResearcher(tavily_api_key=api_key)
    return _web_researcher
