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

    with st.columns(4, gap="small") as cols:
        selected_mode_label = cols[0].radio(
            "Focus Area",
            list(mode_options.keys()),
            index=4,  # Default to "Everything"
            help="Choose what aspect of the system to improve"
        )

    selected_mode, mode_description = mode_options[selected_mode_label]
    cols[1].info(f"**{selected_mode_label}:** {mode_description}")

    # Forever mode checkbox
    with st.columns([3, 1], gap="small") as cols:
        forever_mode = cols[0].checkbox(
            "🔁 Improve me forever (run until stopped)",
            value=False,
            help="Continuously run improvement cycles until you click Stop"
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

    # Start button
    with st.columns(3, gap="small") as cols:
        start_button = cols[1].button(
            "🚀 Start Improvement Cycle",
            use_container_width=True,
            type="primary"
        )

    # Execution
    if start_button:
        if forever_mode:
            run_forever_mode(selected_mode, target_files)
        else:
            run_single_cycle(selected_mode, target_files)


def run_single_cycle(mode: str, target_files: list = None):
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
            max_issues=5
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


def run_forever_mode(mode: str, target_files: list = None):
    """Run continuous improvement cycles"""
    st.markdown("---")
    st.markdown("### 🔁 Forever Mode - Continuous Improvement")

    st.warning("⚠️ **Forever mode is running!** The system will continuously improve until you stop it.")

    # Stop button
    with st.columns(3, gap="small") as cols:
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
                max_issues=3  # Fewer issues per cycle in forever mode
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
    with st.columns(4, gap="small") as cols:
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

    with st.columns(3, gap="small") as cols:
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

    with st.columns(3, gap="small") as cols:
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