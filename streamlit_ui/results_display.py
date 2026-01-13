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


def display_results(results: dict):
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
    st.markdown("---")
    st.markdown("# 🎉 Your App is Ready!")

    # Project summary
    col1, col2 = st.columns([2, 1])

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

    def get_emoji(score):
        for score_range, emoji in score_emojis.items():
            if score in score_range:
                return emoji
        return "⚪"

    score_cols = st.columns(4)

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

    # Screenshots
    st.markdown("### 📸 Screenshots")

    screenshots = results.get('screenshots', [])
    if screenshots:
        screenshot_cols = st.columns(min(len(screenshots), 3))

        for i, screenshot in enumerate(screenshots[:3]):  # Show max 3
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

    col1, col2, col3 = st.columns(3)

    with col1:
        # Download ZIP
        if st.button("📥 Download ZIP", use_container_width=True):
            project_path = results.get('project_path')
            if project_path:
                zip_data = create_project_zip(project_path)
                project_name = results.get('project_name', 'project').replace(' ', '_')
                st.download_button(
                    label="⬇️ Click to Download",
                    data=zip_data,
                    file_name=f"{project_name}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
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


def create_project_zip(project_path: str) -> bytes:
    """
    Create ZIP file of project

    Args:
        project_path: Path to project directory

    Returns:
        Bytes of ZIP file
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        project_path = Path(project_path)

        for root, dirs, files in os.walk(project_path):
            # Skip node_modules, venv, etc.
            dirs[:] = [d for d in dirs if d not in [
                'node_modules', 'venv', '__pycache__', '.git',
                'venv312', 'venv314', '.venv'
            ]]

            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, project_path)
                zip_file.write(file_path, arc_name)

    zip_buffer.seek(0)
    return zip_buffer.read()


def show_hf_upload_dialog(results: dict):
    """Show Hugging Face upload dialog"""
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
        try:
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
            st.error(f"Upload failed: {str(e)}")
