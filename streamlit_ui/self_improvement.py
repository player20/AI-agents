"""
Self-Improvement UI for Code Weaver Pro
Allows the system to analyze and improve its own code
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
from typing import TYPE_CHECKING

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

if TYPE_CHECKING:
    from core.self_improver import SelfImprover, ImprovementMode

try:
    from core.self_improver import SelfImprover, ImprovementMode
    from core.config import load_config
    IMPROVER_AVAILABLE = True
except ImportError as e:
    IMPROVER_AVAILABLE = False
    IMPORT_ERROR = str(e)
    SelfImprover = None  # Define as None for type hints if import fails


def render_self_improvement():
    """Render the self-improvement interface"""

    st.markdown("### 🔄 Meta Self-Improvement")
    st.markdown("The system evaluates and improves its own code, UI/UX, and capabilities.")

    if not IMPROVER_AVAILABLE:
        st.error(f"⚠️ Self-improvement engine not available: {IMPORT_ERROR}")
        return

    # Improvement mode selector
    st.markdown("#### Select Improvement Mode")

    mode_options = {
        "🎨 UI/UX": (ImprovementMode.UI_UX, "Make the interface more intuitive and user-friendly"),
        "⚡ Performance": (ImprovementMode.PERFORMANCE, "Speed up execution and optimize resource usage"),
        "🧠 Agent Quality": (ImprovementMode.AGENT_QUALITY, "Improve AI agent outputs and prompts"),
        "🔧 Code Quality": (ImprovementMode.CODE_QUALITY, "Refactor and optimize code structure"),
        "✨ Everything": (ImprovementMode.EVERYTHING, "Comprehensive improvement across all areas")
    }

    cols = st.columns([2, 2], gap="medium")

    with cols[0]:
        selected_mode_label = st.radio(
            "Focus Area",
            list(mode_options.keys()),
            index=4,  # Default to "Everything"
            help="Choose what aspect of the system to improve"
        )

    selected_mode, mode_description = mode_options[selected_mode_label]

    with cols[1]:
        st.info(f"**{selected_mode_label}:** {mode_description}")

        # Show what will be analyzed
        if selected_mode == ImprovementMode.UI_UX:
            st.caption("📁 Will analyze: streamlit_ui/, workflow_builder/src/")
        elif selected_mode == ImprovementMode.PERFORMANCE:
            st.caption("📁 Will analyze: core/, server/")
        elif selected_mode == ImprovementMode.AGENT_QUALITY:
            st.caption("📁 Will analyze: core/*agent*, agents.config.json")

    # Iterative mode (LangGraph-powered)
    st.markdown("#### Improvement Strategy")

    cols2 = st.columns([2, 2], gap="medium")

    with cols2[0]:
        iterative_mode = st.checkbox(
            "🔄 Iterative Mode (LangGraph)",
            value=True,
            help="Keep improving until quality threshold is met (recommended)"
        )

    with cols2[1]:
        if iterative_mode:
            target_score = st.slider(
                "Target Quality Score",
                min_value=7.0,
                max_value=10.0,
                value=9.0,
                step=0.5,
                help="Stop when this quality score is reached"
            )
        else:
            target_score = None

    if iterative_mode:
        st.info("🧠 **Iterative Mode**: System will automatically run multiple cycles until it reaches the target quality score (max 10 iterations).")
    else:
        st.info("🔄 **Single-Pass Mode**: System will run one improvement cycle and stop.")

    # Enhancement suggestions toggle
    st.markdown("#### Enhancement Options")
    suggest_enhancements = st.checkbox(
        "💡 Include Feature Suggestions",
        value=False,
        help="Add Research & Ideas agents to suggest new features and enhancements (in addition to finding bugs)"
    )

    if suggest_enhancements:
        st.info("💡 **Enhancement Mode**: Research & Ideas agents will analyze the codebase and suggest new features to add.")

    # Forever mode checkbox
    forever_mode = st.checkbox(
        "🔁 Forever mode (manual control)",
        value=False,
        help="Continuously run cycles until you click Stop (ignores target score)"
    )

    # Target specific files (optional)
    st.markdown("#### Target Specific Files (Optional)")
    target_files_text = st.text_area(
        "File paths (one per line)",
        placeholder="core/orchestrator.py\nstreamlit_ui/main_interface.py\n(Leave empty to analyze all files)",
        height=100,
        help="Specify files to analyze, or leave empty to analyze entire codebase"
    )

    # Parse target files
    target_files = [
        line.strip() for line in target_files_text.split('\n')
        if line.strip()
    ] if target_files_text.strip() else None

    # Start button - centered
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        start_button = st.button(
            "🚀 Start Improvement Cycle",
            use_container_width=True,
            type="primary"
        )

    # Execution
    if start_button:
        if forever_mode:
            run_forever_mode(selected_mode, target_files, suggest_enhancements)
        elif iterative_mode:
            run_iterative_mode(selected_mode, target_score, target_files, suggest_enhancements)
        else:
            run_single_cycle(selected_mode, target_files, suggest_enhancements)


def run_single_cycle(mode: str, target_files: list = None, suggest_enhancements: bool = False):
    """Run a single improvement cycle"""
    st.markdown("---")
    st.markdown("### 📋 Improvement Cycle Results")

    # Create progress container
    progress_container = st.container()
    terminal_container = st.container()
    results_container = st.container()

    with progress_container:
        progress_bar = st.progress(0, text="Initializing...")

    with terminal_container:
        st.markdown("#### 💻 Live Output")
        terminal_placeholder = st.empty()
        terminal_messages = []

    def terminal_callback(message: str, level: str = "info"):
        """Update terminal output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "info": "#00ff00",
            "success": "#44ff44",
            "warning": "#ffaa44",
            "error": "#ff4444"
        }.get(level, "#00ff00")

        terminal_messages.append(f'<span style="color: {color};">[{timestamp}] {message}</span>')

        terminal_html = f"""
        <div style="background-color: #1a1d29; border-radius: 8px; padding: 16px;
                    font-family: 'Courier New', monospace; height: 300px; overflow-y: auto;">
            {'<br>'.join(terminal_messages[-20:])}
        </div>
        """
        terminal_placeholder.markdown(terminal_html, unsafe_allow_html=True)

    try:
        # Load config
        config = load_config()
        config['orchestration']['terminal_callback'] = terminal_callback

        # Create improver
        improver = SelfImprover(config)

        # Update progress
        progress_bar.progress(0.1, text="Analyzing codebase...")

        # Run cycle
        result = improver.run_cycle(
            mode=mode,
            target_files=target_files,
            max_issues=5,
            suggest_enhancements=suggest_enhancements
        )

        progress_bar.progress(1.0, text="Complete!")

        # Display results
        with results_container:
            display_improvement_results(result, improver)

    except Exception as e:
        terminal_callback(f"Fatal error: {str(e)}", "error")
        st.error(f"### ❌ Error\n\n{str(e)}")
        import traceback
        st.code(traceback.format_exc())


