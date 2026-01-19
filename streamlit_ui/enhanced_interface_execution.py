import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Callable, Optional, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import loading states for enhanced UX
try:
    from streamlit_ui.loading_states import (
        inject_loading_css,
        render_phase_indicator,
        render_loading_spinner
    )
    LOADING_STATES_AVAILABLE = True
except ImportError:
    LOADING_STATES_AVAILABLE = False


def run_enhanced_execution() -> None:
    """
    Run the complete execution flow with all features - ROUTED THROUGH ORCHESTRATOR.
    Includes comprehensive error handling for all API calls and operations.
    """

    params: Dict = st.session_state['exec_params']

    # Initialize cancel state
    if 'execution_cancelled' not in st.session_state:
        st.session_state.execution_cancelled = False

    # Create containers for live updates
    st.markdown("---")

    # Inject loading CSS for enhanced visuals
    if LOADING_STATES_AVAILABLE:
        inject_loading_css()

    # Progress section with accessibility and cancel button
    progress_container = st.container()
    with progress_container:
        # Header row with progress title and cancel button
        header_col1, header_col2 = st.columns([3, 1])
        with header_col1:
            st.markdown("""
            <div role="region" aria-labelledby="progress-heading" class="progress-header-container">
                <h3 id="progress-heading">📊 Progress</h3>
                <p class="progress-subtitle" id="progress-status" aria-live="polite">Initializing execution...</p>
            </div>
            <div id="progress-live-region" aria-live="assertive" aria-atomic="true" class="sr-only">
                <!-- Screen reader announcements for progress changes -->
            </div>
            """, unsafe_allow_html=True)
        with header_col2:
            if st.button("🛑 Cancel", key="cancel_execution", type="secondary", use_container_width=True, help="Stop the current execution"):
                st.session_state.execution_cancelled = True
                st.warning("Cancellation requested... Please wait for current operation to complete.")

        # Create 4 progress bars
        phases: Dict[str, st.ProgressBar] = {
            'planning': st.progress(0.0, text="Planning..."),
            'drafting': st.progress(0.0, text="Drafting..."),
            'testing': st.progress(0.0, text="Testing..."),
            'done': st.progress(0.0, text="Finalizing...")
        }

    # Terminal output with accessibility
    terminal_container = st.container()
    with terminal_container:
        st.markdown("""
        <div role="region" aria-labelledby="terminal-heading" aria-live="polite">
            <h3 id="terminal-heading">💻 Live Terminal</h3>
        </div>
        """, unsafe_allow_html=True)
        terminal_placeholder = st.empty()

    # Results container
    results_container = st.container()

    # User feedback section for execution phases
    feedback_container = st.container()
    with feedback_container:
        if 'execution_feedback' not in st.session_state:
            st.session_state.execution_feedback = []

        # Feedback expander (collapsed by default, available during execution)
        with st.expander("💬 Provide Feedback During Execution", expanded=False):
            st.markdown("""
            <p style="color: #94A3B8; font-size: 14px; margin-bottom: 12px;">
                Share your thoughts during execution. Your feedback helps improve future runs.
            </p>
            """, unsafe_allow_html=True)

            feedback_cols = st.columns([3, 1])
            with feedback_cols[0]:
                user_feedback = st.text_input(
                    "Your feedback",
                    placeholder="e.g., Please focus more on mobile design...",
                    key="user_execution_feedback",
                    label_visibility="collapsed"
                )
            with feedback_cols[1]:
                if st.button("📤 Submit", key="submit_feedback", use_container_width=True):
                    if user_feedback.strip():
                        from datetime import datetime
                        st.session_state.execution_feedback.append({
                            'timestamp': datetime.now().isoformat(),
                            'message': user_feedback.strip(),
                            'phase': st.session_state.get('current_phase', 'unknown')
                        })
                        st.success("Feedback recorded!")

            # Show submitted feedback
            if st.session_state.execution_feedback:
                st.markdown("**Recent Feedback:**")
                for fb in st.session_state.execution_feedback[-3:]:
                    st.markdown(f"- _{fb['message']}_")

    # Helper function to update terminal
    def add_terminal_line(message: str, level: str = "info") -> None:
        """Add a line to the terminal output"""
        if 'terminal_lines' not in st.session_state:
            st.session_state.terminal_lines = []

        level_colors = {
            'info': 'terminal-info',
            'success': 'terminal-success',
            'error': 'terminal-error',
            'warning': 'terminal-warning'
        }

        color_class = level_colors.get(level, 'terminal-info')
        timestamp = datetime.now().strftime("%H:%M:%S")

        line = f'<div class="terminal-line {color_class}" role="log">[{timestamp}] {message}</div>'
        st.session_state.terminal_lines.append(line)

        # Keep last 30 lines
        if len(st.session_state.terminal_lines) > 30:
            st.session_state.terminal_lines = st.session_state.terminal_lines[-30:]

        # Update terminal
        terminal_html = f"""
        <div class='terminal-output' role="log" aria-live="polite">
            {''.join(st.session_state.terminal_lines)}
        </div>
        """
        terminal_placeholder.markdown(terminal_html, unsafe_allow_html=True)

    # Progress callback for orchestrator
    def update_progress(phase: str, progress: float) -> None:
        """
        Callback for orchestrator to update UI progress.

        Args:
            phase: Phase name (planning, drafting, testing, done)
            progress: Progress value (0.0 to 1.0)
        """
        try:
            if phase in phases:
                text = "In progress..." if progress < 1.0 else "Complete!"
                phases[phase].progress(progress, text=text)
        except Exception as e:
            add_terminal_line(f"⚠️ Progress update failed for {phase}: {str(e)}", "warning")

    # Terminal callback for orchestrator
    def terminal_callback(message: str, level: str = "info") -> None:
        """
        Callback for orchestrator to log terminal messages.

        Args:
            message: Log message
            level: Log level (info, success, warning, error)
        """
        try:
            add_terminal_line(message, level)
        except Exception as e:
            # Fallback logging
            print(f"Terminal callback error: {e}")

    # Agent collaboration view (compact during execution)
    try:
        from streamlit_ui.agent_collaboration_view import AgentCollaborationView, AgentStatus

        # Initialize collaboration view with default agents
        collab_view = AgentCollaborationView()
        default_agents = [
            {'id': 'MetaPrompt', 'name': 'Meta Prompt', 'role': 'Idea Expander'},
            {'id': 'Research', 'name': 'Researcher', 'role': 'Market Analyst'},
            {'id': 'Challenger', 'name': 'Challenger', 'role': 'Critical Review'},
            {'id': 'PM', 'name': 'Product Manager', 'role': 'Requirements'},
            {'id': 'Ideas', 'name': 'Ideas Agent', 'role': 'Feature Ideas'},
            {'id': 'Designs', 'name': 'Designer', 'role': 'UI/UX Design'},
            {'id': 'Senior', 'name': 'Senior Dev', 'role': 'Architecture'},
            {'id': 'Reflector', 'name': 'Reflector', 'role': 'Synthesis'},
        ]
        collab_view.initialize_agents(default_agents)
        collab_container = st.container()
    except ImportError:
        collab_view = None
        collab_container = None

    # Start execution
    add_terminal_line("🚀 Initializing Code Weaver Pro...", "info")
    add_terminal_line(f"📝 Project: {params['project_input'][:80]}...", "info")
    add_terminal_line(f"🎯 Platforms: {', '.join(params['platforms'])}", "info")

    # Helper to update agent status
    def update_agent(agent_id: str, status: str, task: str = "", progress: float = 0.0):
        """Update agent status in collaboration view."""
        if collab_view:
            status_map = {
                'idle': AgentStatus.IDLE,
                'thinking': AgentStatus.THINKING,
                'working': AgentStatus.WORKING,
                'completed': AgentStatus.COMPLETED,
                'error': AgentStatus.ERROR,
                'waiting': AgentStatus.WAITING,
            }
            collab_view.update_agent_status(agent_id, status_map.get(status, AgentStatus.IDLE), task, progress)

    try:
        # Load configuration and create orchestrator
        add_terminal_line("⚙️ Loading configuration...", "info")

        try:
            from core.config import load_config
            from core.orchestrator import CodeWeaverOrchestrator
        except ImportError as e:
            add_terminal_line(f"❌ Failed to import core modules: {str(e)}", "error")
            st.error("### ❌ Configuration Error\n\nFailed to load core modules. Please check your installation.")
            return

        try:
            config = load_config()
        except Exception as e:
            add_terminal_line(f"❌ Failed to load configuration: {str(e)}", "error")
            st.error(f"### ❌ Configuration Error\n\nFailed to load configuration file: {str(e)}")
            return

        # Add UI callbacks to config
        config['orchestration']['progress_callback'] = update_progress  # type: ignore
        config['orchestration']['terminal_callback'] = terminal_callback  # type: ignore

        # Add agent status callback for collaboration view
        def agent_status_callback(agent_id: str, status: str, task: str = "", progress: float = 0.0):
            """Callback for orchestrator to update agent status in UI."""
            update_agent(agent_id, status, task, progress)
            # Also add to terminal for visibility
            if status == 'working':
                add_terminal_line(f"🤖 {agent_id}: {task}", "info")
            elif status == 'completed':
                add_terminal_line(f"✅ {agent_id}: Completed", "success")

        config['orchestration']['agent_callback'] = agent_status_callback  # type: ignore

        add_terminal_line("🔧 Initializing orchestrator with UI callbacks...", "info")

        # Render collaboration view (compact mode during execution)
        if collab_container and collab_view:
            with collab_container:
                collab_view.render(show_messages=False, compact=True)

        try:
            orchestrator = CodeWeaverOrchestrator(config)
        except Exception as e:
            add_terminal_line(f"❌ Failed to initialize orchestrator: {str(e)}", "error")
            st.error(f"### ❌ Initialization Error\n\nFailed to create orchestrator: {str(e)}")
            return

        # Prepare parameters for orchestrator
        orchestrator_params: Dict = {
            # Core parameters
            'platforms': params['platforms'],
            'do_market_research': params['do_market_research'],
            'research_only': params['research_only'],
            'existing_code': params.get('code_files'),
            'app_url': params.get('app_url'),
            'analyze_dropoffs': params.get('analyze_dropoffs', False),
            'test_credentials': st.session_state.get('test_credentials'),

            # Business context (for rich proposals like Brew & Co)
            'business_name': params.get('business_name', ''),
            'industry': params.get('industry', 'Not specified'),
            'target_users': params.get('target_users', ''),
            'business_stage': params.get('business_stage', 'Just an idea'),

            # Brand & Design preferences
            'brand_personality': params.get('brand_personality', []),
            'existing_colors': params.get('existing_colors', ''),
            'design_style': params.get('design_style', 'Let AI decide'),
            'competitor_apps': params.get('competitor_apps', ''),

            # Project scope
            'budget_range': params.get('budget_range', 'Not specified'),
            'timeline': params.get('timeline', 'Not specified'),
            'success_metrics': params.get('success_metrics', []),
            'known_competitors': params.get('known_competitors', ''),

            # Contact info (for proposal footer)
            'company_name': params.get('company_name', ''),
            'company_tagline': params.get('company_tagline', ''),
            'contact_email': params.get('contact_email', ''),
            'contact_phone': params.get('contact_phone', '')
        }

        add_terminal_line("🚀 Starting orchestrated workflow...", "success")

        # Check for cancellation before starting
        if st.session_state.get('execution_cancelled', False):
            add_terminal_line("⚠️ Execution cancelled by user before start", "warning")
            st.warning("Execution was cancelled. Click 'GO' to start a new execution.")
            st.session_state.execution_cancelled = False  # Reset for next run
            return

        # RUN THROUGH ORCHESTRATOR with error handling
        try:
            result: Dict = orchestrator.run(
                user_input=params['project_input'],
                **orchestrator_params
            )
        except Exception as e:
            add_terminal_line(f"❌ Orchestrator execution failed: {str(e)}", "error")
            st.error(f"### ❌ Execution Error\n\n{str(e)}")
            import traceback
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())
            return

        add_terminal_line("✅ Workflow complete!", "success")

        # Store result for display
        st.session_state['execution_result'] = result

        # Handle different result statuses
        if result['status'] == 'no-go':
            add_terminal_line("⚠️ Market research recommendation: NO-GO", "warning")
            with results_container:
                st.markdown("""
                <div role="region" aria-labelledby="nogo-heading">
                    <h3 id="nogo-heading">⚠️ Market Research: NO-GO Decision</h3>
                </div>
                """, unsafe_allow_html=True)
                st.warning(result.get('reason', 'Market research indicates this project may not be viable.'))
                st.markdown("**Agent Outputs:**")
                for agent, output in result.get('agent_outputs', {}).items():
                    with st.expander(f"📊 {agent}"):
                        st.markdown(output)
            return

        elif result['status'] == 'research_complete':
            add_terminal_line("✅ Research-only mode complete", "success")
            with results_container:
                st.markdown("""
                <div role="region" aria-labelledby="research-heading">
                    <h3 id="research-heading">📊 Market Research Complete</h3>
                </div>
                """, unsafe_allow_html=True)
                st.info(result.get('description', 'Research completed successfully.'))
                st.markdown("**Research Findings:**")
                for agent, output in result.get('agent_outputs', {}).items():
                    if 'research' in agent.lower() or 'market' in agent.lower():
                        with st.expander(f"📊 {agent}"):
                            st.markdown(output)
            return

        elif result['status'] == 'error':
            add_terminal_line(f"❌ Execution failed: {result.get('error', 'Unknown error')}", "error")
            with results_container:
                st.markdown("""
                <div role="alert" aria-labelledby="error-heading">
                    <h3 id="error-heading">❌ Execution Failed</h3>
                </div>
                """, unsafe_allow_html=True)
                st.error(result.get('error', 'An unknown error occurred during execution.'))
                if result.get('errors'):
                    with st.expander("🔍 Error Details"):
                        for error in result['errors']:
                            st.code(error)
            return

        # Success case - display comprehensive results
        add_terminal_line("🎉 Displaying results...", "success")

        # Display results (import delayed to avoid circular dependency)
        with results_container:
            try:
                from streamlit_ui.enhanced_interface_results import display_enhanced_results_from_orchestrator
                display_enhanced_results_from_orchestrator(result, params)
            except Exception as e:
                add_terminal_line(f"❌ Failed to display results: {str(e)}", "error")
                st.error(f"### ❌ Display Error\n\n{str(e)}")
                st.info("💡 Your project was generated successfully, but there was an error displaying the results. Check the terminal output above for details.")

    except KeyboardInterrupt:
        add_terminal_line("⚠️ Execution interrupted by user", "warning")
        st.warning("### ⚠️ Execution Interrupted\n\nYou cancelled the execution. You can start a new project above.")

    except MemoryError:
        add_terminal_line("❌ Out of memory", "error")
        st.error("### 💾 Memory Error\n\nThe system ran out of memory. Try simplifying your project or closing other applications.")

    except Exception as e:
        add_terminal_line(f"❌ Fatal error: {str(e)}", "error")
        st.markdown("""
        <div role="alert" aria-labelledby="fatal-error-heading">
            <h3 id="fatal-error-heading">❌ Execution Failed</h3>
        </div>
        """, unsafe_allow_html=True)
        st.error(f"### ❌ Unexpected Error\n\n{str(e)}")
        import traceback
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())
        st.info("💡 **Troubleshooting**: Try refreshing the page or starting with a simpler project description.")