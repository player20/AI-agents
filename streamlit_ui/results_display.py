"""
Results display with screenshots, scores, and action buttons
Shows final output to user with download and next steps
"""

import streamlit as st
from PIL import Image
from pathlib import Path
import zipfile
import io
import os
from typing import Dict, List, Optional
from .constants import COLORS, THRESHOLDS

def display_results(results: dict) -> None:
    """
    Display final results with synopsis, screenshots, and actions

    Args:
        results: Dictionary containing:
            - project_name: str
            - description: str
            - features: List[str]
            - scores: Dict[str, int] (speed, mobile, intuitiveness, functionality)
            - screenshots: List[Dict] with name, path, viewport
            - recommendations: List[str]
            - project_path: str
    """
    try:
        # Validate input
        if not isinstance(results, dict):
            st.error("Invalid results format. Expected dictionary.")
            return

        st.markdown("---")
        st.markdown("# 🎉 Your App is Ready!")

        # Project summary
        col1, col2 = st.columns([2, 1], gap="medium")

        with col1:
            st.markdown(f"### {results.get('project_name', 'Your Project')}")
            st.markdown(results.get('description', 'No description available'))

        with col2:
            # Overall score
            scores = results.get('scores', {})
            total_score = sum(scores.values())
            max_score = len(scores) * 10

            if max_score > 0:
                percentage = (total_score / max_score) * 100
                st.metric(
                    "Overall Score",
                    f"{total_score}/{max_score}",
                    delta=f"{percentage:.0f}%"
                )

        # What we built
        st.markdown("### 📦 What We Built")
        features = results.get('features', [])
        if features:
            for feature in features:
                st.markdown(f"- {feature}")
        else:
            st.info("No features listed")

        # Quality scores
        st.markdown("### 📊 Quality Scores")

        score_emojis = {
            range(9, 11): "🟢",  # 9-10: Excellent
            range(7, 9): "🟡",   # 7-8: Good
            range(5, 7): "🟠",   # 5-6: Fair
            range(0, 5): "🔴"    # 0-4: Needs work
        }

        def get_emoji(score: int) -> str:
            """
            Get status emoji based on score value.

            Args:
                score: Numeric score (0-10)

            Returns:
                Emoji string representing score level (🟢/🟡/🟠/🔴)
            """
            for score_range, emoji in score_emojis.items():
                if score in score_range:
                    return emoji
            return "⚪"

        score_cols = st.columns(4, gap="medium")

        score_labels = {
            'speed': ('Speed', 'Page load & responsiveness'),
            'mobile': ('Mobile', 'Touch & viewport optimization'),
            'intuitiveness': ('Intuitiveness', 'User experience clarity'),
            'functionality': ('Functionality', 'Feature completeness')
        }

        for i, (key, (label, description)) in enumerate(score_labels.items()):
            with score_cols[i]:
                score = scores.get(key, 0)
                st.metric(label, f"{score}/10")
                st.markdown(f"{get_emoji(score)} {description}")

        # Test Results
        test_results = results.get('test_results', [])
        if test_results:
            st.markdown("### 🧪 Test Results")

            # Summary metrics
            passed = len([t for t in test_results if t['status'] == 'passed'])
            failed = len([t for t in test_results if t['status'] == 'failed'])
            skipped = len([t for t in test_results if t['status'] in ['skipped', 'warning']])
            total = len(test_results)

            metric_cols = st.columns(4, gap="medium")
            with metric_cols[0]:
                st.metric("Total Tests", total)
            with metric_cols[1]:
                st.metric("Passed", passed, delta=f"{int(passed/total*100)}%" if total > 0 else "0%")
            with metric_cols[2]:
                st.metric("Failed", failed, delta=f"-{int(failed/total*100)}%" if total > 0 and failed > 0 else None)
            with metric_cols[3]:
                st.metric("Skipped", skipped)

            # Detailed test results
            with st.expander("View detailed test results", expanded=False):
                for test in test_results:
                    status_emoji = {
                        'passed': '✅',
                        'failed': '❌',
                        'skipped': '⏭️',
                        'warning': '⚠️'
                    }.get(test['status'], '❓')

                    status_color = {
                        'passed': COLORS["test_passed"],
                        'failed': COLORS["test_failed"],
                        'skipped': COLORS["test_skipped"],
                        'warning': COLORS["test_warning"]
                    }.get(test['status'], COLORS["text_primary"])

                    st.markdown(f"""
                    <div style="border-left: 3px solid {status_color}; padding-left: 12px; margin: 8px 0;">
                        <strong>{status_emoji} {test['name']}</strong><br/>
                        <span style="color: #888; font-size: 0.9em;">
                            Duration: {test.get('duration_ms', 0)}ms
                            {f" | Error: {test.get('error', 'Unknown')}" if test['status'] == 'failed' else ""}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

        # Performance Metrics
        performance = results.get('performance', {})
        if performance and performance.get('page_load_ms', 0) > 0:
            st.markdown("### ⚡ Performance Metrics")

            perf_cols = st.columns(4, gap="medium")
            with perf_cols[0]:
                load_time = performance.get('page_load_ms', 0)
                load_color = "normal" if load_time < THRESHOLDS["page_load_ms_good"] else "inverse"
                st.metric("Page Load", f"{load_time}ms", delta="Fast" if load_time < THRESHOLDS["page_load_ms_good"] else "Slow", delta_color=load_color)

            with perf_cols[1]:
                tti = performance.get('time_to_interactive_ms', 0)
                st.metric("Time to Interactive", f"{tti}ms")

            with perf_cols[2]:
                fcp = performance.get('first_contentful_paint_ms', 0)
                st.metric("First Paint", f"{fcp}ms")

            with perf_cols[3]:
                size = performance.get('total_size_kb', 0)
                size_color = "normal" if size < THRESHOLDS["bundle_size_kb_good"] else "inverse"
                st.metric("Total Size", f"{size}KB", delta="Light" if size < THRESHOLDS["bundle_size_kb_good"] else "Heavy", delta_color=size_color)

        # Screenshots
        st.markdown("### 📸 Screenshots")

        screenshots = results.get('screenshots', [])
        if screenshots:
            screenshot_cols = st.columns(min(len(screenshots), THRESHOLDS["max_screenshots"]), gap="medium")

            for i, screenshot in enumerate(screenshots[:THRESHOLDS["max_screenshots"]]):
                with screenshot_cols[i]:
                    st.markdown(f"**{screenshot['name']}**")
                    try:
                        img = Image.open(screenshot['path'])
                        st.image(img, use_container_width=True)
                        viewport = screenshot.get('viewport', {})
                        st.caption(f"{viewport.get('width', '?')}x{viewport.get('height', '?')}")
                    except Exception as e:
                        st.error(f"Failed to load screenshot: {str(e)}")
        else:
            st.info("No screenshots available")

        # Top recommendations
        recommendations = results.get('recommendations', [])
        if recommendations:
            st.markdown("### 💡 Top Recommendations")
            for i, rec in enumerate(recommendations[:3], 1):
                st.markdown(f"{i}. {rec}")

        # Action buttons
        st.markdown("### 🎯 Next Steps")

        col1, col2, col3 = st.columns(3, gap="medium")

        with col1:
            # Download ZIP
            if st.button("📥 Download ZIP", use_container_width=True):
                project_path = results.get('project_path')
                if project_path:
                    try:
                        zip_data = create_project_zip(project_path)
                        project_name = results.get('project_name', 'project').replace(' ', '_')
                        st.download_button(
                            label="⬇️ Click to Download",
                            data=zip_data,
                            file_name=f"{project_name}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Failed to create ZIP file: {str(e)}")
                else:
                    st.error("Project path not available")

        with col2:
            # Upload to Hugging Face Hub
            if st.button("🤗 Upload to HF Hub", use_container_width=True):
                show_hf_upload_dialog(results)

        with col3:
            # Improve & Rerun
            if st.button("✨ Improve & Rerun", use_container_width=True):
                st.session_state['improve_mode'] = True
                st.session_state['previous_results'] = results
                st.rerun()
    except Exception as e:
        st.error(f"An error occurred while displaying the results: {str(e)}")

def create_project_zip(project_path: str) -> bytes:
    """
    Create ZIP file of project

    Args:
        project_path: Path to project directory

    Returns:
        Bytes of ZIP file

    Raises:
        FileNotFoundError: If project path doesn't exist
        PermissionError: If files can't be read
    """
    project_path = Path(project_path)

    # Validate project path exists
    if not project_path.exists():
        raise FileNotFoundError(f"Project path does not exist: {project_path}")

    if not project_path.is_dir():
        raise ValueError(f"Project path is not a directory: {project_path}")

    zip_buffer = io.BytesIO()

    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(project_path):
                # Skip node_modules, venv, etc.
                dirs[:] = [d for d in dirs if d not in [
                    'node_modules', 'venv', '__pycache__', '.git',
                    'venv312', 'venv314', '.venv'
                ]]

                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, project_path)
                    try:
                        zip_file.write(file_path, arc_name)
                    except (PermissionError, OSError) as e:
                        # Log but continue with other files
                        st.warning(f"Skipped file {file}: {str(e)}")

        zip_buffer.seek(0)
        return zip_buffer.read()
    except Exception as e:
        raise RuntimeError(f"Failed to create ZIP file: {str(e)}")

def show_hf_upload_dialog(results: dict) -> None:
    """
    Display Hugging Face upload dialog with model info.

    Args:
        results: Project results dictionary with model details
    """
    try:
        st.markdown("### 🤗 Upload to Hugging Face Hub")

        project_name = results.get('project_name', 'my-project')
        repo_name = st.text_input(
            "Repository name:",
            value=project_name.lower().replace(' ', '-')
        )

        repo_type = st.radio(
            "Repository type:",
            ["space", "model", "dataset"],
            index=0,
            help="Space = deployable app, Model = ML model, Dataset = data"
        )

        private = st.checkbox("Private repository", value=False)

        if st.button("🚀 Upload"):
            # Get HF token from environment or user input
            hf_token = os.getenv("HF_TOKEN")
            if not hf_token:
                hf_token = st.text_input("Hugging Face token:", type="password")

            if not hf_token:
                st.error("Please provide a Hugging Face token")
                return

            # Upload to HF Hub
            from huggingface_hub import HfApi

            api = HfApi()

            st.info(f"Uploading to {repo_type}/{repo_name}...")

            api.create_repo(
                repo_id=repo_name,
                repo_type=repo_type,
                private=private,
                token=hf_token
            )

            # Upload files
            project_path = results.get('project_path')
            if project_path:
                api.upload_folder(
                    folder_path=project_path,
                    repo_id=repo_name,
                    repo_type=repo_type,
                    token=hf_token
                )

                st.success(f"✅ Uploaded to https://huggingface.co/{repo_type}s/{repo_name}")
            else:
                st.error("Project path not available")
    except Exception as e:
        st.error(f"An error occurred during Hugging Face upload: {str(e)}")