def run_iterative_mode(mode: str, target_score: float, target_files: list = None, suggest_enhancements: bool = False):
    """Run iterative improvement cycles until quality threshold is met"""
    st.markdown("---")
    st.markdown("### 🔄 Iterative Improvement - LangGraph Powered")

    st.info(f"🎯 **Target Score**: {target_score}/10 | **Max Iterations**: 10 | **Mode**: {mode}")

    # Create progress containers
    progress_container = st.container()
    terminal_container = st.container()
    results_container = st.container()

    with progress_container:
        iteration_metric = st.empty()
        score_metric = st.empty()
        progress_bar = st.progress(0, text="Initializing LangGraph workflow...")

    with terminal_container:
        st.markdown("#### 💻 Live Output")
        terminal_placeholder = st.empty()
        terminal_messages = []

    def terminal_callback(message: str, level: str = "info"):
        """Update terminal output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "info": "#00ff00",
            "success": "#44ff44",
            "warning": "#ffaa44",
            "error": "#ff4444"
        }.get(level, "#00ff00")

        terminal_messages.append(f'<span style="color: {color};">[{timestamp}] {message}</span>')

        terminal_html = f"""
        <div style="background-color: #1a1d29; border-radius: 8px; padding: 16px;
                    font-family: 'Courier New', monospace; height: 400px; overflow-y: auto;">
            {'<br>'.join(terminal_messages[-30:])}
        </div>
        """
        terminal_placeholder.markdown(terminal_html, unsafe_allow_html=True)

    try:
        # Import LangGraph workflow
        from core.langgraph_improver import run_iterative_improvement
        from core.self_improver import ImprovementMode

        # Map string mode to ImprovementMode enum value
        mode_map = {
            'ui_ux': 'ui_ux',
            'performance': 'performance',
            'agent_quality': 'agent_quality',
            'code_quality': 'code_quality',
            'everything': 'everything'
        }

        # Get mode value (handle if mode is already ImprovementMode enum)
        if hasattr(mode, 'value'):
            mode_str = mode.value
        else:
            mode_str = mode_map.get(str(mode).lower(), 'ui_ux')

        terminal_callback(f"🚀 Starting iterative improvement with LangGraph", "info")
        terminal_callback(f"   Mode: {mode_str}", "info")
        terminal_callback(f"   Target score: {target_score}/10", "info")

        progress_bar.progress(0.1, text="Running LangGraph workflow...")

        # Run iterative improvement
        final_state = run_iterative_improvement(
            mode=mode_str,
            target_score=target_score,
            initial_score=5.0,
            suggest_enhancements=suggest_enhancements
        )

        progress_bar.progress(1.0, text="Complete!")

        # Display iteration history
        with results_container:
            st.markdown("---")
            st.markdown("### 📊 Iterative Improvement Results")

            # Summary metrics
            cols = st.columns(4, gap="small")
            iteration_count = len(final_state.get('iteration_history', []))
            cols[0].metric("Iterations", iteration_count)
            cols[1].metric("Final Score", f"{final_state.get('current_score', 0):.1f}/10")
            cols[2].metric("Total Issues", final_state.get('total_issues_found', 0))
            cols[3].metric("Total Fixes", final_state.get('total_fixes_applied', 0))

            # Iteration history
            st.markdown("### 📈 Iteration History")

            history = final_state.get('iteration_history', [])
            if history:
                # Create a table
                for entry in history:
                    with st.expander(f"Iteration {entry['iteration']} - Score: {entry['score']:.1f}/10", expanded=(entry['iteration'] == 1)):
                        cols = st.columns(3)
                        cols[0].metric("Issues Found", entry['issues_found'])
                        cols[1].metric("Fixes Applied", entry['fixes_applied'])
                        cols[2].metric("Score", f"{entry['score']:.1f}/10")

            # Final status
            if final_state.get('current_score', 0) >= target_score:
                st.success(f"✅ **Target score reached!** Final score: {final_state.get('current_score', 0):.1f}/10")
            else:
                st.warning(f"⚠️ **Max iterations reached.** Final score: {final_state.get('current_score', 0):.1f}/10 (target: {target_score}/10)")

            # Next steps
            st.markdown("### 🎯 Next Steps")
            cols = st.columns(2, gap="small")
            if cols[0].button("🔄 Run Another Cycle", use_container_width=True):
                st.rerun()
            if cols[1].button("✅ Done", use_container_width=True):
                st.success("Improvement cycle complete!")

        terminal_callback(f"✅ Iterative improvement complete!", "success")

    except Exception as e:
        terminal_callback(f"Fatal error: {str(e)}", "error")
        st.error(f"### ❌ Error\n\n{str(e)}")
        import traceback
        st.code(traceback.format_exc())


def run_forever_mode(mode: str, target_files: list = None, suggest_enhancements: bool = False):
    """Run continuous improvement cycles"""
    st.markdown("---")
    st.markdown("### 🔁 Forever Mode - Continuous Improvement")

    st.warning("⚠️ **Forever mode is running!** The system will continuously improve until you stop it.")

    # Stop button
    cols = st.columns(3, gap="small")
    stop_button = cols[1].button("🛑 STOP Forever Mode", use_container_width=True, type="secondary")

    if stop_button:
        st.session_state['forever_mode_active'] = False
        st.success("✅ Forever mode stopped")
        return

    # Initialize session state
    if 'forever_mode_active' not in st.session_state:
        st.session_state['forever_mode_active'] = True
        st.session_state['forever_cycles'] = 0

    # Cycle counter
    st.metric("Cycles Completed", st.session_state.get('forever_cycles', 0))

    # Terminal
    terminal_placeholder = st.empty()
    terminal_messages = []

    def terminal_callback(message: str, level: str = "info"):
        """Update terminal output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "info": "#00ff00",
            "success": "#44ff44",
            "warning": "#ffaa44",
            "error": "#ff4444"
        }.get(level, "#00ff00")

        terminal_messages.append(f'<span style="color: {color};">[{timestamp}] {message}</span>')

        terminal_html = f"""
        <div style="background-color: #1a1d29; border-radius: 8px; padding: 16px;
                    font-family: 'Courier New', monospace; height: 400px; overflow-y: auto;">
            {'<br>'.join(terminal_messages[-30:])}
        </div>
        """
        terminal_placeholder.markdown(terminal_html, unsafe_allow_html=True)

    try:
        config = load_config()
        config['orchestration']['terminal_callback'] = terminal_callback
        improver = SelfImprover(config)

        # Run cycles
        while st.session_state.get('forever_mode_active', False):
            cycle_num = st.session_state['forever_cycles'] + 1
            terminal_callback(f"🔄 Starting cycle {cycle_num}...", "info")

            result = improver.run_cycle(
                mode=mode,
                target_files=target_files,
                max_issues=3,  # Fewer issues per cycle in forever mode
                suggest_enhancements=suggest_enhancements
            )

            st.session_state['forever_cycles'] = cycle_num
            terminal_callback(f"✅ Cycle {cycle_num} complete!", "success")

            # Check if there are more issues
            if result['issues_found'] == 0:
                terminal_callback("🎉 No more issues found! Codebase is optimized.", "success")
                st.session_state['forever_mode_active'] = False
                # Force UI update to show final counter
                st.rerun()
                break

            # Rerun to update UI
            st.rerun()

    except Exception as e:
        terminal_callback(f"Fatal error: {str(e)}", "error")
        st.session_state['forever_mode_active'] = False


