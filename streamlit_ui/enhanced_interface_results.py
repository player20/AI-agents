"""
Enhanced Interface - Results Module
Handles results display with comprehensive error handling and accessibility
This module is imported by the execution module to display results.
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Dict
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def display_enhanced_results_from_orchestrator(result: Dict, params: Dict):
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
            <h2 id="results-heading">🎉 Your App is Ready!</h2>
        </div>
        """, unsafe_allow_html=True)

        # Extract result data with fallbacks
        project_name = result.get('project_name', 'My Awesome App')
        description = result.get('description', params.get('project_input', 'No description available'))
        platforms = result.get('platforms', params.get('platforms', []))
        scores = result.get('scores', {'speed': 7, 'mobile': 7, 'intuitiveness': 7, 'functionality': 7})
        features = result.get('features', [])
        recommendations = result.get('recommendations', [])
        test_results = result.get('test_results', [])
        screenshots = result.get('screenshots', [])
        performance = result.get('performance', {})

        # Scores section
        st.markdown("""
        <div role="region" aria-labelledby="scores-heading">
            <h3 id="scores-heading">📊 Quality Scores</h3>
        </div>
        """, unsafe_allow_html=True)

        score_cols = st.columns(4)
        score_names = ['speed', 'mobile', 'intuitiveness', 'functionality']

        for idx, score_name in enumerate(score_names):
            score = scores.get(score_name, 7)
            with score_cols[idx]:
                # Determine emoji based on score
                if score >= 9:
                    emoji = "🟢"
                elif score >= 7:
                    emoji = "🟡"
                else:
                    emoji = "🔴"

                st.metric(
                    f"{emoji} {score_name.title()}",
                    f"{score}/10",
                    help=f"Quality score for {score_name}"
                )

        # Features section
        if features:
            st.markdown("---")
            st.markdown("""
            <div role="region" aria-labelledby="features-heading">
                <h3 id="features-heading">✨ Implemented Features</h3>
            </div>
            """, unsafe_allow_html=True)

            # Display features in columns
            feat_cols = st.columns(2)
            for idx, feature in enumerate(features):
                with feat_cols[idx % 2]:
                    st.success(f"✅ {feature}")

        # Test Results section
        if test_results:
            st.markdown("---")
            st.markdown("""
            <div role="region" aria-labelledby="tests-heading">
                <h3 id="tests-heading">🧪 Test Results</h3>
            </div>
            """, unsafe_allow_html=True)

            passed = len([t for t in test_results if t.get('status') == 'passed'])
            failed = len([t for t in test_results if t.get('status') == 'failed'])
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
                        if test.get('status') == 'failed':
                            st.error(f"**{test.get('name', 'Unknown test')}**")
                            if test.get('error'):
                                st.code(test['error'])

        # Performance Metrics
        if performance:
            st.markdown("---")
            st.markdown("""
            <div role="region" aria-labelledby="performance-heading">
                <h3 id="performance-heading">⚡ Performance</h3>
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
                value = performance.get(key, 0)
                with perf_cols[idx]:
                    # Determine if performance is good
                    if key == 'page_load_ms' and value > 3000:
                        delta_color = "inverse"
                    elif key == 'total_size_kb' and value > 1024:
                        delta_color = "inverse"
                    else:
                        delta_color = "normal"

                    st.metric(label, f"{value:,} {unit}", delta_color=delta_color)

        # Screenshots section
        if screenshots:
            st.markdown("---")
            st.markdown("""
            <div role="region" aria-labelledby="screenshots-heading">
                <h3 id="screenshots-heading">📸 Screenshots</h3>
            </div>
            """, unsafe_allow_html=True)

            screenshot_cols = st.columns(min(3, len(screenshots)))
            for idx, screenshot in enumerate(screenshots[:3]):
                with screenshot_cols[idx]:
                    try:
                        st.image(screenshot, caption=f"Screenshot {idx + 1}", use_container_width=True)
                    except Exception as e:
                        st.error(f"Failed to load screenshot: {str(e)}")

        # Recommendations section
        if recommendations:
            st.markdown("---")
            st.markdown("""
            <div role="region" aria-labelledby="recommendations-heading">
                <h3 id="recommendations-heading">💡 Recommendations</h3>
            </div>
            """, unsafe_allow_html=True)

            for idx, rec in enumerate(recommendations, 1):
                st.info(f"**{idx}.** {rec}")

        # Download section
        st.markdown("---")
        st.markdown("""
        <div role="region" aria-labelledby="download-heading">
            <h3 id="download-heading">📦 Download Your App</h3>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Download Source Code", use_container_width=True, type="primary"):
                st.info("Downloading... (Feature in development)")

        with col2:
            if st.button("🚀 Deploy to Cloud", use_container_width=True):
                st.info("Deploy feature coming soon!")

        # Agent outputs (if available)
        if result.get('agent_outputs'):
            st.markdown("---")
            with st.expander("🤖 View Agent Outputs", expanded=False):
                for agent_name, output in result['agent_outputs'].items():
                    st.markdown(f"### {agent_name}")
                    st.markdown(output)
                    st.markdown("---")

    except KeyError as e:
        st.error(f"### ❌ Results Display Error\n\nMissing required data: {str(e)}")
        st.info("The execution completed but some result data is missing. This might be a bug in the orchestrator.")

    except Exception as e:
        st.error(f"### ❌ Display Error\n\nFailed to render results: {str(e)}")
        import traceback
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())


def display_enhanced_results(params: Dict):
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
            <h2 id="legacy-results-heading">🎉 Your App is Ready!</h2>
        </div>
        """, unsafe_allow_html=True)

        # Demo data (TODO: Replace with real results from legacy path)
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
        st.error(f"### ❌ Legacy Results Display Error\n\n{str(e)}")
        import traceback
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())
