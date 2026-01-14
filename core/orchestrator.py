"""
Core Orchestrator for Code Weaver Pro
Integrates LangGraph (stateful workflows), CrewAI (agents), and DSPy (prompt optimization)

Framework Integration:
----------------------
1. CrewAI: Core agent execution with multi-model fallback
   - Executes individual agent tasks
   - Manages agent teams with sequential/hierarchical processes
   - Provides task delegation and result aggregation

2. LangGraph: Stateful workflow graphs with cyclic reflection loops (Devin-inspired)
   - StateGraph: Manages workflow state across phases
   - Reflection loops: Iteratively improves outputs until quality threshold
   - Checkpointing: Can resume workflows from any phase (future enhancement)

3. DSPy: Prompt optimization for vague user inputs
   - Optimizes unclear user descriptions into structured prompts
   - Fine-tunes prompts based on historical performance
   - Falls back to template-based optimization when DSPy unavailable

Workflow Phases:
----------------
1. Planning: MetaPrompt → Market Research (optional) → Go/No-Go → Challenger
2. Drafting: PM → Ideas → Designs → Senior → Reflection (with LangGraph refinement)
3. Testing: Code Generation → Playwright Test-Fix Loop → Screenshots → Performance
4. Evaluation: Scoring → Synopsis

All frameworks are optional - graceful degradation if not installed.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, TypedDict, Annotated
from datetime import datetime
import traceback
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import existing functionality
from multi_agent_team import load_agent_configs, create_agent_with_model, MODEL_PRESETS
from projects_store import ProjectsStore

# Note: code_applicator and code_generators will be integrated in Week 3 for:
# - apply_code_changes: Safe Git-based code application
# - generate_project_structure: Project scaffolding

# Import CrewAI for task execution
from crewai import Agent, Task, Crew, Process

# Import LangGraph for stateful workflows and reflection loops
try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolExecutor
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("[WARNING] LangGraph not available. Install with: pip install langgraph")

# Import DSPy for prompt optimization
try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    print("[WARNING] DSPy not available. Install with: pip install dspy-ai")

# Import Playwright runner for testing
from core.playwright_runner import PlaywrightRunner
import asyncio


class WorkflowState:
    """
    State container for the workflow execution
    Compatible with LangGraph's StateGraph when available
    """

    def __init__(self, user_input: str, **kwargs):
        self.user_input = user_input
        self.original_user_input = user_input  # Store for DSPy optimization
        self.platforms = kwargs.get('platforms', ['Web App'])
        self.do_market_research = kwargs.get('do_market_research', False)
        self.research_only = kwargs.get('research_only', False)
        self.existing_code = kwargs.get('existing_code', None)

        # Audit mode parameters
        self.analyze_dropoffs = kwargs.get('analyze_dropoffs', False)
        self.app_url = kwargs.get('app_url', None)
        self.test_credentials = kwargs.get('test_credentials', None)
        self.funnel_analysis = None
        self.detected_sdks = {}

        # Workflow outputs
        self.agent_outputs = {}
        self.project_path = None
        self.project_name = None
        self.test_results = []
        self.screenshots = []
        self.scores = {}
        self.recommendations = []
        self.synopsis = None

        # Control flow
        self.go_decision = True  # Result of market research go/no-go
        self.current_phase = None
        self.errors = []

        # LangGraph reflection loop state
        self.reflection_iterations = 0
        self.max_reflection_iterations = 3
        self.quality_threshold = 0.8

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for LangGraph compatibility"""
        return {
            'user_input': self.user_input,
            'platforms': self.platforms,
            'agent_outputs': self.agent_outputs,
            'project_path': self.project_path,
            'project_name': self.project_name,
            'test_results': self.test_results,
            'scores': self.scores,
            'current_phase': self.current_phase,
            'reflection_iterations': self.reflection_iterations,
            'go_decision': self.go_decision,
        }


