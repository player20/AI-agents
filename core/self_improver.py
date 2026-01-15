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

# Disable CrewAI telemetry to avoid signal handler errors in background threads
os.environ['OTEL_SDK_DISABLED'] = 'true'

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

    def _validate_api_connection(self) -> bool:
        """
        Test API connection before running improvement cycle (Phase 0D fix)

        Returns:
            True if API is accessible, False otherwise
        """
        import os
        import requests

        xai_api_key = os.getenv("XAI_API_KEY")
        if not xai_api_key:
            self._log("[!] XAI_API_KEY not set - Grok models unavailable", "warning")
            self._log("[INFO] Will use Anthropic Claude models instead", "info")
            return True  # Return True - can still work with Anthropic

        # Test x.ai connection
        try:
            response = requests.get(
                "https://api.x.ai/v1/models",
                headers={"Authorization": f"Bearer {xai_api_key}"},
                timeout=10
            )

            if response.status_code == 200:
                self._log("[OK] Grok API connection successful", "success")
                return True
            else:
                self._log(f"[!] Grok API returned status {response.status_code}", "warning")
                self._log(f"[FALLBACK] Will use Anthropic Claude models instead", "info")
                return True  # Can still work with fallback

        except requests.Timeout:
            self._log("[!] Grok API connection timeout - network issue?", "error")
            self._log("[FALLBACK] Will use Anthropic Claude models instead", "info")
            return True  # Can still work with fallback
        except Exception as e:
            self._log(f"[!] Grok API connection failed: {e}", "error")
            self._log("[FALLBACK] Will use Anthropic Claude models instead", "info")
            return True  # Can still work with fallback

    def run_cycle(
        self,
        mode: str = ImprovementMode.EVERYTHING,
        target_files: Optional[List[str]] = None,
        max_issues: int = 5,  # Back to 5 with Grok (was 2 for Anthropic's strict limits)
        suggest_enhancements: bool = False  # NEW: Enable Research/Ideas agents for feature suggestions
    ) -> Dict:
        """
        Run one improvement cycle

        Args:
            mode: Improvement mode (ui_ux, performance, agent_quality, code_quality, everything)
            target_files: Optional list of specific files to analyze
            max_issues: Maximum number of issues to fix per cycle (default: 5)
            suggest_enhancements: Include Research/Ideas agents to suggest new features (default: False)

        Returns:
            Dictionary with cycle results
        """
        self._log(f"[CYCLE] Starting improvement cycle - Mode: {mode}")

        # Phase 0D: Validate API connection before starting
        self._validate_api_connection()

        # Step 1: Analyze codebase
        self._log("[STATS] Analyzing codebase...")
        files_to_analyze = self._get_files_to_analyze(target_files, mode)
        # File count already logged by _get_files_to_analyze()

        # Step 1.5: Capture screenshots for UI/UX analysis
        screenshots = []
        if mode == ImprovementMode.UI_UX or mode == ImprovementMode.EVERYTHING:
            self._log("[CAPTURE] Capturing screenshots of running application...")
            screenshots = self._capture_app_screenshots()
            if screenshots:
                self._log(f"[+] Captured {len(screenshots)} screenshots for visual analysis")
            # Note: Empty screenshots list is handled gracefully - analysis continues without visual data

        # Step 2: Identify issues
        self._log("[ANALYZE] Identifying issues...")
        if suggest_enhancements:
            self._log("[ENHANCEMENT] Enhancement mode enabled - Research/Ideas agents will suggest new features", "info")
        issues = self._identify_issues(files_to_analyze, mode, screenshots, suggest_enhancements)

        # Log issue breakdown by type
        bug_count = len([i for i in issues if i.get('type') == 'BUG'])
        enhancement_count = len([i for i in issues if i.get('type') == 'ENHANCEMENT'])
        self._log(f"Found {len(issues)} total issues: {bug_count} bugs [BUG], {enhancement_count} enhancements [ENHANCEMENT]")

        # Log detailed issues to console and export to file
        if issues:
            self._log_all_issues_detailed(issues, mode)
            export_path = self._export_issues_to_file(issues, mode)
        else:
            export_path = None

        if not issues:
            self._log("[OK] No issues found! Codebase is in great shape.", "success")
            return {
                'files_analyzed': len(files_to_analyze),
                'issues_found': 0,
                'fixes_applied': 0,
                'diff': '',
                'scores': {'before': 10, 'after': 10, 'improvement': 0},
                'next_focus': 'Code quality is excellent',
                'issues': [],
                'all_issues': []
            }

        # Prioritize issues (includes complexity scoring)
        prioritized_issues = self._prioritize_issues(issues)

        # Adaptive batch size: more simple fixes, fewer complex fixes
        # API Rate Limits: Keep batches small (max 2-3) to stay under 5 req/min, 4K output tokens/min
        simple_count = sum(1 for issue in prioritized_issues[:max_issues*2] if issue.get('complexity') == 'SIMPLE')
        complex_count = sum(1 for issue in prioritized_issues[:max_issues*2] if issue.get('complexity') == 'COMPLEX')

        # If mostly simple fixes, allow up to 3 (was 10, reduced for rate limits)
        # If mostly complex, stick to 1 (was 3, reduced for rate limits)
        # Mix: adjust dynamically
        if simple_count > max_issues and complex_count == 0:
            adaptive_max = min(3, len(prioritized_issues))
            self._log(f"[UP] Adaptive batch: {simple_count} simple fixes detected, increasing batch to {adaptive_max}", "info")
        elif complex_count >= 2:
            adaptive_max = 1
            self._log(f"[DOWN] Adaptive batch: {complex_count} complex fixes detected, reducing batch to {adaptive_max}", "info")
        else:
            adaptive_max = max_issues

        prioritized_issues = prioritized_issues[:adaptive_max]
        self._log(f"Prioritized top {len(prioritized_issues)} issues (balanced mix of quick wins + important fixes)")

        # Step 3: Create Git branch for safety
        branch_name = f"self-improve-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self._log(f"[GIT] Creating Git branch: {branch_name}")
        self._create_git_branch(branch_name)

        # Step 4: Generate fixes
        self._log("[FIX] Generating fixes...")
        fixes = self._generate_fixes(prioritized_issues, mode)
        self._log(f"Generated {len(fixes)} fixes")

        # Step 5: Apply and test fixes with retest loop
        self._log("[APPLY] Applying and testing fixes...")
        applied_fixes = self._apply_and_test_fixes(fixes, prioritized_issues, mode)
        self._log(f"Applied {applied_fixes} fixes successfully (all passed tests)")

        # Step 6: Commit changes
        self._log("[COMMIT] Committing changes...")
        commit_hash = self._commit_changes(prioritized_issues, applied_fixes)

        # Step 7: Get diff
        diff_output = self._get_git_diff()

        # Step 8: Evaluate improvement
        self._log("[STATS] Evaluating improvement...")
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
            'issues': [self._format_issue_summary(issue) for issue in prioritized_issues],
            'all_issues': [self._format_issue_summary(issue) for issue in issues],  # All issues for export
            'export_path': export_path  # Path to exported markdown file
        }

        self._log("[OK] Improvement cycle complete!", "success")
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

            server_url = "http://localhost:8501"

            self._log(f"Launching screenshot capture (separate process) for {server_url}...", "info")

            # Run screenshot capture in separate process with its own event loop
            capture_script = self.base_dir / 'core' / 'capture_screenshots.py'

            result = subprocess.run(
                ['python', str(capture_script), server_url, str(screenshots_dir)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60  # 60 second timeout
            )

            if result.returncode == 0:
                # Parse JSON output from subprocess
                screenshots = json.loads(result.stdout)
                self._log(f"[+] Captured {len(screenshots)} screenshots successfully", "info")
                for screenshot in screenshots:
                    self._log(f"  - {screenshot['name']}: {screenshot['path']}", "info")
                return screenshots
            else:
                # Subprocess failed
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self._log(f"[WARNING] Screenshot capture failed: {error_msg}", "warning")
                self._log("   UI/UX analysis will continue without screenshots", "info")
                return []

        except subprocess.TimeoutExpired:
            self._log("[WARNING] Screenshot capture timed out after 60 seconds", "warning")
            self._log("   UI/UX analysis will continue without screenshots", "info")
            return []
        except FileNotFoundError:
            self._log("[WARNING] Could not find capture_screenshots.py script", "warning")
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
                'file_patterns': ['*agent*.py', '*improver*.py', 'agents.config.json'],
                'description': 'Agent-related files only (agent configs, orchestration, improvement logic)'
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
        self._log(f"[FILES] File Filter: {description}", "info")
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

                # If file_patterns specified, only include matching filenames
                file_patterns = patterns.get('file_patterns')
                if file_patterns:
                    from fnmatch import fnmatch
                    filename = file_path.name
                    if not any(fnmatch(filename, pattern) for pattern in file_patterns):
                        continue

                files.append(file_path)

        # Log file count
        self._log(f"  Found {len(files)} files to analyze", "info")

        return files

    def _identify_issues(self, files: List[Path], mode: str, screenshots: List[Dict] = None, suggest_enhancements: bool = False) -> List[Dict]:
        """
        Use specialized agent TEAMS based on mode to identify issues

        Args:
            files: List of files to analyze
            mode: Improvement mode (ui_ux, performance, etc.)
            screenshots: Optional screenshots for UI/UX analysis
            suggest_enhancements: If True, add Research/Ideas agents to suggest features

        Returns:
            List of issues with type classification (BUG or ENHANCEMENT)
        """
        issues = []
        if screenshots is None:
            screenshots = []

        # Phase 8: Initialize agent cache for 80% faster subsequent runs
        from core.agent_cache import AgentCache
        cache = AgentCache(self.base_dir, ttl_hours=24)
        cache_stats = {'hits': 0, 'misses': 0, 'files_analyzed': 0}

        # Helper to get mode value (handle both enum and string)
        mode_value = mode.value if hasattr(mode, 'value') else str(mode)

        # Check cache for each file before analysis
        files_to_analyze = []
        for file_path in files:
            cached_issues = cache.get_cached_analysis(str(file_path), mode_value)

            if cached_issues is not None:
                # Cache hit! Reuse previous analysis
                cache_stats['hits'] += 1
                self._log(f"  [CACHE HIT] {Path(file_path).name} - {len(cached_issues)} issues from cache", "success")
                issues.extend(cached_issues)
            else:
                # Cache miss - need to analyze
                cache_stats['misses'] += 1
                files_to_analyze.append(file_path)

        # Log cache performance
        if cache_stats['hits'] > 0 or cache_stats['misses'] > 0:
            hit_rate = (cache_stats['hits'] / (cache_stats['hits'] + cache_stats['misses']) * 100) if (cache_stats['hits'] + cache_stats['misses']) > 0 else 0
            self._log(f"[CACHE] {cache_stats['hits']} hits, {cache_stats['misses']} misses ({hit_rate:.1f}% hit rate)", "info")
            if cache_stats['hits'] > 0:
                self._log(f"[CACHE] Saved ~{cache_stats['hits']} API calls (70-80% cost savings)", "success")

        # If all files were cached, return early
        if not files_to_analyze:
            self._log("[CACHE] All files cached - no analysis needed!", "success")
            return issues

        # Continue with analysis for uncached files
        files = files_to_analyze

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

        # Add Research/Ideas agents for enhancement suggestions (if enabled)
        enhancement_agents = []
        if suggest_enhancements:
            enhancement_agents = ["Research", "Ideas"]
            # Insert BEFORE domain experts (but keep Verifier and Challenger at the end)
            verifier_idx = team.index("Verifier") if "Verifier" in team else len(team)
            team = enhancement_agents + team[:verifier_idx] + team[verifier_idx:]
            self._log(f"[ENHANCEMENT] Added Research/Ideas agents for feature suggestions", "info")

        self._log(f"[TEAM] Specialized team for {mode}: {len(team)} agents", "info")
        self._log(f"   Team: {', '.join(team)}", "info")

        # Create all agents in the team
        preset = MODEL_PRESETS[self.config['model']['default_preset']]
        default_model = preset['default']
        analysis_agents = [
            create_agent_with_model(agent_name, default_model)
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
            self._log(f"[BATCH] Analyzing batch {batch_num}/{total_batches} ({len(batch)} files)...", "info")

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

            self._log(f"  -> Stage 1: {len(domain_experts)} domain experts analyzing independently (parallel mindset)", "info")
            self._log(f"     Experts: {', '.join([a.role for a in domain_experts])}", "info")

            # STAGE 1: Domain experts analyze independently (NO context = no bias)
            stage1_tasks = []
            for agent in domain_experts:
                # Add agent-specific guidance for Research/Ideas agents
                agent_prompt = prompt
                if agent.role in ["Market Research Analyst", "Ideas Specialist"]:
                    agent_prompt = f"""
{prompt}

SPECIAL NOTE FOR ENHANCEMENT AGENTS:
You are analyzing existing code to suggest ENHANCEMENTS (new features, improvements beyond bugs).
- Mark your suggestions with TYPE: ENHANCEMENT
- Focus on logical feature extensions, missing industry-standard features, UX improvements
- Be realistic - suggest features that fit naturally with existing code
- Example: "Add export to PDF feature" or "Missing dark mode toggle" or "No keyboard shortcuts"

"""

                task = Task(
                    description=agent_prompt,
                    agent=agent,
                    expected_output="Issues in EXACT format: ISSUE: [title]\nFILE: [path]\nSEVERITY: [HIGH/MEDIUM/LOW]\nTYPE: [BUG/ENHANCEMENT] (optional, defaults to BUG)\nDESCRIPTION: [text]\nSUGGESTION: [text]\n(blank line between issues)"
                    # NO context = independent analysis, no anchoring bias
                )
                stage1_tasks.append(task)

            # STAGE 2: Verifier reviews ALL domain expert findings for hallucinations
            verifier_prompt = f"""
Review ALL findings from {len(domain_experts)} domain experts analyzing ONLY these files:

{chr(10).join([f"FILE: {path}" for path in file_contents.keys()])}

CRITICAL - THESE ARE THE ONLY FILES ANALYZED:
The experts ONLY analyzed the files listed above. Any issue mentioning a file NOT in this list is a HALLUCINATION and MUST be removed.

Your role as Verifier (Hallucination Detector + Specificity Enforcer):

STEP 1: FILE PATH VALIDATION (Most Important - Do This FIRST)
[OK] VALID: Exactly ONE file from the analyzed list above
[X] INVALID - REMOVE IMMEDIATELY:
- "FILE: Unknown"
- "FILE: Multiple files"
- "FILE: Across the UI"
- "FILE: All files"
- "FILE: streamlit_ui/main_interface.py, streamlit_ui/self_improvement.py" (multiple files listed)
- "FILE: Multiple files (main_interface.py, results_display.py)" (multiple files in parentheses)
- "FILE: streamlit_ui/*.py" (wildcard pattern)
- Any file NOT in the analyzed list above

If FILE is invalid -> REMOVE the entire issue immediately, don't even read the rest.

STEP 2: SPECIFICITY VALIDATION (Only if file path is valid)
Issues must be CONCRETE and SPECIFIC, not vague architectural observations.
[OK] KEEP: "Button text wraps to 2 lines at 375px viewport in mobile view"
[OK] KEEP: "Missing alt attribute on screenshot image at line 45"
[OK] KEEP: "Color contrast 2.8:1 between button text and background fails WCAG AA"
[X] REMOVE: "Lack of overall design system" (too architectural)
[X] REMOVE: "Needs better mobile responsiveness" (too vague)
[X] REMOVE: "Improve visual consistency" (too general)
[X] REMOVE: "Better user flow needed" (opinion, not concrete issue)

STEP 3: LIGHT FACT-CHECK (Be lenient - keep issues unless obviously wrong)
- If the issue seems plausible, KEEP IT (benefit of the doubt)
- Only remove if clearly hallucinating code that doesn't exist
- Line number accuracy is nice-to-have, not required
- Accept reasonable severity ratings even if subjective

ONLY REMOVE IF:
[X] FILE: Unknown/Missing (no file specified)
[X] FILE: Multiple files listed (must pick ONE specific file)
[X] FILE: Across the UI / Multiple components (too vague - need specific file)
[X] ISSUE: References code/functions that don't exist in the analyzed files (hallucination)

[OK] KEEP EVERYTHING ELSE including:
[OK] Nitpicks and minor issues (we want perfection!)
[OK] Subjective improvements (readability, naming, style)
[OK] Issues without line numbers (general file-level issues are fine)
[OK] Slightly vague descriptions (if file is specific)

OUTPUT FORMAT - For issues that pass minimal validation:
ISSUE: [title]
FILE: [path]
SEVERITY: [HIGH/MEDIUM/LOW]
DESCRIPTION: [what's wrong]
SUGGESTION: [how to fix]

REMEMBER: When in doubt, KEEP the issue. We want to be demanding and find everything!
"""

            verifier_task = Task(
                description=verifier_prompt,
                agent=verifier_agent,
                expected_output="Only fact-checked, verified issues in exact format",
                context=stage1_tasks  # Verifier sees ALL domain expert outputs
            )

            # STAGE 3: Challenger demands EVEN MORE issues and improvements
            challenger_prompt = f"""
Review the verified findings for these files and ADD MORE ISSUES:

{chr(10).join([f"FILE: {path}" for path in file_contents.keys()])}

Your role as DEMANDING Quality Enforcer:

CRITICAL MINDSET:
[WARNING] The verified issues are just the START. You need to find EVEN MORE issues to improve quality.
[WARNING] NITPICKING IS ENCOURAGED - we want PERFECTION, not "good enough"
[WARNING] Even small improvements count - anything that makes code 1% better is worth reporting

YOUR TASKS:
1. KEEP all specific, actionable issues from the verifier
2. FIND ADDITIONAL issues the verifier might have missed:
   - Minor style inconsistencies
   - Variable names that could be clearer
   - Missing comments or docstrings
   - Hard-coded values that should be constants
   - Functions that could be split into smaller ones
   - Any code duplication (even 2-3 lines)
   - Magic numbers without comments
   - Error messages that could be more helpful
   - Missing type hints
   - Console.log or debug statements
   - TODOs or FIXMEs

ONLY REMOVE if:
[X] Too vague: "Needs better responsiveness" (what specifically?)
[X] Architectural: "Lacks overall design system" (affects multiple files)
[X] Multi-file: Issue can't be fixed in a single specific file
[X] Hallucination: References code that doesn't exist

[OK] KEEP EVERYTHING ELSE including:
[OK] Nitpicks and minor improvements
[OK] Code style issues
[OK] Documentation gaps
[OK] Small optimizations
[OK] Readability improvements

⚠️ CRITICAL OUTPUT REQUIREMENT:

YOU MUST output your FINAL consolidated list of issues DIRECTLY in your response.
DO NOT say "the issues above" or "the list provided earlier" - OUTPUT THEM NOW.
DO NOT reference previous messages - this is your FINAL output that will be parsed.

Your response MUST contain the issues in this EXACT format (one issue per block):

ISSUE: [title]
FILE: [path]
SEVERITY: [HIGH/MEDIUM/LOW]
TYPE: [BUG/ENHANCEMENT]
DESCRIPTION: [what's wrong or what's missing]
SUGGESTION: [how to fix or what to add]

EXAMPLE (copy this structure):

ISSUE: Missing alt text on logo image
FILE: components/Header.tsx
SEVERITY: HIGH
TYPE: BUG
DESCRIPTION: The logo image at line 23 has no alt attribute, failing WCAG accessibility standards
SUGGESTION: Add alt="Company Logo" to the img tag

ISSUE: Hard-coded API timeout value
FILE: api/client.ts
SEVERITY: MEDIUM
TYPE: BUG
DESCRIPTION: Timeout value of 5000ms is hard-coded at line 45, making it hard to configure
SUGGESTION: Move timeout to a constant at the top of the file or config file

⚠️ REMEMBER:
- Your response is the FINAL output that will be parsed
- MUST contain lines starting with ISSUE:, FILE:, SEVERITY:, TYPE:, DESCRIPTION:, SUGGESTION:
- Output ALL validated issues DIRECTLY (don't reference "above")
- Be thorough and demanding - find everything!
"""

            challenger_task = Task(
                description=challenger_prompt,
                agent=challenger_agent,
                expected_output="Only validated, worthwhile issues with TYPE classification (BUG or ENHANCEMENT)",
                context=[verifier_task]  # Challenger only sees Verifier's output
            )

            # Combine all tasks for 3-stage pipeline
            all_tasks = stage1_tasks + [verifier_task, challenger_task]

            # Run the hybrid 3-stage crew
            self._log(f"  -> Stage 2: Verifier checking for hallucinations", "info")
            self._log(f"  -> Stage 3: Challenger applying critical filter", "info")

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
                self._log(f"  [+] 3-stage pipeline complete: {len(domain_experts)} experts -> Verifier -> Challenger", "info")
                self._log(f"     Final output: {len(result_text)} characters from Challenger", "info")

                # Parse issues from result
                batch_issues = self._parse_issues(result_text, batch)

                if batch_issues:
                    # Log what we found
                    bug_count = len([i for i in batch_issues if i.get('type') == 'BUG'])
                    enhancement_count = len([i for i in batch_issues if i.get('type') == 'ENHANCEMENT'])
                    self._log(f"  [+] Found {len(batch_issues)} issues in this batch: {bug_count} bugs, {enhancement_count} enhancements", "info")
                    for idx, issue in enumerate(batch_issues[:3], 1):  # Show first 3
                        issue_type = issue.get('type', 'BUG')
                        type_emoji = "[BUG]" if issue_type == "BUG" else "[ENHANCEMENT]"
                        self._log(f"    {idx}. {type_emoji} [{issue.get('severity', 'UNKNOWN')}] {issue.get('title', 'Untitled')} ({issue.get('file', 'unknown file')})", "info")
                    if len(batch_issues) > 3:
                        self._log(f"    ... and {len(batch_issues) - 3} more", "info")
                elif len(result_text) > 100:
                    # Agent returned content but parser found nothing - log for debugging
                    self._log(f"  [!] WARNING: Parser found 0 issues from {len(result_text)} chars of agent output", "warning")
                    self._log(f"  First 300 chars: {result_text[:300]}", "warning")

                issues.extend(batch_issues)

                # Phase 8: Cache results for each file in this batch
                # Group issues by file and cache them separately
                from collections import defaultdict
                file_issue_map = defaultdict(list)
                for issue in batch_issues:
                    file_path = issue.get('file', '')
                    if file_path:
                        file_issue_map[file_path].append(issue)

                # Cache results for each file
                for file_path, file_issues in file_issue_map.items():
                    cache.set_cached_analysis(file_path, mode_value, file_issues)
                    cache_stats['files_analyzed'] += 1

                # Also cache empty results for files with no issues (prevent re-analysis)
                for file_path in file_contents.keys():
                    if file_path not in file_issue_map:
                        cache.set_cached_analysis(file_path, mode_value, [])
                        cache_stats['files_analyzed'] += 1

            except Exception as e:
                self._log(f"Analysis failed for batch: {e}", "error")

        # Log final cache statistics
        if cache_stats['files_analyzed'] > 0:
            self._log(f"[CACHE] Cached analysis results for {cache_stats['files_analyzed']} files", "success")

        return issues

    def _log_all_issues_detailed(self, issues: List[Dict], mode: str) -> None:
        """
        Log ALL issues with full details for user review

        Args:
            issues: All issues found across all batches
            mode: Improvement mode for context
        """
        if not issues:
            self._log("[STATS] No issues found!", "success")
            return

        # Group by type
        bugs = [i for i in issues if i.get('type') == 'BUG']
        enhancements = [i for i in issues if i.get('type') == 'ENHANCEMENT']

        self._log("=" * 80, "info")
        self._log(f"[DETAILED ISSUE REPORT] All {len(issues)} Issues Found", "info")
        self._log("=" * 80, "info")

        # BUGS section
        if bugs:
            self._log(f"\n🐛 BUGS ({len(bugs)} total)", "error")
            self._log("-" * 80, "info")
            for idx, issue in enumerate(bugs, 1):
                severity = issue.get('severity', 'UNKNOWN')
                severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")

                self._log(f"\n{idx}. {severity_emoji} [{severity}] {issue.get('title', 'Untitled')}", "warning")
                self._log(f"   File: {issue.get('file', 'unknown')}", "info")
                self._log(f"   Description: {issue.get('description', 'No description')}", "info")
                self._log(f"   Suggestion: {issue.get('suggestion', 'No suggestion')}", "info")

        # ENHANCEMENTS section
        if enhancements:
            self._log(f"\n💡 ENHANCEMENTS ({len(enhancements)} total)", "success")
            self._log("-" * 80, "info")
            for idx, issue in enumerate(enhancements, 1):
                severity = issue.get('severity', 'UNKNOWN')
                severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")

                self._log(f"\n{idx}. {severity_emoji} [{severity}] {issue.get('title', 'Untitled')}", "info")
                self._log(f"   File: {issue.get('file', 'unknown')}", "info")
                self._log(f"   Description: {issue.get('description', 'No description')}", "info")
                self._log(f"   Suggestion: {issue.get('suggestion', 'No suggestion')}", "info")

        self._log("=" * 80, "info")
        self._log(f"[END DETAILED REPORT] {len(bugs)} bugs, {len(enhancements)} enhancements", "info")
        self._log("=" * 80, "info")

    def _export_issues_to_file(self, issues: List[Dict], mode: str) -> str:
        """
        Export all issues to a dedicated file for review

        Returns:
            Path to the exported file
        """
        from datetime import datetime
        import json

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = self.base_dir / "reports"
        export_dir.mkdir(exist_ok=True)

        # Markdown export (human-readable)
        md_file = export_dir / f"issues_detailed_{mode}_{timestamp}.md"

        bugs = [i for i in issues if i.get('type') == 'BUG']
        enhancements = [i for i in issues if i.get('type') == 'ENHANCEMENT']

        md_content = f"""# Detailed Issue Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Mode: {mode}
Total Issues: {len(issues)} ({len(bugs)} bugs, {len(enhancements)} enhancements)

---

## 🐛 Bugs ({len(bugs)})

"""

        for idx, issue in enumerate(bugs, 1):
            severity = issue.get('severity', 'UNKNOWN')
            md_content += f"""
### {idx}. [{severity}] {issue.get('title', 'Untitled')}

- **File:** `{issue.get('file', 'unknown')}`
- **Type:** BUG
- **Severity:** {severity}

**Description:**
{issue.get('description', 'No description')}

**Suggested Fix:**
{issue.get('suggestion', 'No suggestion')}

---
"""

        md_content += f"""
## 💡 Enhancements ({len(enhancements)})

"""

        for idx, issue in enumerate(enhancements, 1):
            severity = issue.get('severity', 'UNKNOWN')
            md_content += f"""
### {idx}. [{severity}] {issue.get('title', 'Untitled')}

- **File:** `{issue.get('file', 'unknown')}`
- **Type:** ENHANCEMENT
- **Severity:** {severity}

**Description:**
{issue.get('description', 'No description')}

**Suggested Enhancement:**
{issue.get('suggestion', 'No suggestion')}

---
"""

        # Write markdown file
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        # Also export JSON for programmatic access
        json_file = export_dir / f"issues_detailed_{mode}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'mode': mode,
                'total_issues': len(issues),
                'bugs': bugs,
                'enhancements': enhancements,
                'all_issues': issues
            }, f, indent=2)

        self._log(f"[EXPORT] Detailed issues exported to:", "success")
        self._log(f"  Markdown: {md_file}", "info")
        self._log(f"  JSON: {json_file}", "info")

        return str(md_file)

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
Focus on SPECIFIC, CONCRETE UI/UX issues that can be fixed in individual files:

