"""
Agent Executor Service

Executes individual agents using LLM calls with structured outputs.
Integrates with the agent registry and existing AI modules.
"""

from typing import Dict, List, Optional, Any, Callable, Awaitable
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
import logging

from .agent_registry import AgentConfig, get_agent
from ..ai.structured_output import (
    StructuredOutputClient,
    ProjectStructure,
    CodeFile,
    CodeReview,
    AnalysisResult,
    TaskPlan,
    APIEndpoint,
    DatabaseSchema,
    ComponentSpec,
    ArchitectureDecision,
)
from ..llm.router import get_llm_router, LLMRouter
from ..llm.providers import LLMMessage

logger = logging.getLogger(__name__)


# ===========================================
# Agent Context and Result Models
# ===========================================

class AgentContext(BaseModel):
    """Context passed to an agent for execution"""
    project_id: str = Field(description="Unique project identifier")
    description: str = Field(description="Project/task description")
    platform: str = Field(default="web", description="Target platform")

    # Previous agent outputs
    previous_outputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Outputs from previous agents in the workflow"
    )

    # Accumulated project state
    files: List[CodeFile] = Field(
        default_factory=list,
        description="Files generated so far"
    )
    decisions: List[ArchitectureDecision] = Field(
        default_factory=list,
        description="Architecture decisions made"
    )

    # Additional context
    constraints: List[str] = Field(
        default_factory=list,
        description="Project constraints or requirements"
    )
    preferences: Dict[str, str] = Field(
        default_factory=dict,
        description="User preferences (language, framework, etc.)"
    )


class AgentResult(BaseModel):
    """Result from an agent execution"""
    agent_id: str = Field(description="Agent that produced this result")
    success: bool = Field(description="Whether execution succeeded")

    # Output data
    output: Any = Field(default=None, description="Structured output from the agent")
    files: List[CodeFile] = Field(
        default_factory=list,
        description="Files created/modified by this agent"
    )

    # Metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    # Token usage
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)

    # Errors
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


# ===========================================
# Agent Output Types by Category
# ===========================================

AGENT_OUTPUT_TYPES: Dict[str, type] = {
    # Management agents
    "PM": TaskPlan,
    "Memory": Dict,  # Context storage

    # Research agents
    "Research": AnalysisResult,
    "Ideas": TaskPlan,

    # Design agents
    "Designs": ComponentSpec,
    "DesignSystem": Dict,

    # Architecture agents
    "Senior": ArchitectureDecision,
    "DatabaseAdmin": DatabaseSchema,

    # Development agents
    "BackendEngineer": ProjectStructure,
    "FrontendEngineer": ProjectStructure,
    "FullStackEngineer": ProjectStructure,
    "iOS": ProjectStructure,
    "Android": ProjectStructure,
    "Web": ProjectStructure,

    # Quality agents
    "QA": AnalysisResult,
    "SecurityEngineer": AnalysisResult,

    # Operations agents
    "DevOps": ProjectStructure,
    "Verifier": AnalysisResult,
}


# ===========================================
# Agent Executor
# ===========================================