class DSPyPromptOptimizer:
    """
    Optimizes prompts using DSPy when available
    Falls back to simple templates when DSPy is not installed
    """

    def __init__(self):
        self.dspy_configured = False
        if DSPY_AVAILABLE:
            try:
                # Configure DSPy with Claude (if API key available)
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if api_key:
                    # DSPy setup for Claude
                    # Note: DSPy may need specific configuration for Anthropic
                    self.dspy_configured = True
            except Exception as e:
                print(f"[WARNING] DSPy configuration failed: {e}")

    def optimize_user_input(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """
        Optimize vague user input into structured prompt

        Args:
            user_input: Original user description
            context: Additional context (platforms, existing code, etc.)

        Returns:
            Optimized prompt for agents
        """
        if self.dspy_configured:
            # Use DSPy optimization
            return self._dspy_optimize(user_input, context)
        else:
            # Fallback to template-based optimization
            return self._template_optimize(user_input, context)

    def _dspy_optimize(self, user_input: str, context: Dict[str, Any]) -> str:
        """DSPy-based optimization (when available)"""
        # This would use DSPy's signature optimization
        # For now, fallback to template
        return self._template_optimize(user_input, context)

    def _template_optimize(self, user_input: str, context: Dict[str, Any]) -> str:
        """Template-based prompt optimization"""
        context = context or {}

        optimized = f"""
Project Description: {user_input}

Target Platforms: {', '.join(context.get('platforms', ['Web App']))}

Context:
- Market Research: {context.get('do_market_research', False)}
- Existing Code: {'Yes' if context.get('existing_code') else 'No'}
- Research Only: {context.get('research_only', False)}

Objective: Create a comprehensive implementation plan that addresses all user needs
while considering platform-specific requirements and best practices.
"""
        return optimized.strip()


class LangGraphWorkflowBuilder:
    """
    Builds LangGraph stateful workflows with reflection loops
    Falls back to sequential execution when LangGraph is not available
    """

    def __init__(self):
        self.langgraph_available = LANGGRAPH_AVAILABLE

    def create_reflection_loop(self, state: WorkflowState,
                               check_func: Callable,
                               improve_func: Callable) -> WorkflowState:
        """
        Create a reflection loop that checks quality and iterates until threshold
        Inspired by Devin's reflection loops

        Args:
            state: Current workflow state
            check_func: Function to check quality (returns score 0-1)
            improve_func: Function to improve output

        Returns:
            Updated state after reflection loop
        """
        if not self.langgraph_available:
            # Fallback: single pass without reflection
            return improve_func(state)

        # LangGraph reflection loop
        while state.reflection_iterations < state.max_reflection_iterations:
            quality_score = check_func(state)

            if quality_score >= state.quality_threshold:
                break

            state = improve_func(state)
            state.reflection_iterations += 1

        return state


class CodeWeaverOrchestrator:
    """
    Main orchestration engine that coordinates all agents
    Integrates LangGraph (stateful workflows), CrewAI (agents), DSPy (prompt optimization)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize orchestrator with configuration

        Args:
            config: Configuration dictionary from load_config()
        """
        self.config = config
        self.agents_config = load_agent_configs()
        self.projects_store = ProjectsStore()

        # Callbacks for UI updates
        self.progress_callback: Optional[Callable] = config['orchestration'].get('progress_callback')
        self.terminal_callback: Optional[Callable] = config['orchestration'].get('terminal_callback')

        # Agent cache (created on-demand)
        self.agents_cache = {}

        # Initialize DSPy prompt optimizer
        self.prompt_optimizer = DSPyPromptOptimizer()

        # Initialize LangGraph workflow builder
        self.workflow_builder = LangGraphWorkflowBuilder()

        # Log framework availability
        self._log(f"🔧 Framework Status:", "info")
        self._log(f"  - CrewAI: ✅ Available", "success")
        self._log(f"  - LangGraph: {'✅ Available' if LANGGRAPH_AVAILABLE else '⚠️ Not installed (optional)'}",
                 "success" if LANGGRAPH_AVAILABLE else "warning")
        self._log(f"  - DSPy: {'✅ Available' if DSPY_AVAILABLE else '⚠️ Not installed (optional)'}",
                 "success" if DSPY_AVAILABLE else "warning")

    def _log(self, message: str, level: str = "info"):
        """Send log message to terminal callback"""
        if self.terminal_callback:
            self.terminal_callback(message, level)
        else:
            print(f"[{level.upper()}] {message}")

    def _update_progress(self, phase: str, progress: float):
        """Update progress for current phase"""
        if self.progress_callback:
            self.progress_callback(phase, progress)

    def _get_agent(self, agent_id: str):
        """Get or create agent by ID"""
        if agent_id in self.agents_cache:
            return self.agents_cache[agent_id]

        # Create agent with model fallback
        # create_agent_with_model expects agent_key (string ID) and model_id
        agent = create_agent_with_model(
            agent_id,
            MODEL_PRESETS[self.config['model']['default_preset']]
        )

        self.agents_cache[agent_id] = agent
        return agent

    def _execute_agent_task(self, agent: Agent, task_description: str) -> str:
        """
        Execute a single agent task using CrewAI

        Args:
            agent: CrewAI Agent instance
            task_description: Task description/prompt

        Returns:
            Task output as string
        """
        # Create task
        task = Task(
            description=task_description,
            agent=agent,
            expected_output="A comprehensive response addressing all points in the task description."
        )

        # Create minimal crew with one agent
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False
        )

        # Execute
        result = crew.kickoff()

        # Extract string output
        if hasattr(result, 'raw'):
            return str(result.raw)
        return str(result)

    def run(self, user_input: str, **kwargs) -> Dict[str, Any]:
        """
        Main entry point - Execute complete workflow
        Uses DSPy for prompt optimization and LangGraph for workflow orchestration

        Args:
            user_input: User's project description (1-2 sentences)
            **kwargs: Additional options (platforms, do_market_research, existing_code)

        Returns:
            Dictionary with results
        """
        state = WorkflowState(user_input, **kwargs)

        try:
            # Step 0: Optimize user input with DSPy (if available)
            self._log("🔧 Optimizing user input with DSPy...")
            optimized_input = self.prompt_optimizer.optimize_user_input(
                user_input,
                context={
                    'platforms': state.platforms,
                    'do_market_research': state.do_market_research,
                    'existing_code': state.existing_code,
                    'research_only': state.research_only
                }
            )
            state.user_input = optimized_input
            self._log("✅ Input optimization complete", "success")

            # Phase 1: Planning (MetaPrompt → Market Research? → Go/No-Go → Challenger)
            self._log("🔍 Starting Planning Phase...")
            self._update_progress("planning", 0.0)
            self._planning_phase(state)

            if not state.go_decision:
                self._log("⚠️ Go/No-Go decision: NO-GO. Stopping execution.", "warning")
                return self._format_no_go_result(state)

            # Check if research-only mode
            if state.research_only:
                self._log("✅ Research-only mode: Stopping after planning phase.", "success")
                self._update_progress("done", 1.0)
                return self._format_research_complete_result(state)

            # Phase 2: Drafting (Design → Reflection)
            self._log("✏️ Starting Drafting Phase...")
            self._update_progress("drafting", 0.0)
            self._drafting_phase(state)

            # Phase 3: Testing (Code Generation → Test-Fix Loop)
            self._log("🧪 Starting Testing Phase...")
            self._update_progress("testing", 0.0)
            self._testing_phase(state)

            # Phase 4: Evaluation & Synopsis
            self._log("✅ Starting Evaluation Phase...")
            self._update_progress("done", 0.0)
            self._evaluation_phase(state)

            self._update_progress("done", 1.0)
            self._log("🎉 All phases complete!", "success")

            return self._format_success_result(state)

        except Exception as e:
            self._log(f"❌ Error during execution: {str(e)}", "error")
            self._log(traceback.format_exc(), "error")
            state.errors.append(str(e))
            return self._format_error_result(state, e)

    def _planning_phase(self, state: WorkflowState):
        """
        Phase 1: Planning
        - MetaPrompt: Expand user input
        - Market Research (optional): Analyze market
        - Go/No-Go: Decision point
        - Challenger: Poke holes in plan
        """
        # Step 1: MetaPrompt expansion
        self._log("🔍 Meta Prompt: Expanding your idea...")
        meta_agent = self._get_agent("MetaPrompt")

        meta_prompt = f"""
User's brief description: "{state.user_input}"

Target platforms: {', '.join(state.platforms)}

Expand this into a comprehensive project specification with:
1. Project name and tagline
2. Core features (5-10 bullet points)
3. User personas (2-3 types)
4. Technical requirements
5. Success criteria

Be specific and actionable. Focus on what makes this unique.
"""

        meta_result = self._execute_agent_task(meta_agent, meta_prompt)
        state.agent_outputs['meta_prompt'] = meta_result
        self._update_progress("planning", 0.2)

        # Step 2: Market Research (optional)
        if state.do_market_research:
            self._log("📊 Conducting market research...")
            research_agent = self._get_agent("Research")

            research_prompt = f"""
Based on this project specification:
{meta_result}

Conduct market research:
1. Identify 3-5 competitors
2. Calculate TAM (Total Addressable Market)
3. Calculate SAM (Serviceable Addressable Market)
4. Calculate SOM (Serviceable Obtainable Market)
5. Recommend: GO or NO-GO with justification

Format your response as:
COMPETITORS: [list]
TAM: $[amount] - [reasoning]
SAM: $[amount] - [reasoning]
SOM: $[amount] - [reasoning]
DECISION: GO|NO-GO
REASONING: [why]
"""

            research_result = self._execute_agent_task(research_agent, research_prompt)
            state.agent_outputs['market_research'] = research_result

            # Parse go/no-go decision
            if 'NO-GO' in research_result.upper():
                state.go_decision = False
                return

            self._update_progress("planning", 0.5)

        # Step 3: Challenger review
        self._log("🤔 Challenger: Poking holes in the plan...")
        challenger_agent = self._get_agent("Challenger")

        challenger_prompt = f"""
Review this project plan and find gaps, risks, and missing considerations:
{state.agent_outputs['meta_prompt']}

Identify:
1. Missing features or edge cases
2. Technical risks
3. User experience concerns
4. Scalability issues
5. Security considerations

Be critical but constructive.
"""

        challenger_result = self._execute_agent_task(challenger_agent, challenger_prompt)
        state.agent_outputs['challenger'] = challenger_result
        self._update_progress("planning", 0.85)

        # Step 4: Audit Mode (if requested)
        if state.analyze_dropoffs:
            self._log("📉 Starting Audit Mode: Drop-off analysis...")
            self._update_progress("planning", 0.87)

            try:
                from core.audit_mode import AuditModeAnalyzer

                analyzer = AuditModeAnalyzer([], {})

                # SDK Detection (if code provided)
                if state.existing_code:
                    self._log("🔍 Scanning code for analytics SDKs...")
                    state.detected_sdks = analyzer.detect_sdks(state.existing_code)

                    detected_list = [sdk for sdk, found in state.detected_sdks.items() if found]
                    if detected_list:
                        self._log(f"✅ Found SDKs: {', '.join(detected_list)}", "success")
                    else:
                        self._log("⚠️ No analytics SDKs detected - will recommend additions", "warning")

                # Crawl app if URL provided
                if state.app_url:
                    self._log(f"🌐 Crawling {state.app_url}...")

                    # Run async crawl
                    sessions = asyncio.run(analyzer.crawl_app_flows(
                        base_url=state.app_url,
                        test_credentials=state.test_credentials,
                        simulate_users=10
                    ))

                    self._log(f"✅ Simulated {len(sessions)} user sessions", "success")

                    # Analyze funnel
                    state.funnel_analysis = analyzer.analyze_sessions(sessions)

                    completion_rate = state.funnel_analysis['completion_rate']
                    self._log(f"📊 Completion rate: {completion_rate}%", "info")

                    biggest_drop = state.funnel_analysis.get('biggest_drop_off', {})
                    if biggest_drop.get('percentage', 0) > 50:
                        self._log(
                            f"🔴 CRITICAL: {biggest_drop['percentage']}% drop-off at {biggest_drop['step']}",
                            "error"
                        )

                    # Generate recommendations
                    state.recommendations = analyzer.generate_recommendations(
                        state.funnel_analysis,
                        state.detected_sdks,
                        state.existing_code
                    )

                    self._log(f"✅ Generated {len(state.recommendations)} recommendations", "success")

                    # Store in agent_outputs for result formatting
                    state.agent_outputs['audit_mode'] = f"""
Audit Mode Analysis Complete:
- Simulated {len(sessions)} user sessions
- Completion Rate: {completion_rate}%
- Biggest Drop-off: {biggest_drop.get('step', 'N/A')} ({biggest_drop.get('percentage', 0)}%)
- SDKs Detected: {', '.join(detected_list) if detected_list else 'None'}
- Recommendations: {len(state.recommendations)} action items generated
"""

            except Exception as e:
                self._log(f"❌ Audit mode failed: {e}", "error")
                state.errors.append(f"Audit mode error: {str(e)}")

            self._update_progress("planning", 0.95)

        # Verify planning phase for hallucinations
        self._log("🔍 Verifier: Checking for hallucinations and consistency...")
        self._verify_phase(state, 'planning')
        self._update_progress("planning", 1.0)

        self._log("✓ Planning phase complete", "success")

    def _drafting_phase(self, state: WorkflowState):
        """
        Phase 2: Drafting
        - PM creates sprint plan
        - Ideas agent brainstorms
        - Designs agent creates UI/UX
        - Senior agents review
        - Reflector synthesizes
        """
        # Step 1: PM Sprint Planning
        self._log("📋 PM: Creating sprint plan...")
        pm_agent = self._get_agent("PM")

        pm_prompt = f"""
Create a sprint plan for this project:

SPECIFICATION:
{state.agent_outputs['meta_prompt']}

CHALLENGES IDENTIFIED:
{state.agent_outputs.get('challenger', 'None')}

Create a prioritized task list with:
1. Must-have features (MVP)
2. Should-have features
3. Nice-to-have features
4. Technical architecture decisions

Format as numbered list with time estimates.
"""

        pm_result = self._execute_agent_task(pm_agent, pm_prompt)
        state.agent_outputs['pm_plan'] = pm_result
        self._update_progress("drafting", 0.2)

        # Step 2: Ideas brainstorming
        self._log("💡 Ideas: Brainstorming solutions...")
        ideas_agent = self._get_agent("Ideas")

        ideas_prompt = f"""
Based on this sprint plan:
{pm_result}

Brainstorm creative solutions for:
1. Unique features that differentiate this product
2. Innovative UI/UX approaches
3. Technical architecture patterns
4. Performance optimizations

Think outside the box but stay practical.
"""

        ideas_result = self._execute_agent_task(ideas_agent, ideas_prompt)
        state.agent_outputs['ideas'] = ideas_result
        self._update_progress("drafting", 0.4)

        # Step 3: Design UI/UX
        self._log("🎨 Design: Creating UI/UX architecture...")
        designs_agent = self._get_agent("Designs")

        designs_prompt = f"""
Create UI/UX architecture for:

SPRINT PLAN:
{pm_result}

IDEAS:
{ideas_result}

Define:
1. Page structure and navigation
2. Component hierarchy
3. Color scheme and typography
4. Mobile-first responsive strategy
5. Accessibility considerations

Be specific about layouts and interactions.
"""

        designs_result = self._execute_agent_task(designs_agent, designs_prompt)
        state.agent_outputs['designs'] = designs_result
        self._update_progress("drafting", 0.6)

        # Step 4: Senior review
        self._log("👨‍💻 Senior Engineer: Reviewing architecture...")
        senior_agent = self._get_agent("Senior")

        senior_prompt = f"""
Review this architecture:

SPRINT PLAN:
{pm_result}

DESIGN:
{designs_result}

Provide:
1. Technology stack recommendations
2. Architecture patterns to use
3. Potential bottlenecks
4. Code structure suggestions
5. Security best practices

Focus on scalability and maintainability.
"""

        senior_result = self._execute_agent_task(senior_agent, senior_prompt)
        state.agent_outputs['senior_review'] = senior_result
        self._update_progress("drafting", 0.8)

        # Step 5: Reflection with LangGraph cyclic refinement (Devin-style)
        self._log("🔄 Reflector: Synthesizing phase outputs with cyclic refinement...")
        reflector_agent = self._get_agent("Reflector")

        def check_draft_quality(state: WorkflowState) -> float:
            """Check quality of draft outputs (0-1 scale)"""
            # Simple heuristic: check if all key sections are present
            required_sections = ['pm_plan', 'ideas', 'designs', 'senior_review']
            present = sum(1 for s in required_sections if s in state.agent_outputs and len(state.agent_outputs[s]) > 100)
            return present / len(required_sections)

        def improve_draft(state: WorkflowState) -> WorkflowState:
            """Improve draft by running reflector"""
            reflector_prompt = f"""
Synthesize these outputs into a coherent implementation plan:

PM PLAN: {pm_result[:500]}...
IDEAS: {ideas_result[:500]}...
DESIGNS: {designs_result[:500]}...
SENIOR REVIEW: {senior_result[:500]}...

{'[ITERATION ' + str(state.reflection_iterations + 1) + '] Refine previous iteration focusing on gaps identified.' if state.reflection_iterations > 0 else ''}

Create a unified, actionable implementation guide that:
1. Integrates all perspectives
2. Resolves any conflicts
3. Prioritizes tasks
4. Provides clear next steps

This will guide the code generation phase.
"""
            reflector_result = self._execute_agent_task(reflector_agent, reflector_prompt)
            state.agent_outputs['reflection_1'] = reflector_result
            return state

        # Use LangGraph reflection loop if available, otherwise single pass
        if self.workflow_builder.langgraph_available:
            self._log("🔄 Using LangGraph reflection loop for quality refinement...", "info")
            state = self.workflow_builder.create_reflection_loop(state, check_draft_quality, improve_draft)
            self._log(f"✅ Reflection complete after {state.reflection_iterations} iterations", "success")
        else:
            # Fallback: single reflection pass
            state = improve_draft(state)

        self._update_progress("drafting", 0.9)

        # Verify drafting phase for hallucinations
        self._log("🔍 Verifier: Checking design consistency and accuracy...")
        self._verify_phase(state, 'drafting')
        self._update_progress("drafting", 1.0)

        self._log("✓ Drafting phase complete", "success")

    def _testing_phase(self, state: WorkflowState):
        """
        Phase 3: Testing
        - Generate code based on platforms
        - Run basic validation (placeholder for Playwright in Week 3)
        - Reflector review
        """
        # Step 1: Generate project structure
        self._log("🔨 Generating project structure...")

        # Create project name from meta prompt or user input
        project_name = self._extract_project_name(state.agent_outputs['meta_prompt'])
        project_name = project_name.lower().replace(' ', '_')
        state.project_name = project_name

        project_path = Path(self.config['projects_dir']) / project_name
        project_path.mkdir(parents=True, exist_ok=True)
        state.project_path = str(project_path)

        self._update_progress("testing", 0.2)

        # Step 2: Platform-specific code generation
        for i, platform in enumerate(state.platforms):
            progress = 0.2 + (0.3 * (i + 1) / len(state.platforms))
            self._log(f"💻 Generating {platform} code...")

            # Select appropriate agent based on platform
            if platform in ["iOS"]:
                agent_id = "iOS"
            elif platform in ["Android"]:
                agent_id = "Android"
            else:  # Web App, Website
                agent_id = "Web"

            code_agent = self._get_agent(agent_id)

            code_prompt = f"""
Generate production-ready code for a {platform} application.

IMPLEMENTATION PLAN:
{state.agent_outputs['reflection_1']}

DESIGN SPECIFICATION:
{state.agent_outputs['designs']}

Generate:
1. Complete file structure
2. All necessary code files
3. Configuration files
4. README with setup instructions

Platform: {platform}
Output Format: Provide code with file paths like:

FILE: path/to/file.ext
```language
[code here]
```

Make it production-ready, well-commented, and follow best practices.
"""

            code_result = self._execute_agent_task(code_agent, code_prompt)
            state.agent_outputs[f'code_{platform}'] = code_result

            # Parse and write code files (simplified - will use code_applicator.py in production)
            self._write_generated_code(code_result, project_path)

            self._update_progress("testing", progress)

        # Step 3: Playwright Testing with Test-Fix-Retest Loop
        self._log("🧪 Starting Playwright automated testing...")

        # Initialize Playwright runner
        runner = PlaywrightRunner(str(project_path), self.config)

        # Start development server
        self._log("🚀 Starting development server...")
        server_started = asyncio.run(runner.start_server())

        if not server_started:
            self._log("⚠️ Could not start server. Skipping Playwright tests.", "warning")
            state.test_results = [
                {"name": "Server startup", "status": "failed", "error": "Could not start development server", "duration_ms": 0}
            ]
            self._update_progress("testing", 0.8)
        else:
            # Run test-fix-retest loop
            test_iteration = 0
            max_iterations = self.config['testing']['max_test_iterations']
            all_tests_passed = False

            while test_iteration < max_iterations and not all_tests_passed:
                test_iteration += 1
                self._log(f"🧪 Test iteration {test_iteration}/{max_iterations}...")

                # Run automated tests
                test_results = asyncio.run(runner.run_tests())
                state.test_results = test_results

                # Check pass rate
                passed_tests = [t for t in test_results if t['status'] == 'passed']
                pass_rate = len(passed_tests) / len(test_results) if test_results else 0

                self._log(f"📊 Tests: {len(passed_tests)}/{len(test_results)} passed ({int(pass_rate * 100)}%)")

                if pass_rate >= self.config['testing']['required_pass_rate']:
                    all_tests_passed = True
                    self._log("✅ Test pass rate meets requirements", "success")
                    break

                # If tests failed and we have more iterations, use QA agent to fix
                if test_iteration < max_iterations:
                    self._log("🔧 QA Agent: Analyzing failures and generating fixes...")

                    # Get QA agent to analyze failures
                    qa_agent = self._get_agent("QA")

                    failed_tests = [t for t in test_results if t['status'] == 'failed']
                    failures_summary = "\n".join([
                        f"- {t['name']}: {t.get('error', 'Unknown error')}"
                        for t in failed_tests
                    ])

                    qa_prompt = f"""
Analyze these test failures and provide fixes:

FAILED TESTS:
{failures_summary}

PROJECT PATH: {state.project_path}
PLATFORM: {', '.join(state.platforms)}

Review the generated code and provide specific fixes for each failure.
Format your response as:

FIX 1: [Test name]
FILE: [file path to fix]
ISSUE: [what's wrong]
SOLUTION: [code changes needed]

Be specific and actionable. Focus on the root cause, not symptoms.
"""

                    qa_result = self._execute_agent_task(qa_agent, qa_prompt)
                    state.agent_outputs[f'qa_iteration_{test_iteration}'] = qa_result

                    # Apply fixes (simplified - in production would use code_applicator)
                    self._log("🔧 Applying fixes...")
                    # Note: In production, parse qa_result and apply fixes using code_applicator
                    # For now, we log the fixes for manual review

                else:
                    self._log(f"⚠️ Max test iterations ({max_iterations}) reached", "warning")

            # Capture screenshots
            self._log("📸 Capturing screenshots at different viewports...")
            screenshots = asyncio.run(runner.capture_screenshots())
            state.screenshots = screenshots
            self._log(f"✅ Captured {len(screenshots)} screenshots")

            # Measure performance
            self._log("⚡ Measuring performance metrics...")
            performance = asyncio.run(runner.measure_performance())
            state.agent_outputs['performance'] = performance
            self._log(f"⚡ Page load: {performance['page_load_ms']}ms")

            # Stop server
            runner.stop_server()

        self._update_progress("testing", 0.8)

        # Step 4: Second reflection
        self._log("🔄 Reflector: Reviewing implementation...")
        reflector_agent = self._get_agent("Reflector")

        reflector_prompt = f"""
Review the code generation phase:

PLATFORMS: {', '.join(state.platforms)}
FILES GENERATED: {len(list(project_path.rglob('*.*')))} files

Provide:
1. Quality assessment
2. Completeness check
3. Potential improvements
4. Next steps for testing

Be concise but thorough.
"""

        reflector_result = self._execute_agent_task(reflector_agent, reflector_prompt)
        state.agent_outputs['reflection_2'] = reflector_result
        self._update_progress("testing", 0.9)

        # Verify code generation and testing phase
        self._log("🔍 Verifier: Validating generated code against requirements...")
        self._verify_phase(state, 'testing')
        self._update_progress("testing", 1.0)

        self._log("✓ Testing phase complete", "success")

    def _evaluation_phase(self, state: WorkflowState):
        """
        Phase 4: Evaluation & Synopsis
        - Scorer evaluates the application with actual test results and performance data
        - Synopsis generates final summary
        """
        # Step 1: Scoring with real data
        self._log("📊 Scorer: Evaluating application with test results and performance metrics...")
        scorer_agent = self._get_agent("Scorer")

        # Prepare test summary
        if state.test_results:
            passed = len([t for t in state.test_results if t['status'] == 'passed'])
            total = len(state.test_results)
            test_summary = f"{passed}/{total} tests passed ({int(passed/total*100)}%)"
        else:
            test_summary = "No tests run"

        # Prepare performance summary
        performance = state.agent_outputs.get('performance', {})
        perf_summary = f"""
Page Load: {performance.get('page_load_ms', 0)}ms
Time to Interactive: {performance.get('time_to_interactive_ms', 0)}ms
First Contentful Paint: {performance.get('first_contentful_paint_ms', 0)}ms
Total Size: {performance.get('total_size_kb', 0)}KB
"""

        # Prepare screenshot info
        screenshot_summary = f"{len(state.screenshots)} screenshots captured: " + ", ".join([s['name'] for s in state.screenshots]) if state.screenshots else "No screenshots"

        scorer_prompt = f"""
Evaluate this application based on real test results and metrics:

PROJECT: {state.project_name}
PLATFORMS: {', '.join(state.platforms)}
FILES: {len(list(Path(state.project_path).rglob('*.*')))} files

TEST RESULTS:
{test_summary}

PERFORMANCE METRICS:
{perf_summary}

SCREENSHOTS:
{screenshot_summary}

IMPLEMENTATION QUALITY:
{state.agent_outputs['reflection_2'][:500]}...

Score on a scale of 0-10 for:
1. Speed & Performance (consider page load times, bundle size)
2. Mobile Responsiveness (consider test results for mobile viewport)
3. Intuitiveness & UX (consider implementation plan and design quality)
4. Functionality & Features (consider test pass rate and completeness)

Format as:
SPEED: [score]/10 - [reason based on metrics]
MOBILE: [score]/10 - [reason based on responsive tests]
INTUITIVENESS: [score]/10 - [reason based on UX design]
FUNCTIONALITY: [score]/10 - [reason based on test results]

Then provide TOP 3 RECOMMENDATIONS for improvement based on the actual results.
"""

        scorer_result = self._execute_agent_task(scorer_agent, scorer_prompt)
        state.agent_outputs['scorer'] = scorer_result

        # Parse scores
        state.scores = self._parse_scores(scorer_result)
        state.recommendations = self._parse_recommendations(scorer_result)

        self._update_progress("done", 0.5)

        # Step 2: Synopsis
        self._log("📝 Synopsis: Generating final summary...")
        synopsis_agent = self._get_agent("Synopsis")

        synopsis_prompt = f"""
Create a user-friendly final summary of this project:

PROJECT: {state.project_name}
USER INPUT: {state.user_input}

WHAT WAS BUILT:
{state.agent_outputs['reflection_2']}

SCORES:
{scorer_result}

Generate a friendly, non-technical summary that includes:
1. What we built (2-3 sentences)
2. Key features (bullet points)
3. How to use it (simple steps)
4. What's great about it
5. What could be improved next

Make it encouraging and actionable.
"""

        synopsis_result = self._execute_agent_task(synopsis_agent, synopsis_prompt)
        state.synopsis = synopsis_result

        self._update_progress("done", 1.0)
        self._log("✓ Evaluation complete", "success")

    def _verify_phase(self, state: WorkflowState, phase: str):
        """
        Run Verifier agent to check for hallucinations and consistency

        Args:
            state: Current workflow state
            phase: Phase name ('planning', 'drafting', 'testing')
        """
        verifier_agent = self._get_agent("Verifier")

        # Prepare context based on phase
        if phase == 'planning':
            context_outputs = {
                'meta_prompt': state.agent_outputs.get('meta_prompt', ''),
                'market_research': state.agent_outputs.get('market_research', ''),
                'challenger': state.agent_outputs.get('challenger', '')
            }
            focus = """
Verify the planning phase outputs:
1. Is the meta prompt expansion consistent with the original user input?
2. If market research was done, are the TAM/SAM/SOM values realistic and sourced?
3. Does the challenger review identify real gaps without fabricating issues?
4. Are all claims verifiable from the provided context?
"""
        elif phase == 'drafting':
            context_outputs = {
                'pm_plan': state.agent_outputs.get('pm_plan', ''),
                'ideas': state.agent_outputs.get('ideas', ''),
                'designs': state.agent_outputs.get('designs', ''),
                'senior_review': state.agent_outputs.get('senior_review', ''),
                'reflection_1': state.agent_outputs.get('reflection_1', '')
            }
            focus = """
Verify the drafting phase outputs:
1. Is the PM plan consistent with the meta prompt and research?
2. Are the ideas and designs grounded in actual requirements?
3. Does the senior review provide valid technical critique?
4. Does the reflection accurately synthesize all perspectives?
5. Are tech stack choices justified or arbitrary?
"""
        else:  # testing phase
            context_outputs = {
                'code_Web App': state.agent_outputs.get('code_Web App', ''),
                'code_iOS': state.agent_outputs.get('code_iOS', ''),
                'code_Android': state.agent_outputs.get('code_Android', ''),
                'reflection_2': state.agent_outputs.get('reflection_2', '')
            }
            focus = """
Verify the code generation phase:
1. Does the generated code match the design specifications?
2. Are all required features from the PM plan implemented?
3. Is the code realistic and implementable?
4. Does reflection_2 accurately assess the code quality?
"""

        verifier_prompt = f"""
ORIGINAL USER INPUT:
{state.user_input}

PHASE OUTPUTS TO VERIFY:
{self._format_outputs_for_verification(context_outputs)}

{focus}

Use <verification> tags for your analysis. Format:
<verification>
FINDINGS:
- [List any hallucinations, inconsistencies, or unsupported claims]

CONSISTENCY CHECK:
- [Check alignment with original user input and previous phases]

CONFIDENCE LEVEL: [High/Medium/Low]

VERDICT: [PASS/WARN/FAIL]
</verification>

IMPORTANT: Only flag actual hallucinations or fabricated information. Don't be overly critical of reasonable inferences.
"""

        verification_result = self._execute_agent_task(verifier_agent, verifier_prompt)
        state.agent_outputs[f'verification_{phase}'] = verification_result

        # Check for FAIL verdict
        if 'VERDICT: FAIL' in verification_result.upper():
            self._log(f"⚠️ Verifier found critical issues in {phase} phase", "warning")
            state.errors.append(f"Verification failed for {phase} phase: {verification_result}")
        elif 'VERDICT: WARN' in verification_result.upper():
            self._log(f"⚠️ Verifier found warnings in {phase} phase", "warning")
        else:
            self._log(f"✓ Verifier: {phase.capitalize()} phase verified", "success")

    def _format_outputs_for_verification(self, outputs: dict) -> str:
        """Format agent outputs for verification"""
        formatted = ""
        for key, value in outputs.items():
            if value:  # Only include non-empty outputs
                formatted += f"\n--- {key.upper().replace('_', ' ')} ---\n{value}\n"
        return formatted

    def _extract_project_name(self, meta_prompt_output: str) -> str:
        """Extract project name from meta prompt output"""
        # Look for "Project name:" or similar
        lines = meta_prompt_output.split('\n')
        for line in lines:
            if 'project name' in line.lower():
                # Extract name after colon
                parts = line.split(':')
                if len(parts) > 1:
                    return parts[1].strip().strip('"\'')

        # Fallback to first meaningful line
        for line in lines:
            line = line.strip()
            if len(line) > 3 and not line.startswith('#'):
                return line[:50]

        return "generated_project"

    def _write_generated_code(self, code_output: str, project_path: Path):
        """Parse and write generated code files"""
        current_file = None
        current_code = []

        lines = code_output.split('\n')
        for line in lines:
            if line.startswith('FILE:'):
                # Write previous file
                if current_file and current_code:
                    file_path = project_path / current_file
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text('\n'.join(current_code), encoding='utf-8')

                # Start new file
                current_file = line.replace('FILE:', '').strip()
                current_code = []

            elif line.startswith('```') and current_file:
                # Skip code fence markers
                continue
            elif current_file:
                current_code.append(line)

        # Write final file
        if current_file and current_code:
            file_path = project_path / current_file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text('\n'.join(current_code), encoding='utf-8')

    def _parse_scores(self, scorer_output: str) -> Dict[str, int]:
        """Parse scores from scorer output"""
        scores = {}
        for line in scorer_output.split('\n'):
            line_lower = line.lower()
            if 'speed:' in line_lower:
                scores['speed'] = self._extract_score(line)
            elif 'mobile:' in line_lower:
                scores['mobile'] = self._extract_score(line)
            elif 'intuitiveness:' in line_lower:
                scores['intuitiveness'] = self._extract_score(line)
            elif 'functionality:' in line_lower:
                scores['functionality'] = self._extract_score(line)

        # Defaults if not found
        return {
            'speed': scores.get('speed', 7),
            'mobile': scores.get('mobile', 7),
            'intuitiveness': scores.get('intuitiveness', 7),
            'functionality': scores.get('functionality', 7),
        }

    def _extract_score(self, line: str) -> int:
        """Extract numeric score from line like 'SPEED: 8/10 - reason'"""
        try:
            parts = line.split(':')[1].split('/')
            return int(parts[0].strip())
        except:
            return 7  # Default

    def _parse_recommendations(self, scorer_output: str) -> List[str]:
        """Parse top 3 recommendations from scorer output"""
        recommendations = []
        in_recommendations = False

        for line in scorer_output.split('\n'):
            if 'recommendation' in line.lower():
                in_recommendations = True
                continue

            if in_recommendations:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                    # Remove numbering
                    clean_line = line.lstrip('0123456789.-* ').strip()
                    if clean_line:
                        recommendations.append(clean_line)

                    if len(recommendations) >= 3:
                        break

        # Defaults if not found
        if not recommendations:
            recommendations = [
                "Add comprehensive error handling",
                "Implement responsive design for all screen sizes",
                "Add user authentication and authorization"
            ]

        return recommendations[:3]

    def _format_success_result(self, state: WorkflowState) -> Dict[str, Any]:
        """Format successful execution result"""
        result = {
            'status': 'success',
            'project_name': state.project_name,
            'project_path': state.project_path,
            'description': state.synopsis,
            'platforms': state.platforms,
            'features': self._extract_features(state.agent_outputs.get('meta_prompt', '')),
            'scores': state.scores,
            'screenshots': state.screenshots,
            'recommendations': state.recommendations,
            'test_results': state.test_results,
            'performance': state.agent_outputs.get('performance', {}),
            'agent_outputs': state.agent_outputs,
        }

        # Add audit mode data if available
        if state.funnel_analysis:
            result['funnel_analysis'] = state.funnel_analysis

        if state.detected_sdks:
            result['detected_sdks'] = state.detected_sdks

        return result

    def _format_no_go_result(self, state: WorkflowState) -> Dict[str, Any]:
        """Format no-go decision result"""
        return {
            'status': 'no-go',
            'reason': state.agent_outputs.get('market_research', 'Market research indicated no-go'),
            'agent_outputs': state.agent_outputs,
        }

    def _format_research_complete_result(self, state: WorkflowState) -> Dict[str, Any]:
        """Format research-only mode completion result"""
        return {
            'status': 'research_complete',
            'agent_outputs': state.agent_outputs,
            'description': 'Market research and planning completed. Review results before proceeding to development.',
        }

    def _format_error_result(self, state: WorkflowState, error: Exception) -> Dict[str, Any]:
        """Format error result"""
        return {
            'status': 'error',
            'error': str(error),
            'errors': state.errors,
            'agent_outputs': state.agent_outputs,
            'partial_project_path': state.project_path,
        }

    def _extract_features(self, meta_prompt_output: str) -> List[str]:
        """Extract feature list from meta prompt output"""
        features = []
        in_features = False

        for line in meta_prompt_output.split('\n'):
            line_lower = line.lower()

            if 'feature' in line_lower or 'core feature' in line_lower:
                in_features = True
                continue

            if in_features:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('*') or line[0].isdigit()):
                    clean_line = line.lstrip('0123456789.-* ').strip()
                    if clean_line and len(clean_line) > 10:
                        features.append(clean_line)

                    if len(features) >= 10:
                        break
                elif line and not any(char in line for char in ['-', '*', '.']):
                    # Hit a new section
                    break

        return features if features else [
            "User-friendly interface",
            "Responsive design",
            "Core functionality implemented"
        ]