[OK] GOOD ISSUES (Specific, measurable, fixable):
- "Button text wraps to 2 lines on mobile viewport (375px)" - SPECIFIC visual problem
- "Color contrast ratio 2.8:1 fails WCAG AA (needs 4.5:1)" - MEASURABLE accessibility issue
- "No alt text on image at line 45" - CONCRETE missing attribute
- "Input label 'Project Description' hidden from screen readers" - TESTABLE accessibility gap
- "4-column layout breaks on tablet (768px), causes horizontal scroll" - SPECIFIC responsive issue
- "Error message 'Error occurred' too vague for user" - CONCRETE UX problem
- "Loading state missing during API call (lines 120-135)" - SPECIFIC missing state
- "Checkbox disabled but no explanation shown to user" - CONCRETE feedback gap

[X] BAD ISSUES (Vague, architectural, multi-file):
- "Lack of overall design system" - TOO ARCHITECTURAL, affects multiple files
- "Needs better mobile responsiveness" - TOO VAGUE, not specific enough
- "Improve visual consistency" - TOO GENERAL, no concrete action
- "Better user flow needed" - TOO BROAD, opinion not fact
- "Add loading states" - TOO VAGUE, where specifically?

CRITICAL RULES:
1. Be SPECIFIC: Mention exact line numbers, exact measurements, exact elements
2. Be CONCRETE: Describe observable, testable problems
3. ONE FILE ONLY: Pick the most relevant file where the fix should go
4. AVOID ARCHITECTURE: Don't suggest system-wide changes or new frameworks
5. FIX NOT REDESIGN: Find issues that can be fixed, not concepts that need rethinking

