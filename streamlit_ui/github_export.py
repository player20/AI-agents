"""
One-Click GitHub Export

Allows users to export generated projects or audit reports to GitHub.
Supports creating new repos or pushing to existing ones.
"""

import streamlit as st
import subprocess
import tempfile
import shutil
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import base64
import requests


class GitHubExporter:
    """
    Handles exporting content to GitHub repositories.

    Supports:
    - Creating new repositories
    - Pushing to existing repositories
    - Branch creation
    - Commit with attribution
    """

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the GitHub exporter.

        Args:
            token: GitHub personal access token (or from env)
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.api_base = "https://api.github.com"

    @property
    def is_configured(self) -> bool:
        """Check if GitHub token is available."""
        return bool(self.token)

    def _headers(self) -> Dict[str, str]:
        """Get API headers with authentication."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def get_user(self) -> Optional[Dict]:
        """Get authenticated user info."""
        if not self.is_configured:
            return None
        try:
            resp = requests.get(f"{self.api_base}/user", headers=self._headers())
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    def create_repo(self, name: str, description: str = "", private: bool = False) -> Optional[Dict]:
        """
        Create a new GitHub repository.

        Args:
            name: Repository name
            description: Repository description
            private: Whether to make it private

        Returns:
            Repository data or None on failure
        """
        if not self.is_configured:
            return None

        payload = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": True  # Initialize with README
        }

        try:
            resp = requests.post(
                f"{self.api_base}/user/repos",
                headers=self._headers(),
                json=payload
            )
            if resp.status_code == 201:
                return resp.json()
            else:
                st.error(f"Failed to create repo: {resp.json().get('message', 'Unknown error')}")
        except Exception as e:
            st.error(f"GitHub API error: {str(e)}")
        return None

    def push_file(self, owner: str, repo: str, path: str, content: str,
                  message: str, branch: str = "main") -> bool:
        """
        Push a single file to a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in repo
            content: File content
            message: Commit message
            branch: Target branch

        Returns:
            True on success
        """
        if not self.is_configured:
            return False

        # Get existing file SHA if it exists
        sha = None
        try:
            resp = requests.get(
                f"{self.api_base}/repos/{owner}/{repo}/contents/{path}",
                headers=self._headers(),
                params={"ref": branch}
            )
            if resp.status_code == 200:
                sha = resp.json().get("sha")
        except Exception:
            pass

        # Create/update file
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": branch
        }
        if sha:
            payload["sha"] = sha

        try:
            resp = requests.put(
                f"{self.api_base}/repos/{owner}/{repo}/contents/{path}",
                headers=self._headers(),
                json=payload
            )
            return resp.status_code in [200, 201]
        except Exception:
            return False

    def push_directory(self, owner: str, repo: str, local_path: str,
                      message: str, branch: str = "main") -> bool:
        """
        Push a local directory to a repository using git.

        Args:
            owner: Repository owner
            repo: Repository name
            local_path: Path to local directory
            message: Commit message
            branch: Target branch

        Returns:
            True on success
        """
        if not self.is_configured:
            return False

        repo_url = f"https://{self.token}@github.com/{owner}/{repo}.git"

        try:
            # Initialize git in the directory
            subprocess.run(["git", "init"], cwd=local_path, capture_output=True, check=True)

            # Configure git
            subprocess.run(["git", "config", "user.email", "weaver-pro@ai.generated"],
                          cwd=local_path, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.name", "Weaver Pro AI"],
                          cwd=local_path, capture_output=True, check=True)

            # Add remote
            subprocess.run(["git", "remote", "add", "origin", repo_url],
                          cwd=local_path, capture_output=True, check=True)

            # Add all files
            subprocess.run(["git", "add", "."],
                          cwd=local_path, capture_output=True, check=True)

            # Commit
            full_message = f"{message}\n\nGenerated by Weaver Pro AI"
            subprocess.run(["git", "commit", "-m", full_message],
                          cwd=local_path, capture_output=True, check=True)

            # Push
            result = subprocess.run(
                ["git", "push", "-u", "origin", branch, "--force"],
                cwd=local_path,
                capture_output=True
            )

            return result.returncode == 0

        except subprocess.CalledProcessError as e:
            st.error(f"Git error: {e.stderr.decode() if e.stderr else str(e)}")
            return False
        except Exception as e:
            st.error(f"Export error: {str(e)}")
            return False


def render_github_export(content: Dict[str, Any], content_type: str = "project"):
    """
    Render the GitHub export UI.

    Args:
        content: Content to export (project files or report data)
        content_type: Type of content ("project" or "report")
    """
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h3>🚀 Export to GitHub</h3>
        <p style='color: #9ca3af;'>Push your project directly to a GitHub repository</p>
    </div>
    """, unsafe_allow_html=True)

    exporter = GitHubExporter()

    # Check for GitHub token
    if not exporter.is_configured:
        st.warning("⚠️ GitHub token not configured")
        st.markdown("""
        **To enable GitHub export:**

        1. Create a GitHub Personal Access Token at [github.com/settings/tokens](https://github.com/settings/tokens)
        2. Select scopes: `repo` (full control)
        3. Add to your `.env` file:
        ```
        GITHUB_TOKEN=ghp_your_token_here
        ```
        4. Restart the app
        """)

        # Allow manual token entry for this session
        with st.expander("🔑 Enter token for this session"):
            session_token = st.text_input("GitHub Token", type="password", key="github_token_input")
            if session_token:
                exporter.token = session_token
                st.success("Token set for this session")

    if not exporter.is_configured:
        return

    # Get user info
    user = exporter.get_user()
    if user:
        st.success(f"✅ Connected as **{user.get('login')}**")
    else:
        st.error("Failed to authenticate with GitHub. Check your token.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Repository Options")

        repo_mode = st.radio(
            "Repository",
            ["Create new repository", "Push to existing"],
            key="repo_mode"
        )

        if repo_mode == "Create new repository":
            repo_name = st.text_input(
                "Repository name",
                value=content.get('project_name', f'weaver-project-{datetime.now().strftime("%Y%m%d")}').lower().replace(' ', '-'),
                key="repo_name"
            )
            repo_desc = st.text_input(
                "Description",
                value=f"Generated by Weaver Pro AI - {content_type.title()}",
                key="repo_desc"
            )
            is_private = st.checkbox("Private repository", value=False, key="is_private")
        else:
            repo_full = st.text_input(
                "Repository (owner/repo)",
                placeholder="username/repo-name",
                key="repo_full"
            )
            repo_name = repo_full.split('/')[-1] if '/' in repo_full else repo_full

    with col2:
        st.markdown("### Export Options")

        branch = st.text_input("Branch", value="main", key="branch")

        commit_msg = st.text_area(
            "Commit message",
            value=f"Initial commit: {content_type.title()} generated by Weaver Pro",
            height=100,
            key="commit_msg"
        )

        if content_type == "project":
            st.info(f"📁 {len(content.get('files', {}))} files will be exported")
        elif content_type == "report":
            st.info("📄 Report will be exported as HTML and JSON")

    st.markdown("---")

    # Export button
    if st.button("🚀 Export to GitHub", type="primary", use_container_width=True, key="export_btn"):
        with st.spinner("Exporting to GitHub..."):
            success = False

            if repo_mode == "Create new repository":
                # Create repository
                repo = exporter.create_repo(repo_name, repo_desc, is_private)
                if repo:
                    owner = user.get('login')
                    st.success(f"✅ Created repository: {owner}/{repo_name}")

                    # Push files
                    if content_type == "project":
                        success = _export_project_files(exporter, owner, repo_name, content, commit_msg, branch)
                    else:
                        success = _export_report(exporter, owner, repo_name, content, commit_msg, branch)
            else:
                # Push to existing
                if '/' in repo_full:
                    owner, repo_name = repo_full.split('/', 1)

                    if content_type == "project":
                        success = _export_project_files(exporter, owner, repo_name, content, commit_msg, branch)
                    else:
                        success = _export_report(exporter, owner, repo_name, content, commit_msg, branch)
                else:
                    st.error("Please enter repository as owner/repo")

            if success:
                repo_url = f"https://github.com/{owner}/{repo_name}"
                st.success(f"✅ Successfully exported to GitHub!")
                st.markdown(f"**[View Repository]({repo_url})**")
                st.balloons()
            else:
                st.error("Export failed. Check the error messages above.")


