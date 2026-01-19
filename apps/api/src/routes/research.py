"""
Research API Routes

Endpoints for market research, competitor analysis, and business intelligence.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import logging
import asyncio

from ..ai.research_models import (
    ResearchRequest,
    ResearchResponse,
    ResearchStatus,
    ResearchReport,
    MarketResearch,
    MarketSize,
    CompetitorAnalysis,
    Competitor,
    CompetitorTier,
    FeatureRecommendations,
    Feature,
    FeaturePriority,
    GTMStrategy,
    SWOTAnalysis,
    SWOTItem,
    MarketSegment,
    PricingModel,
    Channel,
    TargetPersona,
    Milestone,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["Research"])

# In-memory storage for research jobs
_research_jobs: Dict[str, Dict[str, Any]] = {}


async def _run_research_analysis(job_id: str, request: ResearchRequest):
    """
    Background task to run the complete research analysis.

    This orchestrates multiple AI agents to generate comprehensive research.
    """
    job = _research_jobs[job_id]

    try:
        # Phase 1: Market Research
        job["status"] = "researching"
        job["current_phase"] = "Market Analysis"
        job["progress"] = 10

        market = await _generate_market_research(request.business_idea)
        job["progress"] = 25

        # Phase 2: Competitor Analysis
        job["current_phase"] = "Competitor Analysis"
        competitors = await _generate_competitor_analysis(request.business_idea, market)
        job["progress"] = 45

        # Phase 3: Feature Recommendations
        job["current_phase"] = "Feature Analysis"
        features = await _generate_feature_recommendations(
            request.business_idea, market, competitors
        )
        job["progress"] = 60

        # Phase 4: GTM Strategy
        job["current_phase"] = "GTM Strategy"
        gtm = await _generate_gtm_strategy(
            request.business_idea, market, competitors, features
        )
        job["progress"] = 75

        # Phase 5: SWOT Analysis
        job["current_phase"] = "SWOT Analysis"
        swot = await _generate_swot_analysis(
            request.business_idea, market, competitors, features, gtm
        )
        job["progress"] = 90

        # Phase 6: Compile Report
        job["current_phase"] = "Compiling Report"
        report = await _compile_research_report(
            job_id, request.business_idea, market, competitors, features, gtm, swot
        )
        job["progress"] = 100

        job["status"] = "complete"
        job["current_phase"] = "Complete"
        job["report"] = report
        job["completed_at"] = datetime.now()

    except Exception as e:
        logger.error(f"Research analysis failed for job {job_id}: {e}")
        job["status"] = "error"
        job["error"] = str(e)


async def _generate_market_research(business_idea: str) -> MarketResearch:
    """Generate market research using AI"""
    try:
        from ..ai.structured_output import get_structured_client

        client = get_structured_client()

        system = """You are an expert market research analyst. Analyze the business idea
        and provide detailed market research including TAM/SAM/SOM estimates, market trends,
        and growth drivers. Be specific with numbers and cite your methodology."""

        return await client.generate(
            response_model=MarketResearch,
            system=system,
            messages=[{
                "role": "user",
                "content": f"Conduct market research for this business idea: {business_idea}"
            }],
            temperature=0.7
        )

    except Exception as e:
        logger.warning(f"AI market research failed, using mock data: {e}")
        return _mock_market_research(business_idea)


async def _generate_competitor_analysis(
    business_idea: str,
    market: MarketResearch
) -> CompetitorAnalysis:
    """Generate competitor analysis using AI"""
    try:
        from ..ai.structured_output import get_structured_client

        client = get_structured_client()

        system = """You are a competitive intelligence analyst. Identify and analyze
        competitors for this business, comparing features, pricing, and market positioning.
        Identify gaps and differentiation opportunities."""

        return await client.generate(
            response_model=CompetitorAnalysis,
            system=system,
            messages=[{
                "role": "user",
                "content": f"""Analyze competitors for: {business_idea}