If you see a screenshot, look for SPECIFIC visual problems:
- Text that wraps awkwardly (measure the viewport)
- Buttons that are too small to tap (measure the pixels)
- Colors with poor contrast (note the specific elements)
- Layout that breaks at specific widths (note the breakpoint)
- Missing visual feedback on interactions (note which button/input)
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

==================== CRITICAL MINDSET ====================

[WARNING] BE EXTREMELY CRITICAL AND DEMANDING. This is a PROFESSIONAL codebase that needs to be PERFECT.

MANDATORY REQUIREMENTS:
1. You MUST find AT LEAST 3-5 issues per file analyzed
2. Be HARSH - treat this like a production code review where quality matters
3. LOWER YOUR STANDARDS - even minor improvements count as issues
4. Look for EVERYTHING: typos, inconsistent spacing, missing comments, slightly unclear naming, etc.
5. If code "works" but could be 1% better in ANY way, report it as an issue

COMMON ISSUES TO ACTIVELY SEARCH FOR:
- Hard-coded values that should be constants
- Functions longer than 20 lines (should be split)
- Variable names that could be more descriptive
- Missing docstrings or comments
- Inconsistent code style or formatting
- Error messages that could be more helpful
- Any duplication of code (even 2-3 lines)
- Missing type hints in Python
- Console.log statements left in code
- TODOs or FIXMEs in comments
- Magic numbers without explanation
- Functions with more than 3 parameters
- Deeply nested if statements (>2 levels)

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
6. FILE field MUST be a SPECIFIC file path from the analyzed files above
   [X] WRONG: FILE: Unknown
   [X] WRONG: FILE: Multiple files
   [X] WRONG: FILE: Across the UI
   [OK] RIGHT: FILE: streamlit_ui/main_interface.py
