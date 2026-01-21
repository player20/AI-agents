"""
Domain Expertise Synthesizer

Combines all sources of domain knowledge into a unified DomainExpertise profile:
1. User clarifications (from interview mode)
2. Web research (from Tavily/web search)
3. Knowledge store (from successful past generations)
4. Smart presets (from keyword extraction)

The result is a rich domain context that agents use for informed generation.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from .clarification_agent import ClarificationAgent, get_clarification_agent
from .web_researcher import WebResearcher, DomainResearch, get_web_researcher
from .knowledge_store import DomainKnowledgeStore, PatternMatch, get_knowledge_store
from .prompts.smart_presets import ExtractedConcepts, get_smart_preset_system

logger = logging.getLogger(__name__)


class DomainExpertise(BaseModel):
    """
    Rich domain context synthesized from all sources.

    This is the primary input for the agent pipeline, containing
    everything the agents need to generate an expert prototype.
    """

    # Identity
    industry: str = Field(description="Primary industry classification")
    app_name: str = Field(default="", description="Detected or user-provided app name")
    tagline: str = Field(default="", description="Generated tagline")

    # From user clarification
    target_market: str = Field(default="", description="Who are the customers?")
    service_model: str = Field(default="", description="What services/products?")
    pricing_approach: str = Field(default="", description="How do they charge?")
    unique_differentiators: List[str] = Field(default_factory=list, description="What makes them different?")
    scale_expectation: str = Field(default="", description="Expected volume/size")

    # From web research
    market_size: str = Field(default="", description="Market size estimate")
    industry_trends: List[str] = Field(default_factory=list, description="Current industry trends")
    competitor_features: List[str] = Field(default_factory=list, description="Features competitors have")
    competitor_names: List[str] = Field(default_factory=list, description="Named competitors")
    pricing_benchmarks: Dict[str, str] = Field(default_factory=dict, description="Pricing data")
    best_practices: List[str] = Field(default_factory=list, description="Industry best practices")

    # From knowledge retrieval
    successful_patterns: List[str] = Field(default_factory=list, description="Patterns from similar successful builds")
    recommended_metrics: List[str] = Field(default_factory=list, description="Metrics that worked well")
    proven_page_structures: List[str] = Field(default_factory=list, description="Page structures that worked")

    # Synthesized domain knowledge
    terminology: Dict[str, str] = Field(default_factory=dict, description="Industry-specific terms")
    key_entities: List[str] = Field(default_factory=list, description="Core entities in the domain")
    suggested_features: List[str] = Field(default_factory=list, description="Features ranked by relevance")
    color_palette: Dict[str, str] = Field(default_factory=dict, description="Suggested brand colors")
    mock_data_hints: Dict[str, Any] = Field(default_factory=dict, description="Hints for generating mock data")

    # Quality metrics
    confidence_score: float = Field(default=0.0, ge=0, le=1, description="Overall confidence in expertise")
    sources_used: List[str] = Field(default_factory=list, description="Which sources contributed")

    def to_agent_context(self) -> str:
        """
        Generate a rich context string for agent prompts.

        This is what gets injected into agent prompts to make them
        domain-aware without relying on hardcoded presets.
        """
        parts = [
            f"## Domain Expertise for {self.industry.replace('-', ' ').title()}",
            "",
        ]

        if self.target_market:
            parts.append(f"**Target Market:** {self.target_market}")

        if self.service_model:
            parts.append(f"**Services/Products:** {self.service_model}")

        if self.pricing_approach:
            parts.append(f"**Pricing Model:** {self.pricing_approach}")

        if self.scale_expectation:
            parts.append(f"**Expected Scale:** {self.scale_expectation}")

        if self.unique_differentiators:
            parts.append(f"**Differentiators:** {', '.join(self.unique_differentiators)}")

        if self.industry_trends:
            parts.append("")
            parts.append("### Industry Trends")
            for trend in self.industry_trends[:5]:
                parts.append(f"- {trend}")

        if self.competitor_features:
            parts.append("")
            parts.append("### Common Features (from competitors)")
            for feature in self.competitor_features[:7]:
                parts.append(f"- {feature}")

        if self.best_practices:
            parts.append("")
            parts.append("### Best Practices")
            for practice in self.best_practices[:5]:
                parts.append(f"- {practice}")

        if self.terminology:
            parts.append("")
            parts.append("### Industry Terminology")
            for generic, specific in self.terminology.items():
                parts.append(f"- {generic} → {specific}")

        if self.recommended_metrics:
            parts.append("")
            parts.append("### Recommended Metrics")
            for metric in self.recommended_metrics[:6]:
                parts.append(f"- {metric}")

        if self.pricing_benchmarks:
            parts.append("")
            parts.append("### Pricing Benchmarks")
            for key, value in list(self.pricing_benchmarks.items())[:4]:
                parts.append(f"- {key}: {value}")

        parts.append("")
        parts.append(f"_Confidence: {self.confidence_score:.0%} | Sources: {', '.join(self.sources_used)}_")

        return "\n".join(parts)


class DomainExpertiseSynthesizer:
    """
    Synthesizes domain expertise from multiple sources.

    Combines:
    1. User clarifications (from ClarificationAgent)
    2. Web research (from WebResearcher)
    3. Knowledge patterns (from KnowledgeStore)
    4. Smart presets (from SmartPresetSystem)

    Into a unified DomainExpertise profile.
    """

    def __init__(
        self,
        enable_web_research: bool = True,
        enable_knowledge_retrieval: bool = True,
    ):
        """
        Initialize the synthesizer.

        Args:
            enable_web_research: Enable web research (requires Tavily API key)
            enable_knowledge_retrieval: Enable knowledge store queries
        """
        self.enable_web_research = enable_web_research
        self.enable_knowledge_retrieval = enable_knowledge_retrieval

        self._clarification_agent = get_clarification_agent()
        self._web_researcher = get_web_researcher()
        self._knowledge_store = get_knowledge_store()
        self._smart_system = get_smart_preset_system()

    async def synthesize(
        self,
        description: str,
        concepts: Optional[ExtractedConcepts] = None,
        user_clarifications: Optional[Dict[str, str]] = None,
        web_research: Optional[DomainResearch] = None,
        progress_callback: Optional[callable] = None,
    ) -> DomainExpertise:
        """
        Synthesize domain expertise from all available sources.

        Args:
            description: User's project description
            concepts: Pre-extracted concepts (optional, will extract if not provided)
            user_clarifications: User's clarification responses (optional)
            web_research: Pre-fetched web research (optional, will fetch if enabled)
            progress_callback: Optional callback for progress updates

        Returns:
            DomainExpertise with synthesized domain knowledge
        """
        sources_used = []

        # Step 1: Get smart preset concepts
        if concepts is None:
            concepts = self._smart_system.get_concepts(description)

        sources_used.append("smart_presets")

        expertise = DomainExpertise(
            industry=concepts.best_industry,
            app_name=concepts.app_name,
            tagline=concepts.tagline,
            key_entities=concepts.entities[:7],
        )

        # Step 2: Add user clarifications
        if user_clarifications:
            self._apply_clarifications(expertise, user_clarifications)
            sources_used.append("user_clarifications")

        # Step 3: Web research (if enabled and available)
        if self.enable_web_research and self._web_researcher.is_available():
            if web_research is None:
                if progress_callback:
                    await progress_callback("Researching industry...")

                web_research = await self._web_researcher.research_domain(
                    business_idea=description,
                    industry=concepts.best_industry,
                    clarifications=user_clarifications or {},
                    progress_callback=progress_callback,
                )

            self._apply_web_research(expertise, web_research)
            sources_used.append("web_research")

        # Step 4: Knowledge retrieval (if enabled)
        if self.enable_knowledge_retrieval:
            if progress_callback:
                await progress_callback("Finding similar successful patterns...")

            patterns = await self._knowledge_store.find_similar_patterns(
                description=description,
                industry=concepts.best_industry,
                top_k=3,
            )

            if patterns:
                self._apply_patterns(expertise, patterns)
                sources_used.append("knowledge_store")

        # Step 5: Get base preset data (always available)
        domain_preset, arch_preset, mock_preset = self._smart_system.get_preset(description)

        self._apply_preset(expertise, domain_preset, arch_preset, mock_preset)

        # Calculate confidence
        expertise.sources_used = sources_used
        expertise.confidence_score = self._calculate_confidence(
            concepts=concepts,
            has_clarifications=bool(user_clarifications),
            has_web_research=bool(web_research and web_research.confidence_score > 0.3),
            has_patterns=bool(patterns) if self.enable_knowledge_retrieval else False,
        )

        logger.info(
            f"Synthesized domain expertise for '{concepts.best_industry}' "
            f"(confidence={expertise.confidence_score:.2f}, sources={sources_used})"
        )

        return expertise

    def _apply_clarifications(
        self,
        expertise: DomainExpertise,
        clarifications: Dict[str, str],
    ) -> None:
        """Apply user clarification responses to expertise"""
        for key, value in clarifications.items():
            if not value:
                continue

            if key == "target_market":
                expertise.target_market = value
            elif key in ("service_model", "pet_services", "restaurant_type",
                        "healthcare_type", "fitness_type", "product_type",
                        "saas_model", "education_type", "content_focus",
                        "real_estate_type", "finance_type"):
                expertise.service_model = value
            elif key in ("pricing_model", "membership_model", "pricing_tiers", "monetization"):
                expertise.pricing_approach = value
            elif key == "scale":
                expertise.scale_expectation = value
            elif key == "unique_value":
                expertise.unique_differentiators.append(value)

    def _apply_web_research(
        self,
        expertise: DomainExpertise,
        research: DomainResearch,
    ) -> None:
        """Apply web research findings to expertise"""
        expertise.industry_trends = research.industry_trends[:7]
        expertise.best_practices = research.best_practices[:5]
        expertise.pricing_benchmarks = research.pricing_benchmarks

        # Extract competitor features
        for competitor in research.competitors[:5]:
            expertise.competitor_names.append(competitor.name)
            expertise.competitor_features.extend(competitor.features)

        # Deduplicate features
        expertise.competitor_features = list(dict.fromkeys(expertise.competitor_features))[:10]

        # Add common features as suggested features
        expertise.suggested_features.extend(research.common_features[:7])

        if research.market_insights:
            expertise.market_size = research.market_insights.market_size or ""

    def _apply_patterns(
        self,
        expertise: DomainExpertise,
        patterns: List[PatternMatch],
    ) -> None:
        """Apply learned patterns to expertise"""
        for match in patterns:
            pattern = match.pattern

            # Add proven metrics
            for metric in pattern.key_metrics:
                if metric not in expertise.recommended_metrics:
                    expertise.recommended_metrics.append(metric)

            # Add proven page structures
            for page in pattern.page_structure:
                if page not in expertise.proven_page_structures:
                    expertise.proven_page_structures.append(page)

            # Add successful patterns description
            expertise.successful_patterns.append(
                f"Pattern from {pattern.industry} (confidence: {match.relevance_score:.0%})"
            )

            # Merge terminology
            for generic, specific in pattern.terminology.items():
                if generic not in expertise.terminology:
                    expertise.terminology[generic] = specific

        # Limit lists
        expertise.recommended_metrics = expertise.recommended_metrics[:8]
        expertise.proven_page_structures = expertise.proven_page_structures[:6]

    def _apply_preset(
        self,
        expertise: DomainExpertise,
        domain_preset: Dict[str, Any],
        arch_preset: Dict[str, Any],
        mock_preset: Dict[str, Any],
    ) -> None:
        """Apply base preset data to expertise"""
        # Merge terminology (don't overwrite if already set)
        preset_terminology = domain_preset.get("terminology", {})
        for generic, specific in preset_terminology.items():
            if generic not in expertise.terminology:
                expertise.terminology[generic] = specific

        # Add suggested sections as features if not already present
        for section in domain_preset.get("suggested_sections", []):
            if section not in expertise.suggested_features:
                expertise.suggested_features.append(section)

        # Add metrics if not already present
        for metric in domain_preset.get("metrics", []):
            if metric not in expertise.recommended_metrics:
                expertise.recommended_metrics.append(metric)

        # Add color palette
        if not expertise.color_palette:
            expertise.color_palette = domain_preset.get("suggested_colors", {})

        # Add mock data hints
        if not expertise.mock_data_hints:
            expertise.mock_data_hints = {
                "sample_items": domain_preset.get("sample_items", []),
                "terminology": expertise.terminology,
            }

        # Limit lists
        expertise.suggested_features = expertise.suggested_features[:12]
        expertise.recommended_metrics = expertise.recommended_metrics[:8]

    def _calculate_confidence(
        self,
        concepts: ExtractedConcepts,
        has_clarifications: bool,
        has_web_research: bool,
        has_patterns: bool,
    ) -> float:
        """Calculate overall confidence score"""
        # Base confidence from concept extraction
        base = concepts.best_score * 0.3

        # Bonus for each source
        if has_clarifications:
            base += 0.2  # User input is highly valuable

        if has_web_research:
            base += 0.25  # Real market data

        if has_patterns:
            base += 0.15  # Learned from success

        # Preset always contributes
        base += 0.1

        return min(1.0, base)


# Singleton instance
_synthesizer: Optional[DomainExpertiseSynthesizer] = None


def get_expertise_synthesizer() -> DomainExpertiseSynthesizer:
    """Get the singleton expertise synthesizer"""
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = DomainExpertiseSynthesizer()
    return _synthesizer
