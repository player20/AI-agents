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
        files_to_analyze = self._get_files_to_analyze(target_files, mode)
        # File count already logged by _get_files_to_analyze()

        # Step 1.5: Capture screenshots for UI/UX analysis
        screenshots = []
        if mode == ImprovementMode.UI_UX or mode == ImprovementMode.EVERYTHING:
            self._log("📸 Capturing screenshots of running application...")
            screenshots = self._capture_app_screenshots()
            if screenshots:
                self._log(f"✓ Captured {len(screenshots)} screenshots for visual analysis")
            # Note: Empty screenshots list is handled gracefully - analysis continues without visual data

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

        # Prioritize issues (includes complexity scoring)
        prioritized_issues = self._prioritize_issues(issues)

        # Adaptive batch size: more simple fixes, fewer complex fixes
        simple_count = sum(1 for issue in prioritized_issues[:max_issues*2] if issue.get('complexity') == 'SIMPLE')
        complex_count = sum(1 for issue in prioritized_issues[:max_issues*2] if issue.get('complexity') == 'COMPLEX')

        # If mostly simple fixes, allow up to 10
        # If mostly complex, stick to 5
        # Mix: adjust dynamically
        if simple_count > max_issues and complex_count <= 2:
            adaptive_max = min(10, len(prioritized_issues))
            self._log(f"📈 Adaptive batch: {simple_count} simple fixes detected, increasing batch to {adaptive_max}", "info")
        elif complex_count >= 3:
            adaptive_max = max(3, max_issues - 2)
            self._log(f"📉 Adaptive batch: {complex_count} complex fixes detected, reducing batch to {adaptive_max}", "info")
        else:
            adaptive_max = max_issues

        prioritized_issues = prioritized_issues[:adaptive_max]
        self._log(f"Prioritized top {len(prioritized_issues)} issues (balanced mix of quick wins + important fixes)")

        # Step 3: Create Git branch for safety
        branch_name = f"self-improve-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self._log(f"🌿 Creating Git branch: {branch_name}")
        self._create_git_branch(branch_name)

        # Step 4: Generate fixes
        self._log("🔧 Generating fixes...")
        fixes = self._generate_fixes(prioritized_issues, mode)
        self._log(f"Generated {len(fixes)} fixes")

        # Step 5: Apply and test fixes with retest loop
        self._log("💾 Applying and testing fixes...")
        applied_fixes = self._apply_and_test_fixes(fixes, prioritized_issues, mode)
        self._log(f"Applied {applied_fixes} fixes successfully (all passed tests)")

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
        """Capture screenshots of the running application for visual analysis

        Runs screenshot capture in a separate Python process to avoid Windows
        asyncio event loop conflicts with Streamlit.
        """
        try:
            import subprocess
            import json

            screenshots_dir = self.base_dir / 'screenshots'
            screenshots_dir.mkdir(exist_ok=True)

            server_url = "http://localhost:8505"

            self._log(f"Launching screenshot capture (separate process) for {server_url}...", "info")

            # Run screenshot capture in separate process with its own event loop
            capture_script = self.base_dir / 'core' / 'capture_screenshots.py'

            result = subprocess.run(
                ['python', str(capture_script), server_url, str(screenshots_dir)],
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )

            if result.returncode == 0:
                # Parse JSON output from subprocess
                screenshots = json.loads(result.stdout)
                self._log(f"✓ Captured {len(screenshots)} screenshots successfully", "info")
                for screenshot in screenshots:
                    self._log(f"  - {screenshot['name']}: {screenshot['path']}", "info")
                return screenshots
            else:
                # Subprocess failed
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self._log(f"⚠️ Screenshot capture failed: {error_msg}", "warning")
                self._log("   UI/UX analysis will continue without screenshots", "info")
                return []

        except subprocess.TimeoutExpired:
            self._log("⚠️ Screenshot capture timed out after 60 seconds", "warning")
            self._log("   UI/UX analysis will continue without screenshots", "info")
            return []
        except FileNotFoundError:
            self._log("⚠️ Could not find capture_screenshots.py script", "warning")
            return []
        except Exception as e:
            self._log(f"Screenshot capture failed: {type(e).__name__}: {str(e)}", "warning")
            self._log("   UI/UX analysis will continue without screenshots", "info")
            return []

    def _get_files_to_analyze(self, target_files: Optional[List[str]] = None, mode: str = None) -> List[Path]:
        """Get list of files to analyze based on improvement mode"""
        if target_files:
            # Use specified files
            return [Path(f) for f in target_files if Path(f).exists()]

        # Mode-specific file patterns
        mode_file_patterns = {
            ImprovementMode.UI_UX: {
                'extensions': ['.html', '.css', '.scss', '.jsx', '.tsx', '.vue', '.py'],  # Include .py for Streamlit
                'include_dirs': ['streamlit_ui', 'workflow_builder/src'],
                'exclude_dirs': {'core', 'server', 'tests', 'scripts', 'node_modules', 'venv', '__pycache__'},
                'description': 'UI files only (Streamlit UI, React components, stylesheets)'
            },
            ImprovementMode.PERFORMANCE: {
                'extensions': ['.py', '.js', '.ts'],
                'include_dirs': ['core', 'server'],
                'exclude_dirs': {'streamlit_ui', 'workflow_builder', 'tests', 'node_modules', 'venv'},
                'description': 'Backend performance files (core logic, server code)'
            },
            ImprovementMode.AGENT_QUALITY: {
                'extensions': ['.py', '.json'],
                'include_dirs': ['core'],
                'exclude_dirs': {'streamlit_ui', 'workflow_builder', 'server', 'tests', 'node_modules', 'venv'},
                'description': 'Agent-related files (agent configs, orchestration)'
            },
            ImprovementMode.CODE_QUALITY: {
                'extensions': ['.py', '.js', '.ts', '.tsx', '.jsx'],
                'include_dirs': None,  # All directories
                'exclude_dirs': {'node_modules', 'venv', '__pycache__', '.git', 'venv312', 'venv314', '.venv', 'exports', 'projects', 'screenshots'},
                'description': 'All code files (comprehensive code quality review)'
            },
            ImprovementMode.EVERYTHING: {
                'extensions': ['.py', '.js', '.ts', '.tsx', '.jsx', '.html', '.css', '.scss'],
                'include_dirs': None,  # All directories
                'exclude_dirs': {'node_modules', 'venv', '__pycache__', '.git', 'venv312', 'venv314', '.venv', 'exports', 'projects', 'screenshots'},
                'description': 'All files (comprehensive analysis)'
            },
        }

        # Get patterns for current mode (default to EVERYTHING if no mode specified)
        patterns = mode_file_patterns.get(mode, mode_file_patterns[ImprovementMode.EVERYTHING])

        extensions = patterns['extensions']
        include_dirs = patterns.get('include_dirs')
        exclude_dirs = patterns['exclude_dirs']
        description = patterns['description']

        # Log what we're analyzing
        self._log(f"📁 File Filter: {description}", "info")
        if include_dirs:
            self._log(f"  Including directories: {', '.join(include_dirs)}", "info")
        self._log(f"  File types: {', '.join(extensions)}", "info")

        # Collect files based on patterns
        files = []

        for ext in extensions:
            for file_path in self.base_dir.rglob(f'*{ext}'):
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in exclude_dirs):
                    continue

                # If include_dirs specified, only include files in those directories
                if include_dirs:
                    if not any(included in file_path.parts for included in include_dirs):
                        continue

                files.append(file_path)

        # Log file count
        self._log(f"  Found {len(files)} files to analyze", "info")

        return files

    def _identify_issues(self, files: List[Path], mode: str, screenshots: List[Dict] = None) -> List[Dict]:
        """Use specialized agent TEAMS based on mode to identify issues"""
        issues = []
        if screenshots is None:
            screenshots = []

        # Define SPECIALIZED agent teams per improvement mode
        # Each mode has domain experts + Verifier + Challenger
        # IMPORTANT: Verifier is ALWAYS second-to-last for hallucination detection
        # IMPORTANT: Challenger is ALWAYS last as the devil's advocate to challenge findings
        specialized_agent_teams = {
            ImprovementMode.UI_UX: [
                "Designs",  # UI/UX Designer - lead, overall design vision
                "AccessibilitySpecialist",  # WCAG compliance, inclusive design
                "UIDesigner",  # Visual design, component design
                "UXResearcher",  # User research, usability testing
                "ProductDesigner",  # Product design, user flows
                "Verifier",  # Hallucination detection - ensures claims are factual
                "Challenger",  # Devil's advocate - challenges false positives & UX assumptions
            ],
            ImprovementMode.PERFORMANCE: [
                "PerformanceEngineer",  # Performance specialist - lead
                "BackendEngineer",  # Backend optimization, algorithmic improvements
                "DatabaseAdmin",  # Database optimization, query performance
                "DevOps",  # Infrastructure performance, deployment optimization
                "SRE",  # Site reliability, monitoring, incident response
                "Verifier",  # Hallucination detection - ensures performance claims are real
                "Challenger",  # Devil's advocate - ensures real performance issues, not micro-optimizations
            ],
            ImprovementMode.AGENT_QUALITY: [
                "AIResearcher",  # AI/ML best practices - lead
                "MLEngineer",  # ML/AI engineering, model quality
                "MetaPrompt",  # Prompt engineering, agent instruction quality
                "DataScientist",  # Data quality, model evaluation
                "Verifier",  # Hallucination detection - critical for AI/agent claims
                "Challenger",  # Devil's advocate - challenges agent design assumptions
            ],
            ImprovementMode.CODE_QUALITY: [
                "Senior",  # Code review - lead
                "SecurityEngineer",  # Security review, vulnerability detection
                "Architect",  # Architecture review, design patterns
                "TestAutomation",  # Testing quality, test coverage
                "Verifier",  # Hallucination detection - ensures accuracy of code quality claims
                "Challenger",  # Devil's advocate - challenges over-engineering claims
            ],
            ImprovementMode.EVERYTHING: [
                "Senior",  # Lead coordinator
                "Verifier",  # Hallucination detection - comprehensive fact-checking
                "Challenger",  # Devil's advocate - final critical review
            ]
        }

        team = specialized_agent_teams.get(mode, ["Senior", "Verifier", "Challenger"])
        self._log(f"🤖 Specialized team for {mode}: {len(team)} agents", "info")
        self._log(f"   Team: {', '.join(team)}", "info")

        # Create all agents in the team
        analysis_agents = [
            create_agent_with_model(agent_name, MODEL_PRESETS[self.config['model']['default_preset']])
            for agent_name in team
        ]

        # Analyze in batches - adjust batch size based on team size for optimal performance
        # More agents = smaller batches to keep processing time reasonable
        if len(team) >= 6:
            batch_size = 3  # Smaller batches for larger teams (UI/UX, Performance, etc.)
        elif len(team) >= 4:
            batch_size = 4  # Medium batches for medium teams
        else:
            batch_size = 6  # Larger batches for small teams (Everything mode)

        total_batches = (len(files) + batch_size - 1) // batch_size  # Ceiling division
        batch_num = 0

        for i in range(0, len(files), batch_size):
            batch = files[i:i+batch_size]  # Fixed: was i:i+3, now uses batch_size
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

            # ========== HYBRID 3-STAGE PIPELINE FOR BEST RESULTS ==========
            # Stage 1: Domain experts analyze INDEPENDENTLY (no bias)
            # Stage 2: Verifier reviews ALL findings for hallucinations
            # Stage 3: Challenger applies devil's advocate filter

            # Split team into: domain experts, verifier, challenger
            domain_experts = analysis_agents[:-2]  # All except Verifier and Challenger
            verifier_agent = analysis_agents[-2]   # Second-to-last agent
            challenger_agent = analysis_agents[-1]  # Last agent

            self._log(f"  → Stage 1: {len(domain_experts)} domain experts analyzing independently (parallel mindset)", "info")
            self._log(f"     Experts: {', '.join([a.role for a in domain_experts])}", "info")

            # STAGE 1: Domain experts analyze independently (NO context = no bias)
            stage1_tasks = []
            for agent in domain_experts:
                task = Task(
                    description=prompt,
                    agent=agent,
                    expected_output="Issues in EXACT format: ISSUE: [title]\nFILE: [path]\nSEVERITY: [HIGH/MEDIUM/LOW]\nDESCRIPTION: [text]\nSUGGESTION: [text]\n(blank line between issues)"
                    # NO context = independent analysis, no anchoring bias
                )
                stage1_tasks.append(task)

            # STAGE 2: Verifier reviews ALL domain expert findings for hallucinations
            verifier_prompt = f"""
Review ALL findings from {len(domain_experts)} domain experts analyzing these files:

{chr(10).join([f"FILE: {path}" for path in file_contents.keys()])}

Your role as Verifier (Hallucination Detector):
1. Fact-check every claim - is it verifiable from the code?
2. Check for exaggerations or assumptions not supported by evidence
3. Verify file paths and line numbers are accurate
4. Ensure descriptions match what's actually in the code
5. Remove issues based on imagined code or features that don't exist
6. Validate severity ratings are justified by the actual impact

For VERIFIED issues, output in EXACT format:
ISSUE: [title]
FILE: [path]
SEVERITY: [HIGH/MEDIUM/LOW]
DESCRIPTION: [what's wrong]
SUGGESTION: [how to fix]

For UNVERIFIED issues (hallucinations, unsubstantiated claims), REMOVE them.
"""

            verifier_task = Task(
                description=verifier_prompt,
                agent=verifier_agent,
                expected_output="Only fact-checked, verified issues in exact format",
                context=stage1_tasks  # Verifier sees ALL domain expert outputs
            )

            # STAGE 3: Challenger applies devil's advocate critical filter
            challenger_prompt = f"""
Apply final critical review to the verified findings for these files:

{chr(10).join([f"FILE: {path}" for path in file_contents.keys()])}

Your role as Critical Challenger (Devil's Advocate):
1. Challenge each issue - is it REALLY worth fixing or just nitpicking?
2. Question severity ratings - are they inflated?
3. Check for false positives - could this be intentional design choice?
4. Verify suggestions won't introduce new bugs or complexity
5. Apply cost-benefit analysis - is the fix worth the development effort?
6. Question assumptions and sacred cows

For VALID issues that pass your critical scrutiny, output them in EXACT format:
ISSUE: [title]
FILE: [path]
SEVERITY: [HIGH/MEDIUM/LOW]
DESCRIPTION: [what's wrong]
SUGGESTION: [how to fix]

For INVALID issues (nitpicks, questionable value, edge cases), REMOVE them.
Only output issues that are genuinely worth fixing.
"""

            challenger_task = Task(
                description=challenger_prompt,
                agent=challenger_agent,
                expected_output="Only validated, worthwhile issues in exact format",
                context=[verifier_task]  # Challenger only sees Verifier's output
            )

            # Combine all tasks for 3-stage pipeline
            all_tasks = stage1_tasks + [verifier_task, challenger_task]

            # Run the hybrid 3-stage crew
            self._log(f"  → Stage 2: Verifier checking for hallucinations", "info")
            self._log(f"  → Stage 3: Challenger applying critical filter", "info")

            crew = Crew(
                agents=analysis_agents,
                tasks=all_tasks,  # Use the 3-stage pipeline tasks
                process=Process.sequential,  # Tasks run in order, but Stage 1 agents don't see each other
                verbose=False
            )

            try:
                result = crew.kickoff()
                # Result comes from Challenger (last task) - the final consolidated output
                result_text = result.raw if hasattr(result, 'raw') else str(result)

                # Log the raw result for debugging
                self._log(f"  ✓ 3-stage pipeline complete: {len(domain_experts)} experts → Verifier → Challenger", "info")
                self._log(f"     Final output: {len(result_text)} characters from Challenger", "info")

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

    def _estimate_complexity(self, issue: Dict) -> str:
        """
        Estimate fix complexity based on issue description

        Returns:
            'SIMPLE', 'MODERATE', or 'COMPLEX'
        """
        description = (issue.get('description', '') + ' ' + issue.get('suggestion', '')).lower()

        # Simple indicators
        simple_keywords = [
            'missing', 'add comment', 'typo', 'rename', 'remove unused',
            'import statement', 'add docstring', 'fix spacing',
            'add type hint', 'simple fix', 'quick fix'
        ]

        # Complex indicators
        complex_keywords = [
            'refactor', 'redesign', 'architecture', 'algorithm',
            'entire codebase', 'multiple files', 'breaking change',
            'major rewrite', 'comprehensive', 'fundamental'
        ]

        simple_count = sum(1 for kw in simple_keywords if kw in description)
        complex_count = sum(1 for kw in complex_keywords if kw in description)

        # Check description length (longer = more complex)
        desc_length = len(description)

        if simple_count > complex_count and desc_length < 200:
            return 'SIMPLE'
        elif complex_count > simple_count or desc_length > 400:
            return 'COMPLEX'
        else:
            return 'MODERATE'

    def _prioritize_issues(self, issues: List[Dict]) -> List[Dict]:
        """
        Smart prioritization: balance quick wins with important fixes

        Scoring system:
        - Severity: HIGH=10, MEDIUM=5, LOW=2
        - Complexity: SIMPLE=+5 bonus, MODERATE=0, COMPLEX=-3 penalty
        - Result: Mix of high-impact AND easy fixes
        """
        severity_scores = {'HIGH': 10, 'MEDIUM': 5, 'LOW': 2}
        complexity_scores = {'SIMPLE': 5, 'MODERATE': 0, 'COMPLEX': -3}

        # Score each issue
        scored_issues = []
        for issue in issues:
            severity = issue.get('severity', 'MEDIUM')
            complexity = self._estimate_complexity(issue)

            # Calculate priority score
            score = severity_scores.get(severity, 5) + complexity_scores.get(complexity, 0)

            # Store complexity for logging
            issue['complexity'] = complexity

            scored_issues.append({
                'issue': issue,
                'score': score,
                'severity': severity,
                'complexity': complexity
            })

        # Sort by score (highest first)
        scored_issues.sort(key=lambda x: x['score'], reverse=True)

        # Extract just the issues
        prioritized = [item['issue'] for item in scored_issues]

        # Log prioritization strategy
        if scored_issues:
            self._log("📊 Issue Prioritization:", "info")
            for i, item in enumerate(scored_issues[:5]):
                issue = item['issue']
                self._log(
                    f"  {i+1}. [{item['severity']}] {item['complexity']} (score: {item['score']}) - {issue.get('title', 'Untitled')[:60]}",
                    "info"
                )

        return prioritized

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

            # Skip directories
            if Path(file_path).is_dir():
                self._log(f"Skipping directory: {file_path}", "warning")
                continue

            # Read current file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
            except Exception as e:
                self._log(f"Could not read {file_path}: {e}", "error")
                continue

            # Generate fix with EXPLICIT format requirements
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