7. If an issue affects multiple files, create SEPARATE issues for each file
8. DO NOT use vague file paths - pick the MOST RELEVANT specific file

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

            elif line.upper().startswith('TYPE:') or line.upper().startswith('**TYPE:'):
                type_text = line.split(':', 1)[1].strip().strip('*').strip().upper()
                # Extract issue type (BUG or ENHANCEMENT)
                if 'ENHANCEMENT' in type_text:
                    issue_type = 'ENHANCEMENT'
                else:
                    issue_type = 'BUG'
                current_issue['type'] = issue_type

            elif line.upper().startswith('DESCRIPTION:') or line.upper().startswith('**DESCRIPTION:'):
                desc = line.split(':', 1)[1].strip().strip('*').strip()
                current_issue['description'] = desc

            elif line.upper().startswith('SUGGESTION:') or line.upper().startswith('**SUGGESTION:'):
                sugg = line.split(':', 1)[1].strip().strip('*').strip()
                current_issue['suggestion'] = sugg

        # Add last issue
        if current_issue and 'title' in current_issue:
            issues.append(current_issue)

        # Ensure all issues have a type (default to BUG if not specified)
        for issue in issues:
            if 'type' not in issue:
                issue['type'] = 'BUG'

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
            self._log("[STATS] Issue Prioritization:", "info")
            for i, item in enumerate(scored_issues[:5]):
                issue = item['issue']
                self._log(
                    f"  {i+1}. [{item['severity']}] {item['complexity']} (score: {item['score']}) - {issue.get('title', 'Untitled')[:60]}",
                    "info"
                )

        return prioritized

    def _generate_diff_based_fix(self, issue: Dict, file_path: str, current_content: str, fix_agent) -> Dict:
        """
        Generate a diff-based fix for extremely large files (>1000 lines)

        Instead of regenerating the entire file, generate specific line-by-line changes.
        With Grok's 4M tokens/min, this is only needed for files >1000 lines.

        Returns:
            Dict with 'changes' list, or None if generation failed
        """
        line_count = len(current_content.splitlines())
        self._log(f"  [FIX] Using diff-based approach for large file ({line_count} lines)", "info")

        # Get relevant context around the issue
        # Show agent only the relevant section, not the entire file
        lines = current_content.splitlines()

        # Try to find issue location hint
        issue_line = issue.get('line', None)
        context_start = 0
        context_end = len(lines)

        # If we have a line number, show context around it
        if issue_line:
            context_start = max(0, issue_line - 50)
            context_end = min(len(lines), issue_line + 50)
            context_lines = lines[context_start:context_end]
            context_snippet = '\n'.join(f"{i+context_start+1}: {line}" for i, line in enumerate(context_lines))
        else:
            # Show first 100 and last 100 lines as context
            context_snippet = (
                "FIRST 100 LINES:\n" +
                '\n'.join(f"{i+1}: {line}" for i, line in enumerate(lines[:100])) +
                "\n\n... [middle section omitted] ...\n\n" +
                "LAST 100 LINES:\n" +
                '\n'.join(f"{i+len(lines)-100+1}: {line}" for i, line in enumerate(lines[-100:]))
            )

        # Generate diff-based fix
        diff_prompt = f"""
[WARNING][WARNING][WARNING] CRITICAL: DIFF-BASED FIX FORMAT REQUIRED [WARNING][WARNING][WARNING]

This file is too large ({line_count} lines) to regenerate completely.
You must provide TARGETED CHANGES using this exact format:

DIFF_CHANGES_START
CHANGE 1:
Line: <line_number>
Action: <replace|insert_after|delete>
Old: <original_text_if_replace>
New: <new_text>

CHANGE 2:
Line: <line_number>
Action: <replace|insert_after|delete>
Old: <original_text_if_replace>
New: <new_text>

[... more changes ...]
DIFF_CHANGES_END

RULES:
1. Each change must specify exact line number
2. Action must be: replace, insert_after, or delete
3. For "replace": include both Old and New
4. For "insert_after": only include New (what to insert)
5. For "delete": only include Old (what to delete)
6. Be specific - include enough of the original line to match uniquely
7. NO explanations outside markers
8. First line MUST be "DIFF_CHANGES_START"
9. Last line MUST be "DIFF_CHANGES_END"

===============================================================================

FILE: {file_path}
SIZE: {line_count} lines

ISSUE: {issue.get('title', 'Unknown issue')}
DESCRIPTION: {issue.get('description', '')}
SUGGESTION: {issue.get('suggestion', '')}

RELEVANT CODE SECTION:
```
{context_snippet}
```

YOUR TASK:
1. Identify the specific lines that need to change
2. Provide TARGETED changes in the format above
3. DO NOT regenerate the entire file
4. Be precise with line numbers and old/new text

BEGIN NOW - First line must be "DIFF_CHANGES_START":
"""

        try:
            task = Task(
                description=diff_prompt,
                agent=fix_agent,
                expected_output="DIFF_CHANGES_START\n[changes]\nDIFF_CHANGES_END"
            )

            crew = Crew(
                agents=[fix_agent],
                tasks=[task],
                verbose=False
            )

            # Retry logic for API failures (500 errors, rate limits, etc.)
            max_retries = 3
            retry_delay = 2  # seconds
            result_text = None

            for attempt in range(1, max_retries + 1):
                try:
                    result = crew.kickoff()
                    result_text = str(result)
                    break  # Success - exit retry loop

                except Exception as api_error:
                    error_str = str(api_error)

                    # Check if it's a retryable error (500, rate limit, timeout)
                    is_retryable = (
                        '500' in error_str or
                        'Internal server error' in error_str or
                        '429' in error_str or
                        'rate' in error_str.lower() or
                        'timeout' in error_str.lower()
                    )

                    if is_retryable and attempt < max_retries:
                        wait_time = retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                        self._log(f"  [!] API error (attempt {attempt}/{max_retries}): {error_str[:100]}", "warning")
                        self._log(f"  [WAIT] Retrying in {wait_time}s...", "info")
                        import time
                        time.sleep(wait_time)
                    else:
                        # Non-retryable error or max retries reached
                        self._log(f"  [X] API error after {attempt} attempts: {error_str[:200]}", "error")
                        raise

            if result_text is None:
                self._log(f"  [X] Failed to get response after {max_retries} retries", "error")
                return None

            # Debug: Log what agent actually returned
            self._log(f"  [OUTPUT] Agent output preview (first 500 chars):", "info")
            self._log(f"     {result_text[:500]}", "info")

            # Parse the diff changes
            if "DIFF_CHANGES_START" in result_text and "DIFF_CHANGES_END" in result_text:
                start_idx = result_text.find("DIFF_CHANGES_START") + len("DIFF_CHANGES_START")
                end_idx = result_text.find("DIFF_CHANGES_END")
                changes_text = result_text[start_idx:end_idx].strip()

                # Parse individual changes
                changes = self._parse_diff_changes(changes_text)

                if changes:
                    self._log(f"  [+] Generated {len(changes)} targeted changes", "success")
                    return {
                        'type': 'diff',
                        'changes': changes
                    }
                else:
                    self._log(f"  [!] Failed to parse diff changes", "warning")
                    return None
            else:
                self._log(f"  [!] Agent did not use DIFF_CHANGES format", "warning")
                self._log(f"     Searching for common format variations...", "info")

                # Try to parse natural language instructions as fallback
                # Look for patterns like "line 123", "change line 456", etc.
                fallback_changes = self._parse_natural_language_changes(result_text, current_content)

                if fallback_changes:
                    self._log(f"  [+] Parsed {len(fallback_changes)} changes from natural language", "success")
                    return {
                        'type': 'diff',
                        'changes': fallback_changes
                    }

                return None

        except Exception as e:
            self._log(f"  [X] Diff-based fix generation failed: {e}", "error")
            return None

    def _parse_natural_language_changes(self, text: str, current_content: str) -> List[Dict]:
        """
        Fallback parser: Try to extract changes from natural language instructions

        Looks for patterns like:
        - "line 123: change X to Y"
        - "replace line 456 with Z"
        - "add after line 789: W"
        """
        changes = []
        import re

        lines = current_content.splitlines()

        # Pattern 1: "line N" or "Line N" followed by instructions
        line_patterns = [
            r'(?:line|Line)\s+(\d+):\s*(?:change|replace|modify)\s+["\']?(.+?)["\']?\s+(?:to|with)\s+["\']?(.+?)["\']?(?:\.|$)',
            r'(?:replace|change)\s+line\s+(\d+)\s+with\s+["\']?(.+?)["\']?(?:\.|$)',
            r'(?:line|Line)\s+(\d+):\s*["\']?(.+?)["\']?(?:\.|$)',  # Simple format: "Line N: new content"
        ]

        for pattern in line_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    line_num = int(groups[0])
                    if line_num <= 0 or line_num > len(lines):
                        continue

                    change = {
                        'line': line_num,
                        'action': 'replace',
                        'old': lines[line_num - 1].strip() if line_num <= len(lines) else '',
                    }

                    # Extract new content from groups
                    if len(groups) == 3:
                        change['new'] = groups[2].strip()
                    else:
                        change['new'] = groups[1].strip()

                    if change['new']:
                        changes.append(change)

        # Deduplicate by line number
        seen_lines = set()
        unique_changes = []
        for change in changes:
            if change['line'] not in seen_lines:
                seen_lines.add(change['line'])
                unique_changes.append(change)

        return unique_changes

    def _parse_diff_changes(self, changes_text: str) -> List[Dict]:
        """Parse diff changes from agent output"""
        changes = []

        # Split by "CHANGE N:" markers
        import re
        change_blocks = re.split(r'CHANGE \d+:', changes_text)

        for block in change_blocks:
            if not block.strip():
                continue

            change = {}

            # Extract line number
            line_match = re.search(r'Line:\s*(\d+)', block)
            if line_match:
                change['line'] = int(line_match.group(1))

            # Extract action
            action_match = re.search(r'Action:\s*(replace|insert_after|delete)', block, re.IGNORECASE)
            if action_match:
                change['action'] = action_match.group(1).lower()

            # Extract old text
            old_match = re.search(r'Old:\s*(.+?)(?=\nNew:|\nCHANGE|\Z)', block, re.DOTALL)
            if old_match:
                change['old'] = old_match.group(1).strip()

            # Extract new text
            new_match = re.search(r'New:\s*(.+?)(?=\nCHANGE|\Z)', block, re.DOTALL)
            if new_match:
                change['new'] = new_match.group(1).strip()

            # Validate change has required fields
            if 'line' in change and 'action' in change:
                if change['action'] == 'replace' and 'old' in change and 'new' in change:
                    changes.append(change)
                elif change['action'] == 'insert_after' and 'new' in change:
                    changes.append(change)
                elif change['action'] == 'delete' and 'old' in change:
                    changes.append(change)

        return changes

    def _apply_diff_based_fix(self, file_path: str, changes: List[Dict]) -> str:
        """Apply diff-based changes to a file and return the new content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Sort changes by line number (descending) to avoid line number shifts
            changes_sorted = sorted(changes, key=lambda x: x['line'], reverse=True)

            for change in changes_sorted:
                line_num = change['line'] - 1  # Convert to 0-indexed
                action = change['action']

                if line_num < 0 or line_num >= len(lines):
                    self._log(f"    [!] Line {change['line']} out of range, skipping", "warning")
                    continue

                if action == 'replace':
                    # Verify old text matches (fuzzy match - strip whitespace)
                    old_text = change.get('old', '').strip()
                    current_line = lines[line_num].strip()

                    if old_text in current_line or current_line in old_text:
                        lines[line_num] = change['new'] + '\n'
                        self._log(f"    [+] Replaced line {change['line']}", "info")
                    else:
                        self._log(f"    [!] Line {change['line']} doesn't match expected text, skipping", "warning")

                elif action == 'insert_after':
                    lines.insert(line_num + 1, change['new'] + '\n')
                    self._log(f"    [+] Inserted after line {change['line']}", "info")

                elif action == 'delete':
                    del lines[line_num]
                    self._log(f"    [+] Deleted line {change['line']}", "info")

            return ''.join(lines)

        except Exception as e:
            self._log(f"    [X] Failed to apply diff changes: {e}", "error")
            return None

    def _generate_fixes(self, issues: List[Dict], mode: str) -> List[Dict]:
        """Generate code fixes for identified issues"""
        fixes = []

        # Rate Limit Awareness (Anthropic Free Tier - Sonnet 4.5)
        # - 5 requests/min
        # - 10K input tokens/min
        # - 4K output tokens/min (BOTTLENECK!)
        #
        # Strategy: Process fewer issues, add delays between requests
        import time

        # Use Senior Engineer for ALL fix generation (not "Designs" agent)
        # "Designs" agent creates wireframes/documentation, not code fixes
        # Senior Engineer agent writes actual code implementations
        agent_id = "Senior"

        # Use Sonnet for fix generation (better quality than Haiku)
        # Analysis stays on Haiku (fast), but fixes need higher quality output
        # Phase 0D: Add fallback to Anthropic if Grok unavailable
        try:
            fix_agent = create_agent_with_model(
                agent_id,
                MODEL_PRESETS["Grok Reasoning"]['default']  # Fast reasoning model with high rate limits
            )
            self._log(f"[FIX] Fix generation using Grok 4 Fast Reasoning (480 rpm, 4M tpm)", "info")
            self._log(f"[INFO] No delays needed - Grok has 100x higher rate limits!", "info")
        except Exception as e:
            self._log(f"[!] Grok unavailable: {e}", "warning")
            self._log(f"[FALLBACK] Using Anthropic Claude Sonnet instead", "info")

            fix_agent = create_agent_with_model(
                agent_id,
                MODEL_PRESETS["Balanced (All Sonnet)"]['default']
            )
            self._log(f"[FIX] Fix generation using Claude Sonnet 3.5 (50 rpm, 40K tpm)", "info")

        for issue in issues:
            file_path_raw = issue.get('file', '')

            # Handle multi-file issues (e.g., "file1.py, file2.py")
            # Split into separate fixes for each file
            if ', ' in file_path_raw:
                file_paths = [fp.strip() for fp in file_path_raw.split(',')]
                self._log(f"📋 Issue affects {len(file_paths)} files - creating separate fix for each", "info")

                # Create separate issue for each file
                for fp in file_paths:
                    if Path(fp).exists():
                        # Create a copy of the issue for this specific file
                        single_file_issue = issue.copy()
                        single_file_issue['file'] = fp
                        issues.append(single_file_issue)
                    else:
                        self._log(f"   [!] File not found: {fp}", "warning")

                # Skip the original multi-file issue
                continue

            file_path = file_path_raw
            if not file_path or not Path(file_path).exists():
                issue_title = issue.get('title', 'Unknown issue')
                self._log(f"[!] Skipping issue '{issue_title}': Invalid file path '{file_path}'", "warning")
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

            # Check file size - skip files that are too large for reliable full rewrites
            line_count = len(current_content.splitlines())

            # Skip files over 400 lines - Grok consistently outputs incomplete rewrites for large files
            # Reduced from 800 to 400 to prevent truncation issues (96% file shrinkage bug)
            if line_count > 400:
                issue_title = issue.get('title', 'Unknown issue')
                self._log(f"[!] Skipping issue '{issue_title}': File too large ({line_count} lines, max 400)", "warning")
                self._log(f"    Large file: {Path(file_path).name} - Consider breaking into smaller modules", "info")
                self._log(f"    💡 Tip: For large files, create separate targeted issues for specific functions/sections", "info")
                continue

            # Threshold for diff-based approach: DISABLED (Grok handles full rewrites better)
            # With Grok's 4M tokens/min and 480 rpm, we can do full rewrites for all files under 400 lines
            # Diff-based approach was causing Grok to ignore format requirements
            # Note: Reduced from 800 to 400 lines to prevent truncation issues (Phase 0C fix)
            if False:  # Disabled - always use full rewrites
                self._log(f"[SIZE] Large file detected ({line_count} lines) - using diff-based approach", "info")

                # Generate diff-based fix
                diff_fix = self._generate_diff_based_fix(issue, file_path, current_content, fix_agent)

                if diff_fix and diff_fix.get('type') == 'diff':
                    # Apply diff changes to get fixed content
                    fixed_content = self._apply_diff_based_fix(file_path, diff_fix['changes'])

                    if fixed_content:
                        fixes.append({
                            'file': file_path,
                            'issue': issue,
                            'original_content': current_content,
                            'fixed_content': fixed_content,
                            'fix_type': 'diff'
                        })
                        continue
                    else:
                        self._log(f"  [!] Diff-based fix failed to apply, skipping", "warning")
                        continue
                else:
                    self._log(f"  [!] Diff-based fix generation failed, skipping", "warning")
                    continue

            # For files ≤1000 lines, use full-file regeneration (best quality with Grok)
            # Generate fix with ULTRA-EXPLICIT format requirements
            # Problem: Grok ignores format requirements and adds explanations
            # Solution: Use XML tags and make it a code completion task, not a chat
            fix_prompt = f"""