def display_improvement_results(result: dict, improver: 'SelfImprover'):
    """Display improvement cycle results"""
    st.markdown("---")

    # Summary metrics
    cols = st.columns(4, gap="small")
    cols[0].metric("Files Analyzed", result['files_analyzed'])
    cols[1].metric("Issues Found", result['issues_found'])
    cols[2].metric("Fixes Applied", result['fixes_applied'])
    improvement = result['scores']['improvement']
    cols[3].metric(
        "Improvement",
        f"+{improvement}" if improvement > 0 else str(improvement),
        delta=f"{improvement}/10"
    )

    # Issues found
    if result['issues']:
        st.markdown("### 🔍 Issues Found & Fixed")

        for i, issue in enumerate(result['issues'], 1):
            severity = issue['severity']
            severity_color = {
                'HIGH': '#ff4444',
                'MEDIUM': '#ffaa44',
                'LOW': '#44ff44'
            }.get(severity, '#ffffff')

            with st.expander(f"{i}. [{severity}] {issue['title']}", expanded=i == 1):
                st.markdown(f"**File:** `{issue['file']}`")
                st.markdown(f"**Severity:** <span style='color: {severity_color}; font-weight: bold;'>{severity}</span>", unsafe_allow_html=True)
                st.markdown(f"**Description:** {issue['description']}")
                st.markdown(f"**Fix Applied:** {issue['suggestion']}")

    # Git diff
    if result['diff']:
        st.markdown("### 📝 Changes Made")
        st.markdown(f"**Branch:** `{result['branch_name']}`")
        st.markdown(f"**Commit:** `{result['commit_hash'][:8]}`")

        with st.expander("View Git Diff", expanded=False):
            st.code(result['diff'][:3000], language="diff")  # Limit to 3000 chars

    # Impact scores
    st.markdown("### 📊 Impact Assessment")

    cols = st.columns(3, gap="small")
    cols[0].metric("Before", f"{result['scores']['before']}/10")
    cols[1].metric("After", f"{result['scores']['after']}/10")
    improvement = result['scores']['improvement']
    delta_color = "normal" if improvement > 0 else "inverse"
    cols[2].metric(
        "Improvement",
        f"+{improvement}" if improvement > 0 else str(improvement),
        delta=f"{abs(improvement)} points",
        delta_color=delta_color
    )

    # Next focus
    st.markdown("### 🎯 Next Focus")
    st.info(result['next_focus'])

    # Action buttons
    st.markdown("### 🎯 Next Steps")

    cols = st.columns(3, gap="small")
    if cols[0].button("✅ Merge to Main", use_container_width=True):
        merge_to_main(result['branch_name'])
    if cols[1].button("🔄 Run Another Cycle", use_container_width=True):
        st.rerun()
    if cols[2].button("🔙 Rollback Changes", use_container_width=True):
        if improver.rollback_to_main():
            st.success("✅ Rolled back to main branch")
        else:
            st.error("❌ Rollback failed")


def merge_to_main(branch_name: str):
    """Merge improvement branch to main"""
    import subprocess

    try:
        # Switch to main
        subprocess.run(['git', 'checkout', 'main'], check=True, capture_output=True)

        # Merge branch
        subprocess.run(['git', 'merge', branch_name], check=True, capture_output=True)

        st.success(f"✅ Merged {branch_name} to main!")

    except subprocess.CalledProcessError as e:
        st.error(f"❌ Merge failed: {e}")