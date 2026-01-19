"""
Validation Report Generator Module

Generates HTML and JSON reports from validation results.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ValidationSummary:
    """Summary of all validation stages."""
    overall_status: str  # pass, warn, fail
    overall_score: int  # 0-100
    project_name: str
    project_type: str
    stages: Dict[str, Any]
    issues_count: Dict[str, int]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "overall_score": self.overall_score,
            "project_name": self.project_name,
            "project_type": self.project_type,
            "stages": self.stages,
            "issues_count": self.issues_count,
            "timestamp": self.timestamp,
        }


class ValidationReportGenerator:
    """
    Generates validation reports in HTML and JSON formats.
    """

    def __init__(self):
        self.stages = {}
        self.screenshots = []
        self.project_info = None

    def add_stage(self, name: str, result: Dict[str, Any]) -> None:
        """Add a validation stage result."""
        self.stages[name] = result

    def add_screenshots(self, screenshots: list) -> None:
        """Add screenshots from UI validation."""
        self.screenshots = screenshots

    def set_project_info(self, info: Dict[str, Any]) -> None:
        """Set project information."""
        self.project_info = info

    def generate_summary(self) -> ValidationSummary:
        """Generate a summary of all validation results."""
        # Count issues across all stages
        total_errors = 0
        total_warnings = 0
        total_info = 0

        for stage_name, result in self.stages.items():
            if isinstance(result, dict):
                total_errors += result.get("error_count", 0)
                total_warnings += result.get("warning_count", 0)
                total_info += result.get("info_count", 0)

                # Also count from issues list if present
                for issue in result.get("issues", []):
                    severity = issue.get("severity", "info")
                    if severity == "error":
                        total_errors += 1
                    elif severity == "warning":
                        total_warnings += 1
                    else:
                        total_info += 1

        # Calculate overall status
        if total_errors > 0:
            overall_status = "fail"
        elif total_warnings > 0:
            overall_status = "warn"
        else:
            overall_status = "pass"

        # Calculate score (100 - penalties)
        score = 100
        score -= min(50, total_errors * 10)  # -10 per error, max 50
        score -= min(30, total_warnings * 5)  # -5 per warning, max 30
        score = max(0, score)

        return ValidationSummary(
            overall_status=overall_status,
            overall_score=score,
            project_name=self.project_info.get("name", "Unknown") if self.project_info else "Unknown",
            project_type=self.project_info.get("type", "unknown") if self.project_info else "unknown",
            stages={name: {"status": r.get("status", "unknown")} for name, r in self.stages.items()},
            issues_count={
                "errors": total_errors,
                "warnings": total_warnings,
                "info": total_info,
            },
            timestamp=datetime.now().isoformat(),
        )

    def generate_json(self, output_path: Optional[Path] = None) -> str:
        """Generate JSON report."""
        summary = self.generate_summary()

        report = {
            "summary": summary.to_dict(),
            "project": self.project_info,
            "stages": self.stages,
            "screenshots": [
                {"viewport": s.get("viewport"), "file_path": s.get("file_path")}
                for s in self.screenshots
            ] if self.screenshots else [],
        }

        json_str = json.dumps(report, indent=2, default=str)

        if output_path:
            output_path.write_text(json_str, encoding="utf-8")

        return json_str

    def generate_html(self, output_path: Optional[Path] = None) -> str:
        """Generate HTML report."""
        summary = self.generate_summary()

        # Status colors
        status_colors = {
            "pass": "#10b981",
            "warn": "#f59e0b",
            "fail": "#ef4444",
            "skip": "#6b7280",
        }

        # Build stages HTML
        stages_html = ""
        for stage_name, result in self.stages.items():
            status = result.get("status", "unknown") if isinstance(result, dict) else "unknown"
            color = status_colors.get(status, "#6b7280")
            message = result.get("message", "") if isinstance(result, dict) else str(result)

            issues_html = ""
            if isinstance(result, dict) and result.get("issues"):
                issues_html = "<ul class='issues-list'>"
                for issue in result["issues"][:10]:  # Limit to 10
                    severity = issue.get("severity", "info")
                    sev_color = {"error": "#ef4444", "warning": "#f59e0b", "info": "#6b7280"}.get(severity, "#6b7280")
                    issues_html += f"""
                        <li style="border-left: 3px solid {sev_color}; padding-left: 10px; margin: 8px 0;">
                            <strong style="color: {sev_color};">[{severity.upper()}]</strong>
                            {issue.get('message', '')}
                            {f"<br><small>File: {issue.get('file', '')}</small>" if issue.get('file') else ""}
                        </li>
                    """
                issues_html += "</ul>"

            stages_html += f"""
                <div class="stage-card" style="border-left: 4px solid {color};">
                    <h3 style="display: flex; justify-content: space-between; align-items: center;">
                        {stage_name.replace('_', ' ').title()}
                        <span class="status-badge" style="background: {color};">{status.upper()}</span>
                    </h3>
                    <p>{message}</p>
                    {issues_html}
                </div>
            """

        # Build screenshots HTML
        screenshots_html = ""
        if self.screenshots:
            screenshots_html = "<div class='screenshots-grid'>"
            for screenshot in self.screenshots:
                viewport = screenshot.get("viewport", "unknown")
                base64_data = screenshot.get("base64_data", "")
                if base64_data:
                    screenshots_html += f"""
                        <div class="screenshot-card">
                            <h4>{viewport.title()} ({screenshot.get('width', 0)}x{screenshot.get('height', 0)})</h4>
                            <img src="data:image/png;base64,{base64_data}" alt="{viewport} screenshot" />
                        </div>
                    """
            screenshots_html += "</div>"

        # Build full HTML
        overall_color = status_colors.get(summary.overall_status, "#6b7280")

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Validation Report - {summary.project_name}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #1a1d29;
            color: #ffffff;
            line-height: 1.6;
            padding: 24px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            padding: 32px;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
            border-radius: 12px;
            margin-bottom: 32px;
        }}
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 8px;
        }}
        .score-circle {{
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: {overall_color};
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 24px auto;
            font-size: 2.5rem;
            font-weight: bold;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            color: white;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }}
        .summary-card {{
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card h3 {{
            font-size: 2rem;
            margin-bottom: 4px;
        }}
        .summary-card p {{
            color: #94A3B8;
            font-size: 0.875rem;
        }}
        .stage-card {{
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 16px;
        }}
        .stage-card h3 {{
            margin-bottom: 12px;
        }}
        .issues-list {{
            list-style: none;
            margin-top: 12px;
        }}
        .screenshots-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 24px;
            margin-top: 32px;
        }}
        .screenshot-card {{
            background: rgba(255, 255, 255, 0.05);
            padding: 16px;
            border-radius: 8px;
        }}
        .screenshot-card h4 {{
            margin-bottom: 12px;
            color: #94A3B8;
        }}
        .screenshot-card img {{
            width: 100%;
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .footer {{
            text-align: center;
            padding: 32px;
            color: #94A3B8;
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Validation Report</h1>
            <p>{summary.project_name} ({summary.project_type})</p>
            <div class="score-circle">{summary.overall_score}</div>
            <span class="status-badge" style="background: {overall_color};">
                {summary.overall_status.upper()}
            </span>
        </div>

        <div class="summary-grid">
            <div class="summary-card" style="border-top: 3px solid #ef4444;">
                <h3 style="color: #ef4444;">{summary.issues_count['errors']}</h3>
                <p>Errors</p>
            </div>
            <div class="summary-card" style="border-top: 3px solid #f59e0b;">
                <h3 style="color: #f59e0b;">{summary.issues_count['warnings']}</h3>
                <p>Warnings</p>
            </div>
            <div class="summary-card" style="border-top: 3px solid #6b7280;">
                <h3 style="color: #6b7280;">{summary.issues_count['info']}</h3>
                <p>Info</p>
            </div>
            <div class="summary-card" style="border-top: 3px solid #10b981;">
                <h3 style="color: #10b981;">{len(self.stages)}</h3>
                <p>Stages Run</p>
            </div>
        </div>

        <h2 style="margin-bottom: 16px;">Validation Stages</h2>
        {stages_html}

        {f'<h2 style="margin: 32px 0 16px;">Screenshots</h2>{screenshots_html}' if screenshots_html else ''}

        <div class="footer">
            <p>Generated by Universal Code Validator</p>
            <p>{summary.timestamp}</p>
        </div>
    </div>
</body>
</html>
        """

        if output_path:
            output_path.write_text(html, encoding="utf-8")

        return html


# Convenience function
def generate_report(stages: Dict[str, Any], project_info: Dict[str, Any],
                    screenshots: list = None, format: str = "html") -> str:
    """
    Generate a validation report.

    Args:
        stages: Dict of stage name -> result
        project_info: Project information dict
        screenshots: List of screenshot dicts
        format: "html" or "json"

    Returns:
        Report content as string
    """
    generator = ValidationReportGenerator()
    generator.set_project_info(project_info)
    for name, result in stages.items():
        generator.add_stage(name, result)
    if screenshots:
        generator.add_screenshots(screenshots)

    if format == "json":
        return generator.generate_json()
    return generator.generate_html()