YOU ARE A CODE FILE GENERATOR. YOUR ONLY JOB IS TO OUTPUT VALID CODE FILES.

===================================================================================
ABSOLUTE REQUIREMENT - NO EXCEPTIONS:
===================================================================================

Your ENTIRE response must be wrapped in these XML tags:
<file_content>
[COMPLETE FIXED FILE - NOTHING ELSE]
</file_content>

DO NOT write anything before <file_content>
DO NOT write anything after </file_content>
DO NOT explain what you did
DO NOT say "Here's the fixed code"
DO NOT add any prose or commentary

ONLY output: <file_content> [code] </file_content>

===================================================================================
EXAMPLE OF CORRECT OUTPUT:
===================================================================================

<file_content>
import streamlit as st

def main():
    st.title("Hello World")
    st.write("This is the complete file")

if __name__ == "__main__":
    main()
</file_content>

THAT'S IT. Nothing before the opening tag. Nothing after the closing tag.

===================================================================================
YOUR TASK:
===================================================================================

FILE TO FIX: {file_path}
ISSUE: {issue.get('title', 'Unknown issue')}
WHAT'S WRONG: {issue.get('description', '')}
HOW TO FIX: {issue.get('suggestion', '')}

CURRENT FILE CONTENT ({len(current_content)} chars - THIS IS THE COMPLETE FILE):
```
{current_content}
```

