"""
Universal Code Validator

A comprehensive validation system that works with ANY code project.
Auto-detects project type and runs appropriate validation stages:

1. Project Detection - What kind of project is this?
2. Static Analysis - Syntax, imports, types
3. Build Validation - Does it compile/build?
4. Runtime Validation - Does it start/run?
5. UI Validation - Does it render correctly?
6. Report Generation - Unified report with all findings

Usage:
    from core.universal_validator import UniversalValidator

    validator = UniversalValidator()
    result = validator.validate("/path/to/project")
    result.save_report("validation_report.html")

CLI Usage:
    python -m core.universal_validator /path/to/project
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import tempfile
import shutil
import zipfile

from .validators.project_detector import ProjectDetector, ProjectInfo, ProjectType
from .validators.static_analyzer import StaticAnalyzer, StaticAnalysisResult
from .validators.build_validator import BuildValidator, BuildResult
from .validators.runtime_validator import RuntimeValidator, RuntimeResult
from .validators.ui_validator import UIValidator, UIValidationResult
from .validators.report_generator import ValidationReportGenerator, ValidationSummary


@dataclass
class ValidationResult:
    """Complete validation result."""
    overall_status: str  # pass, warn, fail
    overall_score: int  # 0-100
    project_info: ProjectInfo
    stages: Dict[str, Any] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    screenshots: List[Dict[str, Any]] = field(default_factory=list)
    report_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "overall_score": self.overall_score,
            "project": {
                "name": self.project_info.name,
                "type": self.project_info.project_type.value,
                "path": str(self.project_info.path),
            },
            "stages": {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in self.stages.items()},
            "issues": self.issues,
            "screenshots": self.screenshots,
        }

    def save_report(self, path: str | Path, format: str = "html") -> Path:
        """Save validation report to file."""
        path = Path(path)

        generator = ValidationReportGenerator()
        generator.set_project_info({
            "name": self.project_info.name,
            "type": self.project_info.project_type.value,
            "path": str(self.project_info.path),
        })

        for name, result in self.stages.items():
            if hasattr(result, 'to_dict'):
                generator.add_stage(name, result.to_dict())
            else:
                generator.add_stage(name, result)

        if self.screenshots:
            generator.add_screenshots(self.screenshots)

        if format == "json":
            generator.generate_json(path)
        else:
            generator.generate_html(path)

        self.report_path = path
        return path


class UniversalValidator:
    """
    Universal code validation system.

    Validates any code project through a multi-stage pipeline:
    1. Project Detection
    2. Static Analysis
    3. Build Validation
    4. Runtime Validation
    5. UI Validation (for web apps)
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the validator.

        Args:
            output_dir: Directory for reports and screenshots (default: temp dir)
        """
        self.output_dir = output_dir or Path(tempfile.mkdtemp(prefix="validation_"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.detector = ProjectDetector()
        self.static_analyzer = StaticAnalyzer()
        self.build_validator = BuildValidator()
        self.runtime_validator = RuntimeValidator()
        self.ui_validator = UIValidator(self.output_dir / "screenshots")

    def validate(
        self,
        project_path: str | Path,
        stages: Optional[List[str]] = None,
        skip_ui: bool = False,
        auto_stop: bool = True,
    ) -> ValidationResult:
        """
        Validate a code project.

        Args:
            project_path: Path to project directory, zip file, or git URL
            stages: Specific stages to run (default: all applicable)
            skip_ui: Skip UI validation even for web apps
            auto_stop: Stop server after runtime validation

        Returns:
            ValidationResult with all findings
        """
        # Handle different input types
        path = self._resolve_project_path(project_path)

        # Stage 1: Project Detection
        print(f"\n[1/5] Detecting project type...")
        project_info = self.detector.detect(path)
        print(f"      Detected: {project_info.project_type.value} ({project_info.name})")

        results = {}
        all_issues = []
        screenshots = []

        # Stage 2: Static Analysis
        if not stages or "static" in stages:
            print(f"\n[2/5] Running static analysis...")
            static_result = self.static_analyzer.analyze(project_info)
            results["static_analysis"] = static_result
            all_issues.extend([i.to_dict() for i in static_result.issues])
            print(f"      Status: {static_result.status} ({static_result.error_count} errors, {static_result.warning_count} warnings)")

        # Stage 3: Build Validation
        if not stages or "build" in stages:
            print(f"\n[3/5] Validating build...")
            build_result = self.build_validator.validate(project_info)
            results["build"] = build_result
            if build_result.status == "fail":
                all_issues.append({
                    "severity": "error",
                    "category": "build",
                    "message": build_result.message,
                })
            print(f"      Status: {build_result.status} - {build_result.message}")

        # Stage 4: Runtime Validation
        if not stages or "runtime" in stages:
            print(f"\n[4/5] Validating runtime...")
            runtime_result = self.runtime_validator.validate(project_info, auto_stop=False)
            results["runtime"] = runtime_result
            if runtime_result.status == "fail":
                all_issues.append({
                    "severity": "error",
                    "category": "runtime",
                    "message": runtime_result.message,
                })
            print(f"      Status: {runtime_result.status} - {runtime_result.message}")

            # Stage 5: UI Validation (only for web apps that started)
            if not skip_ui and runtime_result.status == "pass" and runtime_result.url:
                if not stages or "ui" in stages:
                    print(f"\n[5/5] Validating UI...")
                    ui_result = self.ui_validator.validate(runtime_result.url)
                    results["ui"] = ui_result
                    all_issues.extend([i.to_dict() for i in ui_result.issues])
                    screenshots = [s.__dict__ for s in ui_result.screenshots]
                    print(f"      Status: {ui_result.status} - {ui_result.message}")

            # Stop the server
            if auto_stop:
                self.runtime_validator.stop()
        else:
            print(f"\n[5/5] Skipping UI validation")

        # Calculate overall status and score
        overall_status, overall_score = self._calculate_overall(results, all_issues)

        return ValidationResult(
            overall_status=overall_status,
            overall_score=overall_score,
            project_info=project_info,
            stages=results,
            issues=all_issues,
            screenshots=screenshots,
        )

    def _resolve_project_path(self, path: str | Path) -> Path:
        """Resolve project path from various input types."""
        path_str = str(path)

        # Handle git URLs
        if path_str.startswith(("http://", "https://", "git@")):
            return self._clone_repo(path_str)

        # Handle zip files
        if path_str.endswith(".zip"):
            return self._extract_zip(Path(path_str))

        # Regular path
        return Path(path).resolve()

    def _clone_repo(self, url: str) -> Path:
        """Clone a git repository to temp directory."""
        import subprocess

        clone_dir = self.output_dir / "repo"
        clone_dir.mkdir(exist_ok=True)

        subprocess.run(
            ["git", "clone", "--depth=1", url, str(clone_dir)],
            check=True,
            capture_output=True,
        )

        return clone_dir

    def _extract_zip(self, zip_path: Path) -> Path:
        """Extract a zip file to temp directory."""
        extract_dir = self.output_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # If the zip contains a single directory, use that
        contents = list(extract_dir.iterdir())
        if len(contents) == 1 and contents[0].is_dir():
            return contents[0]

        return extract_dir

    def _calculate_overall(self, results: Dict[str, Any], issues: List[Dict]) -> tuple:
        """Calculate overall status and score."""
        # Count issues
        error_count = sum(1 for i in issues if i.get("severity") == "error")
        warning_count = sum(1 for i in issues if i.get("severity") == "warning")

        # Check stage statuses
        failed_stages = sum(
            1 for r in results.values()
            if hasattr(r, 'status') and r.status == "fail"
        )

        # Determine status
        if failed_stages > 0 or error_count > 0:
            status = "fail"
        elif warning_count > 0:
            status = "warn"
        else:
            status = "pass"

        # Calculate score
        score = 100
        score -= min(50, error_count * 10)
        score -= min(30, warning_count * 3)
        score -= min(20, failed_stages * 10)
        score = max(0, score)

        return status, score


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Universal Code Validator - Validate any code project"
    )
    parser.add_argument(
        "project",
        help="Path to project directory, zip file, or git URL"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output path for report (default: validation_report.html)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["html", "json"],
        default="html",
        help="Report format (default: html)"
    )
    parser.add_argument(
        "--skip-ui",
        action="store_true",
        help="Skip UI validation"
    )
    parser.add_argument(
        "--stages",
        nargs="+",
        choices=["static", "build", "runtime", "ui"],
        help="Specific stages to run"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("  Universal Code Validator")
    print("=" * 60)

    validator = UniversalValidator()
    result = validator.validate(
        args.project,
        stages=args.stages,
        skip_ui=args.skip_ui,
    )

    # Generate report
    output_path = args.output or f"validation_report.{args.format}"
    result.save_report(output_path, format=args.format)

    print("\n" + "=" * 60)
    print(f"  VALIDATION COMPLETE")
    print("=" * 60)
    print(f"  Status: {result.overall_status.upper()}")
    print(f"  Score:  {result.overall_score}/100")
    print(f"  Issues: {len(result.issues)}")
    print(f"  Report: {output_path}")
    print("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if result.overall_status == "pass" else 1)


if __name__ == "__main__":
    main()
