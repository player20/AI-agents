"""
Agent Orchestrator using LangGraph

Coordinates multi-agent workflows with state management and real-time updates.
Executes agents in sequence or parallel based on workflow configuration.
"""

from typing import Dict, List, Optional, Any, Callable, Awaitable, TypedDict
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import asyncio
import logging

from langgraph.graph import StateGraph, END

from .agent_registry import get_registry, AgentConfig
from .workflows import (
    get_workflow,
    get_workflow_sequence,
    recommend_workflow,
    WorkflowConfig,
)
from .agent_executor import (
    AgentExecutor,
    AgentContext,
    AgentResult,
    execute_agent,
    execute_agents_parallel,
)
from ..ai.structured_output import CodeFile

logger = logging.getLogger(__name__)


# ===========================================
# Workflow State
# ===========================================

class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowState(TypedDict):
    """State tracked through the workflow execution"""
    project_id: str
    description: str
    platform: str
    workflow_type: str

    # Execution tracking
    current_agent: str
    completed_agents: List[str]
    pending_agents: List[str]

    # Accumulated results
    agent_results: Dict[str, Any]  # agent_id -> result dict
    files: List[Dict[str, Any]]  # Generated files
    errors: List[str]

    # Metadata
    started_at: str
    status: str


class WorkflowResult(BaseModel):
    """Final result of workflow execution"""
    project_id: str
    workflow_type: str
    status: WorkflowStatus

    # Results
    files: List[CodeFile] = Field(default_factory=list)
    agent_results: Dict[str, AgentResult] = Field(default_factory=dict)

    # Statistics
    total_agents: int = 0
    successful_agents: int = 0
    failed_agents: int = 0

    # Timing
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    # Errors
    errors: List[str] = Field(default_factory=list)


# ===========================================
# Event Types for Real-time Updates
# ===========================================

class OrchestratorEvent(BaseModel):
    """Event emitted during orchestration"""
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    project_id: str
    data: Dict[str, Any] = Field(default_factory=dict)


EventCallback = Callable[[OrchestratorEvent], Awaitable[None]]


# ===========================================
# Agent Orchestrator
# ===========================================