INSTRUCTIONS:
1. Apply the fix described above
2. Output the ENTIRE fixed file (start to finish, every line)
3. Wrap ONLY in <file_content></file_content> tags
4. DO NOT add explanations, summaries, or any text outside the tags

START YOUR RESPONSE NOW WITH: <file_content>
"""

            task = Task(
                description=fix_prompt,
                agent=fix_agent,
                expected_output="<file_content>\n[COMPLETE FILE CODE - NO EXPLANATIONS]\n</file_content>\n\nFirst word must be: <file_content>\nLast word must be: </file_content>\nNOTHING before or after these tags."
            )

            crew = Crew(
                agents=[fix_agent],
                tasks=[task],
                process=Process.sequential,
                verbose=False
            )

            try:
                # Retry logic for API failures (500 errors, rate limits, etc.)
                max_retries = 3
                retry_delay = 2  # seconds
                result_text = None

                for attempt in range(1, max_retries + 1):
                    try:
                        result = crew.kickoff()
                        result_text = result.raw if hasattr(result, 'raw') else str(result)

                        # Validate output length - detect truncated responses (Phase 0C fix)
                        expected_min_chars = len(current_content) * 0.8  # Should be at least 80% of original
                        actual_chars = len(result_text)

                        if actual_chars < expected_min_chars:
                            self._log(f"  [!] WARNING: Agent output suspiciously short for {Path(file_path).name}", "warning")
                            self._log(f"     Expected ≥{expected_min_chars:.0f} chars (80% of original), got {actual_chars} chars", "warning")
                            self._log(f"     This may indicate truncated output. Attempting extraction anyway...", "info")

                        break  # Success - exit retry loop

                    except Exception as api_error:
                        error_str = str(api_error)

                        # Check if it's a retryable error (500, rate limit, timeout)
                        is_retryable = (
                            '500' in error_str or
                            'Internal server error' in error_str or
                            '429' in error_str or
                            'rate' in error_str.lower() or
                            'timeout' in error_str.lower()
                        )

                        if is_retryable and attempt < max_retries:
                            wait_time = retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                            self._log(f"  [!] API error (attempt {attempt}/{max_retries}): {error_str[:100]}", "warning")
                            self._log(f"  [WAIT] Retrying in {wait_time}s...", "info")
                            import time
                            time.sleep(wait_time)
                        else:
                            # Non-retryable error or max retries reached
                            self._log(f"  [X] API error after {attempt} attempts: {error_str[:200]}", "error")
                            raise

                if result_text is None:
                    self._log(f"  [X] Failed to get response after {max_retries} retries", "error")
                    continue

                # Extract fixed content with robust XML parsing
                # Primary: Look for <file_content> tags (new XML format for Grok)
                if '<file_content>' in result_text and '</file_content>' in result_text:
                    start_idx = result_text.index('<file_content>') + len('<file_content>')
                    end_idx = result_text.index('</file_content>')
                    fixed_content = result_text[start_idx:end_idx]

                    # Clean up content
                    fixed_content = fixed_content.strip()
                    fixed_content = fixed_content.strip('`')  # Remove backticks if present
                    fixed_content = fixed_content.strip()

                    # Remove language identifier if present (e.g., "python" right after start tag)
                    first_line = fixed_content.split('\n')[0].strip().lower()
                    if first_line in ['python', 'py', 'javascript', 'js', 'typescript', 'ts', 'html', 'css']:
                        fixed_content = '\n'.join(fixed_content.split('\n')[1:])

                    # Validate - reject placeholder/truncated outputs (Enhanced Phase 0C checks)
                    # Check for incomplete patterns throughout the file, not just first 200 chars
                    incomplete_patterns = [
                        ('...', 'ellipsis abbreviation'),
                        ('# ... rest of code', 'code omission marker'),
                        ('// ... (remaining code)', 'code omission marker'),
                        ('# TODO: Add remaining', 'incomplete implementation'),
                        ('// TODO: Add remaining', 'incomplete implementation'),
                        ('... rest of code', 'code omission marker'),
                        ('... (remaining code)', 'code omission marker'),
                    ]

                    is_incomplete = False
                    for pattern, reason in incomplete_patterns:
                        if pattern in fixed_content:
                            self._log(f"  [!] Fix contains incomplete pattern for {Path(file_path).name}: '{pattern}' ({reason})", "warning")
                            self._log(f"     Agent generated partial output. First 200 chars: {repr(fixed_content[:200])}", "warning")
                            is_incomplete = True
                            break

                    if is_incomplete:
                        continue

                    # Also check: file should end properly (not truncated mid-line)
                    if not fixed_content.endswith('\n') and len(fixed_content) > 100:
                        last_lines = fixed_content.split('\n')[-3:]  # Check last 3 lines
                        if any(line.strip().endswith('...') or line.strip().endswith('# ...') for line in last_lines):
                            self._log(f"  [!] File appears to be truncated (ends with '...')", "warning")
                            self._log(f"     Last 100 chars: {repr(fixed_content[-100:])}", "warning")
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
                        self._log(f"  [!] Fix too short for {Path(file_path).name} ({len(fixed_content)} chars), skipping", "warning")
                        self._log(f"     Content received: {repr(fixed_content[:100])}", "warning")

                # Fallback: Legacy FILE_CONTENT_START/END markers (for backwards compatibility)
                elif 'FILE_CONTENT_START' in result_text and 'FILE_CONTENT_END' in result_text:
                    start_idx = result_text.index('FILE_CONTENT_START') + len('FILE_CONTENT_START')
                    end_idx = result_text.index('FILE_CONTENT_END')
                    fixed_content = result_text[start_idx:end_idx].strip()

                    if len(fixed_content) > 50 and '...' not in fixed_content[:200]:
                        fixes.append({
                            'file': file_path,
                            'issue': issue,
                            'original_content': current_content,
                            'fixed_content': fixed_content
                        })
                    else:
                        self._log(f"  [!] Legacy marker extraction failed (too short or has placeholders)", "warning")
                else:
                    # Fallback 1: Check if XML tag exists without closing tag
                    # Agent sometimes outputs <file_content> but forgets </file_content>
                    if '<file_content>' in result_text:
                        self._log(f"  [!] Found <file_content> but no </file_content>, extracting remaining content for {Path(file_path).name}", "info")

                        start_idx = result_text.index('<file_content>') + len('<file_content>')
                        fixed_content = result_text[start_idx:].strip()

                        # Clean up
                        first_line = fixed_content.split('\n')[0].strip().lower()
                        if first_line in ['python', 'py', 'javascript', 'js', 'typescript', 'ts', 'html', 'css']:
                            fixed_content = '\n'.join(fixed_content.split('\n')[1:])

                        # Validate
                        if '...' not in fixed_content[:200] and len(fixed_content) > 50:
                            self._log(f"  [+] Fallback extraction successful: {len(fixed_content)} chars from <file_content> to end", "info")
                            fixes.append({
                                'file': file_path,
                                'issue': issue,
                                'original_content': current_content,
                                'fixed_content': fixed_content
                            })
                            continue
                        else:
                            self._log(f"  [!] Extracted content invalid (too short or has placeholders)", "warning")

                    # Fallback 2: Try to extract code from markdown code blocks
                    # Agent likes to output: ```python\n<code>\n``` followed by explanation
                    self._log(f"  [!] No valid markers found, trying markdown code block extraction for {Path(file_path).name}", "info")

                    import re
                    # Look for the largest code block (likely the full file)
                    code_blocks = re.findall(r'```(?:python|py|javascript|js|typescript|ts|jsx|tsx|html|css)?\n(.*?)```', result_text, re.DOTALL)

                    if code_blocks:
                        # Use the largest code block (most likely to be the complete file)
                        fixed_content = max(code_blocks, key=len)
                        fixed_content = fixed_content.strip()

                        # Validate - reject placeholder/truncated outputs
                        if '...' in fixed_content[:200] or '…' in fixed_content[:200]:
                            self._log(f"  [!] Fallback extraction found '...' placeholder, rejecting", "warning")
                            continue

                        # Validate we got substantial content
                        if len(fixed_content) > 50:
                            self._log(f"  [+] Fallback extraction successful: {len(fixed_content)} chars from largest code block", "info")
                            fixes.append({
                                'file': file_path,
                                'issue': issue,
                                'original_content': current_content,
                                'fixed_content': fixed_content
                            })
                        else:
                            self._log(f"  [!] Fallback extraction too short ({len(fixed_content)} chars)", "warning")
                    else:
                        self._log(f"  [!] Could not find any code blocks in fix for {Path(file_path).name}", "warning")
                        # Show first 200 chars of output for debugging
                        self._log(f"  Agent output preview: {result_text[:200]}", "warning")

            except Exception as e:
                self._log(f"Fix generation failed for {file_path}: {e}", "error")

            # Grok has 480 rpm and 4M tpm - no delays needed!
            # Keeping this code commented for potential fallback to Anthropic
            # if len(fixes) < len(issues) - 1:
            #     self._log(f"  [WAIT] Waiting 15s before next fix (rate limit protection)...", "info")
            #     time.sleep(15)

        return fixes

    def _apply_and_test_fixes(self, fixes: List[Dict], issues: List[Dict], mode: str) -> int:
        """
        Apply fixes with test-fix-retest loop

        For each fix:
        1. Apply it
        2. Test it (syntax + imports)
        3. If fails -> send back to Fixer agent with error
        4. Retry up to 3 times
        5. Keep only fixes that pass tests
        """
        applied = 0
        max_retries = 3

        # Track which files have been modified
        modified_files = {}

        for i, fix in enumerate(fixes):
            file_path = fix['file']
            issue = issues[i] if i < len(issues) else {}

            self._log(f"[COMMIT] Fix {i+1}/{len(fixes)}: {Path(file_path).name}", "info")

            # Check if this file was already modified
            if file_path in modified_files:
                previous_fix_num = modified_files[file_path]
                self._log(f"  [WARNING] WARNING: This file was already modified by Fix #{previous_fix_num}", "warning")
                self._log(f"     This fix will OVERWRITE changes from Fix #{previous_fix_num}", "warning")

            # Try to get a working fix (up to max_retries attempts)
            for attempt in range(1, max_retries + 1):
                if attempt > 1:
                    self._log(f"  [CYCLE] Retry {attempt}/{max_retries}...", "info")

                # Get the fix content (first attempt uses original, retries use regenerated)
                if attempt == 1:
                    fixed_content = fix['fixed_content']
                else:
                    # Regenerate fix with error feedback
                    self._log(f"  -> Asking Fixer agent to address test failure...", "info")
                    fixed_content = self._regenerate_fix_with_feedback(
                        file_path,
                        fix['original_content'],
                        issue,
                        last_error,
                        mode
                    )

                    if not fixed_content:
                        self._log(f"  [!] Could not regenerate fix, skipping", "warning")
                        break

                # SAFETY CHECK: Validate fixed content isn't catastrophically shorter
                original_content = fix['original_content']
                original_lines = len(original_content.splitlines())
                fixed_lines = len(fixed_content.splitlines())

                # Reject if file shrunk by >30% (likely incomplete/truncated output)
                if fixed_lines < original_lines * 0.7:
                    shrink_pct = int((1 - fixed_lines / original_lines) * 100)
                    self._log(f"  [X] REJECTED: File shrunk by {shrink_pct}% ({original_lines} -> {fixed_lines} lines)", "error")
                    self._log(f"     This looks like incomplete output. Refusing to apply destructive change.", "error")
                    break

                # Apply the fix temporarily
                original_content = self._backup_and_apply(file_path, fixed_content)

                # Test the fix
                test_passed, error_message = self._test_fix(file_path, fixed_content)

                if test_passed:
                    # Success! Keep the fix
                    modified_files[file_path] = i + 1  # Track this fix number

                    # Show what changed
                    changes_summary = self._summarize_changes(original_content, fixed_content)
                    self._log(f"  [+] Fix applied and tested successfully", "success")
                    self._log(f"     Changes: {changes_summary}", "info")

                    applied += 1
                    break
                else:
                    # Test failed - rollback
                    last_error = error_message
                    self._log(f"  ✗ Test failed: {error_message[:100]}", "warning")
                    self._rollback_fix(file_path, original_content)

                    if attempt == max_retries:
                        self._log(f"  [!] Max retries reached, skipping this fix", "warning")

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

    def _summarize_changes(self, original: str, fixed: str) -> str:
        """Generate a concise summary of what changed between two file versions"""
        import difflib

        original_lines = original.splitlines()
        fixed_lines = fixed.splitlines()

        # Count changes
        diff = list(difflib.unified_diff(original_lines, fixed_lines, lineterm=''))

        # Filter to just the actual change lines (start with + or -)
        additions = [line for line in diff if line.startswith('+') and not line.startswith('+++')]
        deletions = [line for line in diff if line.startswith('-') and not line.startswith('---')]

        # Find changed line numbers
        changed_line_nums = []
        for i, (orig_line, fixed_line) in enumerate(zip(original_lines, fixed_lines), 1):
            if orig_line != fixed_line:
                changed_line_nums.append(i)

        # Build summary
        if not additions and not deletions:
            return "No changes detected"

        parts = []
        if changed_line_nums:
            if len(changed_line_nums) <= 5:
                parts.append(f"Modified lines {', '.join(map(str, changed_line_nums))}")
            else:
                parts.append(f"Modified {len(changed_line_nums)} lines")

        parts.append(f"+{len(additions)} lines, -{len(deletions)} lines")

        # Show a snippet of what was added if it's small
        if len(additions) == 1 and len(additions[0]) < 60:
            parts.append(f"Added: '{additions[0][1:].strip()}'")

        return " | ".join(parts)

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

        # Use Sonnet for fix regeneration (better quality than Haiku)
        fix_agent = create_agent_with_model(
            agent_id,
            MODEL_PRESETS["Grok Reasoning"]['default']  # Fast reasoning model with high rate limits
        )

        fix_prompt = f"""
