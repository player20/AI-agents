import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Callable, Optional, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_enhanced_execution() -> None:
    """
    Run the complete execution flow with all features - ROUTED THROUGH ORCHESTRATOR.
    Includes comprehensive error handling for all API calls and operations.
    """

    params: Dict = st.session_state['exec_params']

    # Create containers for live updates
    st.markdown("---")

    # Progress section with accessibility
    progress_container = st.container()
    with progress_container:
        st.markdown("""
        <div role="region" aria-labelledby="progress-heading">
            <h3 id="progress-heading">📊 Progress</h3>
        </div>
        """, unsafe_allow_html=True)

        # Create 4 progress bars
        phases: Dict[str, st.ProgressBar] = {
            'planning': st.progress(0.0, text="Loading..."),
            'drafting': st.progress(0.0, text="Loading..."),
            'testing': st.progress(0.0, text="Loading..."),
            'done': st.progress(0.0, text="Loading...")
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

    # Start execution
    add_terminal_line("🚀 Initializing Code Weaver Pro...", "info")
    add_terminal_line(f"📝 Project: {params['project_input'][:80]}...", "info")
    add_terminal_line(f"🎯 Platforms: {', '.join(params['platforms'])}", "info")

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

        add_terminal_line("🔧 Initializing orchestrator with UI callbacks...", "info")

        try:
            orchestrator = CodeWeaverOrchestrator(config)
        except Exception as e:
            add_terminal_line(f"❌ Failed to initialize orchestrator: {str(e)}", "error")
            st.error(f"### ❌ Initialization Error\n\nFailed to create orchestrator: {str(e)}")
            return

        # Prepare parameters for orchestrator
        orchestrator_params: Dict = {
            'platforms': params['platforms'],
            'do_market_research': params['do_market_research'],
            'research_only': params['research_only'],
            'existing_code': params.get('code_files'),
            'app_url': params.get('app_url'),
            'analyze_dropoffs': params.get('analyze_dropoffs', False),
            'test_credentials': st.session_state.get('test_credentials')
        }

        add_terminal_line("🚀 Starting orchestrated workflow...", "success")

        # RUN THROUGH ORCHESTRATOR with error handling
        try:
            result: Dict = orchestrator.run(
                user_input=params['project_input'],
                **orchestrator_params
            )
        except TimeoutError as e:
            add_terminal_line("❌ Execution timed out", "error")
            st.error("### ⏱️ Execution Timeout\n\nThe operation took too long to complete. Please try again with a simpler project or check your network connection.")
            return
        except ConnectionError as e:
            add_terminal_line(f"❌ Connection error: {str(e)}", "error")
            st.error("### 🌐 Connection Error\n\nFailed to connect to required services. Please check your internet connection and try again.")
            return
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
            except ImportError as e:
                add_terminal_line(f"❌ Failed to import results display module: {str(e)}", "error")
                st.error("### ❌ Display Error\n\nFailed to load results display module. Please check your installation.")
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