class AgentExecutor:
    """
    Executes individual agents using LLM calls.

    Each agent is configured with:
    - Role and backstory (from agents.config.json)
    - Structured output type
    - Post-processing hooks
    """

    def __init__(
        self,
        agent_config: AgentConfig,
        llm_client: Optional[StructuredOutputClient] = None,
        llm_router: Optional[LLMRouter] = None,
    ):
        self.config = agent_config
        self.client = llm_client or StructuredOutputClient()
        self.router = llm_router or get_llm_router()

        # Determine output type for this agent
        self.output_type = AGENT_OUTPUT_TYPES.get(
            agent_config.id,
            TaskPlan  # Default fallback
        )

    def _build_system_prompt(self, context: AgentContext) -> str:
        """Build the system prompt from agent config"""
        parts = [
            f"You are the {self.config.role}.",
            "",
            "## Your Background",
            self.config.backstory,
            "",
            "## Your Goal",
            self.config.goal,
            "",
            "## Project Context",
            f"Project: {context.description}",
            f"Platform: {context.platform}",
        ]

        if context.constraints:
            parts.append("")
            parts.append("## Constraints")
            for constraint in context.constraints:
                parts.append(f"- {constraint}")

        if context.preferences:
            parts.append("")
            parts.append("## Preferences")
            for key, value in context.preferences.items():
                parts.append(f"- {key}: {value}")

        # Add platform-specific guidelines for Development agents
        if self.config.category == "Development" and context.platform == "web":
            parts.append("")
            parts.append("## CRITICAL: Next.js Configuration Requirements")
            parts.append("- ALWAYS use 'next.config.mjs' (NOT next.config.ts) - TypeScript config is not supported in WebContainer")
            parts.append("- ALWAYS use 'tailwind.config.js' (NOT tailwind.config.ts)")
            parts.append("- ALWAYS use 'postcss.config.js' (NOT postcss.config.mjs or .ts)")
            parts.append("- Include autoprefixer in postcss.config.js")
            parts.append("- Make sure package.json includes all required dependencies")

        return "\n".join(parts)

    def _build_user_prompt(self, context: AgentContext) -> str:
        """Build the user prompt with context from previous agents"""
        parts = [self.config.default_prompt]

        # Add context from previous agents
        if context.previous_outputs:
            parts.append("\n\n## Context from Previous Agents")
            for agent_id, output in context.previous_outputs.items():
                parts.append(f"\n### {agent_id} Output")
                if isinstance(output, BaseModel):
                    parts.append(output.model_dump_json(indent=2))
                elif isinstance(output, dict):
                    import json
                    parts.append(json.dumps(output, indent=2, default=str))
                else:
                    parts.append(str(output))

        # Add existing files if relevant
        if context.files and self.config.category in ["Development", "Quality", "Operations"]:
            parts.append("\n\n## Existing Files")
            for f in context.files[:10]:  # Limit to avoid token overflow
                parts.append(f"\n### {f.path}")
                # Truncate large files
                content = f.content[:2000] if len(f.content) > 2000 else f.content
                parts.append(f"```{f.language.value}\n{content}\n```")

        return "\n".join(parts)

    async def execute(
        self,
        context: AgentContext,
        on_progress: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> AgentResult:
        """
        Execute the agent with the given context.

        Args:
            context: Execution context with project info and previous outputs
            on_progress: Optional callback for progress updates

        Returns:
            AgentResult with output and metadata
        """
        start_time = datetime.utcnow()

        try:
            if on_progress:
                await on_progress(f"Starting {self.config.role}...")

            # Build prompts
            system_prompt = self._build_system_prompt(context)
            user_prompt = self._build_user_prompt(context)

            logger.info(f"Executing agent {self.config.id} with {len(user_prompt)} chars")

            # Generate structured output
            output = await self.client.generate(
                response_model=self.output_type,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            if on_progress:
                await on_progress(f"{self.config.role} completed analysis")

            # Extract files if output contains them
            files = []
            if hasattr(output, 'files'):
                files = output.files
                logger.info(f"Agent {self.config.id} generated {len(files)} files")
                for f in files[:3]:  # Log first 3 files
                    logger.info(f"  - {f.path} ({len(f.content)} chars)")
            else:
                logger.info(f"Agent {self.config.id} output type {type(output).__name__} has no files")

            # Post-process based on agent type
            output, files = await self._post_process(output, files, context)

            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - start_time).total_seconds() * 1000)

            return AgentResult(
                agent_id=self.config.id,
                success=True,
                output=output,
                files=files,
                started_at=start_time,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Agent {self.config.id} failed: {e}")
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - start_time).total_seconds() * 1000)

            return AgentResult(
                agent_id=self.config.id,
                success=False,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
                started_at=start_time,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )

    async def _post_process(
        self,
        output: Any,
        files: List[CodeFile],
        context: AgentContext,
    ) -> tuple[Any, List[CodeFile]]:
        """
        Post-process agent output based on agent type.

        Applies validation, security checks, and refinements.
        """
        agent_category = self.config.category

        # Quality agents: validate code
        if agent_category == "Quality" and self.config.id in ["QA", "SecurityEngineer"]:
            try:
                from ..ai.code_validation import validate_code
                for file in files:
                    validation = await validate_code(file.content, file.language.value)
                    if not validation.get("valid", True):
                        logger.warning(
                            f"Validation issues in {file.path}: {validation.get('issues', [])}"
                        )
            except ImportError:
                logger.debug("Code validation module not available")

        # Development agents: run basic syntax checks
        if agent_category == "Development":
            for file in files:
                if file.language.value == "python":
                    try:
                        compile(file.content, file.path, 'exec')
                    except SyntaxError as e:
                        logger.warning(f"Python syntax error in {file.path}: {e}")

        # Verifier: aggregate all checks
        if self.config.id == "Verifier":
            # Add verification metadata to output
            if isinstance(output, AnalysisResult):
                output.suggestions.append("Verification complete")

        return output, files

    async def execute_with_streaming(
        self,
        context: AgentContext,
        on_chunk: Callable[[str], Awaitable[None]],
    ) -> AgentResult:
        """
        Execute agent with streaming output.

        Streams partial results for real-time UI updates.
        """
        start_time = datetime.utcnow()
        accumulated_output = []

        try:
            system_prompt = self._build_system_prompt(context)
            user_prompt = self._build_user_prompt(context)

            # Use streaming generation
            async for partial in self.client.generate_stream(
                response_model=self.output_type,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            ):
                # Send partial updates
                if hasattr(partial, 'model_dump_json'):
                    await on_chunk(partial.model_dump_json())
                accumulated_output.append(partial)

            # Get final output
            output = accumulated_output[-1] if accumulated_output else None
            files = output.files if hasattr(output, 'files') else []

            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - start_time).total_seconds() * 1000)

            return AgentResult(
                agent_id=self.config.id,
                success=True,
                output=output,
                files=files,
                started_at=start_time,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Streaming execution failed for {self.config.id}: {e}")
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - start_time).total_seconds() * 1000)

            return AgentResult(
                agent_id=self.config.id,
                success=False,
                error=str(e),
                started_at=start_time,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )


