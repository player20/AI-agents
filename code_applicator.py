"""
Code Application System for Multi-Agent Team

Safely applies agent-suggested code changes to existing codebases with:
- Git branch creation for safety
- Automated file modifications
- Rollback capability
- PR creation for review
- GitHub repository cloning and analysis
"""

import os
import re
import git
from datetime import datetime
from pathlib import Path
import subprocess
import json
import tempfile
import shutil

class CodeApplicator:
    """Applies code changes suggested by agents to actual files"""

    def __init__(self, target_repo_path=None):
        """
        Initialize code applicator

        Args:
            target_repo_path: Path to the git repository to modify (optional for GitHub cloning)
        """
        self.target_repo = target_repo_path
        self.repo = None
        self.original_branch = None
        self.changes_made = []
        self.temp_dir = None  # Track temporary directory for cleanup

    def clone_from_github(self, github_url, target_dir=None):
        """
        Clone a GitHub repository to a temporary directory

        Args:
            github_url: GitHub repository URL (e.g., https://github.com/user/repo)
            target_dir: Optional target directory (creates temp dir if not provided)

        Returns:
            Tuple of (success, message)
        """
        try:
            # Create temporary directory if not provided
            if not target_dir:
                self.temp_dir = tempfile.mkdtemp(prefix="ai-agents-")
                target_dir = self.temp_dir

            # Clone repository
            self.repo = git.Repo.clone_from(github_url, target_dir)
            self.target_repo = target_dir

            return True, f"Cloned {github_url} to {target_dir}"
        except git.GitCommandError as e:
            return False, f"Error cloning repository: {str(e)}"
        except Exception as e:
            return False, f"Error cloning repository: {str(e)}"

    def cleanup_temp_repo(self):
        """
        Clean up temporary repository directory

        Returns:
            Tuple of (success, message)
        """
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                return True, f"Cleaned up temporary directory: {self.temp_dir}"
            return True, "No temporary directory to clean up"
        except Exception as e:
            return False, f"Error cleaning up temporary directory: {str(e)}"

    def validate_repo(self):
        """Validate that target is a git repository"""
        try:
            self.repo = git.Repo(self.target_repo)
            if self.repo.bare:
                return False, "Repository is bare"

            # Check for uncommitted changes
            if self.repo.is_dirty():
                return False, "Repository has uncommitted changes. Please commit or stash them first."

            return True, "Repository validated"
        except git.InvalidGitRepositoryError:
            return False, f"{self.target_repo} is not a git repository"
        except Exception as e:
            return False, f"Error validating repository: {str(e)}"

    def create_feature_branch(self, branch_name=None):
        """
        Create a new branch for applying changes

        Args:
            branch_name: Optional custom branch name

        Returns:
            Tuple of (success, message)
        """
        try:
            # Store original branch
            self.original_branch = self.repo.active_branch.name

            # Generate branch name if not provided
            if not branch_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                branch_name = f"ai-agents/changes-{timestamp}"

            # Create and checkout new branch
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()

            return True, f"Created and switched to branch: {branch_name}"
        except Exception as e:
            return False, f"Error creating branch: {str(e)}"

    def parse_code_blocks(self, agent_outputs):
        """
        Extract code suggestions from agent outputs

        Args:
            agent_outputs: Dict of agent role -> output text

        Returns:
            List of dicts with {file_path, old_code, new_code, agent, description}
        """
        suggestions = []

        # Pattern to match code blocks with file references
        # Matches: filename.ext followed by ```language code ```
        pattern = r'(?:File:|Path:|`?)([a-zA-Z0-9_/\\\.\-]+\.[a-zA-Z0-9]+)(?:`?)\s*```(\w+)?\s*(.*?)```'

        for agent_role, output in agent_outputs.items():
            # Skip system logs
            if agent_role == "System":
                continue

            # Find all code blocks
            matches = re.finditer(pattern, output, re.DOTALL)

            for match in matches:
                file_path = match.group(1)
                language = match.group(2) or "unknown"
                code = match.group(3).strip()

                # Extract description (text before the code block)
                code_start = match.start()
                context_start = max(0, code_start - 200)
                context = output[context_start:code_start]

                suggestions.append({
                    "file_path": file_path,
                    "code": code,
                    "language": language,
                    "agent": agent_role,
                    "description": context.strip()[-100:] if context.strip() else "Code suggestion"
                })

        return suggestions

    def apply_code_changes(self, suggestions, create_if_missing=False):
        """
        Apply code changes to files

        Args:
            suggestions: List of code suggestions from parse_code_blocks()
            create_if_missing: Whether to create files that don't exist

        Returns:
            Tuple of (success_count, failure_count, details)
        """
        success_count = 0
        failure_count = 0
        details = []

        for suggestion in suggestions:
            file_path = suggestion["file_path"]
            code = suggestion["code"]
            agent = suggestion["agent"]

            # Resolve file path (could be relative to repo root)
            full_path = os.path.join(self.target_repo, file_path)

            try:
                # Check if file exists
                if not os.path.exists(full_path):
                    if create_if_missing:
                        # Create directory if needed
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)

                        # Write new file
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(code)

                        self.changes_made.append({
                            "file": file_path,
                            "action": "created",
                            "agent": agent
                        })

                        success_count += 1
                        details.append(f"✓ Created: {file_path} (by {agent})")
                    else:
                        failure_count += 1
                        details.append(f"✗ Skipped: {file_path} (file doesn't exist)")
                        continue
                else:
                    # Read existing file
                    with open(full_path, 'r', encoding='utf-8') as f:
                        original_content = f.read()

                    # Write new code
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(code)

                    self.changes_made.append({
                        "file": file_path,
                        "action": "modified",
                        "agent": agent,
                        "original": original_content
                    })

                    success_count += 1
                    details.append(f"✓ Modified: {file_path} (by {agent})")

            except Exception as e:
                failure_count += 1
                details.append(f"✗ Error: {file_path} - {str(e)}")

        return success_count, failure_count, details

    def commit_changes(self, commit_message=None):
        """
        Commit all changes

        Args:
            commit_message: Optional custom commit message

        Returns:
            Tuple of (success, message)
        """
        try:
            # Add all changed files
            self.repo.git.add(A=True)

            # Generate commit message if not provided
            if not commit_message:
                file_count = len(self.changes_made)
                agents = set(change["agent"] for change in self.changes_made)
                agent_list = ", ".join(agents)

                commit_message = f"Apply AI agent suggestions\n\n"
                commit_message += f"Changes from agents: {agent_list}\n"
                commit_message += f"Files modified: {file_count}\n\n"

                for change in self.changes_made:
                    commit_message += f"- {change['action'].capitalize()}: {change['file']} (by {change['agent']})\n"

                commit_message += f"\n🤖 Generated by Multi-Agent Team\n"
                commit_message += f"Timestamp: {datetime.now().isoformat()}"

            # Commit
            self.repo.index.commit(commit_message)

            return True, f"Committed {len(self.changes_made)} changes"
        except Exception as e:
            return False, f"Error committing changes: {str(e)}"

    def create_pull_request(self, title=None, body=None):
        """
        Create a pull request using GitHub CLI

        Args:
            title: PR title
            body: PR description

        Returns:
            Tuple of (success, message/pr_url)
        """
        try:
            # Check if gh CLI is available
            result = subprocess.run(['gh', '--version'],
                                    capture_output=True,
                                    text=True,
                                    timeout=5)

            if result.returncode != 0:
                return False, "GitHub CLI (gh) not installed. Install from: https://cli.github.com/"

            # Generate PR title and body if not provided
            if not title:
                title = f"AI Agent Suggestions - {datetime.now().strftime('%Y-%m-%d')}"

            if not body:
                body = "## AI-Generated Changes\n\n"
                body += "This PR contains code changes suggested by the Multi-Agent Development Team.\n\n"
                body += "### Changes Summary\n\n"

                for change in self.changes_made:
                    body += f"- **{change['action'].capitalize()}**: `{change['file']}` (by {change['agent']} agent)\n"

                body += f"\n### Review Checklist\n\n"
                body += "- [ ] Code changes are correct and safe\n"
                body += "- [ ] No sensitive data or credentials exposed\n"
                body += "- [ ] Tests pass (if applicable)\n"
                body += "- [ ] Documentation updated (if needed)\n\n"
                body += f"🤖 Generated by [Multi-Agent Team](https://github.com/anthropics/multi-agent-team)\n"

            # Push branch to remote
            current_branch = self.repo.active_branch.name
            self.repo.git.push('origin', current_branch, set_upstream=True)

            # Create PR
            result = subprocess.run(
                ['gh', 'pr', 'create', '--title', title, '--body', body],
                cwd=self.target_repo,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                pr_url = result.stdout.strip()
                return True, pr_url
            else:
                return False, f"Error creating PR: {result.stderr}"

        except FileNotFoundError:
            return False, "GitHub CLI (gh) not found. Install from: https://cli.github.com/"
        except Exception as e:
            return False, f"Error creating PR: {str(e)}"

    def rollback_changes(self):
        """
        Rollback all changes and return to original branch

        Returns:
            Tuple of (success, message)
        """
        try:
            # Reset to original branch
            if self.original_branch:
                self.repo.git.checkout(self.original_branch, force=True)

            # Delete feature branch if it exists
            current_branch = self.repo.active_branch.name
            if current_branch != self.original_branch and current_branch.startswith("ai-agents/"):
                self.repo.delete_head(current_branch, force=True)

            self.changes_made = []
            return True, "Rolled back all changes successfully"
        except Exception as e:
            return False, f"Error rolling back: {str(e)}"

    def get_diff_summary(self):
        """
        Get a summary of changes made

        Returns:
            String with diff summary
        """
        try:
            # Get diff between current branch and original
            if self.original_branch:
                diff = self.repo.git.diff(self.original_branch)
                return diff
            return "No changes to show"
        except Exception as e:
            return f"Error getting diff: {str(e)}"


def apply_agent_changes_workflow(agent_outputs, target_repo_path,
                                  create_branch=True, create_pr=True,
                                  auto_commit=True, create_new_files=False):
    """
    Complete workflow for applying agent changes

    Args:
        agent_outputs: Dict of agent outputs
        target_repo_path: Path to target repository
        create_branch: Whether to create a new branch
        create_pr: Whether to create a PR (requires create_branch=True)
        auto_commit: Whether to auto-commit changes
        create_new_files: Whether to create files that don't exist

    Returns:
        Dict with status, messages, and details
    """
    result = {
        "success": False,
        "messages": [],
        "changes": 0,
        "pr_url": None,
        "branch_name": None
    }

    applicator = CodeApplicator(target_repo_path)

    # Validate repository
    valid, msg = applicator.validate_repo()
    result["messages"].append(msg)

    if not valid:
        return result

    # Create feature branch if requested
    if create_branch:
        success, msg = applicator.create_feature_branch()
        result["messages"].append(msg)

        if not success:
            return result

        result["branch_name"] = applicator.repo.active_branch.name

    # Parse code suggestions
    suggestions = applicator.parse_code_blocks(agent_outputs)
    result["messages"].append(f"Found {len(suggestions)} code suggestions")

    if len(suggestions) == 0:
        result["messages"].append("No code changes to apply")
        return result

    # Apply changes
    success_count, failure_count, details = applicator.apply_code_changes(
        suggestions,
        create_if_missing=create_new_files
    )

    result["changes"] = success_count
    result["messages"].extend(details)

    # Commit if requested
    if auto_commit and success_count > 0:
        success, msg = applicator.commit_changes()
        result["messages"].append(msg)

        if not success:
            return result

    # Create PR if requested
    if create_pr and create_branch and success_count > 0:
        success, msg = applicator.create_pull_request()

        if success:
            result["pr_url"] = msg
            result["messages"].append(f"Pull request created: {msg}")
        else:
            result["messages"].append(f"PR creation failed: {msg}")

    # Get diff summary
    diff = applicator.get_diff_summary()
    result["diff"] = diff
    result["success"] = success_count > 0

    return result


def apply_agent_changes_from_github(agent_outputs, github_url,
                                     create_branch=True, create_pr=True,
                                     auto_commit=True, create_new_files=False,
                                     cleanup_after=True):
    """
    Complete workflow for applying agent changes to a GitHub repository

    Args:
        agent_outputs: Dict of agent outputs
        github_url: GitHub repository URL (e.g., https://github.com/user/repo)
        create_branch: Whether to create a new branch
        create_pr: Whether to create a PR (requires create_branch=True)
        auto_commit: Whether to auto-commit changes
        create_new_files: Whether to create files that don't exist
        cleanup_after: Whether to clean up temporary directory after completion

    Returns:
        Dict with status, messages, and details
    """
    result = {
        "success": False,
        "messages": [],
        "changes": 0,
        "pr_url": None,
        "branch_name": None,
        "temp_dir": None
    }

    applicator = CodeApplicator()

    try:
        # Clone repository from GitHub
        success, msg = applicator.clone_from_github(github_url)
        result["messages"].append(msg)
        result["temp_dir"] = applicator.temp_dir

        if not success:
            return result

        # Validate repository
        valid, msg = applicator.validate_repo()
        result["messages"].append(msg)

        if not valid:
            return result

        # Create feature branch if requested
        if create_branch:
            success, msg = applicator.create_feature_branch()
            result["messages"].append(msg)

            if not success:
                return result

            result["branch_name"] = applicator.repo.active_branch.name

        # Parse code suggestions
        suggestions = applicator.parse_code_blocks(agent_outputs)
        result["messages"].append(f"Found {len(suggestions)} code suggestions")

        if len(suggestions) == 0:
            result["messages"].append("No code changes to apply")
            return result

        # Apply changes
        success_count, failure_count, details = applicator.apply_code_changes(
            suggestions,
            create_if_missing=create_new_files
        )

        result["changes"] = success_count
        result["messages"].extend(details)

        # Commit if requested
        if auto_commit and success_count > 0:
            success, msg = applicator.commit_changes()
            result["messages"].append(msg)

            if not success:
                return result

        # Create PR if requested
        if create_pr and create_branch and success_count > 0:
            success, msg = applicator.create_pull_request()

            if success:
                result["pr_url"] = msg
                result["messages"].append(f"Pull request created: {msg}")
            else:
                result["messages"].append(f"PR creation failed: {msg}")

        # Get diff summary
        diff = applicator.get_diff_summary()
        result["diff"] = diff
        result["success"] = success_count > 0

        return result

    finally:
        # Clean up temporary directory if requested
        if cleanup_after:
            cleanup_success, cleanup_msg = applicator.cleanup_temp_repo()
            result["messages"].append(cleanup_msg)