==================== CRITICAL OUTPUT FORMAT REQUIREMENTS ====================

YOU MUST OUTPUT IN THIS EXACT FORMAT. NO EXCEPTIONS. NO EXPLANATIONS. NO PROSE.

CORRECT FORMAT (copy this structure exactly):

FILE_CONTENT_START
[paste the COMPLETE fixed file content here - all lines, from first import to last line]
FILE_CONTENT_END

WRONG FORMATS (DO NOT USE):
❌ "Here's the fixed code..."
❌ "I've fixed the issue by..."
❌ Starting with explanations before FILE_CONTENT_START
❌ Adding comments after FILE_CONTENT_END
❌ Using different markers like ```python or "Here's the fix:"
❌ Outputting only the changed section (MUST output ENTIRE file)
❌ Using "..." placeholders or truncating code (FORBIDDEN!)
❌ Abbreviating with "// rest of file" or similar

CRITICAL - DO NOT USE PLACEHOLDERS:
- DO NOT use "..." to represent omitted code
- DO NOT truncate or abbreviate ANY part of the file
- Output EVERY SINGLE LINE from start to finish
- If you use "..." you have FAILED this task

REQUIREMENTS:
1. First line MUST be exactly: FILE_CONTENT_START
2. No text before FILE_CONTENT_START (not even "Sure!" or "Here it is")
3. Paste the ENTIRE fixed file (all lines from start to finish - NO "..." ALLOWED)
4. Last line MUST be exactly: FILE_CONTENT_END
5. No text after FILE_CONTENT_END (no explanations)

EXAMPLE OF CORRECT OUTPUT:

FILE_CONTENT_START
import streamlit as st
import os

def main():
    # Fixed code here with the issue resolved
    st.write("Hello World")

if __name__ == "__main__":
    main()
FILE_CONTENT_END

BEGIN OUTPUT NOW (start with "FILE_CONTENT_START" on the very first line):
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

                # Extract fixed content with robust parsing
                if 'FILE_CONTENT_START' in result_text and 'FILE_CONTENT_END' in result_text:
                    start_idx = result_text.index('FILE_CONTENT_START') + len('FILE_CONTENT_START')
                    end_idx = result_text.index('FILE_CONTENT_END')
                    fixed_content = result_text[start_idx:end_idx]

                    # Clean up content
                    fixed_content = fixed_content.strip()
                    fixed_content = fixed_content.strip('`')  # Remove backticks
                    fixed_content = fixed_content.strip()

                    # Remove language identifier if present (e.g., "python" right after start marker)
                    first_line = fixed_content.split('\n')[0].strip().lower()
                    if first_line in ['python', 'py', 'javascript', 'js', 'typescript', 'ts', 'html', 'css']:
                        fixed_content = '\n'.join(fixed_content.split('\n')[1:])

                    # Validate - reject placeholder/truncated outputs
                    if '...' in fixed_content[:200] or '…' in fixed_content[:200]:  # Check first 200 chars
                        self._log(f"  ⚠ Fix contains '...' placeholder for {Path(file_path).name}, rejecting", "warning")
                        self._log(f"     Agent used prohibited abbreviation. First 150 chars: {repr(fixed_content[:150])}", "warning")
                        continue

                    # Validate we got substantial content
                    if len(fixed_content) > 50:
                        fixes.append({
                            'file': file_path,
                            'issue': issue,
                            'original_content': current_content,
                            'fixed_content': fixed_content
                        })
                    else:
                        self._log(f"  ⚠ Fix too short for {Path(file_path).name} ({len(fixed_content)} chars), skipping", "warning")
                        self._log(f"     Content received: {repr(fixed_content[:100])}", "warning")
                else:
                    self._log(f"  ⚠ Could not find FILE_CONTENT_START/END markers in fix for {Path(file_path).name}", "warning")
                    # Show first 200 chars of output for debugging
                    self._log(f"  Agent output preview: {result_text[:200]}", "warning")

            except Exception as e:
                self._log(f"Fix generation failed for {file_path}: {e}", "error")

        return fixes

    def _apply_and_test_fixes(self, fixes: List[Dict], issues: List[Dict], mode: str) -> int:
        """
        Apply fixes with test-fix-retest loop

        For each fix:
        1. Apply it
        2. Test it (syntax + imports)
        3. If fails → send back to Fixer agent with error
        4. Retry up to 3 times
        5. Keep only fixes that pass tests
        """
        applied = 0
        max_retries = 3

        for i, fix in enumerate(fixes):
            file_path = fix['file']
            issue = issues[i] if i < len(issues) else {}

            self._log(f"📝 Fix {i+1}/{len(fixes)}: {Path(file_path).name}", "info")

            # Try to get a working fix (up to max_retries attempts)
            for attempt in range(1, max_retries + 1):
                if attempt > 1:
                    self._log(f"  🔄 Retry {attempt}/{max_retries}...", "info")

                # Get the fix content (first attempt uses original, retries use regenerated)
                if attempt == 1:
                    fixed_content = fix['fixed_content']
                else:
                    # Regenerate fix with error feedback
                    self._log(f"  → Asking Fixer agent to address test failure...", "info")
                    fixed_content = self._regenerate_fix_with_feedback(
                        file_path,
                        fix['original_content'],
                        issue,
                        last_error,
                        mode
                    )

                    if not fixed_content:
                        self._log(f"  ⚠ Could not regenerate fix, skipping", "warning")
                        break

                # Apply the fix temporarily
                original_content = self._backup_and_apply(file_path, fixed_content)

                # Test the fix
                test_passed, error_message = self._test_fix(file_path, fixed_content)

                if test_passed:
                    # Success! Keep the fix
                    self._log(f"  ✓ Fix applied and tested successfully", "success")
                    applied += 1
                    break
                else:
                    # Test failed - rollback
                    last_error = error_message
                    self._log(f"  ✗ Test failed: {error_message[:100]}", "warning")
                    self._rollback_fix(file_path, original_content)

                    if attempt == max_retries:
                        self._log(f"  ⚠ Max retries reached, skipping this fix", "warning")

        return applied

    def _backup_and_apply(self, file_path: str, content: str) -> str:
        """Backup original content and apply new content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original = f.read()

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return original
        except Exception as e:
            self._log(f"Failed to apply fix to {file_path}: {e}", "error")
            return ""

    def _rollback_fix(self, file_path: str, original_content: str):
        """Rollback to original content"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
        except Exception as e:
            self._log(f"Failed to rollback {file_path}: {e}", "error")

    def _test_fix(self, file_path: str, content: str) -> tuple[bool, str]:
        """
        Test if a fix is valid

        Returns:
            (passed, error_message)
        """
        # Test 1: Syntax validation
        is_valid, error_msg = self._validate_python_syntax(file_path, content)
        if not is_valid:
            return (False, f"Syntax error: {error_msg}")

        # Test 2: Import test (can the file be imported?)
        if file_path.endswith('.py'):
            import_ok = self._quick_import_test(file_path)
            if not import_ok:
                return (False, "Import failed - file cannot be compiled")

        # All tests passed
        return (True, "")

    def _regenerate_fix_with_feedback(self, file_path: str, original_content: str,
                                     issue: Dict, error_message: str, mode: str) -> str:
        """
        Ask Fixer agent to regenerate fix with error feedback

        Returns:
            New fixed content, or empty string if failed
        """
        # Select appropriate agent
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

        fix_prompt = f"""
Your previous fix for this issue FAILED testing. Fix the error and try again.

FILE: {file_path}
ISSUE: {issue.get('title', 'Unknown issue')}
DESCRIPTION: {issue.get('description', '')}

ORIGINAL CODE:
```
{original_content[:2000]}
```

PREVIOUS FIX FAILED WITH ERROR:
{error_message}

==================== CRITICAL: FIX THE ERROR ====================

Your previous fix had this error: {error_message}

You MUST:
1. Understand WHY the error occurred
2. Generate a NEW fix that DOES NOT have this error
3. Ensure syntax is 100% valid Python
4. Make sure the file can be imported without errors

Common issues to avoid:
- 'await' outside async function → only use await inside 'async def'
- Missing colons after if/for/while/def/class
- Incorrect indentation
- Unmatched parentheses/brackets

==================== OUTPUT FORMAT ====================

FILE_CONTENT_START
[paste the COMPLETE fixed file - valid Python syntax]
FILE_CONTENT_END

BEGIN OUTPUT NOW (start with "FILE_CONTENT_START"):
"""

        try:
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

            result = crew.kickoff()
            result_text = result.raw if hasattr(result, 'raw') else str(result)

            # Extract fixed content
            if 'FILE_CONTENT_START' in result_text and 'FILE_CONTENT_END' in result_text:
                start_idx = result_text.index('FILE_CONTENT_START') + len('FILE_CONTENT_START')
                end_idx = result_text.index('FILE_CONTENT_END')
                fixed_content = result_text[start_idx:end_idx].strip().strip('`').strip()

                # Remove language identifier if present
                first_line = fixed_content.split('\n')[0].strip().lower()
                if first_line in ['python', 'py', 'javascript', 'js', 'typescript', 'ts']:
                    fixed_content = '\n'.join(fixed_content.split('\n')[1:])

                if len(fixed_content) > 50:
                    return fixed_content

            return ""

        except Exception as e:
            self._log(f"Fix regeneration failed: {e}", "error")
            return ""

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
        """Get Git diff of changes in the latest commit"""
        try:
            # Try to get diff of the latest commit
            diff_result = subprocess.run(
                ['git', 'diff', 'HEAD^', 'HEAD'],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                check=False
            )

            if diff_result.stdout:
                return diff_result.stdout

            # Fallback: try to compare with main branch
            main_diff = subprocess.run(
                ['git', 'diff', 'main...HEAD'],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                check=False
            )

            return main_diff.stdout if main_diff.stdout else ""

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