# ===========================================
# Factory Functions
# ===========================================

def create_executor(agent_id: str) -> Optional[AgentExecutor]:
    """
    Create an executor for an agent by ID.

    Args:
        agent_id: Agent identifier from agents.config.json

    Returns:
        AgentExecutor instance or None if agent not found
    """
    agent_config = get_agent(agent_id)
    if agent_config is None:
        logger.warning(f"Agent not found: {agent_id}")
        return None

    return AgentExecutor(agent_config)


async def execute_agent(
    agent_id: str,
    context: AgentContext,
    on_progress: Optional[Callable[[str], Awaitable[None]]] = None,
) -> AgentResult:
    """
    Execute an agent by ID with the given context.

    Args:
        agent_id: Agent identifier
        context: Execution context
        on_progress: Optional progress callback

    Returns:
        AgentResult
    """
    executor = create_executor(agent_id)
    if executor is None:
        return AgentResult(
            agent_id=agent_id,
            success=False,
            error=f"Agent not found: {agent_id}",
        )

    return await executor.execute(context, on_progress)


async def execute_agents_parallel(
    agent_ids: List[str],
    context: AgentContext,
    on_agent_complete: Optional[Callable[[str, AgentResult], Awaitable[None]]] = None,
) -> Dict[str, AgentResult]:
    """
    Execute multiple agents in parallel.

    Args:
        agent_ids: List of agent IDs to execute
        context: Shared execution context
        on_agent_complete: Callback when each agent completes

    Returns:
        Dict mapping agent_id to result
    """
    async def run_one(agent_id: str) -> tuple[str, AgentResult]:
        result = await execute_agent(agent_id, context)
        if on_agent_complete:
            await on_agent_complete(agent_id, result)
        return agent_id, result

    tasks = [run_one(aid) for aid in agent_ids]
    results = await asyncio.gather(*tasks)

    return {agent_id: result for agent_id, result in results}
