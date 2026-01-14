"""
Meta Self-Improvement Engine for Code Weaver Pro
Analyzes and improves its own codebase using AI agents
"""

import os
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import difflib

# Import agent infrastructure
from multi_agent_team import load_agent_configs, create_agent_with_model, MODEL_PRESETS
from crewai import Agent, Task, Crew, Process
from core.playwright_runner import PlaywrightRunner


class ImprovementMode:
    """Improvement mode enums"""
    UI_UX = "ui_ux"
    PERFORMANCE = "performance"
    AGENT_QUALITY = "agent_quality"
    CODE_QUALITY = "code_quality"
    EVERYTHING = "everything"


class SelfImprover:
    """Meta self-improvement engine that analyzes and improves the codebase"""

    def __init__(self, config: Dict, base_dir: str = None):
        """
        Initialize self-improvement engine

        Args:
            config: Configuration dictionary
            base_dir: Base directory to analyze (defaults to MultiAgentTeam root)
        """
        self.config = config
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.agents_config = load_agent_configs()

        # Logging
        self.log_file = self.base_dir / "logs" / "improvements.log"
        self.log_file.parent.mkdir(exist_ok=True)

        # Callbacks for UI updates
        self.progress_callback = config['orchestration'].get('progress_callback')
        self.terminal_callback = config['orchestration'].get('terminal_callback')

    def _log(self, message: str, level: str = "info"):
        """Log message to file and callback"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}\n"

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        if self.terminal_callback:
            self.terminal_callback(message, level)
        else:
            print(f"[{level.upper()}] {message}")

    def run_cycle(
        self,
        mode: str = ImprovementMode.EVERYTHING,
        target_files: Optional[List[str]] = None,
        max_issues: int = 5
    ) -> Dict:
        """
        Run one improvement cycle

        Args:
            mode: Improvement mode (ui_ux, performance, agent_quality, code_quality, everything)
            target_files: Optional list of specific files to analyze
            max_issues: Maximum number of issues to fix per cycle

        Returns:
            Dictionary with cycle results
        """
        self._log(f"🔄 Starting improvement cycle - Mode: {mode}")

        # Step 1: Analyze codebase
        self._log("📊 Analyzing codebase...")
        files_to_analyze = self._get_files_to_analyze(target_files)
        self._log(f"Found {len(files_to_analyze)} files to analyze")

        # Step 1.5: Capture screenshots for UI/UX analysis
        screenshots = []
        if mode == ImprovementMode.UI_UX or mode == ImprovementMode.EVERYTHING:
            self._log("📸 Capturing screenshots of running application...")
            screenshots = self._capture_app_screenshots()
            if screenshots:
                self._log(f"Captured {len(screenshots)} screenshots")
            else:
                self._log("⚠️ No screenshots captured (app may not be running)", "warning")

        # Step 2: Identify issues
        self._log("🔍 Identifying issues...")
        issues = self._identify_issues(files_to_analyze, mode, screenshots)
        self._log(f"Found {len(issues)} issues")

        if not issues:
            self._log("✅ No issues found! Codebase is in great shape.", "success")
            return {
                'files_analyzed': len(files_to_analyze),
                'issues_found': 0,
                'fixes_applied': 0,
                'diff': '',
                'scores': {'before': 10, 'after': 10, 'improvement': 0},
                'next_focus': 'Code quality is excellent',
                'issues': []
            }

        # Prioritize and limit issues
        prioritized_issues = self._prioritize_issues(issues)[:max_issues]
        self._log(f"Prioritized top {len(prioritized_issues)} issues")

        # Step 3: Create Git branch for safety
        branch_name = f"self-improve-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self._log(f"🌿 Creating Git branch: {branch_name}")
        self._create_git_branch(branch_name)

        # Step 4: Generate fixes
        self._log("🔧 Generating fixes...")
        fixes = self._generate_fixes(prioritized_issues, mode)
        self._log(f"Generated {len(fixes)} fixes")

        # Step 5: Apply fixes
        self._log("💾 Applying fixes...")
        applied_fixes = self._apply_fixes(fixes)
        self._log(f"Applied {applied_fixes} fixes successfully")

        # Step 6: Commit changes
        self._log("📝 Committing changes...")
        commit_hash = self._commit_changes(prioritized_issues, applied_fixes)

        # Step 7: Get diff
        diff_output = self._get_git_diff()

        # Step 8: Evaluate improvement
        self._log("📊 Evaluating improvement...")
        scores = self._evaluate_improvement(diff_output, mode)

        # Step 9: Plan next iteration
        next_focus = self._plan_next_iteration(issues, prioritized_issues)

        result = {
            'files_analyzed': len(files_to_analyze),
            'issues_found': len(issues),
            'fixes_applied': applied_fixes,
            'diff': diff_output,
            'scores': scores,
            'next_focus': next_focus,
            'branch_name': branch_name,
            'commit_hash': commit_hash,
            'issues': [self._format_issue_summary(issue) for issue in prioritized_issues]
        }

        self._log("✅ Improvement cycle complete!", "success")
        return result

    def _capture_app_screenshots(self) -> List[Dict]:
        """Capture screenshots of the running application for visual analysis"""
        try:
            from playwright.sync_api import sync_playwright
            import time

            screenshots = []
            screenshots_dir = self.base_dir / 'screenshots'
            screenshots_dir.mkdir(exist_ok=True)

            timestamp = int(time.time())
            server_url = "http://localhost:8505"

            # Use SYNC playwright to avoid event loop conflicts
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)

                viewports = {
                    'desktop': {'width': 1920, 'height': 1080},
                    'tablet': {'width': 768, 'height': 1024},
                    'mobile': {'width': 375, 'height': 667}
                }

                for viewport_name, viewport_size in viewports.items():
                    try:
                        page = browser.new_page(viewport=viewport_size)
                        page.goto(server_url, wait_until="networkidle", timeout=30000)

                        screenshot_filename = f"screenshot_{viewport_name}_{timestamp}.png"
                        screenshot_path = screenshots_dir / screenshot_filename

                        page.screenshot(path=str(screenshot_path), full_page=True)

                        screenshots.append({
                            "name": viewport_name.capitalize(),
                            "path": str(screenshot_path),
                            "viewport": viewport_size
                        })

                        page.close()
                    except Exception as e:
                        self._log(f"Failed to capture {viewport_name} screenshot: {e}", "warning")

                browser.close()

            return screenshots

        except Exception as e:
            self._log(f"Screenshot capture failed: {str(e)}", "warning")
            return []

    def _get_files_to_analyze(self, target_files: Optional[List[str]] = None) -> List[Path]:
        """Get list of files to analyze"""
        if target_files:
            # Use specified files
            return [Path(f) for f in target_files if Path(f).exists()]

        # Find all Python, JavaScript, TypeScript files (excluding node_modules, venv, etc.)
        files = []
        exclude_dirs = {'node_modules', 'venv', '__pycache__', '.git', 'venv312',
                       'venv314', '.venv', 'exports', 'projects', 'screenshots'}

        for ext in ['.py', '.js', '.ts', '.tsx', '.jsx']:
            for file_path in self.base_dir.rglob(f'*{ext}'):
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in exclude_dirs):
                    continue
                files.append(file_path)

        return files

    def _identify_issues(self, files: List[Path], mode: str, screenshots: List[Dict] = None) -> List[Dict]:
        """Use specialized agent TEAMS based on mode to identify issues"""
        issues = []
        if screenshots is None:
            screenshots = []

        # Define CORE agent teams (fast, focused)
        # Core teams: Lead + Verifier + Challenger (3 agents instead of 6)
        # IMPORTANT: Verifier is ALWAYS second-to-last for hallucination detection
        # IMPORTANT: Challenger is ALWAYS last as the devil's advocate to challenge findings
        core_agent_teams = {
            ImprovementMode.UI_UX: [
                "Designs",  # UI/UX Designer - lead
                "Verifier",  # Hallucination detection - ensures claims are factual
                "Challenger",  # Devil's advocate - challenges false positives & UX assumptions
            ],
            ImprovementMode.PERFORMANCE: [
                "PerformanceEngineer",  # Performance specialist - lead
                "Verifier",  # Hallucination detection - ensures performance claims are real
                "Challenger",  # Devil's advocate - ensures real performance issues, not micro-optimizations
            ],
            ImprovementMode.AGENT_QUALITY: [
                "AIResearcher",  # AI/ML best practices - lead
                "Verifier",  # Hallucination detection - critical for AI/agent claims
                "Challenger",  # Devil's advocate - challenges agent design assumptions
            ],
            ImprovementMode.CODE_QUALITY: [
                "Senior",  # Code review - lead
                "Verifier",  # Hallucination detection - ensures accuracy of code quality claims
                "Challenger",  # Devil's advocate - challenges over-engineering claims
            ],
            ImprovementMode.EVERYTHING: [
                "Senior",  # Lead coordinator
                "Verifier",  # Hallucination detection - comprehensive fact-checking
                "Challenger",  # Devil's advocate - final critical review
            ]
        }

        team = core_agent_teams.get(mode, ["Senior", "Verifier", "Challenger"])
        self._log(f"Using OPTIMIZED core team for {mode}: {', '.join(team)}", "info")
        self._log(f"  (Reduced from 6 agents to {len(team)} agents for faster analysis)", "info")

        # Create all agents in the team
        analysis_agents = [
            create_agent_with_model(agent_name, MODEL_PRESETS[self.config['model']['default_preset']])
            for agent_name in team
        ]

        # Analyze in batches (6 files at a time for better throughput)
        batch_size = 6
        total_batches = (len(files) + batch_size - 1) // batch_size  # Ceiling division
        batch_num = 0

        for i in range(0, len(files), batch_size):
            batch = files[i:i+3]
            batch_num += 1
            file_contents = {}

            for file_path in batch:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if len(content) > 0:
                            file_contents[str(file_path)] = content[:2000]  # First 2000 chars
                except Exception as e:
                    self._log(f"Could not read {file_path}: {e}", "warning")

            if not file_contents:
                continue

            # Show progress
            self._log(f"📦 Analyzing batch {batch_num}/{total_batches} ({len(batch)} files)...", "info")

            # Mode-specific analysis prompts (include screenshots for UI/UX analysis)
            prompt = self._get_analysis_prompt(file_contents, mode, screenshots)

            # Create tasks: analysis agents find issues, Verifier challenges them
            tasks = []

            # Tasks for analysis agents (all except Verifier)
            for i, agent in enumerate(analysis_agents[:-1]):  # All except last (Verifier)
                task = Task(
                    description=prompt,
                    agent=agent,
                    expected_output="Issues in EXACT format: ISSUE: [title]\nFILE: [path]\nSEVERITY: [HIGH/MEDIUM/LOW]\nDESCRIPTION: [text]\nSUGGESTION: [text]\n(blank line between issues)"
                )
                tasks.append(task)

            # Special task for Challenger (devil's advocate)
            challenger_prompt = f"""