def _export_project_files(exporter: GitHubExporter, owner: str, repo: str,
                         content: Dict, message: str, branch: str) -> bool:
    """Export project files to GitHub."""
    files = content.get('files', {})
    if not files:
        st.warning("No files to export")
        return False

    # Create temp directory with project files
    with tempfile.TemporaryDirectory() as temp_dir:
        for file_path, file_content in files.items():
            full_path = Path(temp_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(file_content)

        # Add README
        readme_content = f"""# {content.get('project_name', 'Weaver Pro Project')}

{content.get('description', 'Generated by Weaver Pro AI')}

## Generated Files

{chr(10).join(f'- `{f}`' for f in files.keys())}

## About

This project was generated by [Weaver Pro](https://github.com/weaver-pro) - an AI-powered application generator.

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        (Path(temp_dir) / "README.md").write_text(readme_content)

        # Push using git
        return exporter.push_directory(owner, repo, temp_dir, message, branch)


def _export_report(exporter: GitHubExporter, owner: str, repo: str,
                  content: Dict, message: str, branch: str) -> bool:
    """Export audit report to GitHub."""
    success = True

    # Export as JSON
    json_content = json.dumps(content, indent=2, default=str)
    if not exporter.push_file(owner, repo, "report/audit_data.json", json_content, message, branch):
        st.warning("Failed to push JSON data")
        success = False

    # Export HTML if available
    if 'html_content' in content:
        if not exporter.push_file(owner, repo, "report/index.html", content['html_content'], message, branch):
            st.warning("Failed to push HTML report")
            success = False

    # Create README
    readme = f"""# Audit Report

Generated by Weaver Pro AI on {datetime.now().strftime('%Y-%m-%d')}

## Report Files

- `audit_data.json` - Raw audit data
- `index.html` - Interactive HTML report

## View Report

Open `index.html` in a browser or use GitHub Pages to host it.

---

*Generated by [Weaver Pro](https://github.com/weaver-pro)*
"""
    if not exporter.push_file(owner, repo, "README.md", readme, message, branch):
        st.warning("Failed to push README")
        success = False

    return success


# Quick export button component
def github_export_button(content: Dict[str, Any], content_type: str = "project"):
    """
    Render a simple GitHub export button that opens the export dialog.

    Args:
        content: Content to export
        content_type: Type of content
    """
    if st.button("🚀 Export to GitHub", key="quick_github_export", use_container_width=True):
        st.session_state['github_export_content'] = content
        st.session_state['github_export_type'] = content_type
        st.session_state['show_github_export'] = True
        st.rerun()

    # Show export dialog if triggered
    if st.session_state.get('show_github_export', False):
        with st.expander("GitHub Export", expanded=True):
            render_github_export(
                st.session_state.get('github_export_content', {}),
                st.session_state.get('github_export_type', 'project')
            )

            if st.button("Close", key="close_github_export"):
                st.session_state['show_github_export'] = False
                st.rerun()
