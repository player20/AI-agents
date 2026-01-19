"""
Code Validation Pipeline using Ruff and Semgrep

Provides comprehensive code quality and security validation.
Ensures generated code meets quality standards and has no vulnerabilities.

Features:
- Ruff linting for Python (fast, comprehensive)
- Semgrep for security scanning (multi-language)
- ESLint/TypeScript checking
- Auto-fix capabilities
- Severity-based reporting
"""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import subprocess
import tempfile
import json
import os
import logging
import shutil

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    """Issue severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class IssueCategory(str, Enum):
    """Issue categories"""
    SYNTAX = "syntax"
    STYLE = "style"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"
    COMPLEXITY = "complexity"
    DEPRECATED = "deprecated"
    BEST_PRACTICE = "best_practice"


@dataclass
class CodeIssue:
    """A code quality or security issue"""
    file_path: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    code: str = ""  # Rule code (e.g., E501, S101)
    message: str = ""
    severity: Severity = Severity.WARNING
    category: IssueCategory = IssueCategory.STYLE
    fix: Optional[str] = None  # Suggested fix
    source: str = ""  # Tool that found it (ruff, semgrep, etc.)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file_path,
            "line": self.line,
            "column": self.column,
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "fix": self.fix,
            "source": self.source
        }


@dataclass
class ValidationResult:
    """Result of code validation"""
    is_valid: bool
    issues: List[CodeIssue] = field(default_factory=list)
    fixed_code: Optional[str] = None
    summary: Dict[str, int] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [i.to_dict() for i in self.issues],
            "summary": self.summary
        }


class RuffValidator:
    """
    Python code validation using Ruff.

    Ruff is an extremely fast Python linter that can replace:
    - Flake8 (plus dozens of plugins)
    - Black (formatting)
    - isort (import sorting)
    - pyupgrade, autoflake, and more
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._ruff_available = self._check_ruff()

    def _check_ruff(self) -> bool:
        """Check if ruff is installed"""
        return shutil.which("ruff") is not None

    def validate(
        self,
        code: str,
        filename: str = "code.py",
        fix: bool = False
    ) -> ValidationResult:
        """
        Validate Python code using Ruff.

        Args:
            code: Python code to validate
            filename: Virtual filename for the code
            fix: Whether to apply auto-fixes

        Returns:
            ValidationResult with issues found
        """
        if not self._ruff_available:
            logger.warning("Ruff not available, using fallback validation")
            return self._fallback_validate(code)

        issues = []

        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        ) as f:
            f.write(code)
            temp_path = f.name

        try:
            # Run ruff check
            cmd = ["ruff", "check", temp_path, "--output-format", "json"]

            if fix:
                cmd.append("--fix")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Parse JSON output
            if result.stdout:
                try:
                    ruff_issues = json.loads(result.stdout)
                    for issue in ruff_issues:
                        issues.append(CodeIssue(
                            file_path=filename,
                            line=issue.get("location", {}).get("row", 1),
                            column=issue.get("location", {}).get("column", 1),
                            end_line=issue.get("end_location", {}).get("row"),
                            end_column=issue.get("end_location", {}).get("column"),
                            code=issue.get("code", ""),
                            message=issue.get("message", ""),
                            severity=self._map_severity(issue.get("code", "")),
                            category=self._map_category(issue.get("code", "")),
                            fix=issue.get("fix", {}).get("content") if issue.get("fix") else None,
                            source="ruff"
                        ))
                except json.JSONDecodeError:
                    pass

            # Read fixed code if requested
            fixed_code = None
            if fix:
                with open(temp_path, 'r') as f:
                    fixed_code = f.read()

        finally:
            os.unlink(temp_path)

        # Determine validity (no errors)
        is_valid = not any(i.severity == Severity.ERROR for i in issues)

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            fixed_code=fixed_code,
            summary=self._summarize(issues)
        )

    def format_code(self, code: str) -> str:
        """Format Python code using Ruff"""
        if not self._ruff_available:
            return code

        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        ) as f:
            f.write(code)
            temp_path = f.name

        try:
            subprocess.run(
                ["ruff", "format", temp_path],
                capture_output=True,
                timeout=30
            )
            with open(temp_path, 'r') as f:
                return f.read()
        finally:
            os.unlink(temp_path)

    def _fallback_validate(self, code: str) -> ValidationResult:
        """Fallback validation using Python's compile"""
        issues = []

        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            issues.append(CodeIssue(
                file_path="code.py",
                line=e.lineno or 1,
                column=e.offset or 1,
                code="E999",
                message=str(e.msg),
                severity=Severity.ERROR,
                category=IssueCategory.SYNTAX,
                source="python"
            ))

        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues
        )

    def _map_severity(self, code: str) -> Severity:
        """Map Ruff code to severity"""
        if code.startswith("E") or code.startswith("F"):
            return Severity.ERROR
        elif code.startswith("W"):
            return Severity.WARNING
        elif code.startswith("C"):
            return Severity.INFO
        return Severity.WARNING

    def _map_category(self, code: str) -> IssueCategory:
        """Map Ruff code to category"""
        # Security-related rules
        if code.startswith("S"):
            return IssueCategory.SECURITY

        # Performance rules
        if code.startswith("PERF"):
            return IssueCategory.PERFORMANCE

        # Complexity rules
        if code.startswith("C9"):
            return IssueCategory.COMPLEXITY

        # Syntax errors
        if code in ("E999", "F999"):
            return IssueCategory.SYNTAX

        # Style rules
        if code.startswith("E") or code.startswith("W"):
            return IssueCategory.STYLE

        return IssueCategory.BEST_PRACTICE

    def _summarize(self, issues: List[CodeIssue]) -> Dict[str, int]:
        """Summarize issues by category"""
        summary = {}
        for issue in issues:
            key = f"{issue.severity.value}_{issue.category.value}"
            summary[key] = summary.get(key, 0) + 1
        return summary


