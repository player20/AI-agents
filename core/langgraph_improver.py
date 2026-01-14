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
    Evaluate current codebase quality

    Scores the codebase and determines if more iterations are needed.
    """
    from core.self_improver import SelfImprover
    from core.config import load_config

    print(f"\n[EVALUATE] Iteration {state['iteration']}: Evaluating quality...")

    # Simple heuristic scoring
    # Start at current score, add points for fixes, subtract for remaining high-priority issues
    score = state.get('current_score', 5.0)

    # Each fix improves score
    score += state['fixes_applied'] * 0.5

    # Remaining HIGH priority issues lower score
    high_priority_remaining = len([
        issue for issue in state['issues_found']
        if issue.get('severity') == 'HIGH'
    ])
    score -= high_priority_remaining * 0.2

    # Cap at 10
    score = min(10.0, max(0.0, score))

    # Determine if we should continue
    should_continue = (
        score < state['target_score'] and
        state['iteration'] < 10 and  # Max 10 iterations
        state['fixes_applied'] > 0  # Only continue if we're making progress
    )

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
        'should_continue': should_continue,
        'iteration_history': history
    }


def should_continue_improvement(state: ImprovementState) -> str:
    """
    Decision node: Continue improving or stop?

    Returns:
        "continue" if more iterations needed
        "end" if quality threshold reached or max iterations hit
    """
    if state['should_continue']:
        # Increment iteration counter for next loop
        return "continue"
    else:
        return "end"


def create_improvement_graph() -> StateGraph:
    """
    Create the LangGraph workflow for iterative self-improvement

    Flow:
        START → analyze → generate_and_apply → evaluate → should_continue?
                ↑                                              ↓
                └──────────── continue ────────────────────────┘
                                                               ↓
                                                              END
    """
    # Create graph
    workflow = StateGraph(ImprovementState)

    # Add nodes
    workflow.add_node("analyze_issues", analyze_issues_node)
    workflow.add_node("generate_and_apply_fixes", generate_and_apply_fixes_node)
    workflow.add_node("evaluate_quality", evaluate_quality_node)

    # Define edges
    workflow.set_entry_point("analyze_issues")
    workflow.add_edge("analyze_issues", "generate_and_apply_fixes")
    workflow.add_edge("generate_and_apply_fixes", "evaluate_quality")

    # Conditional edge - loop back or end
    workflow.add_conditional_edges(
        "evaluate_quality",
        should_continue_improvement,
        {
            "continue": "analyze_issues",  # Loop back
            "end": END  # Stop
        }
    )

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
        'error_message': ''
    }

    # Run workflow
    config = {"configurable": {"thread_id": "improvement-session-1"}}

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