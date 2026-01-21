"""
Code generation routes with WebSocket support
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Dict, Optional, List
from pydantic import BaseModel
import json
import asyncio
import logging
import uuid

from ..models import GenerationRequest, GenerationEvent, Platform
from ..services import manager, CodeGenerator
from ..services.agent_registry import list_agents, get_registry
from ..services.workflows import list_workflows, get_workflow
from ..services.prompts.smart_presets import get_smart_preset_system, extract_concepts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["Generation"])


# ============================================================================
# Clarification Session Management
# ============================================================================

class ClarificationSession:
    """Manages a pending clarification request"""
    def __init__(self, session_id: str, questions: List[dict], industry: str, confidence: float):
        self.session_id = session_id
        self.questions = questions
        self.detected_industry = industry
        self.confidence = confidence
        self.response_event = asyncio.Event()
        self.responses: Dict[str, str] = {}
        self.created_at = asyncio.get_event_loop().time()

    async def wait_for_response(self, timeout: float = 300.0) -> Optional[Dict[str, str]]:
        """Wait for user to submit responses"""
        try:
            await asyncio.wait_for(self.response_event.wait(), timeout=timeout)
            return self.responses
        except asyncio.TimeoutError:
            return None

    def submit_response(self, responses: Dict[str, str]) -> None:
        """Submit user responses"""
        self.responses = responses
        self.response_event.set()


# Global session store (in production, use Redis)
_clarification_sessions: Dict[str, ClarificationSession] = {}


class ClarificationResponseRequest(BaseModel):
    """Request body for submitting clarification responses"""
    responses: Dict[str, str]


@router.post("/sessions/{session_id}/clarify")
async def submit_clarification_response(
    session_id: str,
    request: ClarificationResponseRequest,
):
    """
    Submit responses to clarification questions.

    Called after the frontend receives a clarification_required event.
    The session_id is included in that event's data.
    """
    session = _clarification_sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Clarification session not found: {session_id}"
        )

    # Submit the responses - this will unblock the waiting generate call
    session.submit_response(request.responses)

    return {
        "status": "ok",
        "session_id": session_id,
        "responses_received": len(request.responses),
    }


@router.get("/sessions/{session_id}")
async def get_clarification_session(session_id: str):
    """
    Get the status of a clarification session.

    Useful for checking if a session is still valid.
    """
    session = _clarification_sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Clarification session not found: {session_id}"
        )

    return {
        "session_id": session_id,
        "questions": session.questions,
        "detected_industry": session.detected_industry,
        "confidence": session.confidence,
        "has_response": session.response_event.is_set(),
    }


def _cleanup_old_sessions():
    """Remove sessions older than 10 minutes"""
    now = asyncio.get_event_loop().time()
    expired = [
        sid for sid, session in _clarification_sessions.items()
        if now - session.created_at > 600
    ]
    for sid in expired:
        del _clarification_sessions[sid]


@router.post("/")
async def generate_code(request: GenerationRequest):
    """
    Generate code via HTTP POST with Server-Sent Events streaming.

    This endpoint streams progress events as the generation progresses.

    When a clarification_required event is emitted:
    1. The event includes a session_id
    2. The frontend shows the ClarificationDialog
    3. User submits responses via POST /generate/sessions/{session_id}/clarify
    4. Generation continues automatically
    """
    # Cleanup old sessions periodically
    _cleanup_old_sessions()

    async def event_stream() -> AsyncGenerator[str, None]:
        """Generate SSE events with clarification support"""
        events_queue: asyncio.Queue = asyncio.Queue()
        pending_session: Optional[ClarificationSession] = None

        async def event_callback(event: GenerationEvent):
            nonlocal pending_session

            # If this is a clarification_required event, create a session
            if event.type == "clarification_required" and event.data:
                session_id = str(uuid.uuid4())
                pending_session = ClarificationSession(
                    session_id=session_id,
                    questions=event.data.get("questions", []),
                    industry=event.data.get("detected_industry", ""),
                    confidence=event.data.get("confidence", 0.5),
                )
                _clarification_sessions[session_id] = pending_session

                # Add session_id to the event
                event.session_id = session_id
                logger.info(f"Created clarification session: {session_id}")

            await events_queue.put(event)

        generator = CodeGenerator(event_callback=event_callback)

        # Create a wrapper that handles clarification responses
        async def generate_with_clarification():
            """Run generation with clarification callback support"""
            from ..services.prototype_orchestrator import PrototypeOrchestrator

            # Get the prototype orchestrator directly for clarification support
            orchestrator = generator._get_prototype_orchestrator()

            # Set up a response callback that waits for user input
            async def clarification_callback(questions):
                nonlocal pending_session
                if pending_session:
                    logger.info(f"Waiting for clarification responses on session {pending_session.session_id}")
                    responses = await pending_session.wait_for_response(timeout=300.0)
                    if responses:
                        logger.info(f"Received {len(responses)} responses")
                        return responses
                return None

            # Update orchestrator with the response callback
            orchestrator.response_callback = clarification_callback

            # Run generation
            return await generator.generate(
                description=request.description,
                platform=request.platform,
                project_id=request.project_id
            )

        # Start generation in background
        generation_task = asyncio.create_task(generate_with_clarification())

        try:
            while True:
                # Wait for events with timeout
                try:
                    event = await asyncio.wait_for(events_queue.get(), timeout=30.0)
                    yield f"data: {event.model_dump_json()}\n\n"

                    # Check if we're done
                    if event.type in ("complete", "error"):
                        break

                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"

                    # Check if task is done
                    if generation_task.done():
                        break

        except Exception as e:
            logger.error(f"Error in event stream: {e}")
            error_event = GenerationEvent(type="error", error=str(e))
            yield f"data: {error_event.model_dump_json()}\n\n"

        finally:
            # Cleanup session
            if pending_session and pending_session.session_id in _clarification_sessions:
                del _clarification_sessions[pending_session.session_id]

            # Ensure task is complete
            if not generation_task.done():
                generation_task.cancel()
                try:
                    await generation_task
                except asyncio.CancelledError:
                    pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.websocket("/ws/{project_id}")
async def generation_websocket(websocket: WebSocket, project_id: str):
    """
    WebSocket endpoint for real-time generation updates.

    Connect to receive live updates as agents process the project.

    Message types sent:
    - status: General status update
    - agent_start: Agent began processing
    - agent_complete: Agent finished processing
    - agent_error: Agent encountered an error
    - files: Generated files are ready
    - complete: Generation finished successfully
    - error: Generation failed
    """
    await manager.connect(websocket, project_id)
    logger.info(f"WebSocket connected for project: {project_id}")

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()

            # Handle different message types
            message_type = data.get("type")

            if message_type == "start":
                # Start generation
                description = data.get("description", "")
                platform = Platform(data.get("platform", "web"))

                if not description:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Description is required"
                    })
                    continue

                # Create callback that sends to WebSocket
                async def ws_callback(event: GenerationEvent):
                    await manager.send_json(websocket, event.model_dump())

                generator = CodeGenerator(event_callback=ws_callback)

                # Run generation
                try:
                    files = await generator.generate(
                        description=description,
                        platform=platform,
                        project_id=project_id
                    )
                except Exception as e:
                    logger.error(f"Generation error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e)
                    })

            elif message_type == "ping":
                # Respond to ping
                await websocket.send_json({"type": "pong"})

            elif message_type == "cancel":
                # Handle cancellation (future implementation)
                await websocket.send_json({
                    "type": "status",
                    "message": "Cancellation not yet implemented"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for project: {project_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


@router.get("/agents")
async def list_available_agents():
    """
    List all available AI agents and their capabilities.

    Returns information about all specialized agents loaded from agents.config.json.
    """
    try:
        agents = list_agents()
        registry = get_registry()
        return {
            "agents": agents,
            "total": len(agents),
            "categories": registry.get_categories(),
            "version": registry._version,
        }
    except Exception as e:
        logger.warning(f"Failed to load agents from registry: {e}")
        # Fallback to basic list
        return {
            "agents": [
                {"id": "PM", "role": "Project Manager", "category": "Management"},
                {"id": "Research", "role": "Market Researcher", "category": "Research"},
                {"id": "Designs", "role": "UI/UX Designer", "category": "Design"},
                {"id": "Senior", "role": "System Architect", "category": "Architecture"},
                {"id": "FrontendEngineer", "role": "Frontend Engineer", "category": "Development"},
                {"id": "BackendEngineer", "role": "Backend Engineer", "category": "Development"},
                {"id": "QA", "role": "Test Engineer", "category": "Quality"},
                {"id": "SecurityEngineer", "role": "Security Auditor", "category": "Quality"},
            ],
            "total": 8,
            "note": "Using fallback agent list - agents.config.json not loaded"
        }


@router.get("/creative-pipeline")
async def get_creative_pipeline_info():
    """
    Get information about the 5-agent creative prototype pipeline.

    This pipeline generates domain-specific prototypes that feel tailored
    to the client's business, not generic templates.

    Now powered by the Smart Preset System which learns from usage.
    """
    # Get cache stats to show learning progress
    try:
        system = get_smart_preset_system()
        cache_stats = system.get_cache_stats()
    except Exception:
        cache_stats = {"total": 0}

    return {
        "name": "Creative Prototype Pipeline v2",
        "description": "Generates domain-specific prototypes using 5 specialized agents with learning capabilities",
        "agents": [
            {
                "id": "DomainAnalyst",
                "role": "Smart Domain Analyst",
                "goal": "Extract weighted keywords, entities, and actions using TF-IDF scoring",
                "output": "Domain analysis with confidence scores and composite industry matching",
                "smart_features": [
                    "TF-IDF weighted keyword extraction",
                    "Entity detection (users, orders, proposals, etc.)",
                    "Action detection (vote, book, track, etc.)",
                    "Multi-industry composite matching"
                ]
            },
            {
                "id": "Architect",
                "role": "Adaptive Architect",
                "goal": "Build page structure driven by detected entities and actions",
                "output": "Concept-driven pages, navigation, and metrics",
                "smart_features": [
                    "Entity-driven page generation",
                    "Action-driven UI components",
                    "Adaptive stat cards based on domain metrics"
                ]
            },
            {
                "id": "ContentGenerator",
                "role": "Contextual Content Generator",
                "goal": "Generate mock data that matches architecture data sources",
                "output": "Entity-specific mock data with realistic values",
                "smart_features": [
                    "Data source matching from architecture",
                    "Entity-specific data generation",
                    "Realistic stat value generation"
                ]
            },
            {
                "id": "UIComposer",
                "role": "UI Composer",
                "goal": "Assemble components with domain-specific content and branding",
                "output": "React components with domain terminology and styling"
            },
            {
                "id": "QualityAnalyst",
                "role": "Quality Analyst",
                "goal": "Evaluate preset quality and auto-enhance weak presets",
                "output": "Quality score with issues fixed and patterns applied",
                "smart_features": [
                    "Multi-dimensional quality scoring (completeness, consistency, structure)",
                    "Issue detection (missing data, orphan pages, generic terminology)",
                    "Auto-enhancement using learned patterns",
                    "Feedback analysis for continuous improvement"
                ]
            },
            {
                "id": "Validator",
                "role": "Code Validator",
                "goal": "Pre-WebContainer validation and auto-fixing",
                "output": "Validated files ready for preview"
            }
        ],
        "supported_industries": [
            "saas (software, platform, api, cloud)",
            "blockchain (dao, defi, web3, crypto, voting)",
            "ai (ml, chatbot, prediction, llm)",
            "healthcare (medical, patient, clinic)",
            "fitness (gym, yoga, workout, wellness)",
            "ecommerce (shop, store, cart, retail)",
            "restaurant (cafe, menu, reservation)",
            "education (course, student, learning)",
            "news-media (journalism, article, publication)",
            "pet-services (grooming, veterinary)",
            "real-estate (property, listing, rental)",
            "finance (banking, investment, accounting)",
            "UNIVERSAL (any project type via smart extraction)"
        ],
        "smart_features": [
            "TF-IDF style keyword weighting (distinctive terms matter more)",
            "Entity + Action extraction for structure decisions",
            "Composite industry matching (blend multiple domains)",
            "Learning cache with weighted similarity matching",
            "Success/failure tracking for continuous improvement",
            "User feedback integration for quality tuning",
            "Quality scoring with 3 dimensions (completeness, consistency, structure)",
            "Auto-enhancement for weak presets using learned patterns",
            "Issue detection (missing data, orphan pages, generic terminology)",
            "Pattern learning from successful generations"
        ],
        "learning_stats": {
            "cached_presets": cache_stats.get("total", 0),
            "total_uses": cache_stats.get("total_uses", 0),
            "avg_confidence": cache_stats.get("avg_confidence", 0)
        },
        "api_endpoints": {
            "analyze": "POST /generate/analyze - Analyze a description without generating",
            "stats": "GET /generate/smart-presets/stats - View cache statistics",
            "feedback": "POST /generate/smart-presets/feedback - Record user feedback",
            "quality_evaluate": "POST /generate/quality/evaluate - Evaluate preset quality",
            "quality_insights": "GET /generate/quality/insights - View success/failure correlations",
            "quality_patterns": "GET /generate/quality/patterns - View learned patterns",
            "quality_enhance": "POST /generate/quality/enhance - Auto-enhance a weak preset"
        }
    }


@router.post("/analyze")
async def analyze_description(request: GenerationRequest):
    """
    Analyze a project description using the smart preset system.

    Returns extracted concepts including:
    - Weighted keywords (distinctive terms score higher)
    - Detected entities (users, orders, proposals, etc.)
    - Detected actions (vote, book, track, etc.)
    - Best matching industry with confidence score
    - Secondary industry matches for composite presets

    This is useful for debugging and understanding how the
    system interprets different project descriptions.
    """
    try:
        concepts = extract_concepts(request.description)

        return {
            "description": request.description,
            "analysis": {
                "best_industry": concepts.best_industry,
                "confidence": round(concepts.best_score, 3),
                "secondary_industries": concepts.secondary_industries,
                "entities": concepts.entities,
                "actions": concepts.actions,
                "app_name": concepts.app_name,
                "tagline": concepts.tagline,
                "top_keywords": concepts.top_keywords,
                "domain_signals": {
                    k: round(v, 3) for k, v in
                    sorted(concepts.domain_signals.items(), key=lambda x: -x[1])[:5]
                },
                "matched_patterns": concepts.matched_patterns,
            }
        }
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/smart-presets/stats")
async def get_smart_preset_stats():
    """
    Get statistics about the smart preset cache.

    Returns:
    - Total cached presets
    - Total usage count
    - Average confidence score
    - Top performing presets

    This helps understand how well the learning system is working.
    """
    try:
        system = get_smart_preset_system()
        return system.get_cache_stats()
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/smart-presets/feedback")
async def record_preset_feedback(request: GenerationRequest, positive: bool = True):
    """
    Record user feedback on a generated preset.

    Args:
        request: The original generation request
        positive: Whether the feedback is positive (True) or negative (False)

    This feedback is used to improve future preset generation.
    """
    try:
        system = get_smart_preset_system()
        system.record_feedback(request.description, positive)
        return {"status": "ok", "feedback_recorded": "positive" if positive else "negative"}
    except Exception as e:
        logger.error(f"Failed to record feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quality/evaluate")
async def evaluate_preset_quality(request: GenerationRequest):
    """
    Evaluate the quality of a preset for a given description.

    Returns:
    - overall_score: 0-1 quality score
    - component_scores: completeness, consistency, structure
    - issues: List of identified problems
    - suggestions: Actionable improvement suggestions
    - can_enhance: Whether auto-enhancement can improve this preset

    This is useful for debugging and understanding preset quality
    before generation completes.
    """
    from ..services.prompts.smart_presets import get_smart_preset_system
    from ..services.prompts.preset_quality import evaluate_preset, get_enhancer

    try:
        system = get_smart_preset_system()
        domain, architecture, mock_data = system.get_preset(request.description)
        concepts = system.get_concepts(request.description)

        quality = evaluate_preset(domain, architecture, mock_data, concepts)

        return {
            "description": request.description,
            "quality": {
                "overall_score": round(quality.overall_score, 3),
                "completeness_score": round(quality.completeness_score, 3),
                "consistency_score": round(quality.consistency_score, 3),
                "structure_score": round(quality.structure_score, 3),
            },
            "issues": [
                {"type": issue[0].value, "description": issue[1]}
                for issue in quality.issues
            ],
            "suggestions": quality.suggestions,
            "can_enhance": quality.can_enhance,
            "enhancement_priority": quality.enhancement_priority,
        }
    except Exception as e:
        logger.error(f"Quality evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/insights")
async def get_quality_insights():
    """
    Get insights about what features correlate with preset success.

    Returns:
    - positive_features: Features that appear in successful presets
    - negative_features: Features that appear in failed presets
    - uncertain_features: Features with mixed results

    This helps understand what makes presets good or bad.
    """
    from ..services.prompts.preset_quality import get_feedback_analyzer

    try:
        analyzer = get_feedback_analyzer()
        insights = analyzer.get_insights()

        return {
            "insights": insights,
            "total_observations": sum(
                v["positive"] + v["negative"]
                for v in analyzer.feature_outcomes.values()
            ),
            "features_tracked": len(analyzer.feature_outcomes),
        }
    except Exception as e:
        logger.error(f"Failed to get quality insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/patterns")
async def get_learned_patterns():
    """
    Get patterns learned from successful preset generations.

    Returns patterns for:
    - entity_page_patterns: Entity → Page configurations
    - stat_card_patterns: Common stat card configurations
    - section_patterns: Successful section templates

    These patterns are used to auto-enhance weak presets.
    """
    from ..services.prompts.preset_quality import get_enhancer

    try:
        enhancer = get_enhancer()
        patterns = enhancer._successful_patterns

        return {
            "learned_patterns": {
                key: len(value)
                for key, value in patterns.items()
            },
            "entity_page_patterns": patterns.get("entity_page_patterns", [])[:10],
            "stat_card_patterns": patterns.get("stat_card_patterns", [])[:10],
            "total_patterns": sum(len(v) for v in patterns.values()),
        }
    except Exception as e:
        logger.error(f"Failed to get learned patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quality/enhance")
async def enhance_weak_preset(request: GenerationRequest):
    """
    Attempt to auto-enhance a weak preset.

    If the preset quality is below threshold but fixable,
    applies learned patterns and fixes identified issues.

    Returns the enhanced preset components if improvements were made.
    """
    from ..services.prompts.smart_presets import get_smart_preset_system
    from ..services.prompts.preset_quality import enhance_preset, evaluate_preset

    try:
        system = get_smart_preset_system()
        domain, architecture, mock_data = system.get_preset(request.description)
        concepts = system.get_concepts(request.description)

        # Evaluate before
        before_quality = evaluate_preset(domain, architecture, mock_data, concepts)

        # Attempt enhancement
        result = enhance_preset(domain, architecture, mock_data, concepts)

        if result.enhanced:
            # Evaluate after
            after_quality = evaluate_preset(
                result.new_domain,
                result.new_architecture,
                result.new_mock_data,
                concepts
            )

            return {
                "enhanced": True,
                "changes_made": result.changes_made,
                "score_before": round(before_quality.overall_score, 3),
                "score_after": round(after_quality.overall_score, 3),
                "improvement": round(after_quality.overall_score - before_quality.overall_score, 3),
                "new_domain": result.new_domain,
                "new_architecture": result.new_architecture,
            }
        else:
            return {
                "enhanced": False,
                "reason": "Preset already meets quality threshold or cannot be enhanced",
                "score": round(before_quality.overall_score, 3),
            }
    except Exception as e:
        logger.error(f"Enhancement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/trends")
async def get_quality_trends(days: int = 30):
    """
    Get quality and success trends over time.

    Returns:
    - daily_averages: Quality score and success rate per day
    - total_generations: Total generations in the period
    - success_rate: Overall success rate
    - industry_distribution: Most common industries

    Args:
        days: Number of days to include (default 30)

    This helps monitor system health and detect quality degradation.
    """
    from ..services.prompts.generation_audit import get_audit_log

    try:
        audit_log = get_audit_log()
        trends = audit_log.get_trends(days=days)
        return trends
    except Exception as e:
        logger.error(f"Failed to get quality trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/failures")
async def get_recent_failures(limit: int = 50):
    """
    Get recent generation failures for debugging.

    Returns a list of recent failures with:
    - timestamp
    - description
    - error message
    - duration

    Args:
        limit: Maximum number of failures to return (default 50)
    """
    from ..services.prompts.generation_audit import get_audit_log

    try:
        audit_log = get_audit_log()
        failures = audit_log.get_failures(limit=limit)
        return {
            "failures": failures,
            "count": len(failures),
        }
    except Exception as e:
        logger.error(f"Failed to get failures: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows")
async def list_available_workflows():
    """
    List all available workflow templates.

    Workflows define which agents run and in what order.
    """
    return {
        "workflows": list_workflows(),
    }


@router.get("/workflows/{workflow_type}")
async def get_workflow_details(workflow_type: str):
    """
    Get details for a specific workflow.
    """
    workflow = get_workflow(workflow_type)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_type}")

    return {
        "type": workflow.type.value,
        "name": workflow.name,
        "description": workflow.description,
        "agent_ids": workflow.agent_ids,
        "estimated_minutes": workflow.estimated_duration_minutes,
        "parallel_groups": workflow.parallel_groups,
    }