class AgentOrchestrator:
    """
    Orchestrates multi-agent workflows using LangGraph.

    Features:
    - Sequential and parallel agent execution
    - State management across agents
    - Real-time event streaming
    - Error recovery and retry
    """

    def __init__(
        self,
        event_callback: Optional[EventCallback] = None,
        max_parallel_agents: int = 3,
    ):
        self.event_callback = event_callback
        self.max_parallel_agents = max_parallel_agents
        self.registry = get_registry()

    async def _emit_event(
        self,
        event_type: str,
        project_id: str,
        data: Dict[str, Any] = None,
    ) -> None:
        """Emit an event through the callback if configured"""
        if self.event_callback:
            event = OrchestratorEvent(
                type=event_type,
                project_id=project_id,
                data=data or {},
            )
            await self.event_callback(event)

    async def run_workflow(
        self,
        description: str,
        platform: str,
        project_id: str,
        workflow_type: Optional[str] = None,
    ) -> WorkflowResult:
        """
        Execute a complete workflow.

        Args:
            description: Project description
            platform: Target platform (web, mobile, api, etc.)
            project_id: Unique project identifier
            workflow_type: Specific workflow or auto-detect

        Returns:
            WorkflowResult with all generated files and agent outputs
        """
        started_at = datetime.utcnow()

        # Auto-detect workflow if not specified
        if workflow_type is None:
            workflow_type = recommend_workflow(description, platform)
            logger.info(f"Auto-selected workflow: {workflow_type}")

        # Get workflow configuration
        workflow_config = get_workflow(workflow_type)
        if workflow_config is None:
            return WorkflowResult(
                project_id=project_id,
                workflow_type=workflow_type,
                status=WorkflowStatus.FAILED,
                started_at=started_at,
                errors=[f"Unknown workflow type: {workflow_type}"],
            )

        agent_sequence = get_workflow_sequence(workflow_type)

        await self._emit_event("workflow_start", project_id, {
            "workflow_type": workflow_type,
            "total_agents": len(agent_sequence),
            "agents": agent_sequence,
        })

        # Initialize state
        state: WorkflowState = {
            "project_id": project_id,
            "description": description,
            "platform": platform,
            "workflow_type": workflow_type,
            "current_agent": "",
            "completed_agents": [],
            "pending_agents": agent_sequence.copy(),
            "agent_results": {},
            "files": [],
            "errors": [],
            "started_at": started_at.isoformat(),
            "status": WorkflowStatus.RUNNING.value,
        }

        # Build and execute the workflow graph
        try:
            final_state = await self._execute_workflow_graph(
                state, workflow_config
            )

            # Compile results
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            # Convert file dicts back to CodeFile objects
            files = []
            for file_dict in final_state.get("files", []):
                try:
                    files.append(CodeFile(**file_dict))
                except Exception as e:
                    logger.warning(f"Could not parse file: {e}")

            # Convert result dicts to AgentResult objects
            agent_results = {}
            for agent_id, result_dict in final_state.get("agent_results", {}).items():
                try:
                    agent_results[agent_id] = AgentResult(**result_dict)
                except Exception:
                    agent_results[agent_id] = result_dict

            success_count = sum(
                1 for r in agent_results.values()
                if (isinstance(r, AgentResult) and r.success) or
                   (isinstance(r, dict) and r.get("success"))
            )

            status = WorkflowStatus.COMPLETED
            if final_state.get("errors"):
                status = WorkflowStatus.FAILED if success_count == 0 else WorkflowStatus.COMPLETED

            result = WorkflowResult(
                project_id=project_id,
                workflow_type=workflow_type,
                status=status,
                files=files,
                agent_results=agent_results,
                total_agents=len(agent_sequence),
                successful_agents=success_count,
                failed_agents=len(agent_sequence) - success_count,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                errors=final_state.get("errors", []),
            )

            await self._emit_event("workflow_complete", project_id, {
                "status": status.value,
                "total_agents": result.total_agents,
                "successful_agents": result.successful_agents,
                "failed_agents": result.failed_agents,
                "duration_ms": duration_ms,
                "file_count": len(files),
            })

            return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            await self._emit_event("workflow_error", project_id, {
                "error": str(e),
            })

            return WorkflowResult(
                project_id=project_id,
                workflow_type=workflow_type,
                status=WorkflowStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                errors=[str(e)],
            )

    async def _execute_workflow_graph(
        self,
        initial_state: WorkflowState,
        workflow_config: WorkflowConfig,
    ) -> WorkflowState:
        """Build and execute the LangGraph workflow"""

        # Create the state graph
        graph = StateGraph(WorkflowState)

        # Add agent nodes
        async def execute_agent_node(state: WorkflowState) -> WorkflowState:
            """Execute the current agent"""
            if not state["pending_agents"]:
                return state

            current_agent = state["pending_agents"][0]
            state["current_agent"] = current_agent

            await self._emit_event("agent_start", state["project_id"], {
                "agent_id": current_agent,
                "progress": len(state["completed_agents"]) / (
                    len(state["completed_agents"]) + len(state["pending_agents"])
                ),
            })

            # Build context from previous results
            context = AgentContext(
                project_id=state["project_id"],
                description=state["description"],
                platform=state["platform"],
                previous_outputs={
                    aid: state["agent_results"].get(aid, {}).get("output")
                    for aid in state["completed_agents"]
                },
                files=[CodeFile(**f) for f in state["files"]],
            )

            # Execute the agent
            result = await execute_agent(
                current_agent,
                context,
                on_progress=lambda msg: self._emit_event(
                    "agent_progress",
                    state["project_id"],
                    {"agent_id": current_agent, "message": msg}
                ),
            )

            # Update state
            new_state = state.copy()
            new_state["agent_results"][current_agent] = result.model_dump()
            new_state["completed_agents"] = state["completed_agents"] + [current_agent]
            new_state["pending_agents"] = state["pending_agents"][1:]
            new_state["current_agent"] = ""

            # Add generated files
            if result.files:
                for f in result.files:
                    new_state["files"].append(f.model_dump())

            # Track errors
            if not result.success and result.error:
                new_state["errors"].append(f"{current_agent}: {result.error}")

            await self._emit_event("agent_complete", state["project_id"], {
                "agent_id": current_agent,
                "success": result.success,
                "duration_ms": result.duration_ms,
                "file_count": len(result.files),
            })

            return new_state

        # Check for parallel execution opportunities
        async def execute_parallel_node(state: WorkflowState) -> WorkflowState:
            """Execute parallelizable agents together"""
            if not state["pending_agents"]:
                return state

            parallel_groups = workflow_config.parallel_groups or []

            # Find agents that can run in parallel
            parallel_agents = []
            for group in parallel_groups:
                group_agents = [
                    a for a in group
                    if a in state["pending_agents"]
                ]
                if len(group_agents) > 1:
                    parallel_agents = group_agents[:self.max_parallel_agents]
                    break

            if not parallel_agents:
                # No parallel group found, run next agent sequentially
                return await execute_agent_node(state)

            await self._emit_event("parallel_start", state["project_id"], {
                "agents": parallel_agents,
            })

            # Emit agent_start for each agent in parallel group
            for agent_id in parallel_agents:
                await self._emit_event("agent_start", state["project_id"], {
                    "agent_id": agent_id,
                    "progress": len(state["completed_agents"]) / (
                        len(state["completed_agents"]) + len(state["pending_agents"])
                    ),
                    "parallel": True,
                })

            # Build shared context
            context = AgentContext(
                project_id=state["project_id"],
                description=state["description"],
                platform=state["platform"],
                previous_outputs={
                    aid: state["agent_results"].get(aid, {}).get("output")
                    for aid in state["completed_agents"]
                },
                files=[CodeFile(**f) for f in state["files"]],
            )

            # Execute in parallel
            results = await execute_agents_parallel(
                parallel_agents,
                context,
                on_agent_complete=lambda aid, r: self._emit_event(
                    "agent_complete",
                    state["project_id"],
                    {"agent_id": aid, "success": r.success}
                ),
            )

            # Update state
            new_state = state.copy()
            for agent_id, result in results.items():
                new_state["agent_results"][agent_id] = result.model_dump()
                if result.files:
                    for f in result.files:
                        new_state["files"].append(f.model_dump())
                if not result.success and result.error:
                    new_state["errors"].append(f"{agent_id}: {result.error}")

            new_state["completed_agents"] = state["completed_agents"] + parallel_agents
            new_state["pending_agents"] = [
                a for a in state["pending_agents"]
                if a not in parallel_agents
            ]

            await self._emit_event("parallel_complete", state["project_id"], {
                "agents": parallel_agents,
            })

            return new_state

        # Add the main execution node
        graph.add_node("execute", execute_parallel_node)

        # Define edges
        def should_continue(state: WorkflowState) -> str:
            """Check if there are more agents to execute"""
            if state["pending_agents"]:
                return "execute"
            return END

        graph.add_conditional_edges(
            "execute",
            should_continue,
            {"execute": "execute", END: END}
        )

        # Set entry point
        graph.set_entry_point("execute")

        # Compile the graph
        workflow = graph.compile()

        # Execute
        final_state = await workflow.ainvoke(initial_state)

        return final_state


# ===========================================
# Convenience Functions
# ===========================================

_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator(
    event_callback: Optional[EventCallback] = None,
) -> AgentOrchestrator:
    """Get or create the global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None or event_callback is not None:
        _orchestrator = AgentOrchestrator(event_callback=event_callback)
    return _orchestrator


async def run_workflow(
    description: str,
    platform: str,
    project_id: str,
    workflow_type: Optional[str] = None,
    event_callback: Optional[EventCallback] = None,
) -> WorkflowResult:
    """
    Run a workflow with optional event streaming.

    Convenience function for simple usage.
    """
    orchestrator = AgentOrchestrator(event_callback=event_callback)
    return await orchestrator.run_workflow(
        description=description,
        platform=platform,
        project_id=project_id,
        workflow_type=workflow_type,
    )
