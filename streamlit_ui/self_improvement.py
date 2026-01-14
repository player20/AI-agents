"""
Self-Improvement UI for Code Weaver Pro
Allows the system to analyze and improve its own code
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
from typing import TYPE_CHECKING
from .constants import COLORS, DIMENSIONS

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize session state for terminal (persistent across reruns)
if 'terminal_messages' not in st.session_state:
    st.session_state.terminal_messages = []

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


def create_terminal_callback(terminal_placeholder):
    """
    Create a terminal callback function with session state persistence.

    Args:
        terminal_placeholder: Streamlit empty placeholder for terminal output

    Returns:
        Function that logs messages to terminal with color-coded levels
    """
    def terminal_callback(message: str, level: str = "info"):
        """Update terminal output with session state persistence"""
        # Initialize session state if needed (defensive check)
        if 'terminal_messages' not in st.session_state:
            st.session_state.terminal_messages = []

        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "info": COLORS["info"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "error": COLORS["error"]
        }.get(level, COLORS["info"])

        # Store in session state for persistence
        st.session_state.terminal_messages.append(
            f'<span style="color: {color};">[{timestamp}] {message}</span>'
        )

        # Keep last 50 messages (increased for better history)
        if len(st.session_state.terminal_messages) > 50:
            st.session_state.terminal_messages = st.session_state.terminal_messages[-50:]

        # Update display with auto-scroll
        terminal_html = f"""
        <div id="terminal-output" style="background-color: {COLORS['terminal_bg']}; border-radius: 8px; padding: 16px;
                    font-family: 'Courier New', monospace; height: 300px; overflow-y: auto;
                    border: 1px solid #444;">
            {'<br>'.join(st.session_state.terminal_messages)}
        </div>
        <script>
            // Auto-scroll to bottom
            var terminalDiv = document.getElementById('terminal-output');
            if (terminalDiv) {{
                terminalDiv.scrollTop = terminalDiv.scrollHeight;
            }}
        </script>
        """
        terminal_placeholder.markdown(terminal_html, unsafe_allow_html=True)

    return terminal_callback


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
            help="Select which part of the codebase to analyze and improve. The agents will scan relevant files and suggest fixes."
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
            help="Continuously run improvement cycles until target score is reached or max 10 iterations (recommended for comprehensive improvements)"
        )

    with cols2[1]:
        if iterative_mode:
            target_score = st.slider(
                "Target Quality Score",
                min_value=7.0,
                max_value=10.0,
                value=9.0,
                step=0.5,
                help="System stops improving once this quality score is achieved (calculated based on issues found and fixed)"
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

    # Create terminal callback with session state persistence
    terminal_callback = create_terminal_callback(terminal_placeholder)

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

    # Create terminal callback with session state persistence
    terminal_callback = create_terminal_callback(terminal_placeholder)

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

    # Create terminal callback with session state persistence
    terminal_callback = create_terminal_callback(terminal_placeholder)

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


def generate_markdown_report(result: dict) -> str:
    """Generate a comprehensive markdown report of improvement results"""
    from datetime import datetime

    all_issues = result.get('all_issues', [])

    # Handle "no issues" case with a positive report
    if not all_issues:
        report = f"""# Code Improvement Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Files Analyzed:** {result['files_analyzed']}
- **Issues Found:** 0
- **Assessment:** ✅ Code quality is excellent!

## Analysis Details
{result['files_analyzed']} files were thoroughly analyzed by specialized AI agents.
No bugs or enhancements were identified. Your codebase follows best practices.

**Score:** {result['scores']['after']}/10

**Next Focus:** {result.get('next_focus', 'Maintain current quality standards')}

---

*Report generated by Code Weaver Pro Self-Improvement System*
"""
        return report

    # Normal report when issues exist
    report = f"""# Code Improvement Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Files Analyzed:** {result['files_analyzed']}
- **Issues Found:** {result['issues_found']}
- **Fixes Applied:** {result['fixes_applied']}
- **Score Before:** {result['scores']['before']}/10
- **Score After:** {result['scores']['after']}/10
- **Improvement:** +{result['scores']['improvement']}/10
- **Git Branch:** `{result.get('branch_name', 'N/A')}`
- **Commit Hash:** `{result.get('commit_hash', 'N/A')}`

---

## All Issues Found ({len(all_issues)})

"""

    # Group by type and severity
    bugs = [i for i in all_issues if i.get('type') == 'BUG']
    enhancements = [i for i in all_issues if i.get('type') == 'ENHANCEMENT']

    if bugs:
        report += f"### 🐛 Bugs ({len(bugs)})\n\n"
        for i, issue in enumerate(bugs, 1):
            severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(issue['severity'], "⚪")
            report += f"{i}. {severity_emoji} **[{issue['severity']}]** {issue['title']}\n"
            report += f"   - **File:** `{issue['file']}`\n"
            report += f"   - **Description:** {issue['description']}\n"
            report += f"   - **Suggested Fix:** {issue['suggestion']}\n\n"

    if enhancements:
        report += f"### 💡 Enhancements ({len(enhancements)})\n\n"
        for i, issue in enumerate(enhancements, 1):
            severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(issue['severity'], "⚪")
            report += f"{i}. {severity_emoji} **[{issue['severity']}]** {issue['title']}\n"
            report += f"   - **File:** `{issue['file']}`\n"
            report += f"   - **Description:** {issue['description']}\n"
            report += f"   - **Suggested Enhancement:** {issue['suggestion']}\n\n"

    report += f"""
