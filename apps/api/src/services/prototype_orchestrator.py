"""
Prototype Orchestrator

Coordinates the 5-agent creative pipeline to generate domain-specific prototypes:

1. Domain Analyst - Understands the business domain
2. Architect - Plans pages and sections
3. Content Generator - Creates realistic mock data
4. UI Composer - Generates components (Web agent with domain context)
5. Validator - Pre-WebContainer validation checks

The result is a prototype that feels tailored to the client's specific business,
not a generic template with placeholder data.

Features Smart Fallback Cascade for reliability:
- Level 1: Full creative pipeline (domain + architecture + content)
- Level 2: Cached similar successful generation
- Level 3: Template with domain-specific mock data
- Level 4: Clean template with generic data
- Level 5: Minimal working prototype
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .prompts.domain_analyst import (
    DomainAnalysis,
    get_domain_analyst_prompt,
    get_industry_preset,
    INDUSTRY_PRESETS,
)
from .prompts.architect import (
    PrototypeArchitecture,
    get_architect_prompt,
    get_architecture_preset,
)
from .prompts.content_generator import (
    get_content_generator_prompt,
    get_mock_data_preset,
    customize_mock_data,
)
from .prompts.smart_presets import (
    get_smart_preset_system,
    get_smart_preset,
    extract_concepts,
    SmartPresetSystem,
    ExtractedConcepts,
)
from .prompts.preset_quality import (
    evaluate_preset,
    enhance_preset,
    get_enhancer,
    get_feedback_analyzer,
    QualityScore,
    EnhancementResult,
)
from .clarification_agent import (
    ClarificationAgent,
    ClarificationResult,
    ClarificationQuestion,
    get_clarification_agent,
)
from .domain_expertise import (
    DomainExpertise,
    DomainExpertiseSynthesizer,
    get_expertise_synthesizer,
)
from .web_researcher import get_web_researcher, DomainResearch
from .knowledge_store import get_knowledge_store
from .template_loader import get_template_loader, Template
from .template_customizer import BrandProfile, get_template_customizer
from .code_validator import validate_and_fix, ValidationResult
from .report_generator import BusinessReportGenerator, generate_business_report
from ..models.report import (
    BusinessReport,
    ReportType,
    ExecutiveSummary,
    MetricItem,
    BadgeType,
    IssueCard,
    Recommendation,
    RoadmapPhase,
    RoadmapItem,
    KPIRow,
    ROIProjection,
    ROIMetric,
    IndustrySection,
    IndustryInsight,
    DesignSystem,
    FeatureRow,
    Severity,
)

logger = logging.getLogger(__name__)


class FallbackLevel(Enum):
    """
    Fallback levels for the cascade system.

    Higher levels = less customization but more reliability.
    We always try lower levels first and cascade up on failure.
    """
    FULL_CREATIVE = 1      # Complete pipeline: domain + architecture + content
    CACHED_SIMILAR = 2     # Use cached successful generation for similar description
    TEMPLATE_CUSTOMIZED = 3  # Template with domain-specific mock data
    TEMPLATE_CLEAN = 4     # Clean template with generic data
    MINIMAL = 5            # Minimal working prototype


@dataclass
class FallbackInfo:
    """Information about which fallback level was used and why"""
    level: FallbackLevel
    reason: Optional[str] = None
    original_error: Optional[str] = None
    customization_applied: List[str] = field(default_factory=list)

    @property
    def user_message(self) -> str:
        """Human-readable message explaining what happened"""
        messages = {
            FallbackLevel.FULL_CREATIVE: "Fully customized to your business",
            FallbackLevel.CACHED_SIMILAR: "Based on a similar successful project",
            FallbackLevel.TEMPLATE_CUSTOMIZED: "Template customized with your industry data",
            FallbackLevel.TEMPLATE_CLEAN: "Professional template ready for customization",
            FallbackLevel.MINIMAL: "Minimal starter - add your content",
        }
        base_msg = messages.get(self.level, "Prototype generated")

        if self.customization_applied:
            customizations = ", ".join(self.customization_applied[:3])
            return f"{base_msg} ({customizations})"
        return base_msg

    @property
    def is_degraded(self) -> bool:
        """Whether we fell back from the ideal full creative level"""
        return self.level != FallbackLevel.FULL_CREATIVE


@dataclass
class PrototypeEvent:
    """Event emitted during prototype generation"""
    type: str  # "agent_start", "agent_complete", "status", "error", "fallback", "clarification_required", "research_progress"
    agent: Optional[str] = None
    message: str = ""
    progress: int = 0
    data: Optional[Dict[str, Any]] = None
    requires_response: bool = False  # For clarification events that need user input


@dataclass
class PrototypeResult:
    """Result of prototype generation"""
    success: bool
    files: Dict[str, str]
    domain_analysis: Optional[Dict[str, Any]] = None
    architecture: Optional[Dict[str, Any]] = None
    mock_data: Optional[Dict[str, Any]] = None
    validation: Optional[ValidationResult] = None
    error: Optional[str] = None
    duration_ms: int = 0
    fallback_info: Optional[FallbackInfo] = None
    # Business report HTML (new for consultant mode)
    report_html: Optional[str] = None
    report_type: Optional[str] = None  # "transformation_proposal", "ux_audit", "comprehensive"

    @property
    def customization_level(self) -> str:
        """User-friendly customization level description"""
        if self.fallback_info:
            return self.fallback_info.user_message
        return "Fully customized"


class PrototypeOrchestrator:
    """
    Orchestrates the 5-agent creative pipeline for prototype generation.

    Pipeline:
    1. Domain Analyst → Understands the business (smart keyword extraction)
    2. Architect → Plans the structure (concept-driven page building)
    3. Content Generator → Creates mock data (entity-aware data generation)
    4. UI Composer → Generates components (template + customization)
    5. Validator → Checks for issues (pre-WebContainer validation)

    Uses the Smart Preset System for intelligent, learning-based preset generation.
    The more it's used, the smarter it gets at understanding project types.
    """

    def __init__(
        self,
        event_callback: Optional[Callable[[PrototypeEvent], Awaitable[None]]] = None,
        use_smart_presets: bool = True,
        response_callback: Optional[Callable[[List[ClarificationQuestion]], Awaitable[Dict[str, str]]]] = None,
        skip_clarification: bool = False,
    ):
        """
        Initialize the orchestrator.

        Args:
            event_callback: Optional callback for progress events
            use_smart_presets: Use smart preset system (learns from usage)
            response_callback: Optional callback to get user responses to clarification questions
            skip_clarification: Skip the clarification phase (for testing or quick generation)
        """
        self.event_callback = event_callback
        self.response_callback = response_callback
        self.use_smart_presets = use_smart_presets
        self.skip_clarification = skip_clarification
        self._template_loader = get_template_loader()
        self._template_customizer = get_template_customizer()
        self._smart_system = get_smart_preset_system() if use_smart_presets else None
        self._clarification_agent = get_clarification_agent()
        self._expertise_synthesizer = get_expertise_synthesizer()
        self._knowledge_store = get_knowledge_store()

    async def _emit(self, event: PrototypeEvent) -> None:
        """Emit an event if callback is set"""
        if self.event_callback:
            await self.event_callback(event)

    async def _run_clarification_phase(
        self,
        description: str,
        concepts: ExtractedConcepts,
    ) -> Optional[Dict[str, Any]]:
        """
        Run the clarification phase to gather more information from the user.

        This phase:
        1. Checks if clarification is needed based on domain confidence
        2. Generates smart questions targeted to the detected domain
        3. Emits clarification_required event with questions
        4. Waits for user responses via the response_callback
        5. Returns enriched description with user's answers

        Args:
            description: Original user description
            concepts: Extracted concepts from smart preset system

        Returns:
            Dict with 'enriched_description' and 'responses', or None if skipped
        """
        # Check if clarification is needed
        if not self._clarification_agent.needs_clarification(concepts, description):
            logger.info("Clarification not needed - high confidence domain match")
            return None

        # Generate questions
        clarification_result = self._clarification_agent.generate_questions(
            description=description,
            concepts=concepts,
        )

        if not clarification_result.questions:
            logger.info("No clarification questions generated")
            return None

        # Emit clarification_required event
        await self._emit(PrototypeEvent(
            type="clarification_required",
            agent="Clarification Agent",
            message="I need some details to build a better prototype for you",
            progress=0,
            data={
                "questions": [q.to_dict() for q in clarification_result.questions],
                "detected_industry": clarification_result.detected_industry,
                "confidence": clarification_result.confidence_before,
                "missing_info": clarification_result.missing_info,
            },
            requires_response=True,
        ))

        # If we have a response callback, wait for user responses
        if self.response_callback:
            try:
                responses = await self.response_callback(clarification_result.questions)

                if responses:
                    # Enrich the description with user's answers
                    enriched = self._clarification_agent.enrich_description(
                        description, responses
                    )

                    # Emit completion event
                    await self._emit(PrototypeEvent(
                        type="agent_complete",
                        agent="Clarification Agent",
                        message=f"Got {len(responses)} answers - proceeding with enriched context",
                        progress=5,
                        data={"response_count": len(responses)},
                    ))

                    return {
                        "enriched_description": enriched,
                        "responses": responses,
                    }

            except asyncio.TimeoutError:
                logger.warning("Clarification response timed out, proceeding without")
            except Exception as e:
                logger.warning(f"Clarification callback failed: {e}, proceeding without")

        # If no response callback or it failed, proceed without clarification
        logger.info("No response callback or responses - proceeding without clarification")
        return None

    async def _try_cached_similar(
        self,
        description: str,
        brand: Optional[BrandProfile] = None,
    ) -> Optional[PrototypeResult]:
        """
        Fallback Level 2: Try to find a cached similar successful generation.

        This looks for descriptions with high similarity that previously succeeded.
        Returns None if no suitable cached result is found.
        """
        if not self._smart_system:
            return None

        try:
            # Check cache for similar descriptions (SmartPresetSystem.cache, not _cache)
            cache = self._smart_system.cache
            if not cache or not hasattr(cache, 'get_most_similar'):
                return None

            # Get most similar cached entry
            similar = cache.get_most_similar(description, min_similarity=0.6)
            if not similar:
                return None

            # Only use if the cached entry was successful
            if similar.get('success_count', 0) < 1:
                return None

            logger.info(f"Found similar cached preset (similarity: {similar.get('similarity', 0):.2f})")

            # Get preset data from cache
            domain = similar.get('domain', {})
            architecture = similar.get('architecture', {})
            mock_data = similar.get('mock_data', {})

            if not domain or not architecture:
                return None

            # Customize for this specific request
            words = description.split()
            app_name = " ".join(words[:3]).title() if len(words) >= 3 else description[:30].title()
            architecture["app_name"] = app_name
            architecture["_source_description"] = description

            # Compose UI with cached data
            files = await self._compose_ui(
                description=description,
                domain_analysis=domain,
                architecture=architecture,
                mock_data=mock_data,
                brand=brand,
            )

            # Validate
            validated_files, validation = validate_and_fix(files)

            if not validation.is_valid and len(validation.errors) > 5:
                # Too many errors, don't use cached version
                return None

            return PrototypeResult(
                success=True,
                files=validated_files,
                domain_analysis=domain,
                architecture=architecture,
                mock_data=mock_data,
                validation=validation,
                fallback_info=FallbackInfo(
                    level=FallbackLevel.CACHED_SIMILAR,
                    reason="Used similar successful project as base",
                    customization_applied=["app_name", "brand_colors"] if brand else ["app_name"],
                ),
            )

        except Exception as e:
            logger.warning(f"Cached similar fallback failed: {e}")
            return None

    async def _try_template_customized(
        self,
        description: str,
        brand: Optional[BrandProfile] = None,
    ) -> Optional[PrototypeResult]:
        """
        Fallback Level 3: Template with domain-specific mock data.

        Uses static industry presets to customize a template without
        the full creative pipeline.
        """
        try:
            # Get industry preset (static, fast)
            domain = get_industry_preset(description)
            industry = domain.get("industry", "")

            # Get architecture preset
            architecture = get_architecture_preset(industry)
            words = description.split()
            app_name = " ".join(words[:3]).title() if len(words) >= 3 else description[:30].title()
            architecture["app_name"] = app_name
            architecture["tagline"] = f"Your {domain.get('industry_display_name', 'business')} dashboard"
            architecture["_source_description"] = description

            # Get mock data preset
            mock_data = get_mock_data_preset(industry)

            # Compose UI
            files = await self._compose_ui(
                description=description,
                domain_analysis=domain,
                architecture=architecture,
                mock_data=mock_data,
                brand=brand,
            )

            # Validate
            validated_files, validation = validate_and_fix(files)

            customizations = ["industry_preset", "mock_data"]
            if brand:
                customizations.append("brand_colors")

            return PrototypeResult(
                success=True,
                files=validated_files,
                domain_analysis=domain,
                architecture=architecture,
                mock_data=mock_data,
                validation=validation,
                fallback_info=FallbackInfo(
                    level=FallbackLevel.TEMPLATE_CUSTOMIZED,
                    reason="Template customized with industry preset",
                    customization_applied=customizations,
                ),
            )

        except Exception as e:
            logger.warning(f"Template customized fallback failed: {e}")
            return None

    async def _try_template_clean(
        self,
        description: str,
        brand: Optional[BrandProfile] = None,
    ) -> Optional[PrototypeResult]:
        """
        Fallback Level 4: Clean template with generic data.

        Just loads the template as-is, with optional brand colors.
        """
        try:
            template = self._template_loader.select_template(description)
            if not template:
                return None

            files = self._template_loader.get_template_files_dict(template.id)

            # Apply brand if provided
            if brand:
                files = self._template_customizer.apply_brand_to_template(files, brand)

            customizations = []
            if brand:
                customizations.append("brand_colors")

            return PrototypeResult(
                success=True,
                files=files,
                fallback_info=FallbackInfo(
                    level=FallbackLevel.TEMPLATE_CLEAN,
                    reason="Using professional template",
                    customization_applied=customizations if customizations else ["none"],
                ),
            )

        except Exception as e:
            logger.warning(f"Template clean fallback failed: {e}")
            return None

    async def generate(
        self,
        description: str,
        brand: Optional[BrandProfile] = None,
        project_id: Optional[str] = None,
        user_clarifications: Optional[Dict[str, str]] = None,
    ) -> PrototypeResult:
        """
        Generate a domain-specific prototype.

        Args:
            description: Business/app description from user
            brand: Optional brand profile for colors/styling
            project_id: Optional project ID for tracking
            user_clarifications: Pre-provided clarification responses (skips clarification phase)

        Returns:
            PrototypeResult with files and metadata
        """
        start_time = datetime.utcnow()

        # Extract concepts ONCE at the start (performance optimization)
        concepts = None
        if self._smart_system:
            concepts = self._smart_system.get_concepts(description)

        # PHASE 0: Clarification (if needed and not skipped)
        enriched_description = description
        if concepts and not self.skip_clarification and not user_clarifications:
            clarification_result = await self._run_clarification_phase(
                description=description,
                concepts=concepts,
            )
            if clarification_result:
                enriched_description = clarification_result.get("enriched_description", description)
                user_clarifications = clarification_result.get("responses", {})

                # Re-extract concepts with enriched description for better matching
                if enriched_description != description:
                    concepts = self._smart_system.get_concepts(enriched_description)

        # If clarifications were provided, enrich the description
        if user_clarifications and not enriched_description.endswith("Additional details:"):
            enriched_description = self._clarification_agent.enrich_description(
                description, user_clarifications
            )
            # Re-extract concepts with enriched description
            if self._smart_system:
                concepts = self._smart_system.get_concepts(enriched_description)

        # Store domain expertise for enhanced agent context (optional, computed lazily)
        domain_expertise: Optional[DomainExpertise] = None

        try:
            # Step 0.5: Domain Expertise Synthesis (optional, runs in background or on-demand)
            # This enriches the domain analysis with web research and learned patterns
            try:
                await self._emit(PrototypeEvent(
                    type="research_progress",
                    agent="Domain Expert",
                    message="Synthesizing domain expertise...",
                    progress=3
                ))

                domain_expertise = await self._expertise_synthesizer.synthesize(
                    description=enriched_description,
                    concepts=concepts,
                    user_clarifications=user_clarifications,
                    progress_callback=None,  # Could emit progress events here
                )

                await self._emit(PrototypeEvent(
                    type="agent_complete",
                    agent="Domain Expert",
                    message=f"Built expertise profile (confidence: {domain_expertise.confidence_score:.0%})",
                    progress=5,
                    data={
                        "confidence": domain_expertise.confidence_score,
                        "sources": domain_expertise.sources_used,
                        "industry_trends": domain_expertise.industry_trends[:3],
                    }
                ))
            except Exception as expertise_error:
                logger.warning(f"Domain expertise synthesis failed (non-fatal): {expertise_error}")
                # Continue without expertise - domain analysis will use presets

            # Step 1: Domain Analysis
            await self._emit(PrototypeEvent(
                type="agent_start",
                agent="Domain Analyst",
                message="Understanding your business domain...",
                progress=5
            ))

            domain_analysis = await self._analyze_domain(enriched_description, concepts, domain_expertise)

            await self._emit(PrototypeEvent(
                type="agent_complete",
                agent="Domain Analyst",
                message=f"Identified industry: {domain_analysis.get('industry_display_name', domain_analysis.get('industry', 'general'))}",
                progress=20,
                data={"domain": domain_analysis}
            ))

            # Step 2: Architecture Planning
            await self._emit(PrototypeEvent(
                type="agent_start",
                agent="Architect",
                message="Planning app structure...",
                progress=20
            ))

            architecture = await self._plan_architecture(enriched_description, domain_analysis)

            # Store description for downstream use
            architecture["_source_description"] = enriched_description

            await self._emit(PrototypeEvent(
                type="agent_complete",
                agent="Architect",
                message=f"Planned {len(architecture.get('pages', []))} pages with {len(architecture.get('stat_cards', []))} key metrics",
                progress=40,
                data={"architecture": architecture}
            ))

            # Step 3: Content Generation
            await self._emit(PrototypeEvent(
                type="agent_start",
                agent="Content Generator",
                message="Creating realistic mock data...",
                progress=40
            ))

            mock_data = await self._generate_content(domain_analysis, architecture)

            await self._emit(PrototypeEvent(
                type="agent_complete",
                agent="Content Generator",
                message=f"Generated data for {len(mock_data.keys())} data sources",
                progress=55,
                data={"mock_data_keys": list(mock_data.keys())}
            ))

            # Step 3.5: Quality Evaluation & Enhancement
            await self._emit(PrototypeEvent(
                type="agent_start",
                agent="Quality Analyst",
                message="Evaluating preset quality...",
                progress=55
            ))

            quality_result = await self._evaluate_and_enhance(
                description=description,
                domain_analysis=domain_analysis,
                architecture=architecture,
                mock_data=mock_data,
                concepts=concepts  # Reuse pre-extracted concepts
            )

            # Update with enhanced versions if improvements were made
            if quality_result.get("enhanced"):
                if quality_result.get("new_domain"):
                    domain_analysis = quality_result["new_domain"]
                if quality_result.get("new_architecture"):
                    architecture = quality_result["new_architecture"]
                    architecture["_source_description"] = description  # Preserve
                if quality_result.get("new_mock_data"):
                    mock_data = quality_result["new_mock_data"]

                await self._emit(PrototypeEvent(
                    type="agent_complete",
                    agent="Quality Analyst",
                    message=f"Enhanced preset: {len(quality_result.get('changes', []))} improvements applied",
                    progress=60,
                    data={
                        "quality_score": quality_result.get("score"),
                        "changes": quality_result.get("changes", [])
                    }
                ))
            else:
                await self._emit(PrototypeEvent(
                    type="agent_complete",
                    agent="Quality Analyst",
                    message=f"Quality check passed (score: {quality_result.get('score', 0):.0%})",
                    progress=60,
                    data={"quality_score": quality_result.get("score")}
                ))

            # Step 4: UI Composition
            await self._emit(PrototypeEvent(
                type="agent_start",
                agent="UI Composer",
                message="Building interface components...",
                progress=60
            ))

            files = await self._compose_ui(
                description=enriched_description,
                domain_analysis=domain_analysis,
                architecture=architecture,
                mock_data=mock_data,
                brand=brand,
            )

            await self._emit(PrototypeEvent(
                type="agent_complete",
                agent="UI Composer",
                message=f"Generated {len(files)} files",
                progress=80,
                data={"file_count": len(files)}
            ))

            # Step 5: Validation
            await self._emit(PrototypeEvent(
                type="agent_start",
                agent="Validator",
                message="Validating generated code...",
                progress=80
            ))

            validated_files, validation = validate_and_fix(files)

            if validation.is_valid:
                await self._emit(PrototypeEvent(
                    type="agent_complete",
                    agent="Validator",
                    message="All checks passed!",
                    progress=85
                ))
            else:
                # Log issues but continue with fixed files
                issue_count = len(validation.errors) + len(validation.warnings)
                await self._emit(PrototypeEvent(
                    type="agent_complete",
                    agent="Validator",
                    message=f"Fixed {issue_count} issues",
                    progress=85,
                    data={"fixed_issues": issue_count}
                ))

            # Step 6: Business Report Generation (NEW - consultant mode)
            report_html = None
            report_type = None
            try:
                await self._emit(PrototypeEvent(
                    type="agent_start",
                    agent="Report Generator",
                    message="Generating business insights report...",
                    progress=85
                ))

                report_html, report_type = await self._generate_business_report(
                    description=enriched_description,
                    domain_analysis=domain_analysis,
                    architecture=architecture,
                    mock_data=mock_data,
                    domain_expertise=domain_expertise,
                    user_clarifications=user_clarifications,
                    concepts=concepts,
                )

                await self._emit(PrototypeEvent(
                    type="agent_complete",
                    agent="Report Generator",
                    message=f"Generated {report_type.replace('_', ' ').title()} report",
                    progress=100,
                    data={"report_type": report_type}
                ))

                # Emit report as a separate event for the frontend
                await self._emit(PrototypeEvent(
                    type="report_complete",
                    agent="Report Generator",
                    message="Business report ready!",
                    progress=100,
                    data={
                        "report_html": report_html,
                        "report_type": report_type,
                    }
                ))

            except Exception as report_error:
                logger.warning(f"Report generation failed (non-fatal): {report_error}")
                await self._emit(PrototypeEvent(
                    type="agent_complete",
                    agent="Report Generator",
                    message="Report generation skipped",
                    progress=100
                ))

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Record success for learning
            if self._smart_system:
                self._smart_system.record_success(description)

            # Record positive feedback for pattern analysis
            feedback_analyzer = get_feedback_analyzer()
            feedback_analyzer.record_outcome(domain_analysis, architecture, positive=True)

            # Learn from this successful generation
            if quality_result.get("score", 0) >= 0.7:
                enhancer = get_enhancer()
                enhancer.learn_from_success(
                    domain_analysis,
                    architecture,
                    mock_data,
                    quality_result.get("score", 0.7)
                )

            # Determine customizations applied
            customizations = ["domain_analysis", "architecture", "mock_data"]
            if brand:
                customizations.append("brand_colors")
            if quality_result.get("enhanced"):
                customizations.append("quality_enhanced")

            return PrototypeResult(
                success=True,
                files=validated_files,
                domain_analysis=domain_analysis,
                architecture=architecture,
                mock_data=mock_data,
                validation=validation,
                duration_ms=duration_ms,
                fallback_info=FallbackInfo(
                    level=FallbackLevel.FULL_CREATIVE,
                    reason="Full creative pipeline completed",
                    customization_applied=customizations,
                ),
                report_html=report_html,
                report_type=report_type,
            )

        except Exception as e:
            logger.error(f"Prototype generation failed: {e}")

            # Record failure for learning
            if self._smart_system:
                self._smart_system.record_failure(description)

            # Record negative feedback if we have domain/architecture info
            try:
                if 'domain_analysis' in dir() and 'architecture' in dir():
                    feedback_analyzer = get_feedback_analyzer()
                    feedback_analyzer.record_outcome(domain_analysis, architecture, positive=False)
            except Exception:
                pass  # Don't fail on analytics

            # Mark any running agents as complete (interrupted) before fallback
            # This ensures the UI doesn't show agents stuck in "running" state
            await self._emit(PrototypeEvent(
                type="agent_complete",
                agent="Domain Analyst",
                message="Switching to fallback system",
                progress=50
            ))

            # Execute fallback cascade
            await self._emit(PrototypeEvent(
                type="status",
                message="Trying alternative generation methods...",
                progress=50
            ))

            fallback_result = await self._execute_fallback_cascade(
                description=description,
                brand=brand,
                original_error=str(e),
                start_time=start_time,
            )

            return fallback_result

    async def _execute_fallback_cascade(
        self,
        description: str,
        brand: Optional[BrandProfile],
        original_error: str,
        start_time: datetime,
    ) -> PrototypeResult:
        """
        Execute the fallback cascade to ensure users always get something useful.

        Cascade order:
        1. CACHED_SIMILAR - Try to use a similar successful generation
        2. TEMPLATE_CUSTOMIZED - Template with industry-specific data
        3. TEMPLATE_CLEAN - Plain template
        4. MINIMAL - Absolute minimum working prototype

        Each level provides less customization but more reliability.
        """
        cascade_levels = [
            (FallbackLevel.CACHED_SIMILAR, self._try_cached_similar, "Checking similar projects..."),
            (FallbackLevel.TEMPLATE_CUSTOMIZED, self._try_template_customized, "Applying industry preset..."),
            (FallbackLevel.TEMPLATE_CLEAN, self._try_template_clean, "Loading professional template..."),
        ]

        # Start the Fallback System agent
        await self._emit(PrototypeEvent(
            type="agent_start",
            agent="Fallback System",
            message="Activating fallback system...",
            progress=55
        ))

        for level, method, status_msg in cascade_levels:
            await self._emit(PrototypeEvent(
                type="status",
                message=status_msg,
                progress=60,
                data={"fallback_level": level.name}
            ))

            try:
                result = await method(description, brand)
                if result:
                    duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    result.duration_ms = duration_ms

                    # Update fallback info with original error
                    if result.fallback_info:
                        result.fallback_info.original_error = original_error

                    logger.info(f"Fallback successful at level: {level.name}")

                    await self._emit(PrototypeEvent(
                        type="agent_complete",
                        agent="Fallback System",
                        message=result.fallback_info.user_message if result.fallback_info else "Prototype ready",
                        progress=100,
                        data={"fallback_level": level.name}
                    ))

                    return result

            except Exception as fallback_error:
                logger.warning(f"Fallback level {level.name} failed: {fallback_error}")
                continue

        # Last resort: minimal fallback (Level 5)
        logger.warning("All fallback levels failed, using minimal prototype")

        await self._emit(PrototypeEvent(
            type="fallback",
            message="Creating minimal starter prototype...",
            progress=80,
            data={"fallback_level": FallbackLevel.MINIMAL.name}
        ))

        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        minimal_files = self._generate_minimal_fallback(description)

        await self._emit(PrototypeEvent(
            type="agent_complete",
            agent="Fallback System",
            message="Minimal starter ready - add your content",
            progress=100
        ))

        return PrototypeResult(
            success=True,  # We always succeed at this level
            files=minimal_files,
            error=f"Original error: {original_error}",
            duration_ms=duration_ms,
            fallback_info=FallbackInfo(
                level=FallbackLevel.MINIMAL,
                reason="All customization attempts failed",
                original_error=original_error,
                customization_applied=["none"],
            ),
        )

    async def _analyze_domain(
        self,
        description: str,
        concepts: Optional[Any] = None,
        domain_expertise: Optional[DomainExpertise] = None,
    ) -> Dict[str, Any]:
        """
        Step 1: Analyze the business domain using smart keyword extraction.

        The smart preset system:
        - Extracts weighted keywords (distinctive terms score higher)
        - Identifies entities (users, orders, proposals, etc.)
        - Identifies actions (vote, book, track, etc.)
        - Matches to best industry with confidence scoring
        - Checks cache for similar previous generations

        Enhanced with DomainExpertise (if available):
        - Web research insights (trends, competitors, pricing)
        - Knowledge store patterns (from successful builds)
        - User clarifications (target market, services, etc.)

        Args:
            description: User's project description
            concepts: Pre-extracted concepts (optimization to avoid re-extraction)
            domain_expertise: Rich domain expertise from synthesizer (optional)
        """
        if self._smart_system:
            # Use smart preset system
            domain, _, _ = self._smart_system.get_preset(description)

            # Use pre-extracted concepts if available (performance optimization)
            if concepts is None:
                concepts = self._smart_system.get_concepts(description)

            # Add concepts info to domain for richer context
            domain["_concepts"] = {
                "entities": concepts.entities,
                "actions": concepts.actions,
                "best_industry": concepts.best_industry,
                "confidence": concepts.best_score,
                "secondary_industries": concepts.secondary_industries,
            }

            # Enrich with domain expertise (if available)
            if domain_expertise:
                # Add expertise-derived data
                domain["_expertise"] = {
                    "target_market": domain_expertise.target_market,
                    "service_model": domain_expertise.service_model,
                    "pricing_approach": domain_expertise.pricing_approach,
                    "scale_expectation": domain_expertise.scale_expectation,
                    "industry_trends": domain_expertise.industry_trends[:5],
                    "competitor_features": domain_expertise.competitor_features[:7],
                    "best_practices": domain_expertise.best_practices[:5],
                    "pricing_benchmarks": domain_expertise.pricing_benchmarks,
                    "confidence_score": domain_expertise.confidence_score,
                }

                # Merge terminology (expertise takes priority)
                if domain_expertise.terminology:
                    existing_terminology = domain.get("terminology", {})
                    merged_terminology = {**existing_terminology, **domain_expertise.terminology}
                    domain["terminology"] = merged_terminology

                # Enhance metrics with expertise recommendations
                if domain_expertise.recommended_metrics:
                    existing_metrics = domain.get("metrics", [])
                    for metric in domain_expertise.recommended_metrics:
                        if metric not in existing_metrics:
                            existing_metrics.append(metric)
                    domain["metrics"] = existing_metrics[:8]

                # Add suggested sections from expertise
                if domain_expertise.suggested_features:
                    existing_sections = domain.get("suggested_sections", [])
                    for feature in domain_expertise.suggested_features[:4]:
                        if feature not in existing_sections:
                            existing_sections.append(feature)
                    domain["suggested_sections"] = existing_sections[:8]

                # Add agent context string for prompts
                domain["_agent_context"] = domain_expertise.to_agent_context()

                logger.info(
                    f"Enhanced domain with expertise: "
                    f"confidence={domain_expertise.confidence_score:.2f}, "
                    f"sources={domain_expertise.sources_used}"
                )

            logger.info(
                f"Smart domain analysis: industry={concepts.best_industry} "
                f"(confidence={concepts.best_score:.2f}), "
                f"entities={concepts.entities[:3]}, "
                f"actions={concepts.actions[:3]}"
            )
            return domain
        else:
            # Fallback to static presets
            preset = get_industry_preset(description)
            logger.info(f"Using static domain preset for: {preset.get('industry', 'universal')}")
            return preset

    async def _plan_architecture(
        self,
        description: str,
        domain_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 2: Plan the prototype architecture.

        When using smart presets:
        - Pages are built based on detected entities
        - Stat cards reflect domain-specific metrics
        - Navigation adapts to the business type
        """
        if self._smart_system:
            # Get architecture from smart system (already computed with domain)
            _, architecture, _ = self._smart_system.get_preset(description)

            # Ensure app name is set
            if not architecture.get("app_name"):
                words = description.split()
                architecture["app_name"] = " ".join(words[:3]).title() if len(words) >= 3 else description[:30].title()

            logger.info(
                f"Smart architecture: {len(architecture.get('pages', []))} pages, "
                f"{len(architecture.get('stat_cards', []))} stat cards"
            )
            return architecture
        else:
            # Fallback to static presets
            industry = domain_analysis.get("industry", "")
            preset = get_architecture_preset(industry)
            architecture = dict(preset)

            words = description.split()
            app_name = " ".join(words[:3]) if len(words) >= 3 else description[:30]
            architecture["app_name"] = app_name.title()
            architecture["tagline"] = f"Your {domain_analysis.get('industry_display_name', 'application')} dashboard"

            logger.info(f"Using static architecture preset for: {industry or 'universal'}")
            return architecture

    async def _generate_content(
        self,
        domain_analysis: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 3: Generate realistic mock data.

        When using smart presets:
        - Data matches architecture's data sources
        - Entity-specific data is included (proposals, orders, etc.)
        - Stats align with domain metrics
        """
        # Get description from architecture for smart lookup
        description = architecture.get("_source_description", "")

        if self._smart_system and description:
            # Get mock data from smart system
            _, _, mock_data = self._smart_system.get_preset(description)
            logger.info(f"Smart mock data: {len(mock_data)} data sources")
            return mock_data
        else:
            # Fallback to static presets
            industry = domain_analysis.get("industry", "")
            mock_data = get_mock_data_preset(industry)
            logger.info(f"Using static mock data preset for: {industry or 'universal'}")
            return mock_data

    async def _evaluate_and_enhance(
        self,
        description: str,
        domain_analysis: Dict[str, Any],
        architecture: Dict[str, Any],
        mock_data: Dict[str, Any],
        concepts: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Step 3.5: Evaluate preset quality and enhance if needed.

        This step:
        - Scores the preset quality (completeness, consistency, structure)
        - Identifies issues that could cause problems
        - Auto-enhances weak presets using learned patterns
        - Records patterns from good presets for future learning

        Args:
            concepts: Pre-extracted concepts (optimization to avoid re-extraction)

        Returns dict with quality info and potentially enhanced components.
        """
        result = {
            "score": 0.0,
            "enhanced": False,
            "changes": [],
            "issues": [],
        }

        # Use pre-extracted concepts if available (performance optimization)
        if concepts is None and self._smart_system:
            concepts = self._smart_system.get_concepts(description)

        # 1. Evaluate current quality
        quality_score = evaluate_preset(
            domain_analysis,
            architecture,
            mock_data,
            concepts
        )

        result["score"] = quality_score.overall_score
        result["issues"] = [
            {"type": issue[0].value, "description": issue[1]}
            for issue in quality_score.issues
        ]

        logger.info(
            f"Quality evaluation: score={quality_score.overall_score:.2f}, "
            f"issues={len(quality_score.issues)}, "
            f"can_enhance={quality_score.can_enhance}"
        )

        # 2. If quality is low but fixable, try to enhance
        if quality_score.can_enhance:
            enhancer = get_enhancer()
            enhancement = enhance_preset(
                domain_analysis,
                architecture,
                mock_data,
                concepts
            )

            if enhancement.enhanced:
                result["enhanced"] = True
                result["changes"] = enhancement.changes_made
                result["new_domain"] = enhancement.new_domain
                result["new_architecture"] = enhancement.new_architecture
                result["new_mock_data"] = enhancement.new_mock_data

                # Re-evaluate after enhancement
                new_score = evaluate_preset(
                    enhancement.new_domain,
                    enhancement.new_architecture,
                    enhancement.new_mock_data,
                    concepts
                )
                result["score"] = new_score.overall_score

                logger.info(
                    f"Enhancement complete: {len(enhancement.changes_made)} changes, "
                    f"new_score={new_score.overall_score:.2f}"
                )

        # 3. If quality is high, learn from this preset
        elif quality_score.overall_score >= 0.8 and self._smart_system:
            enhancer = get_enhancer()
            enhancer.learn_from_success(
                domain_analysis,
                architecture,
                mock_data,
                quality_score.overall_score
            )
            logger.debug("Learned patterns from high-quality preset")

        # 4. Record for feedback analysis
        feedback_analyzer = get_feedback_analyzer()
        # We'll record the outcome later after validation

        return result

    async def _compose_ui(
        self,
        description: str,
        domain_analysis: Dict[str, Any],
        architecture: Dict[str, Any],
        mock_data: Dict[str, Any],
        brand: Optional[BrandProfile] = None,
    ) -> Dict[str, str]:
        """
        Step 4: Compose the UI by combining template with domain-specific content.

        For now, uses templates with customized mock data.
        Future: Generate custom components based on architecture.
        """
        # Select base template
        template_id = architecture.get("template_id", "dashboard")
        template = self._template_loader.get_template(template_id)

        if not template:
            template = self._template_loader.select_template(description)

        if not template:
            logger.warning("No template found, using minimal fallback")
            return self._generate_minimal_fallback(description)

        # Get template files
        files = self._template_loader.get_template_files_dict(template.id)

        # Inject mock data
        mock_json = json.dumps(mock_data, indent=2)
        if "src/data/mock.json" in files:
            files["src/data/mock.json"] = mock_json
        else:
            # Add mock.json to appropriate location
            files["src/data/mock.json"] = mock_json

        # Apply brand colors if provided
        if brand:
            files = self._template_customizer.apply_brand_to_template(files, brand)
        elif domain_analysis.get("suggested_colors"):
            # Use domain-suggested colors
            colors = domain_analysis["suggested_colors"]
            temp_brand = BrandProfile(
                primary_color=colors.get("primary", "#3B82F6"),
                secondary_color=colors.get("secondary", "#10B981"),
                accent_color=colors.get("accent", "#F59E0B"),
                company_name=architecture.get("app_name", "Dashboard"),
            )
            files = self._template_customizer.apply_brand_to_template(files, temp_brand)

        # Customize page content based on architecture
        files = self._customize_page_content(files, architecture, domain_analysis)

        return files

    def _customize_page_content(
        self,
        files: Dict[str, str],
        architecture: Dict[str, Any],
        domain_analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """Customize page content with domain-specific text"""
        app_name = architecture.get("app_name", "Dashboard")
        tagline = architecture.get("tagline", "Your business dashboard")

        # Update page.tsx with welcome message
        if "src/app/page.tsx" in files:
            content = files["src/app/page.tsx"]

            # Replace generic welcome with domain-specific
            if "Good morning, Sarah!" in content:
                content = content.replace(
                    "Good morning, Sarah!",
                    f"Welcome to {app_name}!"
                )

            if "Your dashboard is looking great" in content:
                content = content.replace(
                    "Your dashboard is looking great. Revenue is up 24% this month. Keep up the momentum!",
                    tagline
                )

            files["src/app/page.tsx"] = content

        # Update sidebar with app name
        if "src/components/Sidebar.tsx" in files:
            content = files["src/components/Sidebar.tsx"]

            if "Acme" in content:
                short_name = app_name.split()[0] if " " in app_name else app_name[:10]
                content = content.replace("Acme", short_name)

            files["src/components/Sidebar.tsx"] = content

        # Update layout metadata
        if "src/app/layout.tsx" in files:
            content = files["src/app/layout.tsx"]

            if "title:" in content:
                content = content.replace(
                    "title: 'Modern Dashboard'",
                    f"title: '{app_name}'"
                )

            files["src/app/layout.tsx"] = content

        return files

    async def _generate_business_report(
        self,
        description: str,
        domain_analysis: Dict[str, Any],
        architecture: Dict[str, Any],
        mock_data: Dict[str, Any],
        domain_expertise: Optional[DomainExpertise] = None,
        user_clarifications: Optional[Dict[str, str]] = None,
        concepts: Optional[ExtractedConcepts] = None,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Generate a professional business insights report alongside the prototype.

        Returns:
            Tuple of (report_html, report_type) or (None, None) if generation fails
        """
        try:
            # Determine report type based on context
            # - If we have funnel data or UX issues, use UX_AUDIT
            # - If we have industry insights and recommendations, use TRANSFORMATION_PROPOSAL
            # - If we have both, use COMPREHENSIVE
            has_industry_data = domain_expertise and domain_expertise.industry_trends
            has_ux_context = domain_analysis.get("ux_focus") or domain_analysis.get("audit_mode")

            if has_industry_data and has_ux_context:
                report_type = ReportType.COMPREHENSIVE
            elif has_ux_context:
                report_type = ReportType.UX_AUDIT
            else:
                report_type = ReportType.TRANSFORMATION_PROPOSAL

            # Build the report model from available data
            company_name = architecture.get("app_name", domain_analysis.get("company_name", "Your Company"))
            industry = domain_analysis.get("industry", "general")

            # Build cover stats
            cover_stats = []
            if domain_expertise:
                cover_stats.append(MetricItem(
                    label="Confidence",
                    value=f"{domain_expertise.confidence_score:.0%}",
                    badge=BadgeType.GOOD if domain_expertise.confidence_score >= 0.7 else BadgeType.WARNING
                ))
            cover_stats.append(MetricItem(
                label="Pages",
                value=str(len(architecture.get("pages", []))),
                badge=BadgeType.INFO
            ))
            cover_stats.append(MetricItem(
                label="Features",
                value=str(len(architecture.get("key_features", []))),
                badge=BadgeType.INFO
            ))
            cover_stats.append(MetricItem(
                label="Data Sources",
                value=str(len(mock_data.keys())),
                badge=BadgeType.SUCCESS
            ))

            # Build executive summary
            key_features = architecture.get("key_features", [])
            exec_headline = f"Your {industry.replace('-', ' ').title()} prototype is ready!"
            exec_bottom_line = f"We've built a {len(architecture.get('pages', []))}-page prototype with {len(key_features)} key features tailored to the {industry.replace('-', ' ')} industry."

            if domain_expertise and domain_expertise.industry_trends:
                exec_bottom_line += f" Based on market research, we've incorporated trends like {', '.join(domain_expertise.industry_trends[:2])}."

            metrics = []
            metrics.append(MetricItem(
                label="Industry",
                value=industry.replace("-", " ").title(),
                badge=BadgeType.INFO,
                badge_text="Detected"
            ))
            if user_clarifications:
                for key, value in list(user_clarifications.items())[:3]:
                    metrics.append(MetricItem(
                        label=key.replace("_", " ").title(),
                        value=value[:50],
                        badge=BadgeType.GOOD,
                        badge_text="From you"
                    ))

            executive_summary = ExecutiveSummary(
                headline=exec_headline,
                metrics=metrics,
                bottom_line=exec_bottom_line,
                bottom_line_type="success"
            )

            # Build industry section from domain expertise
            industry_section = None
            if domain_expertise:
                insights = []
                if domain_expertise.market_size:
                    insights.append(IndustryInsight(
                        title="Market Size",
                        value=domain_expertise.market_size
                    ))
                for trend in domain_expertise.industry_trends[:3]:
                    insights.append(IndustryInsight(title="Trend", value=trend))

                industry_section = IndustrySection(
                    market_size=domain_expertise.market_size,
                    key_trends=domain_expertise.industry_trends[:5],
                    insights=insights
                )

            # Build design system from domain analysis colors
            design_system = None
            if domain_analysis.get("suggested_colors"):
                colors = domain_analysis["suggested_colors"]
                design_system = DesignSystem(
                    primary_color=colors.get("primary", "#3B82F6"),
                    secondary_color=colors.get("secondary", "#10B981"),
                    accent_color=colors.get("accent", "#F59E0B"),
                    mood_tags=domain_analysis.get("mood_tags", ["Modern", "Professional"])
                )

            # Build recommended features from architecture
            recommended_features = []
            for i, feature in enumerate(key_features[:10]):
                priority = "Must Have" if i < 3 else ("Should Have" if i < 6 else "Nice to Have")
                recommended_features.append(FeatureRow(
                    feature=feature,
                    priority=priority,
                    investment="Included",
                    timeline="Sprint 1" if i < 3 else ("Sprint 2" if i < 6 else "Sprint 3")
                ))

            # Build recommendations from architecture decisions
            recommendations = []
            if architecture.get("key_features"):
                recommendations.append(Recommendation(
                    priority=1,
                    title="Implement Core Features",
                    subtitle="HIGH - Primary functionality",
                    current_state="Not built",
                    recommended_state="Fully functional prototype",
                    expected_lift="Foundation for your product",
                    confidence=0.9,
                    changes=architecture.get("key_features", [])[:5]
                ))

            if domain_expertise and domain_expertise.best_practices:
                recommendations.append(Recommendation(
                    priority=2,
                    title="Follow Industry Best Practices",
                    subtitle="HIGH - Market expectations",
                    current_state="Generic implementation",
                    recommended_state="Industry-optimized",
                    expected_lift="Better user adoption",
                    confidence=0.85,
                    changes=domain_expertise.best_practices[:5]
                ))

            # Build roadmap
            roadmap = []
            pages = architecture.get("pages", [])
            if pages:
                phase1_items = [RoadmapItem(task=f"Implement {p.get('name', p) if isinstance(p, dict) else p} page") for p in pages[:3]]
                roadmap.append(RoadmapPhase(
                    title="Phase 1: Core Pages",
                    color="#3B82F6",
                    items=phase1_items
                ))

            if key_features:
                phase2_items = [RoadmapItem(task=f"Add {f}") for f in key_features[:5]]
                roadmap.append(RoadmapPhase(
                    title="Phase 2: Key Features",
                    color="#10B981",
                    items=phase2_items
                ))

            # Build the report
            report = BusinessReport(
                report_type=report_type,
                company_name=company_name,
                industry=industry,
                cover_stats=cover_stats,
                executive_summary=executive_summary,
                industry_section=industry_section,
                design_system=design_system,
                recommended_features=recommended_features,
                recommendations=recommendations,
                roadmap=roadmap,
                data_sources=["AI Analysis", "Market Research", "Domain Expertise"] if domain_expertise else ["AI Analysis"],
                confidence_level=f"{domain_expertise.confidence_score:.0%} on primary recommendations" if domain_expertise else "85% on primary recommendations"
            )

            # Generate HTML
            generator = BusinessReportGenerator()
            report_html = generator.generate_report(report)

            return report_html, report_type.value

        except Exception as e:
            logger.error(f"Business report generation failed: {e}")
            return None, None

    def _generate_minimal_fallback(self, description: str) -> Dict[str, str]:
        """Generate minimal working app as last resort"""
        return {
            "package.json": json.dumps({
                "name": "prototype",
                "version": "0.1.0",
                "private": True,
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start"
                },
                "dependencies": {
                    "next": "13.5.6",
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0"
                },
                "devDependencies": {
                    "@types/node": "^20.0.0",
                    "@types/react": "^18.2.0",
                    "typescript": "^5.3.0",
                    "tailwindcss": "^3.4.0",
                    "postcss": "^8.4.0",
                    "autoprefixer": "^10.4.0"
                }
            }, indent=2),
            "src/app/page.tsx": f'''\'use client\'

export default function Home() {{
  return (
    <main style={{{{ minHeight: '100vh', padding: '2rem', background: '#0f172a', color: 'white' }}}}>
      <h1 style={{{{ fontSize: '2rem', fontWeight: 'bold' }}}}>
        {description[:50]}...
      </h1>
      <p style={{{{ color: '#94a3b8', marginTop: '1rem' }}}}>
        Your prototype is ready. Customize it to match your vision.
      </p>
    </main>
  )
}}
''',
            "src/app/layout.tsx": '''import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Prototype',
  description: 'Generated prototype',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
''',
            "src/app/globals.css": '''@tailwind base;
@tailwind components;
@tailwind utilities;
''',
            "tailwind.config.js": '''/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: {} },
  plugins: [],
}
''',
            "postcss.config.js": '''module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
''',
            "tsconfig.json": json.dumps({
                "compilerOptions": {
                    "target": "es5",
                    "lib": ["dom", "esnext"],
                    "allowJs": True,
                    "skipLibCheck": True,
                    "strict": True,
                    "noEmit": True,
                    "esModuleInterop": True,
                    "module": "esnext",
                    "moduleResolution": "bundler",
                    "resolveJsonModule": True,
                    "isolatedModules": True,
                    "jsx": "preserve",
                    "incremental": True,
                    "plugins": [{"name": "next"}],
                    "paths": {"@/*": ["./src/*"]}
                },
                "include": ["**/*.ts", "**/*.tsx"],
                "exclude": ["node_modules"]
            }, indent=2),
            ".babelrc": '{"presets": ["next/babel"]}',
            "next.config.mjs": '''const nextConfig = {
  reactStrictMode: true,
  swcMinify: false,
}
export default nextConfig
'''
        }


# Singleton instance
_orchestrator: Optional[PrototypeOrchestrator] = None


def get_prototype_orchestrator() -> PrototypeOrchestrator:
    """Get the singleton prototype orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PrototypeOrchestrator()
    return _orchestrator


async def generate_prototype(
    description: str,
    brand: Optional[BrandProfile] = None,
    event_callback: Optional[Callable[[PrototypeEvent], Awaitable[None]]] = None,
) -> PrototypeResult:
    """
    Convenience function to generate a prototype.

    Args:
        description: Business/app description
        brand: Optional brand profile
        event_callback: Optional progress callback

    Returns:
        PrototypeResult with files and metadata
    """
    orchestrator = PrototypeOrchestrator(event_callback=event_callback)
    return await orchestrator.generate(description, brand)
