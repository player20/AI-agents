import streamlit as st
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests
import os
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import GitHub export functionality
try:
    from streamlit_ui.github_export import render_github_export, GitHubExporter
    GITHUB_EXPORT_AVAILABLE = True
except ImportError:
    GITHUB_EXPORT_AVAILABLE = False


def display_enhanced_results_from_orchestrator(result: Dict[str, Any], params: Dict[str, Any]) -> None:
    """
    Display results from orchestrator execution.
    Includes accessibility support and comprehensive error handling.

    Args:
        result: Result dictionary from orchestrator
        params: Execution parameters
    """

    try:
        st.markdown("---")
        st.markdown("""
        <div role="region" aria-labelledby="results-heading">
            <h2 id="results-heading" role="heading" aria-level="2"><span aria-hidden="true">🎉</span> Your App is Ready!</h2>
        </div>
        """, unsafe_allow_html=True)

        if not isinstance(result, dict):
            st.error("Invalid result format: expected a dictionary")
            st.stop()

        # Extract basic data
        project_name = result.get('project_name', 'My Awesome App')
        description = result.get('description', params.get('project_input', 'No description available'))
        platforms = result.get('platforms', params.get('platforms', []))

        # Validate and extract scores
        scores = result.get('scores')
        if scores is None:
            st.error("Missing 'scores' key in results")
            st.stop()
        if not isinstance(scores, dict):
            st.error(f"Invalid 'scores' data: expected dict, got {type(scores).__name__}")
            st.stop()

        # Validate features
        features = result.get('features', [])
        if features is not None and not isinstance(features, list):
            st.error(f"Invalid 'features' data: expected list, got {type(features).__name__}")
            features = []

        # Validate recommendations
        recommendations = result.get('recommendations', [])
        if recommendations is not None and not isinstance(recommendations, list):
            st.error(f"Invalid 'recommendations' data: expected list, got {type(recommendations).__name__}")
            recommendations = []

        # Validate test_results
        test_results = result.get('test_results', [])
        if test_results is not None and not isinstance(test_results, list):
            st.error(f"Invalid 'test_results' data: expected list, got {type(test_results).__name__}")
            test_results = []

        # Validate screenshots
        screenshots = result.get('screenshots', [])
        if screenshots is not None and not isinstance(screenshots, list):
            st.error(f"Invalid 'screenshots' data: expected list, got {type(screenshots).__name__}")
            screenshots = []

        # Validate performance
        performance = result.get('performance', {})
        if performance is None:
            st.warning("Missing 'performance' key in results, using defaults")
            performance = {}
        elif not isinstance(performance, dict):
            st.error(f"Invalid 'performance' data: expected dict, got {type(performance).__name__}")
            performance = {}

        # Validate agent_outputs
        agent_outputs = result.get('agent_outputs', {})
        if agent_outputs is not None and not isinstance(agent_outputs, dict):
            st.warning(f"Invalid 'agent_outputs' data: expected dict, got {type(agent_outputs).__name__}, skipping")
            agent_outputs = {}

        # Scores section
        st.markdown("""
        <div role="region" aria-labelledby="scores-heading">
            <h3 id="scores-heading" role="heading" aria-level="3"><span aria-hidden="true">📊</span> Quality Scores</h3>
        </div>
        """, unsafe_allow_html=True)

        # Check if visual score is available to adjust column layout
        has_visual_score = 'visual' in scores
        score_names = ['speed', 'mobile', 'intuitiveness', 'functionality']
        if has_visual_score:
            score_names.append('visual')

        score_cols = st.columns(len(score_names))

        for idx, score_name in enumerate(score_names):
            score_val = scores.get(score_name)
            try:
                score = float(score_val) if score_val is not None else 7.0
            except (ValueError, TypeError):
                score = 7.0
            score_int = int(round(score))

            with score_cols[idx]:
                # Determine emoji based on score
                if score_int >= 9:
                    emoji = "🟢"
                elif score_int >= 7:
                    emoji = "🟡"
                else:
                    emoji = "🔴"

                # Special label for visual score
                label = score_name.title()
                help_text = f"Quality score for {score_name}"
                if score_name == 'visual':
                    label = "Visual"
                    help_text = "AI vision analysis score for design quality, consistency, and accessibility"

                st.metric(
                    f"{emoji} {label}",
                    f"{score_int}/10",
                    help=help_text
                )

        # Features section
        if features:
            st.markdown("---")
            st.markdown("""
            <div role="region" aria-labelledby="features-heading">
                <h3 id="features-heading" role="heading" aria-level="3"><span aria-hidden="true">✨</span> Implemented Features</h3>
            </div>
            """, unsafe_allow_html=True)

            # Display features in columns
            feat_cols = st.columns(2)
            for idx, feature in enumerate(features):
                with feat_cols[idx % 2]:
                    st.success(f"✅ {str(feature)}")

        # Test Results section
        if test_results:
            st.markdown("---")
            st.markdown("""
            <div role="region" aria-labelledby="tests-heading">
                <h3 id="tests-heading" role="heading" aria-level="3"><span aria-hidden="true">🧪</span> Test Results</h3>
            </div>
            """, unsafe_allow_html=True)

            passed = len([t for t in test_results if isinstance(t, dict) and t.get('status') == 'passed'])
            failed = len([t for t in test_results if isinstance(t, dict) and t.get('status') == 'failed'])
            total = len(test_results)

            test_cols = st.columns(3)
            with test_cols[0]:
                st.metric("Total Tests", total)
            with test_cols[1]:
                st.metric("✅ Passed", passed, delta=None if failed == 0 else f"-{failed} failed")
            with test_cols[2]:
                st.metric("❌ Failed", failed)

            # Show test details in expander
            if failed > 0:
                with st.expander("🔍 View Failed Tests", expanded=True):
                    for test in test_results:
                        if isinstance(test, dict) and test.get('status') == 'failed':
                            name = test.get('name', 'Unknown test')
                            st.error(f"**{name}**")
                            error_msg = test.get('error')
                            if error_msg is not None:
                                st.code(str(error_msg))

        # Performance Metrics
        if performance:
            st.markdown("---")
            st.markdown("""
            <div role="region" aria-labelledby="performance-heading">
                <h3 id="performance-heading" role="heading" aria-level="3"><span aria-hidden="true">⚡</span> Performance</h3>
            </div>
            """, unsafe_allow_html=True)

            perf_cols = st.columns(4)

            metrics = [
                ('page_load_ms', 'Page Load', 'ms'),
                ('time_to_interactive_ms', 'Time to Interactive', 'ms'),
                ('first_contentful_paint_ms', 'First Paint', 'ms'),
                ('total_size_kb', 'Bundle Size', 'KB')
            ]

            for idx, (key, label, unit) in enumerate(metrics):
                value_raw = performance.get(key)
                try:
                    value = float(value_raw) if value_raw is not None else 0.0
                except (ValueError, TypeError):
                    value = 0.0
                value_int = int(round(value))

                with perf_cols[idx]:
                    # Determine if performance is good
                    delta_color = "normal"
                    if key == 'page_load_ms' and value > 3000:
                        delta_color = "inverse"
                    elif key == 'total_size_kb' and value > 1024:
                        delta_color = "inverse"

                    st.metric(label, f"{value_int:,} {unit}", delta_color=delta_color)

        # Visual Assessment section (AI Vision Analysis)
        visual_assessment = agent_outputs.get('visual_assessment', '')
        if visual_assessment and visual_assessment != "Visual assessment not performed.":
            st.markdown("---")
            st.markdown("""
            <div role="region" aria-labelledby="visual-assessment-heading">
                <h3 id="visual-assessment-heading" role="heading" aria-level="3"><span aria-hidden="true">👁️</span> Visual Assessment (AI Vision Analysis)</h3>
                <p style='color: #888888; font-size: 14px; margin-bottom: 16px;'>
                    AI-powered visual analysis of your application's design, layout, and accessibility
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Display visual assessment in an expandable section
            with st.expander("📋 Full Visual Analysis Report", expanded=True):
                st.markdown(visual_assessment)

            # Extract and display key insights if available
            vision_screenshots = agent_outputs.get('vision_screenshots', [])
            if vision_screenshots:
                st.markdown("**📸 Pages Analyzed:**")
                # Get unique URLs
                analyzed_urls = list(set([s.get('url', 'Unknown') for s in vision_screenshots]))
                for url in analyzed_urls[:10]:  # Show first 10
                    st.markdown(f"- `{url}`")
                if len(analyzed_urls) > 10:
                    st.markdown(f"_...and {len(analyzed_urls) - 10} more pages_")

        # Screenshots section
        if screenshots:
            st.markdown("---")
            st.markdown("""
            <div role="region" aria-labelledby="screenshots-heading">
                <h3 id="screenshots-heading" role="heading" aria-level="3"><span aria-hidden="true">📸</span> Screenshots</h3>
            </div>
            """, unsafe_allow_html=True)

            num_cols = min(3, len(screenshots))
            screenshot_cols = st.columns(num_cols)
            for idx, screenshot in enumerate(screenshots[:3]):
                with screenshot_cols[idx]:
                    try:
                        st.image(screenshot, caption=f"Screenshot {idx + 1}", use_container_width=True)
                    except Exception as e:
                        st.error(f"Failed to load screenshot {idx + 1}: {str(e)}")

        # Recommendations section
        if recommendations:
            st.markdown("---")
            st.markdown("""
            <div role="region" aria-labelledby="recommendations-heading">
                <h3 id="recommendations-heading" role="heading" aria-level="3"><span aria-hidden="true">💡</span> Recommendations</h3>
            </div>
            """, unsafe_allow_html=True)

            for idx, rec in enumerate(recommendations, 1):
                st.info(f"**{idx}.** {str(rec)}")

        # Download section
        st.markdown("---")
        st.markdown("""
        <div role="region" aria-labelledby="download-heading">
            <h3 id="download-heading" role="heading" aria-level="3"><span aria-hidden="true">📦</span> Download Your App</h3>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            try:
                download_data = json.dumps(result, indent=2).encode("utf-8")
                st.download_button(
                    label="💾 Download Results (JSON)",
                    data=download_data,
                    file_name=f"{project_name.replace(' ', '_').replace('/', '_')}_results.json",
                    mime="application/json",
                    use_container_width=True,
                )
            except Exception as dl_e:
                st.error(f"Failed to prepare download data: {str(dl_e)}")

        with col2:
            if GITHUB_EXPORT_AVAILABLE:
                if st.button("🚀 Export to GitHub", use_container_width=True, key="github_export_btn"):
                    st.session_state['show_github_export_modal'] = True

        # GitHub Export Modal
        if GITHUB_EXPORT_AVAILABLE and st.session_state.get('show_github_export_modal', False):
            st.markdown("---")
            st.markdown("""
            <div role="region" aria-labelledby="github-export-heading">
                <h3 id="github-export-heading"><span aria-hidden="true">🚀</span> Export to GitHub</h3>
            </div>
            """, unsafe_allow_html=True)

            # Prepare export content
            export_content = {
                'project_name': project_name,
                'description': description,
                'files': result.get('files', {}),
                'platforms': platforms
            }

            # Render the GitHub export UI
            render_github_export(export_content, content_type="project")

            if st.button("❌ Close Export", key="close_github_export"):
                st.session_state['show_github_export_modal'] = False
                st.rerun()

        # Agent outputs (if available) - VISIBLE BY DEFAULT for transparency
        if agent_outputs:
            st.markdown("---")
            st.markdown("""
            <div role="region" aria-labelledby="agent-outputs-heading">
                <h3 id="agent-outputs-heading"><span aria-hidden="true">🤖</span> Agent Outputs</h3>
                <p style='color: #888888; font-size: 14px; margin-bottom: 16px;'>
                    See what each AI agent contributed to your project
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Show agent outputs in tabs for better organization
            agent_names = list(agent_outputs.keys())
            if len(agent_names) > 1:
                agent_tabs = st.tabs(agent_names)
                for idx, agent_name in enumerate(agent_names):
                    with agent_tabs[idx]:
                        st.markdown(str(agent_outputs[agent_name]))
            else:
                # Single agent - show directly
                for agent_name, output in agent_outputs.items():
                    st.markdown(f"**{agent_name}**")
                    st.markdown(str(output))

    except Exception as e:
        st.error(f"### ❌ Unexpected Results Display Error\n\nFailed to render results: {str(e)}")
        import traceback
        with st.expander("🔍 Full Error Details"):
            st.code(traceback.format_exc())


def display_enhanced_results(params: Dict[str, Any]) -> None:
    """
    Display comprehensive results with all features (legacy function).
    This is a fallback for non-orchestrator execution paths.

    Args:
        params: Execution parameters
    """

    try:
        st.markdown("---")
        st.markdown("""
        <div role="region" aria-labelledby="legacy-results-heading">
            <h2 id="legacy-results-heading" role="heading" aria-level="2"><span aria-hidden="true">🎉</span> Your App is Ready!</h2>
        </div>
        """, unsafe_allow_html=True)

        # Fallback demo data for legacy path (orchestrator bypass)
        st.warning("⚠️ **Note**: You're viewing demo results. Full results require orchestrator execution.")

        result = {
            'project_name': 'My Awesome App',
            'description': params.get('project_input', 'No description'),
            'platforms': params.get('platforms', ['Web App']),
            'scores': {'speed': 7, 'mobile': 7, 'intuitiveness': 7, 'functionality': 7},
            'features': [
                'User Authentication',
                'Responsive Design',
                'API Integration',
                'Database Storage'
            ],
            'recommendations': [
                'Add caching to improve performance',
                'Implement rate limiting for API endpoints',
                'Add comprehensive error handling'
            ],
            'test_results': [
                {'name': 'Login flow', 'status': 'passed', 'duration_ms': 450},
                {'name': 'API endpoints', 'status': 'passed', 'duration_ms': 320},
                {'name': 'Form validation', 'status': 'passed', 'duration_ms': 180}
            ],
            'performance': {
                'page_load_ms': 2500,
                'time_to_interactive_ms': 1800,
                'first_contentful_paint_ms': 900,
                'total_size_kb': 850
            },
            'screenshots': []
        }

        # Use the main display function
        display_enhanced_results_from_orchestrator(result, params)

        # Add note about legacy path
        st.info("💡 **Tip**: This is a demo result. For real execution, the orchestrator should be used.")

    except Exception as e:
        st.error(f"### ❌ Legacy Results Display Error\n\nFailed to render legacy results: {str(e)}")
        import traceback
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())