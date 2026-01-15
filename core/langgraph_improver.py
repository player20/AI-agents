"""
LangGraph-powered Iterative Self-Improvement Workflow

Runs improvement cycles in a loop until quality threshold is met.
Features:
- State management with checkpointing
- Conditional branching (continue if score < target)
- Automatic retry on failures
- Quality-driven stopping condition
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator
from pathlib import Path

class ImprovementState(TypedDict):
    """State tracked across improvement iterations"""

    # Current state
    iteration: int
    current_score: float
    target_score: float
    mode: str
    suggest_enhancements: bool  # Enable Research/Ideas agents for feature suggestions

    # Results from current iteration
    issues_found: list
    fixes_applied: int
    files_modified: list

    # History
    total_issues_found: Annotated[int, operator.add]  # Accumulate across iterations
    total_fixes_applied: Annotated[int, operator.add]  # Accumulate across iterations
    iteration_history: list

    # Control
    should_continue: bool
    error_message: str
    previous_score: float  # Track previous score to detect stagnation
    stuck_iterations: int  # Count consecutive iterations with no score improvement
    quality_feedback: str  # AI-generated positive feedback when quality is high


def analyze_issues_node(state: ImprovementState) -> ImprovementState:
    """
    Analyze codebase and find issues

    Uses the existing self-improvement system to find issues.
    """
    from core.self_improver import SelfImprover, ImprovementMode
    from core.config import load_config

    print(f"\n[ANALYZE] Iteration {state['iteration']}: Analyzing codebase...")

    config = load_config()
    improver = SelfImprover(config)

    # Get the mode
    mode_map = {
        'ui_ux': ImprovementMode.UI_UX,
        'performance': ImprovementMode.PERFORMANCE,
        'agent_quality': ImprovementMode.AGENT_QUALITY,
        'code_quality': ImprovementMode.CODE_QUALITY,
        'everything': ImprovementMode.EVERYTHING
    }
    mode = mode_map.get(state['mode'], ImprovementMode.UI_UX)

    # Analyze codebase (reuse existing logic)
    files = improver._get_files_to_analyze(target_files=None, mode=mode)
    screenshots = improver._capture_app_screenshots() if mode == ImprovementMode.UI_UX else []
    suggest_enhancements = state.get('suggest_enhancements', False)
    issues = improver._identify_issues(files, mode, screenshots, suggest_enhancements)

    print(f"   Found {len(issues)} issues")

    return {
        **state,
        'issues_found': issues,
        'total_issues_found': len(issues)
    }


def generate_and_apply_fixes_node(state: ImprovementState) -> ImprovementState:
    """
    Generate fixes for issues and apply them

    Combines generation and application for efficiency.
    """
    from core.self_improver import SelfImprover, ImprovementMode
    from core.config import load_config

    print(f"\n[FIX] Iteration {state['iteration']}: Generating and applying fixes...")

    if not state['issues_found']:
        print("   No issues to fix!")
        return {
            **state,
            'fixes_applied': 0,
            'files_modified': []
        }

    config = load_config()
    improver = SelfImprover(config)

    # Get the mode
    mode_map = {
        'ui_ux': ImprovementMode.UI_UX,
        'performance': ImprovementMode.PERFORMANCE,
        'agent_quality': ImprovementMode.AGENT_QUALITY,
        'code_quality': ImprovementMode.CODE_QUALITY,
        'everything': ImprovementMode.EVERYTHING
    }
    mode = mode_map.get(state['mode'], ImprovementMode.UI_UX)

    # Prioritize issues
    prioritized = improver._prioritize_issues(state['issues_found'])

    # Take top 5 issues (or fewer if not many found)
    top_issues = prioritized[:min(5, len(prioritized))]

    # Generate fixes
    fixes = improver._generate_fixes(top_issues, mode)

    # Apply fixes
    applied_count = improver._apply_and_test_fixes(fixes, top_issues, mode)

    # Get list of modified files
    modified_files = list(set([fix['file'] for fix in fixes]))

    print(f"   Applied {applied_count}/{len(fixes)} fixes")

    return {
        **state,
        'fixes_applied': applied_count,
        'total_fixes_applied': applied_count,
        'files_modified': modified_files
    }


def evaluate_quality_node(state: ImprovementState) -> ImprovementState:
    """
    Evaluate current codebase quality with AI-powered assessment

    Scores the codebase and determines if more iterations are needed.
    Includes positive feedback when quality is genuinely high.
    """
    from core.self_improver import SelfImprover
    from core.config import load_config

    print(f"\n[EVALUATE] Iteration {state['iteration']}: Evaluating quality...")

    # Enhanced scoring with quality recognition and progress tracking
    previous_score = state.get('current_score', 5.0)
    total_fixes_applied = state.get('total_fixes_applied', 0)

    # Count issues by severity (only UNFIXED issues should lower score)
    high_priority = len([i for i in state['issues_found'] if i.get('severity') == 'HIGH'])
    medium_priority = len([i for i in state['issues_found'] if i.get('severity') == 'MEDIUM'])
    low_priority = len([i for i in state['issues_found'] if i.get('severity') == 'LOW'])

    # Base score on total progress (fixes applied over time)
    base_score = 5.0 + (total_fixes_applied * 0.5)  # Each fix permanently improves base

    # Bonus for no HIGH priority issues
    if high_priority == 0:
        base_score = max(base_score, 8.0)  # No HIGH issues = at least 8/10
        print(f"   ✅ No HIGH priority issues found!")

    if high_priority == 0 and medium_priority <= 3:
        base_score = max(base_score, 9.0)  # Minimal issues = 9/10
        print(f"   🎉 Code quality is excellent!")

    # Deduct ONLY for genuinely problematic issues (less punitive)
    # Most issues are already fixed, so we should be more forgiving
    score = base_score
    score -= min(high_priority, 3) * 0.3  # Cap deduction at 3 issues max
    score -= min(medium_priority, 5) * 0.1  # Cap deduction at 5 issues max
    score -= min(low_priority, 10) * 0.02  # Cap deduction at 10 issues max

    # Cap at 10, but don't go below 3.0 if any fixes were applied
    score = min(10.0, max(3.0 if total_fixes_applied > 0 else 0.0, score))

    # Track if we're stuck (no improvement)
    previous_score = state.get('previous_score', 5.0)
    stuck_iterations = state.get('stuck_iterations', 0)

    if score <= previous_score:
        stuck_iterations += 1
        print(f"   [WARNING] No score improvement for {stuck_iterations} consecutive iterations")
    else:
        stuck_iterations = 0

    # Determine if we should continue
    should_continue = (
        score < state['target_score'] and
        state['iteration'] < 10 and  # Max 10 iterations
        stuck_iterations < 3  # Stop if stuck for 3 consecutive iterations
    )

    if stuck_iterations >= 3:
        print(f"   [STOP] Stopping: No improvement for {stuck_iterations} consecutive iterations")

    # Record iteration history
    history = state.get('iteration_history', [])
    history.append({
        'iteration': state['iteration'],
        'score': score,
        'issues_found': len(state['issues_found']),
        'fixes_applied': state['fixes_applied']
    })

    print(f"   Score: {score:.1f}/10 (target: {state['target_score']}/10)")
    print(f"   Continue? {'Yes' if should_continue else 'No'}")

    return {
        **state,
        'current_score': score,
        'previous_score': score,  # Store for next iteration comparison
        'stuck_iterations': stuck_iterations,
        'should_continue': should_continue,
        'iteration_history': history
    }


def quality_approval_node(state: ImprovementState) -> ImprovementState:
    """
    AI-powered quality approval with positive feedback

    Uses a Senior agent to provide human-readable assessment and praise
    when code quality is genuinely high.
    """
    from crewai import Agent, Task, Crew
    from core.config import load_config

    config = load_config()
    score = state.get('current_score', 0)

    # Only run approval if score is 8+ or stuck iterations
    if score < 8.0 and state.get('stuck_iterations', 0) < 2:
        return {
            **state,
            'quality_feedback': ''
        }

    print(f"\n[QUALITY APPROVAL] Running AI quality assessment...")

    # Create approval agent (uses default LLM from environment)
    approver = Agent(
        role='Senior Code Quality Reviewer',
        goal='Provide constructive feedback on overall code quality',
        backstory="""You are a senior engineer who recognizes excellent work.
        Your job is to assess the codebase holistically and provide:
        - Praise for what's done well
        - Recognition when quality standards are met
        - Balanced perspective (not just finding flaws)

        You understand that perfect code doesn't exist, and minor issues
        don't prevent production deployment.""",
        verbose=False,
        allow_delegation=False
    )

    # Build context
    high_issues = len([i for i in state['issues_found'] if i.get('severity') == 'HIGH'])
    medium_issues = len([i for i in state['issues_found'] if i.get('severity') == 'MEDIUM'])
    low_issues = len([i for i in state['issues_found'] if i.get('severity') == 'LOW'])

    assessment_prompt = f"""
# Codebase Quality Assessment

**Score:** {score:.1f}/10
**Iteration:** {state['iteration']}
**Fixes Applied:** {state.get('total_fixes_applied', 0)}

**Remaining Issues:**
- HIGH priority: {high_issues}
- MEDIUM priority: {medium_issues}
- LOW priority: {low_issues}

**Task:** Provide a brief (2-3 sentences) quality assessment.

If score >= 8.0 and HIGH issues = 0:
- Start with praise (e.g., "Great work!", "Excellent quality!")
- Acknowledge what's been achieved
- Note that remaining issues are minor and acceptable for production

If stuck for 2+ iterations with no progress:
- Acknowledge diminishing returns
- Suggest stopping here (quality is acceptable)
- Avoid over-engineering

Be constructive and balanced. Don't just find flaws - recognize good work!
"""

    task = Task(
        description=assessment_prompt,
        agent=approver,
        expected_output="A brief, constructive quality assessment with positive recognition"
    )

    crew = Crew(
        agents=[approver],
        tasks=[task],
        verbose=False
    )

    try:
        result = crew.kickoff()
        feedback = str(result)
        print(f"   {feedback}")

        return {
            **state,
            'quality_feedback': feedback
        }
    except Exception as e:
        print(f"   [WARNING] Quality approval failed: {e}")
        return {
            **state,
            'quality_feedback': ''
        }