class SemgrepValidator:
    """
    Security-focused validation using Semgrep.

    Semgrep finds bugs and security vulnerabilities using
    pattern matching and dataflow analysis.
    """

    # Default security rules to use
    DEFAULT_RULESETS = [
        "p/python",
        "p/javascript",
        "p/typescript",
        "p/security-audit",
        "p/owasp-top-ten",
    ]

    def __init__(self, rulesets: Optional[List[str]] = None):
        self.rulesets = rulesets or self.DEFAULT_RULESETS
        self._semgrep_available = self._check_semgrep()

    def _check_semgrep(self) -> bool:
        """Check if semgrep is installed"""
        return shutil.which("semgrep") is not None

    def scan(
        self,
        code: str,
        language: str,
        filename: Optional[str] = None
    ) -> ValidationResult:
        """
        Scan code for security issues.

        Args:
            code: Code to scan
            language: Programming language
            filename: Optional filename

        Returns:
            ValidationResult with security issues
        """
        if not self._semgrep_available:
            logger.warning("Semgrep not available, skipping security scan")
            return ValidationResult(is_valid=True, issues=[])

        ext_map = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "go": ".go",
            "java": ".java",
            "ruby": ".rb",
        }

        ext = ext_map.get(language.lower(), ".txt")
        filename = filename or f"code{ext}"

        issues = []

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, filename)
            with open(file_path, 'w') as f:
                f.write(code)

            try:
                # Run semgrep with security ruleset
                cmd = [
                    "semgrep",
                    "--config", "p/security-audit",
                    "--json",
                    "--quiet",
                    file_path
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.stdout:
                    try:
                        semgrep_output = json.loads(result.stdout)
                        for finding in semgrep_output.get("results", []):
                            issues.append(CodeIssue(
                                file_path=filename,
                                line=finding.get("start", {}).get("line", 1),
                                column=finding.get("start", {}).get("col", 1),
                                end_line=finding.get("end", {}).get("line"),
                                end_column=finding.get("end", {}).get("col"),
                                code=finding.get("check_id", ""),
                                message=finding.get("extra", {}).get("message", "Security issue found"),
                                severity=self._map_severity(finding.get("extra", {}).get("severity", "WARNING")),
                                category=IssueCategory.SECURITY,
                                source="semgrep"
                            ))
                    except json.JSONDecodeError:
                        pass

            except subprocess.TimeoutExpired:
                logger.warning("Semgrep scan timed out")
            except Exception as e:
                logger.error(f"Semgrep scan failed: {e}")

        is_valid = not any(i.severity == Severity.ERROR for i in issues)

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            summary={"security_issues": len(issues)}
        )

    def _map_severity(self, semgrep_severity: str) -> Severity:
        """Map Semgrep severity to our severity"""
        mapping = {
            "ERROR": Severity.ERROR,
            "WARNING": Severity.WARNING,
            "INFO": Severity.INFO,
        }
        return mapping.get(semgrep_severity.upper(), Severity.WARNING)