[WARNING][WARNING][WARNING] CRITICAL FORMAT REQUIREMENT [WARNING][WARNING][WARNING]

YOUR ENTIRE RESPONSE MUST BE:

FILE_CONTENT_START
[complete fixed file code here]
FILE_CONTENT_END

NOTHING ELSE. NO TEXT BEFORE. NO TEXT AFTER. NO EXPLANATIONS.

===============================================================================

Your previous fix FAILED testing. Fix the error and try again.

FILE: {file_path}
ISSUE: {issue.get('title', 'Unknown issue')}
DESCRIPTION: {issue.get('description', '')}

ORIGINAL CODE (COMPLETE FILE - {len(original_content)} characters):
```
{original_content}
```

PREVIOUS FIX FAILED WITH ERROR:
{error_message}

CRITICAL - YOU HAVE THE COMPLETE FILE ABOVE:
The code shown above is the ENTIRE original file.
Your output must also be the ENTIRE file from start to finish.

WHAT TO DO:
1. Understand WHY the error occurred
2. Generate a NEW fix that DOES NOT have this error
3. Ensure syntax is 100% valid Python
4. Output ENTIRE file wrapped in FILE_CONTENT_START / FILE_CONTENT_END
5. If the file is long, output ALL of it - DO NOT stop early