---

## Issues Prioritized & Fixed ({len(result.get('issues', []))})

"""

    for i, issue in enumerate(result.get('issues', []), 1):
        severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(issue['severity'], "⚪")
        report += f"{i}. {severity_emoji} **[{issue['severity']}]** {issue['title']}\n"
        report += f"   - **File:** `{issue['file']}`\n"
        report += f"   - **Status:** ✅ FIXED\n"
        report += f"   - **Description:** {issue['description']}\n"
        report += f"   - **Fix Applied:** {issue['suggestion']}\n\n"

    report += f"""
---

## Next Focus
{result.get('next_focus', 'Continue improving code quality')}

---

*Report generated by Code Weaver Pro Self-Improvement System*
"""

    return report


def generate_json_report(result: dict) -> str:
    """Generate a JSON report of improvement results"""
    import json
    from datetime import datetime

    report_data = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "files_analyzed": result['files_analyzed'],
            "issues_found": result['issues_found'],
            "fixes_applied": result['fixes_applied'],
            "scores": result['scores'],
            "git_branch": result.get('branch_name', 'N/A'),
            "commit_hash": result.get('commit_hash', 'N/A')
        },
        "all_issues": result.get('all_issues', []),
        "prioritized_issues": result.get('issues', []),
        "next_focus": result.get('next_focus', ''),
        "diff_summary": result.get('diff', '')[:500] + "..." if len(result.get('diff', '')) > 500 else result.get('diff', '')
    }

    return json.dumps(report_data, indent=2)


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

    # Export buttons - ALWAYS show (even if no issues found)
    st.markdown("---")
    st.markdown("### 📥 Export Reports")

    # Generate reports
    markdown_report = generate_markdown_report(result)
    json_report = generate_json_report(result)

    # Show issue count with appropriate message
    issue_count = len(result.get('all_issues', []))
    if issue_count > 0:
        st.info(f"📊 **{issue_count} issues found** - Download comprehensive reports below")
    else:
        st.success("✅ **No issues found!** Your codebase is in excellent shape. Download report for details.")

    cols = st.columns(2, gap="small")

    with cols[0]:
        st.download_button(
            label="📄 Download Markdown Report",
            data=markdown_report,
            file_name=f"improvement_report_{result.get('branch_name', 'report')}.md",
            mime="text/markdown",
            use_container_width=True,
            help="Human-readable report with all findings and suggestions"
        )

    with cols[1]:
        st.download_button(
            label="📊 Download JSON Report",
            data=json_report,
            file_name=f"improvement_report_{result.get('branch_name', 'report')}.json",
            mime="application/json",
            use_container_width=True,
            help="Machine-readable report for programmatic analysis"
        )

    # Issues found (prioritized for fixing)
    if result['issues']:
        st.markdown("### 🔍 Issues Prioritized & Fixed")

        for i, issue in enumerate(result['issues'], 1):
            severity = issue['severity']
            severity_color = {
                'HIGH': COLORS["severity_high"],
                'MEDIUM': COLORS["severity_medium"],
                'LOW': COLORS["severity_low"]
            }.get(severity, COLORS["text_primary"])

            with st.expander(f"{i}. [{severity}] {issue['title']}", expanded=i == 1):
                st.markdown(f"**File:** `{issue['file']}`")
                st.markdown(f"**Severity:** <span style='color: {severity_color}; font-weight: bold;'>{severity}</span>", unsafe_allow_html=True)
                st.markdown(f"**Description:** {issue['description']}")
                st.markdown(f"**Fix Applied:** {issue['suggestion']}")

    # All issues found
    if result.get('all_issues') and len(result.get('all_issues', [])) > len(result.get('issues', [])):
        remaining_issues = len(result['all_issues']) - len(result['issues'])
        st.markdown(f"### 📋 All Issues Found ({len(result['all_issues'])} total)")
        st.info(f"**Note:** {len(result['issues'])} issues were prioritized and fixed. {remaining_issues} additional issues were identified for future improvement.")

        with st.expander(f"View All {len(result['all_issues'])} Issues", expanded=False):
            # Group by type
            bugs = [i for i in result['all_issues'] if i.get('type') == 'BUG']
            enhancements = [i for i in result['all_issues'] if i.get('type') == 'ENHANCEMENT']

            if bugs:
                st.markdown(f"#### 🐛 Bugs ({len(bugs)})")
                for i, issue in enumerate(bugs, 1):
                    severity = issue['severity']
                    severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")
                    st.markdown(f"{i}. {severity_emoji} **[{severity}]** {issue['title']}")
                    st.markdown(f"   - File: `{issue['file']}`")
                    st.markdown(f"   - {issue['description']}")
                    st.markdown("")

            if enhancements:
                st.markdown(f"#### 💡 Enhancements ({len(enhancements)})")
                for i, issue in enumerate(enhancements, 1):
                    severity = issue['severity']
                    severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")
                    st.markdown(f"{i}. {severity_emoji} **[{severity}]** {issue['title']}")
                    st.markdown(f"   - File: `{issue['file']}`")
                    st.markdown(f"   - {issue['description']}")
                    st.markdown("")

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