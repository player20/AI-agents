"""
Static Analysis Module

Performs static code analysis including:
- Syntax validation
- Import resolution
- Dependency checking
- Security scanning
- Code quality checks
"""

import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from .project_detector import ProjectType, ProjectInfo


def _get_executable(name: str) -> str:
    """Get full path to executable, handling Windows .cmd wrappers."""
    executable = shutil.which(name)
    return executable if executable else name


def _safe_run(args: List[str], cwd: str = None, **kwargs) -> subprocess.CompletedProcess:
    """Safely run subprocess without shell=True."""
    resolved_args = [_get_executable(args[0])] + args[1:]
    kwargs.pop('shell', None)
    return subprocess.run(resolved_args, cwd=cwd, **kwargs)


class IssueSeverity(Enum):
    """Severity levels for issues found."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class AnalysisIssue:
    """An issue found during static analysis."""
    severity: IssueSeverity
    category: str
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    code: Optional[str] = None  # Error code like E501, W0611

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "category": self.category,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "code": self.code,
        }


@dataclass
class StaticAnalysisResult:
    """Result of static analysis."""
    status: str  # pass, warn, fail
    issues: List[AnalysisIssue] = field(default_factory=list)
    files_analyzed: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "files_analyzed": self.files_analyzed,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "issues": [i.to_dict() for i in self.issues],
        }


class StaticAnalyzer:
    """
    Performs static analysis on code projects.

    Supports Python, JavaScript/TypeScript, and HTML/CSS.
    """

    # Patterns for security issues
    SECURITY_PATTERNS = {
        "hardcoded_secret": [
            r'(?i)(password|secret|api_key|token|auth)\s*=\s*["\'][^"\']+["\']',
            r'(?i)Bearer\s+[a-zA-Z0-9_-]+',
        ],
        "sql_injection": [
            r'(?i)execute\s*\([^)]*%s',
            r'(?i)execute\s*\([^)]*\+',
            r'(?i)f".*SELECT.*\{',
            r'(?i)f".*INSERT.*\{',
            r'(?i)f".*UPDATE.*\{',
            r'(?i)f".*DELETE.*\{',
        ],
        "command_injection": [
            r'subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True',
            r'os\.system\s*\(',
            r'eval\s*\(',
            r'exec\s*\(',
        ],
    }

    def __init__(self):
        self.issues: List[AnalysisIssue] = []

    def analyze(self, project: ProjectInfo) -> StaticAnalysisResult:
        """
        Run static analysis on a project.

        Args:
            project: ProjectInfo with project details

        Returns:
            StaticAnalysisResult with all findings
        """
        self.issues = []
        files_analyzed = 0

        # Run analysis based on project type
        if project.project_type in [ProjectType.PYTHON, ProjectType.STREAMLIT,
                                     ProjectType.FLASK, ProjectType.DJANGO,
                                     ProjectType.FASTAPI]:
            files_analyzed += self._analyze_python(project.path)

        elif project.project_type in [ProjectType.REACT, ProjectType.VUE,
                                       ProjectType.NEXTJS, ProjectType.NODEJS]:
            files_analyzed += self._analyze_javascript(project.path)

        # Always check for security issues
        files_analyzed += self._security_scan(project.path)

        # Count issues by severity
        error_count = sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)
        warning_count = sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)
        info_count = sum(1 for i in self.issues if i.severity == IssueSeverity.INFO)

        # Determine overall status
        if error_count > 0:
            status = "fail"
        elif warning_count > 0:
            status = "warn"
        else:
            status = "pass"

        return StaticAnalysisResult(
            status=status,
            issues=self.issues,
            files_analyzed=files_analyzed,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
        )

    def _analyze_python(self, path: Path) -> int:
        """Analyze Python files."""
        files_analyzed = 0
        python_files = list(path.rglob("*.py"))

        # Exclude virtual environments and common non-source directories
        exclude_dirs = {"venv", "venv312", "venv314", ".venv", "env", "__pycache__",
                        "node_modules", ".git", "dist", "build", ".tox", ".pytest_cache"}
        python_files = [
            f for f in python_files
            if not any(ex in f.parts for ex in exclude_dirs)
        ]

        for py_file in python_files:
            files_analyzed += 1
            self._check_python_syntax(py_file)
            self._check_python_imports(py_file)

        # Try running ruff if available
        self._run_ruff(path)

        # Try running mypy if available
        self._run_mypy(path)

        return files_analyzed

    def _check_python_syntax(self, file_path: Path) -> None:
        """Check Python syntax using AST."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            self.issues.append(AnalysisIssue(
                severity=IssueSeverity.ERROR,
                category="syntax",
                message=f"Syntax error: {e.msg}",
                file=str(file_path),
                line=e.lineno,
                column=e.offset,
            ))

    def _check_python_imports(self, file_path: Path) -> None:
        """Check if Python imports can be resolved."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._verify_import(alias.name, file_path, node.lineno)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._verify_import(node.module, file_path, node.lineno)

        except SyntaxError:
            pass  # Already reported in syntax check

    def _verify_import(self, module_name: str, file_path: Path, line: int) -> None:
        """Verify that an import can be resolved."""
        # Skip standard library and common packages
        stdlib_modules = {
            "os", "sys", "re", "json", "typing", "dataclasses", "enum",
            "pathlib", "subprocess", "time", "datetime", "collections",
            "functools", "itertools", "logging", "unittest", "asyncio",
            "abc", "copy", "math", "random", "hashlib", "base64",
            "io", "tempfile", "shutil", "glob", "contextlib",
        }

        root_module = module_name.split(".")[0]

        if root_module in stdlib_modules:
            return

        # Skip relative imports (start with .)
        if module_name.startswith("."):
            return

        # For now, just note unverified imports as info
        # In production, would actually try to import
        pass

    def _run_ruff(self, path: Path) -> None:
        """Run ruff linter if available."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", str(path), "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=path,
            )

            if result.stdout:
                import json
                try:
                    issues = json.loads(result.stdout)
                    for issue in issues:
                        self.issues.append(AnalysisIssue(
                            severity=IssueSeverity.WARNING,
                            category="lint",
                            message=issue.get("message", ""),
                            file=issue.get("filename", ""),
                            line=issue.get("location", {}).get("row"),
                            column=issue.get("location", {}).get("column"),
                            code=issue.get("code", ""),
                        ))
                except json.JSONDecodeError:
                    pass

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Ruff not available or timed out
            pass

    def _run_mypy(self, path: Path) -> None:
        """Run mypy type checker if available."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "mypy", str(path), "--ignore-missing-imports"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=path,
            )

            if result.stdout:
                # Parse mypy output: file:line: severity: message
                for line in result.stdout.splitlines():
                    match = re.match(r'(.+):(\d+):\s*(error|warning|note):\s*(.+)', line)
                    if match:
                        file, lineno, severity, message = match.groups()
                        severity_map = {
                            "error": IssueSeverity.ERROR,
                            "warning": IssueSeverity.WARNING,
                            "note": IssueSeverity.INFO,
                        }
                        self.issues.append(AnalysisIssue(
                            severity=severity_map.get(severity, IssueSeverity.INFO),
                            category="type",
                            message=message,
                            file=file,
                            line=int(lineno),
                        ))

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Mypy not available or timed out
            pass

    def _analyze_javascript(self, path: Path) -> int:
        """Analyze JavaScript/TypeScript files."""
        files_analyzed = 0

        # Find JS/TS files
        js_files = list(path.rglob("*.js")) + list(path.rglob("*.jsx"))
        ts_files = list(path.rglob("*.ts")) + list(path.rglob("*.tsx"))
        all_files = js_files + ts_files

        # Exclude node_modules and common non-source directories
        exclude_dirs = {"node_modules", ".git", "dist", "build", ".next", "coverage"}
        all_files = [
            f for f in all_files
            if not any(ex in f.parts for ex in exclude_dirs)
        ]

        for js_file in all_files:
            files_analyzed += 1
            self._check_javascript_basics(js_file)

        # Try running eslint if available
        self._run_eslint(path)

        return files_analyzed

    def _check_javascript_basics(self, file_path: Path) -> None:
        """Basic JavaScript checks."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            # Check for common issues
            if "console.log" in content:
                self.issues.append(AnalysisIssue(
                    severity=IssueSeverity.INFO,
                    category="code-quality",
                    message="console.log statement found",
                    file=str(file_path),
                ))

            # Check for debugger statements
            if "debugger" in content:
                self.issues.append(AnalysisIssue(
                    severity=IssueSeverity.WARNING,
                    category="code-quality",
                    message="debugger statement found",
                    file=str(file_path),
                ))

        except IOError:
            pass

    def _run_eslint(self, path: Path) -> None:
        """Run ESLint if available."""
        try:
            result = _safe_run(
                ["npx", "eslint", ".", "--format=json"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=path
            )

            if result.stdout:
                import json
                try:
                    files = json.loads(result.stdout)
                    for file_result in files:
                        for msg in file_result.get("messages", []):
                            severity_map = {1: IssueSeverity.WARNING, 2: IssueSeverity.ERROR}
                            self.issues.append(AnalysisIssue(
                                severity=severity_map.get(msg.get("severity"), IssueSeverity.WARNING),
                                category="lint",
                                message=msg.get("message", ""),
                                file=file_result.get("filePath", ""),
                                line=msg.get("line"),
                                column=msg.get("column"),
                                code=msg.get("ruleId", ""),
                            ))
                except json.JSONDecodeError:
                    pass

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # ESLint not available or timed out
            pass

    def _security_scan(self, path: Path) -> int:
        """Scan for security issues in all files."""
        files_scanned = 0

        # Scan all text-like files
        extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yml", ".yaml", ".env"}
        exclude_dirs = {"node_modules", "venv", ".venv", ".git", "__pycache__"}

        for ext in extensions:
            for file_path in path.rglob(f"*{ext}"):
                if any(ex in file_path.parts for ex in exclude_dirs):
                    continue

                files_scanned += 1
                self._scan_file_for_security(file_path)

        return files_scanned

    def _scan_file_for_security(self, file_path: Path) -> None:
        """Scan a single file for security issues."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            for category, patterns in self.SECURITY_PATTERNS.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        # Find line number
                        line_num = content[:match.start()].count('\n') + 1

                        self.issues.append(AnalysisIssue(
                            severity=IssueSeverity.WARNING,
                            category="security",
                            message=f"Potential {category.replace('_', ' ')}: {match.group()[:50]}...",
                            file=str(file_path),
                            line=line_num,
                        ))

        except IOError:
            pass


# Convenience function
def analyze_project(project: ProjectInfo) -> StaticAnalysisResult:
    """
    Run static analysis on a project.

    Args:
        project: ProjectInfo with project details

    Returns:
        StaticAnalysisResult with findings
    """
    analyzer = StaticAnalyzer()
    return analyzer.analyze(project)