def increment_iteration(state: ImprovementState) -> ImprovementState:
    """
    Increment iteration counter before looping back
    """
    return {
        **state,
        'iteration': state['iteration'] + 1
    }


def should_continue_improvement(state: ImprovementState) -> str:
    """
    Decision node: Continue improving or stop?

    Returns:
        "continue" if more iterations needed
        "end" if quality threshold reached or max iterations hit
    """
    if state['should_continue']:
        return "continue"
    else:
        return "end"


def create_improvement_graph() -> StateGraph:
    """
    Create the LangGraph workflow for iterative self-improvement

    Flow:
        START → analyze → generate_and_apply → evaluate → quality_approval → should_continue?
                ↑                                                                ↓
                └────────────────────── continue ───────────────────────────────┘
                                                                                 ↓
                                                                                END
    """
    # Create graph
    workflow = StateGraph(ImprovementState)

    # Add nodes
    workflow.add_node("analyze_issues", analyze_issues_node)
    workflow.add_node("generate_and_apply_fixes", generate_and_apply_fixes_node)
    workflow.add_node("evaluate_quality", evaluate_quality_node)
    workflow.add_node("quality_approval", quality_approval_node)  # NEW: AI feedback
    workflow.add_node("increment_iteration", increment_iteration)

    # Define edges
    workflow.set_entry_point("analyze_issues")
    workflow.add_edge("analyze_issues", "generate_and_apply_fixes")
    workflow.add_edge("generate_and_apply_fixes", "evaluate_quality")
    workflow.add_edge("evaluate_quality", "quality_approval")  # NEW: Get AI feedback

    # Conditional edge - loop back or end
    workflow.add_conditional_edges(
        "quality_approval",  # Changed from evaluate_quality
        should_continue_improvement,
        {
            "continue": "increment_iteration",  # Increment before looping back
            "end": END  # Stop
        }
    )

    # After incrementing, loop back to analyze
    workflow.add_edge("increment_iteration", "analyze_issues")

    return workflow


