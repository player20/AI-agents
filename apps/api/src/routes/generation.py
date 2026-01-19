"""
Code generation routes with WebSocket support
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import asyncio
import logging

from ..models import GenerationRequest, GenerationEvent, Platform
from ..services import manager, CodeGenerator
from ..services.agent_registry import list_agents, get_registry
from ..services.workflows import list_workflows, get_workflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["Generation"])


@router.post("/")
async def generate_code(request: GenerationRequest):
    """
    Generate code via HTTP POST with Server-Sent Events streaming.

    This endpoint streams progress events as the generation progresses.
    """

    async def event_stream() -> AsyncGenerator[str, None]:
        """Generate SSE events"""
        events_queue: asyncio.Queue = asyncio.Queue()

        async def event_callback(event: GenerationEvent):
            await events_queue.put(event)

        generator = CodeGenerator(event_callback=event_callback)

        # Start generation in background
        generation_task = asyncio.create_task(
            generator.generate(
                description=request.description,
                platform=request.platform,
                project_id=request.project_id
            )
        )

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