Market context:
- Industry: {market.industry_vertical}
- Market size: ${market.tam.value}B TAM
- Key trends: {', '.join(market.key_trends[:3])}"""
            }],
            temperature=0.7
        )

    except Exception as e:
        logger.warning(f"AI competitor analysis failed, using mock data: {e}")
        return _mock_competitor_analysis(business_idea)


async def _generate_feature_recommendations(
    business_idea: str,
    market: MarketResearch,
    competitors: CompetitorAnalysis
) -> FeatureRecommendations:
    """Generate feature recommendations using AI"""
    try:
        from ..ai.structured_output import get_structured_client

        client = get_structured_client()

        gaps = competitors.market_gaps[:3] if competitors.market_gaps else []

        system = """You are a product strategist. Based on market research and
        competitive analysis, recommend prioritized features for the MVP and beyond.
        Consider user needs, competitive parity, and differentiation."""

        return await client.generate(
            response_model=FeatureRecommendations,
            system=system,
            messages=[{
                "role": "user",
                "content": f"""Recommend features for: {business_idea}

Market gaps identified: {', '.join(gaps)}
Target demographics: {', '.join(market.target_demographics[:3])}
Differentiation opportunities: {', '.join(competitors.differentiation_opportunities[:3])}"""
            }],
            temperature=0.7
        )

    except Exception as e:
        logger.warning(f"AI feature recommendations failed, using mock data: {e}")
        return _mock_feature_recommendations(business_idea)


async def _generate_gtm_strategy(
    business_idea: str,
    market: MarketResearch,
    competitors: CompetitorAnalysis,
    features: FeatureRecommendations
) -> GTMStrategy:
    """Generate go-to-market strategy using AI"""
    try:
        from ..ai.structured_output import get_structured_client

        client = get_structured_client()

        system = """You are a go-to-market strategist. Create a comprehensive
        launch strategy including target personas, channels, pricing, and timeline.
        Be specific and actionable."""

        return await client.generate(
            response_model=GTMStrategy,
            system=system,
            messages=[{
                "role": "user",
                "content": f"""Create GTM strategy for: {business_idea}

Target market: {', '.join(market.target_demographics[:3])}
MVP features: {len(features.mvp_features)} core features
Market maturity: {market.market_maturity}"""
            }],
            temperature=0.7
        )

    except Exception as e:
        logger.warning(f"AI GTM strategy failed, using mock data: {e}")
        return _mock_gtm_strategy(business_idea)


async def _generate_swot_analysis(
    business_idea: str,
    market: MarketResearch,
    competitors: CompetitorAnalysis,
    features: FeatureRecommendations,
    gtm: GTMStrategy
) -> SWOTAnalysis:
    """Generate SWOT analysis using AI"""
    try:
        from ..ai.structured_output import get_structured_client

        client = get_structured_client()

        system = """You are a strategic business analyst. Conduct a thorough SWOT
        analysis considering all aspects of the business, market, and competition.
        Provide actionable insights and recommendations."""

        return await client.generate(
            response_model=SWOTAnalysis,
            system=system,
            messages=[{
                "role": "user",
                "content": f"""Conduct SWOT analysis for: {business_idea}

Key context:
- Market size: ${market.tam.value}B
- Competitors: {len(competitors.competitors)} identified
- Differentiation opportunities: {', '.join(competitors.differentiation_opportunities[:2])}
- Pricing strategy: {gtm.pricing_strategy.value}"""
            }],
            temperature=0.7
        )

    except Exception as e:
        logger.warning(f"AI SWOT analysis failed, using mock data: {e}")
        return _mock_swot_analysis(business_idea)


async def _compile_research_report(
    job_id: str,
    business_idea: str,
    market: MarketResearch,
    competitors: CompetitorAnalysis,
    features: FeatureRecommendations,
    gtm: GTMStrategy,
    swot: SWOTAnalysis
) -> ResearchReport:
    """Compile all research into a complete report"""
    try:
        from ..ai.structured_output import get_structured_client

        client = get_structured_client()

        # Generate executive summary
        summary_prompt = f"""Write an executive summary for this market research:

Business: {business_idea}
TAM: ${market.tam.value}B
SAM: ${market.sam.value}B
SOM: ${market.som.value}B
Competitors: {len(competitors.competitors)}
Key strengths: {[s.item for s in swot.strengths[:3]]}
Key opportunities: {[o.item for o in swot.opportunities[:3]]}
Pricing: {gtm.pricing_strategy.value}

Write 2-3 paragraphs summarizing key findings and recommendations."""

        # For now, generate a simple summary
        executive_summary = f"""This research analyzes the market opportunity for {business_idea}.

The total addressable market (TAM) is estimated at ${market.tam.value}B with a {market.tam.growth_rate}% annual growth rate. Analysis identified {len(competitors.competitors)} key competitors, revealing opportunities for differentiation through {', '.join(competitors.differentiation_opportunities[:2]) if competitors.differentiation_opportunities else 'unique positioning'}.

The recommended go-to-market approach involves a {gtm.pricing_strategy.value} pricing model, targeting {', '.join([s.value for s in gtm.target_segments[:2]])} segments through {', '.join([c.value for c in gtm.primary_channels[:3]])} channels. Key success factors include executing on the {len(features.mvp_features)} MVP features while addressing identified market gaps."""

        return ResearchReport(
            id=job_id,
            business_idea=business_idea,
            executive_summary=executive_summary,
            key_findings=[
                f"TAM of ${market.tam.value}B with {market.tam.growth_rate}% growth",
                f"{len(competitors.competitors)} competitors analyzed",
                f"{len(competitors.market_gaps)} market gaps identified",
                f"{len(features.mvp_features)} MVP features recommended",
                f"{len(swot.strengths)} key strengths identified",
            ],
            recommendations=[
                f"Focus on: {competitors.differentiation_opportunities[0]}" if competitors.differentiation_opportunities else "Build unique value proposition",
                f"Launch with {gtm.pricing_strategy.value} pricing model",
                f"Target {gtm.target_segments[0].value if gtm.target_segments else 'primary'} segment first",
            ],
            market=market,
            competitors=competitors,
            features=features,
            gtm=gtm,
            swot=swot,
            differentiation_strategy=competitors.differentiation_opportunities[0] if competitors.differentiation_opportunities else "Focus on superior user experience",
            risk_factors=[t.item for t in swot.threats[:3]],
            next_steps=swot.recommended_actions[:5],
            status="complete"
        )

    except Exception as e:
        logger.error(f"Report compilation failed: {e}")
        raise


# ===========================================
# Mock Data Generators (for development)
# ===========================================

def _mock_market_research(business_idea: str) -> MarketResearch:
    """Generate mock market research data"""
    return MarketResearch(
        tam=MarketSize(value=50.0, year=2024, growth_rate=12.5, source="Industry analysis"),
        sam=MarketSize(value=15.0, year=2024, growth_rate=15.0, source="Market segmentation"),
        som=MarketSize(value=1.5, year=2024, growth_rate=25.0, source="Realistic capture estimate"),
        methodology="Top-down analysis using industry reports and bottom-up validation",
        key_trends=[
            "Digital transformation acceleration",
            "Mobile-first user expectations",
            "AI/ML integration becoming table stakes",
            "Sustainability and social responsibility focus",
        ],
        market_drivers=[
            "Increasing demand for efficiency",
            "Remote work normalization",
            "Generational shift in technology adoption",
        ],
        market_barriers=[
            "Established incumbents",
            "Customer acquisition costs",
            "Regulatory compliance requirements",
        ],
        target_demographics=[
            "Tech-savvy professionals 25-45",
            "Small business owners",
            "Enterprise decision makers",
        ],
        geographic_focus=["North America", "Europe", "Asia Pacific"],
        industry_vertical="Technology / SaaS",
        market_maturity="growing"
    )


def _mock_competitor_analysis(business_idea: str) -> CompetitorAnalysis:
    """Generate mock competitor analysis"""
    competitors = [
        Competitor(
            name="MarketLeader Pro",
            description="Established market leader with comprehensive features",
            tier=CompetitorTier.MARKET_LEADER,
            price_position=8.0,
            feature_position=9.0,
            strengths=["Brand recognition", "Large customer base", "Full feature set"],
            weaknesses=["Complex UI", "Expensive", "Slow to innovate"],
            pricing_model=PricingModel.TIERED,
            price_range="$99-499/month"
        ),
        Competitor(
            name="AgileStart",
            description="Nimble startup with modern approach",
            tier=CompetitorTier.DIRECT,
            price_position=4.0,
            feature_position=6.0,
            strengths=["Modern UI", "Fast iteration", "Good support"],
            weaknesses=["Limited features", "Small team", "Less proven"],
            pricing_model=PricingModel.FREEMIUM,
            price_range="Free-$49/month"
        ),
        Competitor(
            name="EnterpriseSuite",
            description="Enterprise-focused solution",
            tier=CompetitorTier.INDIRECT,
            price_position=9.5,
            feature_position=8.5,
            strengths=["Enterprise features", "Security", "Compliance"],
            weaknesses=["Not SMB friendly", "Long sales cycles", "Heavy weight"],
            pricing_model=PricingModel.SUBSCRIPTION,
            price_range="$500-5000/month"
        ),
    ]

    return CompetitorAnalysis(
        competitors=competitors,
        positioning={c.name: (c.price_position, c.feature_position) for c in competitors},
        market_gaps=[
            "Lack of AI-powered automation",
            "Poor mobile experience",
            "No self-service onboarding",
            "Missing integration ecosystem",
        ],
        differentiation_opportunities=[
            "AI-first approach with intelligent automation",
            "Superior mobile experience",
            "Instant value with self-service setup",
            "Open API and integration marketplace",
        ],
        competitive_threats=[
            "Market leader may copy innovations",
            "New entrants with venture funding",
            "Adjacent products expanding scope",
        ],
        feature_comparison_matrix={}
    )


def _mock_feature_recommendations(business_idea: str) -> FeatureRecommendations:
    """Generate mock feature recommendations"""
    return FeatureRecommendations(
        mvp_features=[
            Feature(
                name="User Authentication",
                description="Secure login with social auth options",
                priority=FeaturePriority.MVP,
                effort="medium",
                impact="high",
                rationale="Core requirement for any user-facing app",
                competitor_parity=True
            ),
            Feature(
                name="Dashboard",
                description="Clean, intuitive main dashboard",
                priority=FeaturePriority.MVP,
                effort="medium",
                impact="high",
                rationale="First impression and daily interaction point",
                competitor_parity=True
            ),
            Feature(
                name="Core Workflow",
                description="Primary value-delivering functionality",
                priority=FeaturePriority.MVP,
                effort="high",
                impact="high",
                rationale="The main reason users will adopt the product",
                competitor_parity=False
            ),
        ],
        nice_to_have=[
            Feature(
                name="Advanced Analytics",
                description="Detailed reporting and insights",
                priority=FeaturePriority.NICE_TO_HAVE,
                effort="high",
                impact="medium",
                rationale="Valuable for power users and retention",
                competitor_parity=True
            ),
            Feature(
                name="Team Collaboration",
                description="Multi-user support with permissions",
                priority=FeaturePriority.NICE_TO_HAVE,
                effort="medium",
                impact="medium",
                rationale="Expands use case to teams",
                competitor_parity=True
            ),
        ],
        future_roadmap=[
            Feature(
                name="AI Assistant",
                description="Intelligent automation and suggestions",
                priority=FeaturePriority.FUTURE,
                effort="high",
                impact="high",
                rationale="Key differentiator for long-term",
                competitor_parity=False
            ),
        ],
        mvp_summary="Focus on core value proposition with clean UX",
        total_features=6,
        prioritization_criteria=["User value", "Competitive necessity", "Development effort", "Business impact"]
    )


def _mock_gtm_strategy(business_idea: str) -> GTMStrategy:
    """Generate mock GTM strategy"""
    return GTMStrategy(
        target_segments=[MarketSegment.B2C, MarketSegment.SMB],
        target_personas=[
            TargetPersona(
                name="Tech-Savvy Sarah",
                role="Product Manager",
                demographics="28-40, urban, $80-150k income",
                pain_points=["Too many tools", "Manual processes", "Data silos"],
                goals=["Increase efficiency", "Better insights", "Save time"],
                objections=["Learning curve", "Integration concerns", "Budget approval"],
                channels=[Channel.CONTENT_MARKETING, Channel.SOCIAL_MEDIA, Channel.REFERRAL],
                messaging="Get more done with less effort - intelligent automation that works"
            )
        ],
        value_proposition="The simplest way to achieve [outcome] without [pain point]",
        positioning_statement="For [target users] who [need], our product provides [benefit] unlike [competitors] because [differentiator]",
        key_messages=[
            "Save 10+ hours per week with intelligent automation",
            "Set up in minutes, not days",
            "Trusted by 1000+ teams worldwide",
        ],
        primary_channels=[Channel.CONTENT_MARKETING, Channel.SEO, Channel.SOCIAL_MEDIA],
        secondary_channels=[Channel.PAID_ADS, Channel.EMAIL, Channel.REFERRAL],
        channel_strategy={
            Channel.CONTENT_MARKETING.value: "Educational blog posts, guides, and tutorials",
            Channel.SEO.value: "Target high-intent keywords and build authority",
            Channel.SOCIAL_MEDIA.value: "Community building and engagement on LinkedIn/Twitter",
        },
        pricing_strategy=PricingModel.FREEMIUM,
        pricing_rationale="Lower barrier to entry, convert with value",
        price_points={
            "Free": "$0 - Core features, limited usage",
            "Pro": "$29/month - Full features, unlimited usage",
            "Team": "$79/month - Collaboration features",
        },
        launch_timeline=[
            Milestone(
                name="Private Beta",
                description="Limited release to early adopters",
                phase="pre-launch",
                success_metrics=["50 beta users", "NPS > 40", "3+ daily active users"]
            ),
            Milestone(
                name="Public Launch",
                description="Open registration and PR push",
                phase="launch",
                success_metrics=["1000 signups", "100 paying customers", "Press coverage"]
            ),
        ],
        launch_strategy="Build waitlist with content marketing, launch to engaged community first",
        key_metrics=["MRR", "CAC", "LTV", "Churn rate", "NPS"],
        success_criteria={
            "Month 3": "$10k MRR",
            "Month 6": "$50k MRR",
            "Month 12": "$150k MRR",
        }
    )


def _mock_swot_analysis(business_idea: str) -> SWOTAnalysis:
    """Generate mock SWOT analysis"""
    return SWOTAnalysis(
        strengths=[
            SWOTItem(
                item="Modern technology stack",
                impact="high",
                description="Built with latest technologies for speed and reliability",
                leverage="Highlight technical advantages in marketing"
            ),
            SWOTItem(
                item="Lean team structure",
                impact="medium",
                description="Ability to move fast and adapt quickly",
                leverage="Iterate faster than larger competitors"
            ),
            SWOTItem(
                item="Focus on user experience",
                impact="high",
                description="Design-first approach differentiates from legacy tools",
                leverage="Make UX a core brand pillar"
            ),
        ],
        weaknesses=[
            SWOTItem(
                item="Limited brand recognition",
                impact="high",
                description="New entrant in established market",
                mitigation="Invest in content marketing and thought leadership"
            ),
            SWOTItem(
                item="Small team",
                impact="medium",
                description="Limited bandwidth for support and development",
                mitigation="Focus on self-service and automation"
            ),
        ],
        opportunities=[
            SWOTItem(
                item="AI/ML integration",
                impact="high",
                description="Emerging technology can create new value",
                leverage="Build AI features as core differentiator"
            ),
            SWOTItem(
                item="Remote work trend",
                impact="high",
                description="Increased need for digital tools",
                leverage="Position as remote-first solution"
            ),
        ],
        threats=[
            SWOTItem(
                item="Well-funded competitors",
                impact="high",
                description="Incumbents may copy features or acquire",
                mitigation="Build unique value and community"
            ),
            SWOTItem(
                item="Economic uncertainty",
                impact="medium",
                description="Budget cuts may affect adoption",
                mitigation="Emphasize ROI and cost savings"
            ),
        ],
        key_insights=[
            "Technology advantage is temporary - focus on UX and community",
            "AI integration is the key differentiator opportunity",
            "Brand building is critical for long-term success",
        ],
        recommended_actions=[
            "Launch with freemium to build user base quickly",
            "Invest heavily in content marketing for brand awareness",
            "Prioritize AI features to create defensible differentiation",
            "Build community to create switching costs",
            "Focus on specific niche before expanding",
        ]
    )


# ===========================================
# API Endpoints
# ===========================================

@router.post("/analyze", response_model=ResearchStatus, status_code=202)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a new research analysis job.

    This initiates a comprehensive research process including:
    - Market size analysis (TAM/SAM/SOM)
    - Competitor analysis
    - Feature recommendations
    - Go-to-market strategy
    - SWOT analysis

    Returns a job ID that can be used to check status and retrieve results.
    """
    job_id = str(uuid.uuid4())

    _research_jobs[job_id] = {
        "id": job_id,
        "status": "pending",
        "progress": 0,
        "current_phase": "Initializing",
        "request": request.model_dump(),
        "report": None,
        "error": None,
        "created_at": datetime.now(),
        "completed_at": None,
    }

    # Start background analysis
    background_tasks.add_task(_run_research_analysis, job_id, request)

    return ResearchStatus(
        id=job_id,
        status="pending",
        progress=0,
        current_phase="Initializing"
    )