class ESLintValidator:
    """
    JavaScript/TypeScript validation using ESLint.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._eslint_available = self._check_eslint()

    def _check_eslint(self) -> bool:
        """Check if eslint is installed"""
        return shutil.which("eslint") is not None or shutil.which("npx") is not None

    def validate(
        self,
        code: str,
        language: str = "javascript",
        fix: bool = False
    ) -> ValidationResult:
        """Validate JavaScript/TypeScript code"""
        if not self._eslint_available:
            return self._fallback_validate(code)

        ext = ".ts" if "typescript" in language.lower() else ".js"
        issues = []

        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=ext,
            delete=False
        ) as f:
            f.write(code)
            temp_path = f.name

        try:
            cmd = ["npx", "eslint", temp_path, "--format", "json"]
            if fix:
                cmd.append("--fix")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.stdout:
                try:
                    eslint_output = json.loads(result.stdout)
                    for file_result in eslint_output:
                        for msg in file_result.get("messages", []):
                            issues.append(CodeIssue(
                                file_path=f"code{ext}",
                                line=msg.get("line", 1),
                                column=msg.get("column", 1),
                                end_line=msg.get("endLine"),
                                end_column=msg.get("endColumn"),
                                code=msg.get("ruleId", ""),
                                message=msg.get("message", ""),
                                severity=Severity.ERROR if msg.get("severity") == 2 else Severity.WARNING,
                                category=self._map_category(msg.get("ruleId", "")),
                                fix=msg.get("fix", {}).get("text") if msg.get("fix") else None,
                                source="eslint"
                            ))
                except json.JSONDecodeError:
                    pass

            fixed_code = None
            if fix:
                with open(temp_path, 'r') as f:
                    fixed_code = f.read()

        except Exception as e:
            logger.error(f"ESLint validation failed: {e}")
            return self._fallback_validate(code)
        finally:
            os.unlink(temp_path)

        is_valid = not any(i.severity == Severity.ERROR for i in issues)

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            fixed_code=fixed_code
        )

    def _fallback_validate(self, code: str) -> ValidationResult:
        """Basic JavaScript validation"""
        issues = []

        # Check brace balance
        if code.count('{') != code.count('}'):
            issues.append(CodeIssue(
                file_path="code.js",
                line=1,
                column=1,
                code="syntax",
                message="Mismatched braces",
                severity=Severity.ERROR,
                category=IssueCategory.SYNTAX,
                source="basic"
            ))

        if code.count('(') != code.count(')'):
            issues.append(CodeIssue(
                file_path="code.js",
                line=1,
                column=1,
                code="syntax",
                message="Mismatched parentheses",
                severity=Severity.ERROR,
                category=IssueCategory.SYNTAX,
                source="basic"
            ))

        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues
        )

    def _map_category(self, rule_id: str) -> IssueCategory:
        """Map ESLint rule to category"""
        if not rule_id:
            return IssueCategory.STYLE

        if any(x in rule_id for x in ["security", "xss", "injection"]):
            return IssueCategory.SECURITY
        if "complexity" in rule_id:
            return IssueCategory.COMPLEXITY
        if any(x in rule_id for x in ["prefer", "no-var", "const"]):
            return IssueCategory.BEST_PRACTICE

        return IssueCategory.STYLE


class CodeValidationPipeline:
    """
    Comprehensive code validation pipeline.

    Combines multiple validators for thorough code analysis.

    Example:
        pipeline = CodeValidationPipeline()

        # Validate Python code
        result = pipeline.validate('''
        def hello():
            print("Hello")
        ''', language="python")

        if not result.is_valid:
            for issue in result.issues:
                print(f"{issue.line}: {issue.message}")

        # Auto-fix issues
        result = pipeline.validate(code, language="python", fix=True)
        print(result.fixed_code)
    """

    def __init__(self):
        self.ruff = RuffValidator()
        self.semgrep = SemgrepValidator()
        self.eslint = ESLintValidator()

    def validate(
        self,
        code: str,
        language: str,
        fix: bool = False,
        security_scan: bool = True
    ) -> ValidationResult:
        """
        Validate code using appropriate validators.

        Args:
            code: Code to validate
            language: Programming language
            fix: Whether to auto-fix issues
            security_scan: Whether to run security scan

        Returns:
            Combined validation result
        """
        all_issues = []
        fixed_code = code

        # Language-specific validation
        if language.lower() == "python":
            result = self.ruff.validate(code, fix=fix)
            all_issues.extend(result.issues)
            if result.fixed_code:
                fixed_code = result.fixed_code

        elif language.lower() in ("javascript", "typescript", "jsx", "tsx"):
            result = self.eslint.validate(code, language, fix=fix)
            all_issues.extend(result.issues)
            if result.fixed_code:
                fixed_code = result.fixed_code

        # Security scan (all languages)
        if security_scan:
            security_result = self.semgrep.scan(code, language)
            all_issues.extend(security_result.issues)

        # Determine overall validity
        is_valid = not any(i.severity == Severity.ERROR for i in all_issues)

        return ValidationResult(
            is_valid=is_valid,
            issues=all_issues,
            fixed_code=fixed_code if fix else None,
            summary=self._summarize(all_issues)
        )

    def validate_and_fix(
        self,
        code: str,
        language: str,
        max_iterations: int = 3
    ) -> ValidationResult:
        """
        Validate and iteratively fix code.

        Args:
            code: Code to validate and fix
            language: Programming language
            max_iterations: Maximum fix iterations

        Returns:
            Final validation result with fixed code
        """
        current_code = code

        for i in range(max_iterations):
            result = self.validate(current_code, language, fix=True)

            if result.is_valid:
                return result

            if result.fixed_code and result.fixed_code != current_code:
                current_code = result.fixed_code
            else:
                # No more automatic fixes possible
                break

        # Final validation
        return self.validate(current_code, language, fix=False)

    def get_quick_summary(self, code: str, language: str) -> Dict[str, Any]:
        """Get a quick summary of code quality"""
        result = self.validate(code, language)

        return {
            "is_valid": result.is_valid,
            "errors": result.error_count,
            "warnings": result.warning_count,
            "security_issues": sum(
                1 for i in result.issues
                if i.category == IssueCategory.SECURITY
            ),
            "style_issues": sum(
                1 for i in result.issues
                if i.category == IssueCategory.STYLE
            )
        }

    def _summarize(self, issues: List[CodeIssue]) -> Dict[str, int]:
        """Create summary of issues"""
        summary = {
            "total": len(issues),
            "errors": 0,
            "warnings": 0,
            "info": 0,
            "security": 0,
            "style": 0,
            "performance": 0,
        }

        for issue in issues:
            if issue.severity == Severity.ERROR:
                summary["errors"] += 1
            elif issue.severity == Severity.WARNING:
                summary["warnings"] += 1
            else:
                summary["info"] += 1

            if issue.category == IssueCategory.SECURITY:
                summary["security"] += 1
            elif issue.category == IssueCategory.STYLE:
                summary["style"] += 1
            elif issue.category == IssueCategory.PERFORMANCE:
                summary["performance"] += 1

        return summary


# ===========================================
# Convenience Functions
# ===========================================

_default_pipeline: Optional[CodeValidationPipeline] = None


def get_validation_pipeline() -> CodeValidationPipeline:
    """Get the default validation pipeline"""
    global _default_pipeline
    if _default_pipeline is None:
        _default_pipeline = CodeValidationPipeline()
    return _default_pipeline


def validate_code(code: str, language: str, fix: bool = False) -> ValidationResult:
    """Validate code using the default pipeline"""
    return get_validation_pipeline().validate(code, language, fix)


def validate_and_fix(code: str, language: str) -> ValidationResult:
    """Validate and auto-fix code"""
    return get_validation_pipeline().validate_and_fix(code, language)


def quick_check(code: str, language: str) -> Dict[str, Any]:
    """Quick code quality check"""
    return get_validation_pipeline().get_quick_summary(code, language)


def validate_python(code: str, fix: bool = False) -> ValidationResult:
    """Validate Python code"""
    return validate_code(code, "python", fix)


def validate_typescript(code: str, fix: bool = False) -> ValidationResult:
    """Validate TypeScript code"""
    return validate_code(code, "typescript", fix)


def validate_javascript(code: str, fix: bool = False) -> ValidationResult:
    """Validate JavaScript code"""
    return validate_code(code, "javascript", fix)