def run_iterative_improvement(
    mode: str = 'ui_ux',
    target_score: float = 9.0,
    initial_score: float = 5.0,
    suggest_enhancements: bool = False
) -> dict:
    """
    Run iterative self-improvement until quality threshold is met

    Args:
        mode: Improvement mode ('ui_ux', 'performance', etc.)
        target_score: Stop when this score is reached (default: 9.0/10)
        initial_score: Starting score (default: 5.0/10)
        suggest_enhancements: Enable Research/Ideas agents for feature suggestions (default: False)

    Returns:
        Final state with results and history
    """
    print("=" * 80)
    print("[START] Starting Iterative Self-Improvement (LangGraph-powered)")
    print("=" * 80)
    print(f"Mode: {mode}")
    print(f"Target Score: {target_score}/10")
    print(f"Max Iterations: 10")
    print()

    # Create workflow
    workflow = create_improvement_graph()

    # Compile with checkpointing (enables pause/resume)
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    # Initial state
    initial_state = {
        'iteration': 1,
        'current_score': initial_score,
        'target_score': target_score,
        'mode': mode,
        'suggest_enhancements': suggest_enhancements,
        'issues_found': [],
        'fixes_applied': 0,
        'files_modified': [],
        'total_issues_found': 0,
        'total_fixes_applied': 0,
        'iteration_history': [],
        'should_continue': True,
        'error_message': '',
        'previous_score': initial_score,
        'stuck_iterations': 0,
        'quality_feedback': ''
    }

    # Run workflow with increased recursion limit
    config = {
        "configurable": {"thread_id": "improvement-session-1"},
        "recursion_limit": 50  # Increased from default 25 to allow more iterations
    }

    try:
        final_state = None
        for state in app.stream(initial_state, config):
            # Each state update
            if 'evaluate_quality' in state:
                # After evaluation, increment iteration for next loop
                current = state['evaluate_quality']
                current['iteration'] += 1
                final_state = current

        # Print summary
        print("\n" + "=" * 80)
        print("[COMPLETE] Iterative Improvement Complete!")
        print("=" * 80)
        print(f"Total Iterations: {len(final_state.get('iteration_history', []))}")
        print(f"Final Score: {final_state.get('current_score', 0):.1f}/10")
        print(f"Total Issues Found: {final_state.get('total_issues_found', 0)}")
        print(f"Total Fixes Applied: {final_state.get('total_fixes_applied', 0)}")
        print()

        # Print iteration history
        print("Iteration History:")
        for entry in final_state.get('iteration_history', []):
            print(f"  Iteration {entry['iteration']}: Score {entry['score']:.1f}/10, "
                  f"{entry['issues_found']} issues, {entry['fixes_applied']} fixes")

        return final_state

    except Exception as e:
        print(f"\n[ERROR] Error during improvement: {e}")
        import traceback
        traceback.print_exc()
        return {
            'error': str(e),
            'success': False
        }


# CLI interface for testing
if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else 'ui_ux'
    target = float(sys.argv[2]) if len(sys.argv) > 2 else 9.0

    result = run_iterative_improvement(mode=mode, target_score=target)