@router.get("/{job_id}", response_model=ResearchResponse)
async def get_research(job_id: str):
    """
    Get the status and results of a research job.

    Returns the complete research report when the job is complete.
    """
    if job_id not in _research_jobs:
        raise HTTPException(status_code=404, detail="Research job not found")

    job = _research_jobs[job_id]

    return ResearchResponse(
        id=job_id,
        status=job["status"],
        report=job.get("report")
    )


@router.get("/{job_id}/status", response_model=ResearchStatus)
async def get_research_status(job_id: str):
    """
    Get just the status of a research job (lightweight endpoint for polling).
    """
    if job_id not in _research_jobs:
        raise HTTPException(status_code=404, detail="Research job not found")

    job = _research_jobs[job_id]

    return ResearchStatus(
        id=job_id,
        status=job["status"],
        progress=job["progress"],
        current_phase=job["current_phase"],
        error=job.get("error")
    )


@router.delete("/{job_id}", status_code=204)
async def cancel_research(job_id: str):
    """
    Cancel a research job.
    """
    if job_id not in _research_jobs:
        raise HTTPException(status_code=404, detail="Research job not found")

    # Note: This only marks the job as cancelled, doesn't stop background task
    _research_jobs[job_id]["status"] = "cancelled"
    return None


@router.get("/", response_model=list[ResearchStatus])
async def list_research_jobs(
    status: Optional[str] = None,
    limit: int = 20
):
    """
    List all research jobs with optional status filter.
    """
    jobs = list(_research_jobs.values())

    if status:
        jobs = [j for j in jobs if j["status"] == status]

    # Sort by created_at descending
    jobs.sort(key=lambda j: j["created_at"], reverse=True)

    return [
        ResearchStatus(
            id=j["id"],
            status=j["status"],
            progress=j["progress"],
            current_phase=j["current_phase"],
            error=j.get("error")
        )
        for j in jobs[:limit]
    ]
