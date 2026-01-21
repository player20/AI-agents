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
            parts.append("## CRITICAL: Next.js Configuration Requirements for WebContainer")
            parts.append("- MUST use Next.js version '13.5.6' (NOT 14.x) - version 14 has SWC issues in WebContainer")
            parts.append("- ALWAYS use 'next.config.mjs' (NOT next.config.ts) - TypeScript config is not supported")
            parts.append("- ALWAYS use 'tailwind.config.js' (NOT tailwind.config.ts)")
            parts.append("- ALWAYS use 'postcss.config.js' (NOT postcss.config.mjs or .ts)")
            parts.append("- ALWAYS include '.babelrc' with {\"presets\": [\"next/babel\"]} for WebContainer compatibility")
            parts.append("- In next.config.mjs, set swcMinify: false (do NOT include experimental.appDir - it's default now)")
            parts.append("- Include autoprefixer in postcss.config.js")
            parts.append("- package.json dependencies MUST have: \"next\": \"13.5.6\" (exact version, no caret)")
            parts.append("- NEVER use 'next/font' - it requires SWC which conflicts with Babel")
            parts.append("- For fonts, use Google Fonts via <link> tag in layout.tsx head or @import in globals.css")
            parts.append("")
            parts.append("## React Server Components Rules (CRITICAL)")
            parts.append("- Any file using React hooks (useState, useEffect, useContext, etc.) MUST have 'use client' at the very top")
            parts.append("- Any file using browser APIs (window, document, localStorage) MUST have 'use client' at the top")
            parts.append("- If page.tsx uses useState or any hook, add 'use client' as the FIRST line before any imports")
            parts.append("- layout.tsx should stay as Server Component (no 'use client') - wrap children with client ErrorBoundary")
            parts.append("- Components with onClick, onChange, or any event handlers MUST have 'use client'")
            parts.append("- NEVER export 'metadata' from a 'use client' file - metadata exports only work in Server Components")
            parts.append("- Use 'next/navigation' for useRouter, usePathname, useSearchParams (NOT 'next/router' which is for Pages Router)")
            parts.append("")
            parts.append("## Common Mistakes to Avoid")
            parts.append("- NEVER use next/image - use regular <img> tags instead (next/image has WebContainer issues)")
            parts.append("- NEVER access window, document, or localStorage at module level - only inside useEffect or event handlers")
            parts.append("- ALWAYS include ALL imported packages in package.json dependencies before using them")
            parts.append("- tsconfig.json MUST have: paths: { '@/*': ['./src/*'] } for @/ import aliases to work")
            parts.append("- tsconfig.json MUST have: resolveJsonModule: true if importing JSON files")
            parts.append("- NEVER mix Pages Router (pages/) with App Router (app/) - use App Router only")
            parts.append("")
            parts.append("## Tailwind CSS Rules")
            parts.append("- ONLY use standard Tailwind classes (bg-blue-500, text-white, p-4, etc.)")
            parts.append("- NEVER use shadcn/ui style classes like 'border-border', 'bg-background', 'text-foreground' unless defined in tailwind.config.js")
            parts.append("- If using CSS variables, define them in globals.css AND extend them in tailwind.config.js")
            parts.append("- globals.css should ONLY contain: @tailwind base; @tailwind components; @tailwind utilities; and optional @import for fonts")
            parts.append("- DO NOT add @layer rules with undefined classes in globals.css")
            parts.append("")
            parts.append("## Error Handling Requirements (CRITICAL for visibility)")
            parts.append("- Create src/components/ErrorBoundary.tsx with 'use client' directive containing an ErrorBoundary class component")
            parts.append("- ErrorBoundary MUST render errors with high-contrast colors (red background #dc2626, white text, 20px padding, minHeight 100vh)")
            parts.append("- In layout.tsx, import ErrorBoundary and wrap {children} with it (layout.tsx stays as Server Component)")
            parts.append("- In layout.tsx <head>, add error reporting: <script dangerouslySetInnerHTML={{__html: `window.onerror=function(m){window.parent?.postMessage({type:'preview-error',message:m},'*')}`}} />")
            parts.append("- page.tsx MUST have visible content even if Tailwind CSS fails to load (use inline styles as fallback)")
            parts.append("- NEVER return null, undefined, or empty JSX from page components")
            parts.append("- ALWAYS wrap main page content with: style={{ minHeight: '100vh', background: '#0f172a', color: 'white' }}")
            parts.append("- Include both Tailwind classes AND inline style fallbacks for critical visibility")

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

        Applies validation, security checks, test generation, and refinements.
        """
        agent_category = self.config.category

        # Quality agents: validate code and generate tests
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

            # Generate tests for QA agent
            if self.config.id == "QA":
                try:
                    from ..ai.test_generator import TestGenerator, TestFramework
                    test_gen = TestGenerator()
                    for file in files:
                        if file.language.value in ["python", "typescript", "javascript"]:
                            try:
                                test_suite = test_gen.generate_tests(
                                    file.content,
                                    file.language.value,
                                    coverage_target=0.8,
                                    include_edge_cases=True
                                )
                                # Generate test file
                                framework = TestFramework.PYTEST if file.language.value == "python" else TestFramework.VITEST
                                test_code = test_suite.to_code(framework, file.language.value)
                                if test_code:
                                    # Add test file to output
                                    test_path = self._get_test_path(file.path, file.language.value)
                                    files.append(CodeFile(
                                        path=test_path,
                                        content=test_code,
                                        language=file.language,
                                        description=f"Auto-generated tests for {file.path}"
                                    ))
                                    logger.info(f"Generated test file: {test_path}")
                            except Exception as e:
                                logger.warning(f"Test generation failed for {file.path}: {e}")
                except ImportError:
                    logger.debug("Test generator module not available")

        # Development agents: run validation and syntax checks
        if agent_category == "Development":
            try:
                from ..ai.code_validation import CodeValidationPipeline
                validator = CodeValidationPipeline()
                for file in files:
                    try:
                        result = await validator.validate(file.content, file.language.value)
                        if result.issues:
                            logger.warning(f"Validation issues in {file.path}: {len(result.issues)} issues")
                    except Exception as e:
                        logger.debug(f"Validation skipped for {file.path}: {e}")
            except ImportError:
                logger.debug("Code validation pipeline not available")

            # Basic syntax checks as fallback
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

    def _get_test_path(self, source_path: str, language: str) -> str:
        """Generate test file path from source file path"""
        import os
        dir_name = os.path.dirname(source_path)
        base_name = os.path.basename(source_path)
        name, ext = os.path.splitext(base_name)

        if language == "python":
            return os.path.join(dir_name, f"test_{name}{ext}")
        else:
            # JavaScript/TypeScript: use .test.ts/.test.js pattern
            return os.path.join(dir_name, f"{name}.test{ext}")

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