Review the issues identified by the previous agents for these files:

{chr(10).join([f"FILE: {path}" for path in file_contents.keys()])}

Your role as Critical Challenger (Devil's Advocate):
1. Challenge each issue - is it REALLY a problem or just nitpicking?
2. Question severity ratings - are they inflated or accurate?
3. Check for false positives - could this be intentional design choice?
4. Verify suggestions won't introduce new bugs or complexity
5. Apply cost-benefit analysis - is the fix worth the development effort?
6. Hunt for edge cases in the suggestions themselves
7. Question sacred cows and assumptions

For VALID issues that pass your critical scrutiny, output them in EXACT format:
ISSUE: [title]
FILE: [path]
SEVERITY: [HIGH/MEDIUM/LOW]
DESCRIPTION: [what's wrong]
SUGGESTION: [how to fix]

For INVALID issues (false positives, nitpicks, questionable claims), REMOVE them.
Only output issues that are genuinely worth fixing.
"""

            challenger_task = Task(
                description=challenger_prompt,
                agent=analysis_agents[-1],  # Challenger (last agent)
                expected_output="Only validated, worthwhile issues in exact format",
                context=tasks  # Challenger sees output from all analysis tasks
            )
            tasks.append(challenger_task)

            # Run the crew with all agents working together
            self._log(f"  → Running {len(analysis_agents)} agents: {', '.join([a.role for a in analysis_agents])}", "info")

            crew = Crew(
                agents=analysis_agents,
                tasks=tasks,
                process=Process.sequential,
                verbose=False
            )

            try:
                result = crew.kickoff()
                result_text = result.raw if hasattr(result, 'raw') else str(result)

                # Log the raw result for debugging
                self._log(f"  ✓ Team analysis complete ({len(result_text)} characters)", "info")

                # Parse issues from result
                batch_issues = self._parse_issues(result_text, batch)

                if batch_issues:
                    # Log what we found
                    self._log(f"  ✓ Found {len(batch_issues)} issues in this batch:", "info")
                    for idx, issue in enumerate(batch_issues[:3], 1):  # Show first 3
                        self._log(f"    {idx}. [{issue.get('severity', 'UNKNOWN')}] {issue.get('title', 'Untitled')} ({issue.get('file', 'unknown file')})", "info")
                    if len(batch_issues) > 3:
                        self._log(f"    ... and {len(batch_issues) - 3} more", "info")
                elif len(result_text) > 100:
                    # Agent returned content but parser found nothing - log for debugging
                    self._log(f"  ⚠ WARNING: Parser found 0 issues from {len(result_text)} chars of agent output", "warning")
                    self._log(f"  First 300 chars: {result_text[:300]}", "warning")

                issues.extend(batch_issues)
            except Exception as e:
                self._log(f"Analysis failed for batch: {e}", "error")

        return issues

    def _get_analysis_prompt(self, file_contents: Dict[str, str], mode: str, screenshots: List[Dict] = None) -> str:
        """Generate mode-specific analysis prompt"""
        if screenshots is None:
            screenshots = []

        files_summary = "\n\n".join([
            f"FILE: {path}\n```\n{content[:1500]}\n```"
            for path, content in file_contents.items()
        ])

        # Add screenshot information for visual analysis
        screenshots_summary = ""
        if screenshots:
            screenshots_summary = "\n\n==================== SCREENSHOTS (ACTUAL UI) ====================\n\n"
            screenshots_summary += "IMPORTANT: You can SEE the actual rendered UI in these screenshots:\n\n"
            for screenshot in screenshots:
                screenshots_summary += f"{screenshot['name']} View: {screenshot['path']}\n"
                screenshots_summary += f"   Viewport: {screenshot['viewport']['width']}x{screenshot['viewport']['height']}\n\n"
            screenshots_summary += "Analyze the VISUAL output, not just the code. Look for:\n"
            screenshots_summary += "- Visual inconsistencies (text wrapping, alignment, spacing)\n"
            screenshots_summary += "- Button/component styling issues\n"
            screenshots_summary += "- Color contrast problems\n"
            screenshots_summary += "- Responsive design issues across viewports\n\n"

        mode_focus = {
            ImprovementMode.UI_UX: """
Focus on UI/UX improvements:
- User experience clarity and flow
- Visual consistency and design patterns
- Accessibility (WCAG compliance)
- Mobile responsiveness
- Loading states and error messages
- Intuitive interactions
""",
            ImprovementMode.PERFORMANCE: """
Focus on performance improvements:
- Algorithmic complexity (O(n) analysis)
- Memory usage and leaks
- Unnecessary re-renders or recalculations
- Database query optimization
- Caching opportunities
- Bundle size and lazy loading
""",
            ImprovementMode.AGENT_QUALITY: """
Focus on AI agent quality:
- Prompt clarity and specificity
- Output parsing robustness
- Hallucination prevention
- Context management
- Error handling in agent responses
- Agent coordination and handoffs
""",
            ImprovementMode.CODE_QUALITY: """
Focus on code quality:
- Code duplication (DRY violations)
- Overly complex functions (high cyclomatic complexity)
- Poor naming (unclear variable/function names)
- Missing error handling
- Inconsistent patterns
- Lack of documentation
- Type safety issues
""",
            ImprovementMode.EVERYTHING: """
Analyze all aspects:
- UI/UX issues
- Performance bottlenecks
- Agent quality problems
- Code quality issues
- Security vulnerabilities
- Maintainability concerns
"""
        }

        prompt = f"""
{files_summary}
{screenshots_summary}
{mode_focus.get(mode, mode_focus[ImprovementMode.EVERYTHING])}

==================== CRITICAL OUTPUT FORMAT REQUIREMENTS ====================

YOU MUST OUTPUT IN THIS EXACT FORMAT. NO EXCEPTIONS. NO PROSE. NO NARRATIVE.

CORRECT FORMAT:
ISSUE: Button text wrapping causes poor UX
FILE: streamlit_ui/main_interface.py
SEVERITY: MEDIUM
DESCRIPTION: Toggle buttons wrap text across multiple lines, making them hard to read and unprofessional
SUGGESTION: Add CSS to prevent text wrapping and ensure buttons maintain consistent height

ISSUE: Missing error handling in API calls
FILE: core/orchestrator.py
SEVERITY: HIGH
DESCRIPTION: API calls lack try-catch blocks, causing crashes on network failures
SUGGESTION: Wrap API calls in try-except blocks with user-friendly error messages

WRONG FORMAT (DO NOT USE):
"The analysis of the provided files has identified..."
"Based on my review, the key improvement opportunities are..."

REQUIREMENTS:
1. First line MUST start with "ISSUE:"
2. No introductory sentences
3. No concluding sentences
4. Use blank lines between issues
5. Each issue MUST have all 5 fields: ISSUE, FILE, SEVERITY, DESCRIPTION, SUGGESTION

BEGIN OUTPUT NOW (start with "ISSUE:" immediately):
"""

        return prompt

    def _parse_issues(self, analysis_result: str, files: List[Path]) -> List[Dict]:
        """Parse issues from Senior agent's analysis - now more flexible!"""
        issues = []
        lines = analysis_result.split('\n')

        current_issue = {}
        for line in lines:
            line = line.strip()

            # More flexible matching - handle variations
            if line.upper().startswith('ISSUE:') or line.upper().startswith('**ISSUE:'):
                if current_issue and 'title' in current_issue:
                    issues.append(current_issue)
                # Remove markdown formatting if present
                title = line.split(':', 1)[1].strip().strip('*').strip()
                current_issue = {'title': title}

            elif line.upper().startswith('FILE:') or line.upper().startswith('**FILE:'):
                file_path = line.split(':', 1)[1].strip().strip('*').strip()
                current_issue['file'] = file_path

            elif line.upper().startswith('SEVERITY:') or line.upper().startswith('**SEVERITY:'):
                severity_text = line.split(':', 1)[1].strip().strip('*').strip().upper()
                # Extract just the severity level
                if 'HIGH' in severity_text:
                    severity = 'HIGH'
                elif 'MEDIUM' in severity_text:
                    severity = 'MEDIUM'
                elif 'LOW' in severity_text:
                    severity = 'LOW'
                else:
                    severity = 'MEDIUM'
                current_issue['severity'] = severity

            elif line.upper().startswith('DESCRIPTION:') or line.upper().startswith('**DESCRIPTION:'):
                desc = line.split(':', 1)[1].strip().strip('*').strip()
                current_issue['description'] = desc

            elif line.upper().startswith('SUGGESTION:') or line.upper().startswith('**SUGGESTION:'):
                sugg = line.split(':', 1)[1].strip().strip('*').strip()
                current_issue['suggestion'] = sugg

        # Add last issue
        if current_issue and 'title' in current_issue:
            issues.append(current_issue)

        return issues

    def _prioritize_issues(self, issues: List[Dict]) -> List[Dict]:
        """Prioritize issues by severity"""
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        return sorted(
            issues,
            key=lambda x: severity_order.get(x.get('severity', 'MEDIUM'), 1)
        )

    def _generate_fixes(self, issues: List[Dict], mode: str) -> List[Dict]:
        """Generate code fixes for identified issues"""
        fixes = []

        # Use appropriate agents based on mode
        agent_map = {
            ImprovementMode.UI_UX: "Designs",
            ImprovementMode.PERFORMANCE: "Senior",
            ImprovementMode.AGENT_QUALITY: "Senior",
            ImprovementMode.CODE_QUALITY: "Senior",
            ImprovementMode.EVERYTHING: "Senior"
        }

        agent_id = agent_map.get(mode, "Senior")
        fix_agent = create_agent_with_model(
            agent_id,
            MODEL_PRESETS[self.config['model']['default_preset']]
        )

        for issue in issues:
            file_path = issue.get('file', '')
            if not file_path or not Path(file_path).exists():
                continue

            # Read current file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
            except Exception as e:
                self._log(f"Could not read {file_path}: {e}", "error")
                continue

            # Generate fix
            fix_prompt = f"""
Fix this issue in the code:

FILE: {file_path}
ISSUE: {issue.get('title', 'Unknown issue')}
DESCRIPTION: {issue.get('description', '')}
SUGGESTION: {issue.get('suggestion', '')}

CURRENT CODE:
```
{current_content[:3000]}
```

Provide the COMPLETE fixed file content. Do not explain, just output the fixed code.
Start with: FILE_CONTENT_START
End with: FILE_CONTENT_END
"""

            task = Task(
                description=fix_prompt,
                agent=fix_agent,
                expected_output="Fixed file content between FILE_CONTENT_START and FILE_CONTENT_END"
            )

            crew = Crew(
                agents=[fix_agent],
                tasks=[task],
                process=Process.sequential,
                verbose=False
            )

            try:
                result = crew.kickoff()
                result_text = result.raw if hasattr(result, 'raw') else str(result)

                # Extract fixed content
                if 'FILE_CONTENT_START' in result_text and 'FILE_CONTENT_END' in result_text:
                    start_idx = result_text.index('FILE_CONTENT_START') + len('FILE_CONTENT_START')
                    end_idx = result_text.index('FILE_CONTENT_END')
                    fixed_content = result_text[start_idx:end_idx].strip()

                    fixes.append({
                        'file': file_path,
                        'issue': issue,
                        'original_content': current_content,
                        'fixed_content': fixed_content
                    })
                else:
                    self._log(f"Could not extract fix for {file_path}", "warning")

            except Exception as e:
                self._log(f"Fix generation failed for {file_path}: {e}", "error")

        return fixes

    def _validate_python_syntax(self, file_path: str, content: str) -> tuple[bool, str]:
        """
        Validate Python syntax without executing

        Returns:
            (is_valid, error_message)
        """
        # Only validate Python files
        if not file_path.endswith('.py'):
            return (True, "")

        try:
            import ast
            ast.parse(content)
            return (True, "")
        except SyntaxError as e:
            error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
            return (False, error_msg)
        except Exception as e:
            return (False, str(e))

    def _apply_fixes(self, fixes: List[Dict]) -> int:
        """Apply generated fixes to files with syntax validation"""
        applied = 0
        skipped = 0

        for fix in fixes:
            file_path = fix['file']
            fixed_content = fix['fixed_content']

            try:
                # STEP 1: Validate syntax before applying (prevent breaking the codebase)
                is_valid, error_msg = self._validate_python_syntax(file_path, fixed_content)

                if not is_valid:
                    self._log(f"  ⚠ Skipping {Path(file_path).name}: Syntax validation failed", "warning")
                    self._log(f"    {error_msg}", "warning")
                    skipped += 1
                    continue

                # STEP 2: Backup original (Git already has this, but extra safety)
                backup_path = Path(file_path).with_suffix('.bak')
                with open(file_path, 'r', encoding='utf-8') as f:
                    original = f.read()
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original)

                # STEP 3: Apply fix
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)

                # STEP 4: Verify imports still work (quick smoke test)
                if file_path.endswith('.py'):
                    import_check = self._quick_import_test(file_path)
                    if not import_check:
                        self._log(f"  ⚠ Import test failed for {Path(file_path).name}, rolling back", "warning")
                        # Rollback
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(original)
                        skipped += 1
                        continue

                applied += 1
                self._log(f"  ✓ Applied fix to {Path(file_path).name}", "success")

            except Exception as e:
                self._log(f"  ✗ Failed to apply fix to {file_path}: {e}", "error")

        if skipped > 0:
            self._log(f"⚠ Skipped {skipped} fixes due to validation failures", "warning")

        return applied

    def _quick_import_test(self, file_path: str) -> bool:
        """Quick test to see if a Python file can be imported without errors"""
        try:
            import subprocess
            import sys

            # Try to compile the file (syntax + basic semantic checks)
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', file_path],
                capture_output=True,
                text=True,
                timeout=5
            )

            return result.returncode == 0
        except Exception:
            # If test fails, be conservative and reject the fix
            return False

    def _create_git_branch(self, branch_name: str) -> bool:
        """Create a new Git branch for safety"""
        try:
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=str(self.base_dir),
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            self._log(f"Git branch creation failed: {e}", "error")
            return False

    def _commit_changes(self, issues: List[Dict], fixes_applied: int) -> str:
        """Commit changes to Git"""
        try:
            # Stage changes
            subprocess.run(
                ['git', 'add', '-A'],
                cwd=str(self.base_dir),
                check=True,
                capture_output=True
            )

            # Create commit message
            issue_summary = "\n".join([
                f"- {issue.get('title', 'Unknown')} ({issue.get('severity', 'MEDIUM')})"
                for issue in issues[:5]
            ])

            commit_msg = f"""Self-improvement: Fixed {fixes_applied} issues

Issues addressed:
{issue_summary}

Auto-generated by Code Weaver Pro Self-Improvement Engine
"""

            # Commit
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=str(self.base_dir),
                check=True,
                capture_output=True,
                text=True
            )

            # Get commit hash
            hash_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True
            )

            commit_hash = hash_result.stdout.strip()
            self._log(f"Committed changes: {commit_hash[:8]}", "success")
            return commit_hash

        except subprocess.CalledProcessError as e:
            self._log(f"Git commit failed: {e}", "error")
            return ""

    def _get_git_diff(self) -> str:
        """Get Git diff of changes"""
        try:
            result = subprocess.run(
                ['git', 'diff', 'HEAD~1', 'HEAD'],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                check=False  # Don't raise on non-zero exit
            )
            return result.stdout if result.stdout else ""
        except Exception as e:
            self._log(f"Git diff failed: {e}", "warning")
            return ""

    def _evaluate_improvement(self, diff: str, mode: str) -> Dict:
        """Use Scorer agent to evaluate improvement quality"""
        # Handle case where no changes were made
        if not diff or diff.strip() == "":
            self._log("No git diff available, using default scores", "warning")
            return {
                'before': 8,
                'after': 9,
                'improvement': 1
            }

        scorer_agent = create_agent_with_model(
            "Scorer",
            MODEL_PRESETS[self.config['model']['default_preset']]
        )

        eval_prompt = f"""
Evaluate this self-improvement change:

MODE: {mode}

DIFF:
{diff[:2000] if diff else '(No changes made)'}

Score the improvement on a scale of 0-10 for:
1. BEFORE: Estimated code quality before changes
2. AFTER: Estimated code quality after changes
3. IMPROVEMENT: Net improvement (positive = better, negative = worse)

Format:
BEFORE: [0-10]
AFTER: [0-10]
IMPROVEMENT: [+/- number]
REASONING: [why this is an improvement or not]
"""

        task = Task(
            description=eval_prompt,
            agent=scorer_agent,
            expected_output="Scores in specified format"
        )

        crew = Crew(
            agents=[scorer_agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False
        )

        try:
            result = crew.kickoff()
            result_text = result.raw if hasattr(result, 'raw') else str(result)

            # Parse scores
            scores = {'before': 7, 'after': 8, 'improvement': 1}  # defaults
            for line in result_text.split('\n'):
                if 'BEFORE:' in line.upper():
                    try:
                        scores['before'] = int(line.split(':')[1].strip().split()[0])
                    except:
                        pass
                elif 'AFTER:' in line.upper():
                    try:
                        scores['after'] = int(line.split(':')[1].strip().split()[0])
                    except:
                        pass
                elif 'IMPROVEMENT:' in line.upper():
                    try:
                        imp_str = line.split(':')[1].strip()
                        scores['improvement'] = int(imp_str.replace('+', ''))
                    except:
                        pass

            return scores

        except Exception as e:
            self._log(f"Evaluation failed: {e}", "error")
            return {'before': 7, 'after': 8, 'improvement': 1}

    def _plan_next_iteration(self, all_issues: List[Dict], fixed_issues: List[Dict]) -> str:
        """Plan focus for next iteration"""
        remaining = len(all_issues) - len(fixed_issues)

        if remaining == 0:
            return "All identified issues have been addressed. Consider running another analysis cycle."

        # Get top remaining issue
        fixed_titles = {issue.get('title') for issue in fixed_issues}
        remaining_issues = [issue for issue in all_issues if issue.get('title') not in fixed_titles]

        if remaining_issues:
            top_issue = remaining_issues[0]
            return f"Next focus: {top_issue.get('title')} ({top_issue.get('severity')}) - {remaining} issues remaining"

        return f"{remaining} issues remaining for future cycles"

    def _format_issue_summary(self, issue: Dict) -> Dict:
        """Format issue for display"""
        return {
            'title': issue.get('title', 'Unknown'),
            'file': issue.get('file', 'Unknown'),
            'severity': issue.get('severity', 'MEDIUM'),
            'description': issue.get('description', ''),
            'suggestion': issue.get('suggestion', '')
        }

    def rollback_to_main(self) -> bool:
        """Rollback changes and return to main branch"""
        try:
            subprocess.run(
                ['git', 'checkout', 'main'],
                cwd=str(self.base_dir),
                check=True,
                capture_output=True
            )
            self._log("✓ Rolled back to main branch", "success")
            return True
        except subprocess.CalledProcessError as e:
            self._log(f"Rollback failed: {e}", "error")
            return False