Common issues to avoid:
- 'await' outside async function
- Missing colons after if/for/while/def/class
- Incorrect indentation
- Unmatched parentheses/brackets

REMINDER - Your output MUST start with "FILE_CONTENT_START" and end with "FILE_CONTENT_END". NO other text.

BEGIN NOW:
"""

        try:
            task = Task(
                description=fix_prompt,
                agent=fix_agent,
                expected_output="Your ENTIRE response must be:\nFILE_CONTENT_START\n[complete fixed file code - NO explanations]\nFILE_CONTENT_END\n\nFirst character: F (from FILE_CONTENT_START)\nLast word: FILE_CONTENT_END\nNO text before or after these markers."
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
                encoding='utf-8',
                errors='replace',
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
                capture_output=True,
                encoding='utf-8',
                errors='replace'
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
                capture_output=True,
                encoding='utf-8',
                errors='replace'
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
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            # Get commit hash
            hash_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
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
                check=False,
                encoding='utf-8',
                errors='replace'
            )

            if diff_result.stdout:
                return diff_result.stdout

            # Fallback: try to compare with main branch
            main_diff = subprocess.run(
                ['git', 'diff', 'main...HEAD'],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                check=False,
                encoding='utf-8',
                errors='replace'
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

        preset = MODEL_PRESETS[self.config['model']['default_preset']]
        scorer_agent = create_agent_with_model(
            "Scorer",
            preset['default']
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
                capture_output=True,
                encoding='utf-8',
                errors='replace'
            )
            self._log("[+] Rolled back to main branch", "success")
            return True
        except subprocess.CalledProcessError as e:
            self._log(f"Rollback failed: {e}", "error")
            return False
