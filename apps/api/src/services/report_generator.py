"""
Report Generator - Creates shareable HTML reports for Code Audits and Business Analysis

Generates professional, visually appealing reports that companies can use
to understand exactly what to fix and the expected impact.

Two main generators:
1. CodeAuditReportGenerator - For code analysis reports
2. BusinessReportGenerator - For business insights reports (new builds, UX audits)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

from ..models.report import (
    BusinessReport,
    ReportType,
    ExecutiveSummary,
    MetricItem,
    BadgeType,
    IssueCard,
    Recommendation,
    RoadmapPhase,
    RoadmapItem,
    KPIRow,
    ROIProjection,
    ROIMetric,
    FunnelAnalysis,
    FunnelStep,
    IndustrySection,
    IndustryInsight,
    CompetitorAnalysis,
    DesignSystem,
    ScoreBreakdown,
    HeuristicScore,
    FeatureRow,
    AppScreen,
    AILogEntry,
    Severity,
)


class CodeAuditReportGenerator:
    """Generate beautiful shareable HTML reports for code audits"""

    def __init__(self):
        self.timestamp = datetime.now().strftime("%B %Y")

    def generate_report(self, audit_result: Dict[str, Any]) -> str:
        """Generate a complete HTML report from audit results"""
        repo_name = audit_result.get("repo_url", "").split("/")[-1] or "Repository"
        owner = audit_result.get("repo_url", "").split("/")[-2] if "/" in audit_result.get("repo_url", "") else ""

        # Use company name if provided (for branded reports)
        company_name = audit_result.get("company_name")
        display_name = company_name if company_name else repo_name
        industry = audit_result.get("industry", "general")

        context = audit_result.get("context", {})
        scores = audit_result.get("scores", {})
        analysis = audit_result.get("analysis", {})
        recommendations = audit_result.get("recommendations", [])
        issues = audit_result.get("issues", {})
        summary = audit_result.get("summary", {})

        # Calculate totals
        total_issues = sum(issues.values()) if isinstance(issues, dict) else 0
        critical_high = issues.get("critical", 0) + issues.get("high", 0)

        # Get platform info
        platform_purpose = context.get("platform_purpose", "Software application")
        platform_type = context.get("platform_type", "unknown")
        frameworks = context.get("frameworks", [])
        total_files = context.get("total_files", summary.get("total_files", 0))
        total_lines = context.get("total_lines", summary.get("lines_of_code", 0))

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_name} - Comprehensive Code Audit Report | {self.timestamp}</title>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

    <style>
        :root {{
            --primary: #6366F1;
            --primary-light: #818CF8;
            --secondary: #8B5CF6;
            --accent: #10B981;
            --dark: #0F172A;
            --dark-secondary: #1E293B;
            --light: #F8FAFC;
            --text: #334155;
            --text-light: #64748B;
            --success: #10B981;
            --warning: #F59E0B;
            --danger: #EF4444;
            --info: #3B82F6;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--light);
            color: var(--text);
            line-height: 1.6;
        }}

        /* Navigation */
        .nav {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(15, 23, 42, 0.97);
            backdrop-filter: blur(12px);
            padding: 12px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 1000;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}

        .nav-brand {{
            font-size: 16px;
            font-weight: 700;
            color: white;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .nav-brand span {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .nav-links {{
            display: flex;
            gap: 4px;
            flex-wrap: wrap;
        }}

        .nav-link {{
            color: rgba(255,255,255,0.7);
            text-decoration: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s ease;
            white-space: nowrap;
        }}

        .nav-link:hover, .nav-link.active {{
            color: white;
            background: rgba(255,255,255,0.1);
        }}

        /* Cover */
        .cover {{
            background: linear-gradient(135deg, var(--dark) 0%, var(--dark-secondary) 100%);
            color: white;
            padding: 100px 60px 80px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }}

        .cover::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 800px;
            height: 800px;
            background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
            border-radius: 50%;
        }}

        .cover-content {{
            position: relative;
            z-index: 1;
            max-width: 1000px;
        }}

        .cover-badge {{
            display: inline-block;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            padding: 8px 20px;
            border-radius: 30px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 24px;
        }}

        .cover h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 48px;
            font-weight: 700;
            line-height: 1.15;
            margin-bottom: 16px;
        }}

        .cover h1 span {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .cover .subtitle {{
            font-size: 18px;
            opacity: 0.85;
            margin-bottom: 40px;
            max-width: 700px;
        }}

        .cover-stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            max-width: 900px;
        }}

        .cover-stat {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 24px 20px;
            text-align: center;
            transition: all 0.2s ease;
        }}

        .cover-stat:hover {{
            transform: translateY(-4px);
            background: rgba(255,255,255,0.08);
        }}

        .cover-stat-value {{
            font-size: 32px;
            font-weight: 800;
        }}

        .cover-stat-value.danger {{ color: var(--danger); }}
        .cover-stat-value.warning {{ color: var(--warning); }}
        .cover-stat-value.success {{ color: var(--success); }}
        .cover-stat-value.info {{ color: var(--info); }}

        .cover-stat-label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            opacity: 0.7;
            margin-top: 8px;
        }}

        /* Container */
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 60px 40px;
        }}

        /* Section */
        .section {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 28px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        }}

        .section-header {{
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 20px;
        }}

        .section-icon {{
            width: 48px;
            height: 48px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 22px;
        }}

        .section-icon.danger {{ background: linear-gradient(135deg, #EF4444, #DC2626); }}
        .section-icon.success {{ background: linear-gradient(135deg, #10B981, #059669); }}
        .section-icon.warning {{ background: linear-gradient(135deg, #F59E0B, #D97706); }}
        .section-icon.info {{ background: linear-gradient(135deg, #3B82F6, #2563EB); }}
        .section-icon.purple {{ background: linear-gradient(135deg, #8B5CF6, #7C3AED); }}

        .section h2 {{
            font-size: 24px;
            font-weight: 700;
            color: var(--dark);
        }}

        .section-intro {{
            font-size: 15px;
            color: var(--text-light);
            margin-bottom: 28px;
            line-height: 1.6;
        }}

        /* Bottom Line Box */
        .bottom-line {{
            background: linear-gradient(135deg, #FEF2F2, #FEE2E2);
            border: 2px solid #FECACA;
            border-radius: 16px;
            padding: 24px;
            margin: 24px 0;
        }}

        .bottom-line.success {{
            background: linear-gradient(135deg, #ECFDF5, #D1FAE5);
            border-color: #A7F3D0;
        }}

        .bottom-line.success h4 {{ color: #065F46; }}
        .bottom-line.success p {{ color: #047857; }}

        .bottom-line h4 {{
            color: #991B1B;
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .bottom-line p {{
            color: #7F1D1D;
            font-size: 14px;
            line-height: 1.6;
        }}

        /* Tables */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}

        .data-table th {{
            text-align: left;
            padding: 14px 16px;
            background: var(--light);
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-light);
            border-bottom: 2px solid #E2E8F0;
        }}

        .data-table td {{
            padding: 14px 16px;
            border-bottom: 1px solid #E2E8F0;
        }}

        .data-table tr:hover {{
            background: #F8FAFC;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }}

        .badge.critical {{ background: #FEE2E2; color: #DC2626; }}
        .badge.high {{ background: #FEF3C7; color: #D97706; }}
        .badge.medium {{ background: #DBEAFE; color: #2563EB; }}
        .badge.low {{ background: #E0E7FF; color: #4F46E5; }}
        .badge.good {{ background: #D1FAE5; color: #059669; }}
        .badge.info {{ background: #DBEAFE; color: #2563EB; }}

        /* Score Cards */
        .score-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 16px;
            margin: 24px 0;
        }}

        .score-card {{
            background: var(--light);
            border-radius: 14px;
            padding: 20px;
            text-align: center;
        }}

        .score-card-value {{
            font-size: 32px;
            font-weight: 800;
        }}

        .score-card-label {{
            font-size: 12px;
            color: var(--text-light);
            margin-top: 4px;
            text-transform: uppercase;
        }}

        /* Issues */
        .issue-card {{
            background: var(--light);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 12px;
            border-left: 4px solid;
            transition: transform 0.2s ease;
        }}

        .issue-card:hover {{
            transform: translateX(4px);
        }}

        .issue-card.critical {{ border-left-color: #DC2626; }}
        .issue-card.high {{ border-left-color: #D97706; }}
        .issue-card.medium {{ border-left-color: #2563EB; }}
        .issue-card.low {{ border-left-color: #4F46E5; }}

        .issue-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 8px;
        }}

        .issue-title {{
            font-size: 15px;
            font-weight: 600;
            color: var(--dark);
        }}

        .issue-description {{
            font-size: 13px;
            color: var(--text-light);
            margin-bottom: 10px;
        }}

        .issue-meta {{
            display: flex;
            gap: 16px;
            font-size: 12px;
            color: var(--text-light);
        }}

        .issue-meta span {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        /* Recommendations */
        .rec-card {{
            background: var(--light);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            border: 2px solid transparent;
            transition: all 0.2s ease;
        }}

        .rec-card:hover {{
            border-color: var(--accent);
            transform: translateY(-2px);
        }}

        .rec-header {{
            display: flex;
            gap: 16px;
            margin-bottom: 16px;
        }}

        .rec-priority {{
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 800;
            font-size: 18px;
            flex-shrink: 0;
        }}

        .rec-priority.critical {{ background: linear-gradient(135deg, #EF4444, #DC2626); }}
        .rec-priority.high {{ background: linear-gradient(135deg, #F59E0B, #D97706); }}
        .rec-priority.medium {{ background: linear-gradient(135deg, #3B82F6, #2563EB); }}

        .rec-title {{
            font-size: 17px;
            font-weight: 700;
            color: var(--dark);
            margin-bottom: 4px;
        }}

        .rec-subtitle {{
            font-size: 13px;
            color: var(--text-light);
        }}

        .rec-content {{
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #E2E8F0;
        }}

        .rec-stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 16px;
        }}

        .rec-stat {{
            text-align: center;
            padding: 12px;
            background: white;
            border-radius: 8px;
        }}

        .rec-stat-value {{
            font-size: 18px;
            font-weight: 700;
            color: var(--accent);
        }}

        .rec-stat-label {{
            font-size: 11px;
            color: var(--text-light);
            margin-top: 2px;
        }}

        .rec-details {{
            font-size: 14px;
            color: var(--text);
            line-height: 1.6;
        }}

        /* Positive Items */
        .positive-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin: 20px 0;
        }}

        .positive-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            background: linear-gradient(135deg, #ECFDF5, #D1FAE5);
            border-radius: 10px;
            font-size: 13px;
            color: #065F46;
        }}

        .positive-item::before {{
            content: "\\2713";
            color: #10B981;
            font-weight: bold;
        }}

        /* Tech Stack */
        .tech-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 16px 0;
        }}

        .tech-badge {{
            background: linear-gradient(135deg, var(--dark), var(--dark-secondary));
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}

        /* Roadmap */
        .roadmap-phase {{
            background: var(--light);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 12px;
            border-left: 4px solid var(--accent);
        }}

        .roadmap-phase h4 {{
            font-size: 15px;
            font-weight: 700;
            color: var(--dark);
            margin-bottom: 12px;
        }}

        .roadmap-items {{
            display: grid;
            gap: 8px;
        }}

        .roadmap-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13px;
            color: var(--text);
        }}

        .roadmap-item input[type="checkbox"] {{
            width: 18px;
            height: 18px;
            accent-color: var(--accent);
        }}

        /* Charts */
        .charts-row {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
            margin: 24px 0;
        }}

        .chart-card {{
            background: var(--light);
            border-radius: 16px;
            padding: 24px;
        }}

        .chart-card h3 {{
            font-size: 15px;
            font-weight: 600;
            color: var(--dark);
            margin-bottom: 16px;
        }}

        .chart-wrapper {{
            position: relative;
            height: 250px;
        }}

        /* Footer */
        .footer {{
            background: var(--dark);
            color: white;
            padding: 32px 40px;
            text-align: center;
        }}

        .footer p {{
            font-size: 13px;
            opacity: 0.7;
        }}

        .footer a {{
            color: var(--primary-light);
            text-decoration: none;
        }}

        /* Responsive */
        @media (max-width: 900px) {{
            .cover {{ padding: 80px 24px 60px; }}
            .cover h1 {{ font-size: 36px; }}
            .cover-stats {{ grid-template-columns: repeat(2, 1fr); }}
            .container {{ padding: 40px 20px; }}
            .section {{ padding: 24px; }}
            .charts-row {{ grid-template-columns: 1fr; }}
            .score-grid {{ grid-template-columns: repeat(3, 1fr); }}
            .rec-stats {{ grid-template-columns: 1fr; }}
            .positive-grid {{ grid-template-columns: 1fr; }}
            .nav {{ padding: 10px 16px; flex-direction: column; gap: 8px; }}
            .nav-links {{ justify-content: center; }}
        }}

        @media print {{
            .nav {{ display: none; }}
            .cover {{ min-height: auto; padding: 40px; }}
            .section {{ break-inside: avoid; page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="nav">
        <div class="nav-brand"><span>Code Weaver Pro</span> Audit Report</div>
        <div class="nav-links">
            <a href="#executive" class="nav-link active">Executive</a>
            <a href="#scores" class="nav-link">Scores</a>
            <a href="#issues" class="nav-link">Issues</a>
            <a href="#strengths" class="nav-link">Strengths</a>
            <a href="#recommendations" class="nav-link">Actions</a>
            <a href="#roadmap" class="nav-link">Roadmap</a>
        </div>
    </nav>

    <!-- Cover -->
    <section class="cover" id="executive">
        <div class="cover-content">
            <div class="cover-badge">Comprehensive Code Audit</div>
            <h1>{display_name}<br><span>Code Analysis Report</span></h1>
            <p class="subtitle">{platform_purpose} | {self.timestamp} | Deep analysis of {total_files:,} files across {total_lines:,} lines of code. Your team will know exactly what to fix and the expected impact.</p>

            <div class="cover-stats">
                <div class="cover-stat">
                    <div class="cover-stat-value {self._get_score_class(scores.get('overall', 0))}">{scores.get('overall', 0)}/10</div>
                    <div class="cover-stat-label">Overall Score</div>
                </div>
                <div class="cover-stat">
                    <div class="cover-stat-value info">{total_issues}</div>
                    <div class="cover-stat-label">Issues Found</div>
                </div>
                <div class="cover-stat">
                    <div class="cover-stat-value danger">{critical_high}</div>
                    <div class="cover-stat-label">Critical/High</div>
                </div>
                <div class="cover-stat">
                    <div class="cover-stat-value success">{len(recommendations)}</div>
                    <div class="cover-stat-label">Recommendations</div>
                </div>
            </div>
        </div>
    </section>

    <div class="container">
        <!-- Executive Summary -->
        <section class="section">
            <div class="section-header">
                <div class="section-icon info">&#128202;</div>
                <h2>Executive Summary</h2>
            </div>

            <h3 style="font-size: 16px; margin-bottom: 16px; color: var(--dark);">Project Overview</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Attribute</th>
                        <th>Value</th>
                        <th>Assessment</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Platform Type</td>
                        <td><strong>{platform_type.replace('_', ' ').title()}</strong></td>
                        <td><span class="badge info">Detected</span></td>
                    </tr>
                    <tr>
                        <td>Total Files Analyzed</td>
                        <td>{total_files:,}</td>
                        <td><span class="badge good">Complete</span></td>
                    </tr>
                    <tr>
                        <td>Lines of Code</td>
                        <td>{total_lines:,}</td>
                        <td>{self._assess_codebase_size(total_lines)}</td>
                    </tr>
                    <tr>
                        <td>Tech Stack</td>
                        <td>{', '.join(frameworks[:4])}</td>
                        <td><span class="badge info">Modern</span></td>
                    </tr>
                    <tr>
                        <td>Critical Issues</td>
                        <td>{issues.get('critical', 0)}</td>
                        <td>{self._assess_critical(issues.get('critical', 0))}</td>
                    </tr>
                    <tr>
                        <td>High Priority Issues</td>
                        <td>{issues.get('high', 0)}</td>
                        <td>{self._assess_high(issues.get('high', 0))}</td>
                    </tr>
                </tbody>
            </table>

            {self._generate_bottom_line(scores, issues, recommendations)}
        </section>

        <!-- Domain Scores -->
        <section class="section" id="scores">
            <div class="section-header">
                <div class="section-icon purple">&#127919;</div>
                <h2>Domain Analysis Scores</h2>
            </div>
            <p class="section-intro">Breakdown of scores across different aspects of your codebase. Each domain is analyzed independently with specific criteria.</p>

            <div class="score-grid">
                {self._generate_score_cards(scores)}
            </div>

            <div class="charts-row">
                <div class="chart-card">
                    <h3>Score Distribution</h3>
                    <div class="chart-wrapper">
                        <canvas id="scoresChart"></canvas>
                    </div>
                </div>
                <div class="chart-card">
                    <h3>Issues by Severity</h3>
                    <div class="chart-wrapper">
                        <canvas id="issuesChart"></canvas>
                    </div>
                </div>
            </div>
        </section>

        <!-- Issues -->
        <section class="section" id="issues">
            <div class="section-header">
                <div class="section-icon warning">&#9888;</div>
                <h2>Issues Identified</h2>
            </div>
            <p class="section-intro">Critical and high-priority issues discovered during the code analysis. Each issue includes severity, impact, and suggested fix effort.</p>

            {self._generate_issues_section(analysis)}
        </section>

        <!-- Strengths -->
        <section class="section" id="strengths">
            <div class="section-header">
                <div class="section-icon success">&#10003;</div>
                <h2>Code Strengths</h2>
            </div>
            <p class="section-intro">Positive patterns and best practices found in your codebase. These are things you're doing well!</p>

            {self._generate_strengths_section(analysis)}
        </section>

        <!-- Recommendations -->
        <section class="section" id="recommendations">
            <div class="section-header">
                <div class="section-icon success">&#128161;</div>
                <h2>Actionable Recommendations</h2>
            </div>
            <p class="section-intro">Prioritized actions with expected impact. Each recommendation includes effort level and business impact.</p>

            {self._generate_recommendations_section(recommendations)}
        </section>

        <!-- Roadmap -->
        <section class="section" id="roadmap">
            <div class="section-header">
                <div class="section-icon purple">&#128197;</div>
                <h2>Implementation Roadmap</h2>
            </div>
            <p class="section-intro">Phased approach starting with highest-impact fixes. Use the checkboxes to track your progress.</p>

            {self._generate_roadmap_section(recommendations)}
        </section>
    </div>

    <!-- Footer -->
    <footer class="footer">
        <p>Generated by <a href="#">Code Weaver Pro</a> | {datetime.now().strftime("%B %d, %Y at %H:%M")} | Repository: {audit_result.get('repo_url', 'N/A')}</p>
    </footer>

    <!-- Charts Script -->
    <script>
        // Scores Chart
        const scoresCtx = document.getElementById('scoresChart').getContext('2d');
        new Chart(scoresCtx, {{
            type: 'radar',
            data: {{
                labels: ['Frontend', 'Backend', 'Architecture', 'Security', 'Overall'],
                datasets: [{{
                    label: 'Score',
                    data: [{scores.get('frontend', 0)}, {scores.get('backend', 0)}, {scores.get('architecture', 0)}, {scores.get('security', 0)}, {scores.get('overall', 0)}],
                    backgroundColor: 'rgba(99, 102, 241, 0.2)',
                    borderColor: 'rgba(99, 102, 241, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(99, 102, 241, 1)'
                }}]
            }},
            options: {{
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 10,
                        ticks: {{ stepSize: 2 }}
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});

        // Issues Chart
        const issuesCtx = document.getElementById('issuesChart').getContext('2d');
        new Chart(issuesCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Critical', 'High', 'Medium', 'Low'],
                datasets: [{{
                    data: [{issues.get('critical', 0)}, {issues.get('high', 0)}, {issues.get('medium', 0)}, {issues.get('low', 0)}],
                    backgroundColor: ['#DC2626', '#F59E0B', '#3B82F6', '#8B5CF6'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                cutout: '60%',
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{ usePointStyle: true, padding: 15 }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>'''

    def _get_score_class(self, score: float) -> str:
        """Get CSS class based on score"""
        if score >= 8:
            return "success"
        elif score >= 6:
            return "warning"
        else:
            return "danger"

    def _assess_codebase_size(self, lines: int) -> str:
        """Assess codebase size"""
        if lines > 100000:
            return '<span class="badge high">Large codebase</span>'
        elif lines > 50000:
            return '<span class="badge info">Medium codebase</span>'
        else:
            return '<span class="badge good">Manageable size</span>'

    def _assess_critical(self, count: int) -> str:
        """Assess critical issues count"""
        if count == 0:
            return '<span class="badge good">None found</span>'
        elif count <= 2:
            return '<span class="badge high">Needs attention</span>'
        else:
            return '<span class="badge critical">Critical</span>'

    def _assess_high(self, count: int) -> str:
        """Assess high issues count"""
        if count <= 2:
            return '<span class="badge good">Acceptable</span>'
        elif count <= 5:
            return '<span class="badge high">Review needed</span>'
        else:
            return '<span class="badge critical">High priority</span>'

    def _generate_bottom_line(self, scores: Dict, issues: Dict, recommendations: List) -> str:
        """Generate the bottom line summary"""
        overall = scores.get('overall', 0)
        critical = issues.get('critical', 0)
        high = issues.get('high', 0)

        if overall >= 8 and critical == 0:
            return f'''
            <div class="bottom-line success">
                <h4>&#10003; The Bottom Line</h4>
                <p><strong>Your codebase is in great shape!</strong> With an overall score of {overall}/10 and no critical issues, you're following best practices. Focus on the {len(recommendations)} recommendations to take your code to the next level.</p>
            </div>'''
        elif critical > 0:
            return f'''
            <div class="bottom-line">
                <h4>&#9888; The Bottom Line</h4>
                <p><strong>You have {critical} critical issue(s) that need immediate attention.</strong> Additionally, {high} high-priority issues were found. Addressing these will significantly improve your code quality and security. The {len(recommendations)} recommendations are prioritized by impact.</p>
            </div>'''
        else:
            return f'''
            <div class="bottom-line">
                <h4>&#9888; The Bottom Line</h4>
                <p><strong>Your codebase has room for improvement.</strong> With an overall score of {overall}/10 and {high} high-priority issues, there are clear opportunities to enhance code quality. Follow the {len(recommendations)} prioritized recommendations to see measurable improvement.</p>
            </div>'''

    def _generate_score_cards(self, scores: Dict) -> str:
        """Generate score cards HTML"""
        cards = []
        score_items = [
            ('overall', 'Overall'),
            ('frontend', 'Frontend'),
            ('backend', 'Backend'),
            ('architecture', 'Architecture'),
            ('security', 'Security'),
        ]

        for key, label in score_items:
            score = scores.get(key, 0)
            color_class = self._get_score_class(score)
            cards.append(f'''
                <div class="score-card">
                    <div class="score-card-value" style="color: var(--{color_class});">{score}/10</div>
                    <div class="score-card-label">{label}</div>
                </div>''')

        return '\n'.join(cards)

    def _generate_issues_section(self, analysis: Dict) -> str:
        """Generate issues section HTML"""
        all_issues = []

        # Collect issues from all domains
        for domain in ['frontend', 'backend', 'architecture']:
            domain_data = analysis.get(domain, {})
            issues = domain_data.get('issues', [])
            for issue in issues:
                issue['domain'] = domain
                all_issues.append(issue)

        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        all_issues.sort(key=lambda x: severity_order.get(x.get('severity', 'low'), 3))

        if not all_issues:
            return '''
            <div class="bottom-line success">
                <h4>&#10003; No Major Issues Found</h4>
                <p>Great news! No critical or high-priority issues were detected in your codebase. Continue following best practices!</p>
            </div>'''

        html_parts = []
        for issue in all_issues[:15]:  # Limit to top 15
            severity = issue.get('severity', 'medium')
            title = issue.get('title', 'Unknown Issue')
            description = issue.get('description', '')
            file_path = issue.get('file_path', '')
            domain = issue.get('domain', '').title()

            effort = 'Medium fix'
            if 'refactor' in title.lower() or 'complex' in title.lower():
                effort = 'High effort'
            elif 'add' in title.lower() or 'missing' in title.lower():
                effort = 'Easy fix'

            html_parts.append(f'''
            <div class="issue-card {severity}">
                <div class="issue-header">
                    <span class="issue-title">{title}</span>
                    <span class="badge {severity}">{severity.upper()}</span>
                </div>
                <p class="issue-description">{description}</p>
                <div class="issue-meta">
                    <span>&#128193; {domain}</span>
                    {f'<span>&#128196; {file_path}</span>' if file_path else ''}
                    <span>&#128736; {effort}</span>
                </div>
            </div>''')

        return '\n'.join(html_parts)

    def _generate_strengths_section(self, analysis: Dict) -> str:
        """Generate code strengths section"""
        strengths = []

        # Collect positive items from frontend UX patterns
        frontend = analysis.get('frontend', {})
        ux_patterns = frontend.get('ux_patterns', {})

        for pattern_name, pattern_data in ux_patterns.items():
            if isinstance(pattern_data, dict):
                positive = pattern_data.get('positive', [])
                for item in positive:
                    strengths.append(item)

        # Add some defaults based on scores
        if frontend.get('score', 0) >= 8:
            strengths.append("Strong frontend implementation with modern patterns")

        backend = analysis.get('backend', {})
        if backend.get('score', 0) >= 8:
            strengths.append("Well-structured backend architecture")
        if backend.get('auth_score', 0) >= 8:
            strengths.append("Robust authentication implementation")
        if backend.get('validation_score', 0) >= 8:
            strengths.append("Comprehensive input validation")

        if not strengths:
            strengths = [
                "Codebase structure detected and analyzed",
                "Multiple languages/frameworks identified",
                "Analysis completed successfully"
            ]

        # Generate HTML
        html = '<div class="positive-grid">'
        for strength in strengths[:10]:  # Limit to 10
            html += f'<div class="positive-item">{strength}</div>'
        html += '</div>'

        return html

    def _generate_recommendations_section(self, recommendations: List) -> str:
        """Generate recommendations section HTML"""
        if not recommendations:
            return '<p>No specific recommendations at this time. Your codebase is following best practices!</p>'

        html_parts = []
        for i, rec in enumerate(recommendations[:10], 1):  # Top 10
            priority = rec.get('priority', 'medium')
            category = rec.get('category', 'general')
            title = rec.get('title', '')
            description = rec.get('description', '')
            impact = rec.get('impact', 'Improves code quality')
            effort = rec.get('effort', 'medium')
            file_path = rec.get('file_path', '')

            priority_class = priority if priority in ['critical', 'high', 'medium'] else ''

            html_parts.append(f'''
            <div class="rec-card">
                <div class="rec-header">
                    <div class="rec-priority {priority_class}">{i}</div>
                    <div>
                        <div class="rec-title">{title}</div>
                        <div class="rec-subtitle">{priority.upper()} - {category.title()}</div>
                    </div>
                </div>
                <div class="rec-content">
                    <div class="rec-stats">
                        <div class="rec-stat">
                            <div class="rec-stat-value">{priority.title()}</div>
                            <div class="rec-stat-label">Priority</div>
                        </div>
                        <div class="rec-stat">
                            <div class="rec-stat-value">{effort.title()}</div>
                            <div class="rec-stat-label">Effort</div>
                        </div>
                        <div class="rec-stat">
                            <div class="rec-stat-value">{category.title()}</div>
                            <div class="rec-stat-label">Category</div>
                        </div>
                    </div>
                    <div class="rec-details">
                        <p><strong>Description:</strong> {description}</p>
                        <p style="margin-top: 8px;"><strong>Impact:</strong> {impact}</p>
                        {f'<p style="margin-top: 8px;"><strong>File:</strong> <code>{file_path}</code></p>' if file_path else ''}
                    </div>
                </div>
            </div>''')

        return '\n'.join(html_parts)

    def _generate_roadmap_section(self, recommendations: List) -> str:
        """Generate implementation roadmap"""
        # Group by priority
        critical_high = [r for r in recommendations if r.get('priority') in ['critical', 'high']]
        medium = [r for r in recommendations if r.get('priority') == 'medium']
        low = [r for r in recommendations if r.get('priority') == 'low']

        html = '''
        <div class="roadmap">'''

        if critical_high:
            html += '''
            <div class="roadmap-phase" style="border-left-color: #EF4444;">
                <h4>&#128293; Phase 1: Critical & High Priority (Week 1-2)</h4>
                <div class="roadmap-items">'''
            for rec in critical_high[:5]:
                html += f'''
                    <label class="roadmap-item"><input type="checkbox"> {rec.get('title', '')}</label>'''
            html += '''
                </div>
            </div>'''

        if medium:
            html += '''
            <div class="roadmap-phase" style="border-left-color: #F59E0B;">
                <h4>&#128736; Phase 2: Medium Priority (Week 3-4)</h4>
                <div class="roadmap-items">'''
            for rec in medium[:5]:
                html += f'''
                    <label class="roadmap-item"><input type="checkbox"> {rec.get('title', '')}</label>'''
            html += '''
                </div>
            </div>'''

        if low:
            html += '''
            <div class="roadmap-phase" style="border-left-color: #10B981;">
                <h4>&#127919; Phase 3: Enhancements (Month 2+)</h4>
                <div class="roadmap-items">'''
            for rec in low[:5]:
                html += f'''
                    <label class="roadmap-item"><input type="checkbox"> {rec.get('title', '')}</label>'''
            html += '''
                </div>
            </div>'''

        html += '''
        </div>'''

        return html


def generate_audit_report(audit_result: Dict[str, Any]) -> str:
    """Convenience function to generate an audit report"""
    generator = CodeAuditReportGenerator()
    return generator.generate_report(audit_result)


# ============================================================================
# Business Report Generator - For business insights alongside prototypes
# ============================================================================

class BusinessReportGenerator:
    """
    Generates professional HTML business insights reports.

    Supports three report types:
    1. transformation_proposal - For new builds (like brew_&_co style)
    2. ux_audit - For existing site audits (like ene-audit style)
    3. comprehensive - Combines both (like JUICENET style)
    """

    def __init__(self):
        self.timestamp = datetime.now().strftime("%B %Y")

    def generate_report(self, report: BusinessReport) -> str:
        """
        Generate a complete HTML report from a BusinessReport model.

        Args:
            report: Pydantic BusinessReport model with all sections populated

        Returns:
            Complete HTML document as a string
        """
        if report.report_type == ReportType.TRANSFORMATION_PROPOSAL:
            return self._generate_transformation_proposal(report)
        elif report.report_type == ReportType.UX_AUDIT:
            return self._generate_ux_audit(report)
        else:  # COMPREHENSIVE
            return self._generate_comprehensive(report)

    def _get_common_styles(self) -> str:
        """Get shared CSS styles used across all report types"""
        return '''
        :root {
            --primary: #6366F1;
            --primary-light: #818CF8;
            --secondary: #8B5CF6;
            --accent: #10B981;
            --dark: #0F172A;
            --dark-secondary: #1E293B;
            --light: #F8FAFC;
            --text: #334155;
            --text-light: #64748B;
            --success: #10B981;
            --warning: #F59E0B;
            --danger: #EF4444;
            --info: #3B82F6;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--light);
            color: var(--text);
            line-height: 1.6;
        }

        /* Navigation */
        .nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(15, 23, 42, 0.97);
            backdrop-filter: blur(12px);
            padding: 12px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 1000;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .nav-brand {
            font-size: 16px;
            font-weight: 700;
            color: white;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .nav-brand span {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .nav-links {
            display: flex;
            gap: 4px;
            flex-wrap: wrap;
        }

        .nav-link {
            color: rgba(255,255,255,0.7);
            text-decoration: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s ease;
            white-space: nowrap;
        }

        .nav-link:hover, .nav-link.active {
            color: white;
            background: rgba(255,255,255,0.1);
        }

        /* Cover */
        .cover {
            background: linear-gradient(135deg, var(--dark) 0%, var(--dark-secondary) 100%);
            color: white;
            padding: 100px 60px 80px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }

        .cover::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 800px;
            height: 800px;
            background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
            border-radius: 50%;
        }

        .cover-content {
            position: relative;
            z-index: 1;
            max-width: 1000px;
        }

        .cover-badge {
            display: inline-block;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            padding: 8px 20px;
            border-radius: 30px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 24px;
        }

        .cover h1 {
            font-family: 'Playfair Display', serif;
            font-size: 48px;
            font-weight: 700;
            line-height: 1.15;
            margin-bottom: 16px;
        }

        .cover h1 span {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .cover .subtitle {
            font-size: 18px;
            opacity: 0.85;
            margin-bottom: 40px;
            max-width: 700px;
        }

        .cover-stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            max-width: 900px;
        }

        .cover-stat {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 24px 20px;
            text-align: center;
            transition: all 0.2s ease;
        }

        .cover-stat:hover {
            transform: translateY(-4px);
            background: rgba(255,255,255,0.08);
        }

        .cover-stat-value {
            font-size: 32px;
            font-weight: 800;
        }

        .cover-stat-value.danger { color: var(--danger); }
        .cover-stat-value.warning { color: var(--warning); }
        .cover-stat-value.success { color: var(--success); }
        .cover-stat-value.info { color: var(--info); }

        .cover-stat-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            opacity: 0.7;
            margin-top: 8px;
        }

        /* Container */
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 60px 40px;
        }

        /* Section */
        .section {
            background: white;
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 28px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        }

        .section-header {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 20px;
        }

        .section-icon {
            width: 48px;
            height: 48px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 22px;
        }

        .section-icon.danger { background: linear-gradient(135deg, #EF4444, #DC2626); }
        .section-icon.success { background: linear-gradient(135deg, #10B981, #059669); }
        .section-icon.warning { background: linear-gradient(135deg, #F59E0B, #D97706); }
        .section-icon.info { background: linear-gradient(135deg, #3B82F6, #2563EB); }
        .section-icon.purple { background: linear-gradient(135deg, #8B5CF6, #7C3AED); }

        .section h2 {
            font-size: 24px;
            font-weight: 700;
            color: var(--dark);
        }

        .section-intro {
            font-size: 15px;
            color: var(--text-light);
            margin-bottom: 28px;
            line-height: 1.6;
        }

        /* Bottom Line Box */
        .bottom-line {
            background: linear-gradient(135deg, #FEF2F2, #FEE2E2);
            border: 2px solid #FECACA;
            border-radius: 16px;
            padding: 24px;
            margin: 24px 0;
        }

        .bottom-line.success {
            background: linear-gradient(135deg, #ECFDF5, #D1FAE5);
            border-color: #A7F3D0;
        }

        .bottom-line.success h4 { color: #065F46; }
        .bottom-line.success p { color: #047857; }

        .bottom-line.info {
            background: linear-gradient(135deg, #EFF6FF, #DBEAFE);
            border-color: #93C5FD;
        }

        .bottom-line.info h4 { color: #1E40AF; }
        .bottom-line.info p { color: #1D4ED8; }

        .bottom-line h4 {
            color: #991B1B;
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .bottom-line p {
            color: #7F1D1D;
            font-size: 14px;
            line-height: 1.6;
        }

        /* Tables */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }

        .data-table th {
            text-align: left;
            padding: 14px 16px;
            background: var(--light);
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-light);
            border-bottom: 2px solid #E2E8F0;
        }

        .data-table td {
            padding: 14px 16px;
            border-bottom: 1px solid #E2E8F0;
        }

        .data-table tr:hover {
            background: #F8FAFC;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }

        .badge.critical { background: #FEE2E2; color: #DC2626; }
        .badge.high { background: #FEF3C7; color: #D97706; }
        .badge.warning { background: #FEF3C7; color: #D97706; }
        .badge.medium { background: #DBEAFE; color: #2563EB; }
        .badge.low { background: #E0E7FF; color: #4F46E5; }
        .badge.good { background: #D1FAE5; color: #059669; }
        .badge.info { background: #DBEAFE; color: #2563EB; }

        /* Issues */
        .issue-card {
            background: var(--light);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 12px;
            border-left: 4px solid;
            transition: transform 0.2s ease;
        }

        .issue-card:hover {
            transform: translateX(4px);
        }

        .issue-card.critical { border-left-color: #DC2626; }
        .issue-card.high { border-left-color: #D97706; }
        .issue-card.medium { border-left-color: #2563EB; }
        .issue-card.low { border-left-color: #4F46E5; }
        .issue-card.confirmed { border-left-color: #10B981; }

        .issue-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 8px;
        }

        .issue-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--dark);
        }

        .issue-description {
            font-size: 13px;
            color: var(--text-light);
            margin-bottom: 10px;
        }

        .issue-meta {
            display: flex;
            gap: 16px;
            font-size: 12px;
            color: var(--text-light);
        }

        .issue-meta span {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        /* Recommendations */
        .rec-card {
            background: var(--light);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            border: 2px solid transparent;
            transition: all 0.2s ease;
        }

        .rec-card:hover {
            border-color: var(--accent);
            transform: translateY(-2px);
        }

        .rec-header {
            display: flex;
            gap: 16px;
            margin-bottom: 16px;
        }

        .rec-priority {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 800;
            font-size: 18px;
            flex-shrink: 0;
        }

        .rec-title {
            font-size: 17px;
            font-weight: 700;
            color: var(--dark);
            margin-bottom: 4px;
        }

        .rec-subtitle {
            font-size: 13px;
            color: var(--text-light);
        }

        .rec-content {
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #E2E8F0;
        }

        .rec-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 16px;
        }

        .rec-stat {
            text-align: center;
            padding: 12px;
            background: white;
            border-radius: 8px;
        }

        .rec-stat-value {
            font-size: 20px;
            font-weight: 700;
            color: var(--accent);
        }

        .rec-stat-label {
            font-size: 11px;
            color: var(--text-light);
            margin-top: 2px;
        }

        .rec-details {
            font-size: 14px;
            color: var(--text);
            line-height: 1.6;
        }

        /* Roadmap */
        .roadmap-phase {
            background: var(--light);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 12px;
            border-left: 4px solid var(--accent);
        }

        .roadmap-phase h4 {
            font-size: 15px;
            font-weight: 700;
            color: var(--dark);
            margin-bottom: 12px;
        }

        .roadmap-items {
            display: grid;
            gap: 8px;
        }

        .roadmap-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13px;
            color: var(--text);
        }

        .roadmap-item input[type="checkbox"] {
            width: 18px;
            height: 18px;
            accent-color: var(--accent);
        }

        /* KPI Table */
        .kpi-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }

        .kpi-table th {
            text-align: left;
            padding: 12px 16px;
            background: var(--dark);
            color: white;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .kpi-table td {
            padding: 14px 16px;
            border-bottom: 1px solid #E2E8F0;
            font-size: 14px;
        }

        .kpi-current { color: var(--danger); font-weight: 600; }
        .kpi-target { color: var(--success); font-weight: 600; }

        /* ROI Box */
        .roi-box {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            border-radius: 16px;
            padding: 28px;
            color: white;
            margin: 24px 0;
        }

        .roi-box h3 {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 20px;
        }

        .roi-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }

        .roi-scenario {
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
        }

        .roi-scenario h4 {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 12px;
            opacity: 0.9;
        }

        .roi-metric {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            font-size: 13px;
        }

        .roi-metric:last-child { border-bottom: none; }
        .roi-value { font-weight: 700; }

        /* Charts */
        .charts-row {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
            margin: 24px 0;
        }

        .chart-card {
            background: var(--light);
            border-radius: 16px;
            padding: 24px;
        }

        .chart-card h3 {
            font-size: 15px;
            font-weight: 600;
            color: var(--dark);
            margin-bottom: 16px;
        }

        .chart-wrapper {
            position: relative;
            height: 280px;
        }

        /* Funnel ASCII */
        .funnel-ascii {
            background: var(--dark);
            border-radius: 12px;
            padding: 24px;
            overflow-x: auto;
            margin: 24px 0;
        }

        .funnel-ascii pre {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            line-height: 1.5;
            color: #E2E8F0;
            margin: 0;
            white-space: pre;
        }

        .funnel-ascii .highlight { color: #F59E0B; }
        .funnel-ascii .danger { color: #EF4444; }
        .funnel-ascii .success { color: #10B981; }
        .funnel-ascii .info { color: #60A5FA; }

        /* Industry Insights */
        .insight-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin: 20px 0;
        }

        .insight-card {
            background: var(--light);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }

        .insight-value {
            font-size: 24px;
            font-weight: 800;
            color: var(--primary);
        }

        .insight-label {
            font-size: 12px;
            color: var(--text-light);
            margin-top: 4px;
        }

        /* Design System */
        .color-grid {
            display: flex;
            gap: 12px;
            margin: 16px 0;
        }

        .color-swatch {
            width: 60px;
            height: 60px;
            border-radius: 12px;
            display: flex;
            align-items: flex-end;
            justify-content: center;
            padding: 4px;
            font-size: 10px;
            color: white;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }

        .mood-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 12px 0;
        }

        .mood-tag {
            background: var(--light);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            color: var(--text);
        }

        /* Features Table */
        .features-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }

        .features-table th {
            text-align: left;
            padding: 12px 16px;
            background: var(--dark);
            color: white;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .features-table td {
            padding: 14px 16px;
            border-bottom: 1px solid #E2E8F0;
        }

        .priority-must { color: var(--danger); font-weight: 600; }
        .priority-should { color: var(--warning); font-weight: 600; }
        .priority-nice { color: var(--info); font-weight: 600; }

        /* Footer */
        .footer {
            background: var(--dark);
            color: white;
            padding: 32px 40px;
            text-align: center;
        }

        .footer p {
            font-size: 13px;
            opacity: 0.7;
        }

        /* Responsive */
        @media (max-width: 900px) {
            .cover { padding: 80px 24px 60px; }
            .cover h1 { font-size: 36px; }
            .cover-stats { grid-template-columns: repeat(2, 1fr); }
            .container { padding: 40px 20px; }
            .section { padding: 24px; }
            .charts-row { grid-template-columns: 1fr; }
            .insight-grid { grid-template-columns: 1fr; }
            .rec-stats { grid-template-columns: 1fr; }
            .roi-grid { grid-template-columns: 1fr; }
            .nav { padding: 10px 16px; flex-direction: column; gap: 8px; }
            .nav-links { justify-content: center; }
        }

        @media print {
            .nav { display: none; }
            .cover { min-height: auto; padding: 40px; }
            .section { break-inside: avoid; page-break-inside: avoid; }
        }
        '''

    def _generate_transformation_proposal(self, report: BusinessReport) -> str:
        """Generate a Digital Transformation Proposal report"""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.company_name} - Digital Transformation Proposal | {self.timestamp}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>{self._get_common_styles()}</style>
</head>
<body>
    <nav class="nav">
        <div class="nav-brand"><span>{report.company_name}</span> Transformation Proposal</div>
        <div class="nav-links">
            <a href="#executive" class="nav-link active">Executive</a>
            <a href="#industry" class="nav-link">Industry</a>
            <a href="#design" class="nav-link">Design</a>
            <a href="#features" class="nav-link">Features</a>
            <a href="#roadmap" class="nav-link">Roadmap</a>
            <a href="#roi" class="nav-link">ROI</a>
        </div>
    </nav>

    <section class="cover" id="executive">
        <div class="cover-content">
            <div class="cover-badge">Digital Transformation Proposal</div>
            <h1>{report.company_name}<br><span>Business Analysis</span></h1>
            <p class="subtitle">{report.industry.replace('-', ' ').title()} Industry | {self.timestamp} | Comprehensive analysis with market research, competitor insights, and actionable recommendations.</p>
            {self._render_cover_stats(report.cover_stats)}
        </div>
    </section>

    <div class="container">
        {self._render_executive_summary(report.executive_summary)}
        {self._render_industry_section(report.industry_section)}
        {self._render_design_system(report.design_system)}
        {self._render_features_table(report.recommended_features)}
        {self._render_roadmap(report.roadmap)}
        {self._render_roi_section(report.kpis, report.roi_projections)}
        {self._render_ai_log(report.ai_analysis_log)}
    </div>

    <footer class="footer">
        <p>Generated by Code Weaver Pro | {datetime.now().strftime("%B %d, %Y")} | {', '.join(report.data_sources) if report.data_sources else 'AI Analysis'}</p>
        <p style="margin-top: 8px;">Confidence level: {report.confidence_level}</p>
    </footer>
</body>
</html>'''

    def _generate_ux_audit(self, report: BusinessReport) -> str:
        """Generate a UX & Performance Audit report"""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.company_name} - UX Audit Report | {self.timestamp}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>{self._get_common_styles()}</style>
</head>
<body>
    <nav class="nav">
        <div class="nav-brand"><span>{report.company_name}</span> UX Audit</div>
        <div class="nav-links">
            <a href="#executive" class="nav-link active">Executive</a>
            <a href="#funnel" class="nav-link">Funnel</a>
            <a href="#issues" class="nav-link">Issues</a>
            <a href="#recommendations" class="nav-link">Actions</a>
            <a href="#roadmap" class="nav-link">Roadmap</a>
            <a href="#roi" class="nav-link">ROI</a>
        </div>
    </nav>

    <section class="cover" id="executive">
        <div class="cover-content">
            <div class="cover-badge">UX & Performance Audit</div>
            <h1>{report.company_name}<br><span>Comprehensive Analysis</span></h1>
            <p class="subtitle">{report.industry.replace('-', ' ').title()} | {self.timestamp} | Deep dive into user experience, conversion funnel, and growth opportunities.</p>
            {self._render_cover_stats(report.cover_stats)}
        </div>
    </section>

    <div class="container">
        {self._render_executive_summary(report.executive_summary)}
        {self._render_score_breakdown(report.score_breakdown, report.heuristic_scores)}
        {self._render_funnel_analysis(report.funnel_analysis)}
        {self._render_issues_section(report.issues_found)}
        {self._render_recommendations(report.recommendations)}
        {self._render_roadmap(report.roadmap)}
        {self._render_roi_section(report.kpis, report.roi_projections)}
    </div>

    <footer class="footer">
        <p>Generated by Code Weaver Pro | {datetime.now().strftime("%B %d, %Y")} | {', '.join(report.data_sources) if report.data_sources else 'Production Testing & Analysis'}</p>
        <p style="margin-top: 8px;">Confidence level: {report.confidence_level}</p>
    </footer>
</body>
</html>'''

    def _generate_comprehensive(self, report: BusinessReport) -> str:
        """Generate a Comprehensive report combining proposal and audit"""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.company_name} - Comprehensive Analysis | {self.timestamp}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>{self._get_common_styles()}</style>
</head>
<body>
    <nav class="nav">
        <div class="nav-brand"><span>{report.company_name}</span> Comprehensive Report</div>
        <div class="nav-links">
            <a href="#executive" class="nav-link active">Executive</a>
            <a href="#industry" class="nav-link">Industry</a>
            <a href="#funnel" class="nav-link">Funnel</a>
            <a href="#issues" class="nav-link">Issues</a>
            <a href="#prototype" class="nav-link">Prototype</a>
            <a href="#recommendations" class="nav-link">Actions</a>
            <a href="#roadmap" class="nav-link">Roadmap</a>
            <a href="#roi" class="nav-link">ROI</a>
        </div>
    </nav>

    <section class="cover" id="executive">
        <div class="cover-content">
            <div class="cover-badge">Comprehensive Business Analysis</div>
            <h1>{report.company_name}<br><span>Full Report</span></h1>
            <p class="subtitle">{report.industry.replace('-', ' ').title()} | {self.timestamp} | Complete analysis with market research, UX audit, prototype, and implementation roadmap.</p>
            {self._render_cover_stats(report.cover_stats)}
        </div>
    </section>

    <div class="container">
        {self._render_executive_summary(report.executive_summary)}
        {self._render_industry_section(report.industry_section)}
        {self._render_score_breakdown(report.score_breakdown, report.heuristic_scores)}
        {self._render_funnel_analysis(report.funnel_analysis)}
        {self._render_issues_section(report.issues_found)}
        {self._render_prototype_section(report.prototype_embed_url)}
        {self._render_recommendations(report.recommendations)}
        {self._render_design_system(report.design_system)}
        {self._render_features_table(report.recommended_features)}
        {self._render_roadmap(report.roadmap)}
        {self._render_roi_section(report.kpis, report.roi_projections)}
        {self._render_ai_log(report.ai_analysis_log)}
    </div>

    <footer class="footer">
        <p>Generated by Code Weaver Pro | {datetime.now().strftime("%B %d, %Y")} | {', '.join(report.data_sources) if report.data_sources else 'AI Analysis + Production Testing'}</p>
        <p style="margin-top: 8px;">Confidence level: {report.confidence_level}</p>
    </footer>
</body>
</html>'''

    # ========================================================================
    # Section Renderers
    # ========================================================================

    def _render_cover_stats(self, stats: List[MetricItem]) -> str:
        """Render cover page statistics"""
        if not stats:
            return ''

        html = '<div class="cover-stats">'
        for stat in stats[:4]:
            badge_class = stat.badge.value if stat.badge else 'info'
            html += f'''
            <div class="cover-stat">
                <div class="cover-stat-value {badge_class}">{stat.value}</div>
                <div class="cover-stat-label">{stat.label}</div>
            </div>'''
        html += '</div>'
        return html

    def _render_executive_summary(self, summary: ExecutiveSummary) -> str:
        """Render executive summary section"""
        bottom_line_class = 'success' if summary.bottom_line_type == 'success' else ('info' if summary.bottom_line_type == 'info' else '')

        metrics_html = ''
        if summary.metrics:
            metrics_html = '''
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Assessment</th>
                    </tr>
                </thead>
                <tbody>'''
            for metric in summary.metrics:
                badge_class = metric.badge.value if metric.badge else 'info'
                badge_text = metric.badge_text or badge_class.title()
                metrics_html += f'''
                    <tr>
                        <td>{metric.label}</td>
                        <td><strong>{metric.value}</strong></td>
                        <td><span class="badge {badge_class}">{badge_text}</span></td>
                    </tr>'''
            metrics_html += '</tbody></table>'

        return f'''
        <section class="section">
            <div class="section-header">
                <div class="section-icon info">&#128202;</div>
                <h2>Executive Summary</h2>
            </div>
            {metrics_html}
            <div class="bottom-line {bottom_line_class}">
                <h4>&#9888; The Bottom Line</h4>
                <p><strong>{summary.headline}</strong> {summary.bottom_line}</p>
            </div>
        </section>'''

    def _render_industry_section(self, industry: Optional[IndustrySection]) -> str:
        """Render industry insights section"""
        if not industry:
            return ''

        insights_html = '<div class="insight-grid">'
        if industry.market_size:
            insights_html += f'''
            <div class="insight-card">
                <div class="insight-value">{industry.market_size}</div>
                <div class="insight-label">Market Size</div>
            </div>'''
        if industry.digital_adoption_rate:
            insights_html += f'''
            <div class="insight-card">
                <div class="insight-value">{industry.digital_adoption_rate}</div>
                <div class="insight-label">Digital Adoption</div>
            </div>'''
        for insight in industry.insights[:3]:
            insights_html += f'''
            <div class="insight-card">
                <div class="insight-value">{insight.value}</div>
                <div class="insight-label">{insight.title}</div>
            </div>'''
        insights_html += '</div>'

        trends_html = ''
        if industry.key_trends:
            trends_html = '<h4 style="margin: 20px 0 12px;">Key Industry Trends</h4><ul style="margin-left: 20px;">'
            for trend in industry.key_trends:
                trends_html += f'<li>{trend}</li>'
            trends_html += '</ul>'

        return f'''
        <section class="section" id="industry">
            <div class="section-header">
                <div class="section-icon purple">&#127758;</div>
                <h2>Industry Insights</h2>
            </div>
            <p class="section-intro">Market research and industry trends to inform your strategy.</p>
            {insights_html}
            {trends_html}
        </section>'''

    def _render_design_system(self, design: Optional[DesignSystem]) -> str:
        """Render design system section"""
        if not design:
            return ''

        colors_html = '<div class="color-grid">'
        colors_html += f'<div class="color-swatch" style="background: {design.primary_color};">Primary</div>'
        colors_html += f'<div class="color-swatch" style="background: {design.secondary_color};">Secondary</div>'
        colors_html += f'<div class="color-swatch" style="background: {design.accent_color};">Accent</div>'
        colors_html += f'<div class="color-swatch" style="background: {design.text_color};">Text</div>'
        colors_html += '</div>'

        mood_html = ''
        if design.mood_tags:
            mood_html = '<div class="mood-tags">'
            for tag in design.mood_tags:
                mood_html += f'<span class="mood-tag">{tag}</span>'
            mood_html += '</div>'

        return f'''
        <section class="section" id="design">
            <div class="section-header">
                <div class="section-icon success">&#127912;</div>
                <h2>Recommended Design System</h2>
            </div>
            <p class="section-intro">Visual guidelines based on industry best practices and your brand positioning.</p>
            <h4 style="margin-bottom: 12px;">Color Palette</h4>
            {colors_html}
            <h4 style="margin: 20px 0 8px;">Typography</h4>
            <p><code>{design.font_family}</code></p>
            {f'<h4 style="margin: 20px 0 8px;">Mood & Style</h4>{mood_html}' if mood_html else ''}
        </section>'''

    def _render_features_table(self, features: List[FeatureRow]) -> str:
        """Render recommended features table"""
        if not features:
            return ''

        rows_html = ''
        for feature in features:
            priority_class = 'priority-must' if feature.priority == 'Must Have' else ('priority-should' if feature.priority == 'Should Have' else 'priority-nice')
            rows_html += f'''
            <tr>
                <td>{feature.feature}</td>
                <td class="{priority_class}">{feature.priority}</td>
                <td>{feature.investment}</td>
                <td>{feature.timeline}</td>
            </tr>'''

        return f'''
        <section class="section" id="features">
            <div class="section-header">
                <div class="section-icon info">&#128640;</div>
                <h2>Recommended Features</h2>
            </div>
            <p class="section-intro">Prioritized feature recommendations based on market research and industry standards.</p>
            <table class="features-table">
                <thead>
                    <tr>
                        <th>Feature</th>
                        <th>Priority</th>
                        <th>Investment</th>
                        <th>Timeline</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </section>'''

    def _render_score_breakdown(self, scores: Optional[ScoreBreakdown], heuristics: List[HeuristicScore]) -> str:
        """Render score breakdown section for audit reports"""
        if not scores:
            return ''

        return f'''
        <section class="section" id="scores">
            <div class="section-header">
                <div class="section-icon purple">&#127919;</div>
                <h2>Score Breakdown</h2>
            </div>
            <p class="section-intro">Assessment across key areas of user experience and technical performance.</p>
            <div class="insight-grid" style="grid-template-columns: repeat(4, 1fr);">
                <div class="insight-card">
                    <div class="insight-value" style="color: var(--{'success' if scores.ux_score >= 7 else 'warning' if scores.ux_score >= 5 else 'danger'});">{scores.ux_score}/10</div>
                    <div class="insight-label">UX Score</div>
                </div>
                <div class="insight-card">
                    <div class="insight-value" style="color: var(--{'success' if scores.performance_score >= 80 else 'warning' if scores.performance_score >= 50 else 'danger'});">{int(scores.performance_score)}%</div>
                    <div class="insight-label">Performance</div>
                </div>
                <div class="insight-card">
                    <div class="insight-value" style="color: var(--{'success' if scores.accessibility_score >= 80 else 'warning' if scores.accessibility_score >= 50 else 'danger'});">{int(scores.accessibility_score)}%</div>
                    <div class="insight-label">Accessibility</div>
                </div>
                <div class="insight-card">
                    <div class="insight-value" style="color: var(--{'success' if scores.seo_score >= 80 else 'warning' if scores.seo_score >= 50 else 'danger'});">{int(scores.seo_score)}%</div>
                    <div class="insight-label">SEO</div>
                </div>
            </div>
        </section>'''

    def _render_funnel_analysis(self, funnel: Optional[FunnelAnalysis]) -> str:
        """Render funnel analysis section"""
        if not funnel or not funnel.steps:
            return ''

        ascii_funnel = f'''
<span class="info">{funnel.title.upper()}</span>
<span class="highlight">{"=" * 60}</span>
'''
        for i, step in enumerate(funnel.steps):
            ascii_funnel += f'''
[{step.name.upper()}]
         <span class="success">{step.count:,}</span> users ({step.percentage:.1f}%)'''
            if step.drop_off and i < len(funnel.steps) - 1:
                ascii_funnel += f'''
              │
              │ <span class="danger">{step.drop_off:.1f}% DROP-OFF</span>
              ▼'''

        ascii_funnel += f'''

<span class="highlight">{"=" * 60}</span>
<span class="danger">OVERALL CONVERSION: {funnel.overall_conversion:.1f}%</span>
<span class="highlight">{"=" * 60}</span>'''

        return f'''
        <section class="section" id="funnel">
            <div class="section-header">
                <div class="section-icon danger">&#128200;</div>
                <h2>{funnel.title}</h2>
            </div>
            <p class="section-intro">Visual breakdown of where users are dropping off. Each percentage represents real users lost.</p>
            <div class="funnel-ascii">
                <pre>{ascii_funnel}</pre>
            </div>
            {f'<div class="bottom-line"><h4>&#9888; Biggest Drop-off</h4><p>{funnel.biggest_drop_off}</p></div>' if funnel.biggest_drop_off else ''}
        </section>'''

    def _render_issues_section(self, issues: List[IssueCard]) -> str:
        """Render issues found section"""
        if not issues:
            return '''
        <section class="section" id="issues">
            <div class="section-header">
                <div class="section-icon success">&#10003;</div>
                <h2>Issues Identified</h2>
            </div>
            <div class="bottom-line success">
                <h4>&#10003; No Major Issues Found</h4>
                <p>Great news! No critical issues were detected. Continue following best practices!</p>
            </div>
        </section>'''

        html = '''
        <section class="section" id="issues">
            <div class="section-header">
                <div class="section-icon warning">&#9888;</div>
                <h2>Issues Identified</h2>
            </div>
            <p class="section-intro">Critical issues discovered during analysis. Each includes severity, impact, and how to fix.</p>'''

        for issue in issues[:15]:
            confirmed_badge = '<span class="badge good">&#10003; CONFIRMED</span>' if issue.confirmed else ''
            drop_off_meta = f'<span>&#128200; {issue.drop_off_percentage}% drop-off</span>' if issue.drop_off_percentage else ''

            html += f'''
            <div class="issue-card {issue.severity.value}">
                <div class="issue-header">
                    <span class="issue-title">{issue.title}</span>
                    <span class="badge {issue.severity.value}">{issue.severity.value.upper()}</span>
                </div>
                <p class="issue-description">{issue.description}</p>
                <p class="issue-description"><strong>Business Impact:</strong> {issue.business_impact}</p>
                <p class="issue-description"><strong>How to Fix:</strong> {issue.how_to_fix}</p>
                <div class="issue-meta">
                    {drop_off_meta}
                    {confirmed_badge}
                    {f'<span>&#128193; {issue.category}</span>' if issue.category else ''}
                </div>
            </div>'''

        html += '</section>'
        return html

    def _render_prototype_section(self, embed_url: Optional[str]) -> str:
        """Render embedded prototype section"""
        if not embed_url:
            return ''

        return f'''
        <section class="section" id="prototype" style="background: linear-gradient(135deg, var(--dark) 0%, var(--dark-secondary) 100%); color: white;">
            <div class="section-header">
                <div class="section-icon success">&#128187;</div>
                <h2 style="color: white;">Interactive Prototype</h2>
            </div>
            <p class="section-intro" style="color: rgba(255,255,255,0.7);">Live preview of the recommended improvements. Click through to experience the proposed UX flow.</p>
            <div style="background: #e8e8e8; border-radius: 12px; min-height: 650px; overflow: hidden;">
                <iframe src="{embed_url}" style="width: 100%; height: 650px; border: none;"></iframe>
            </div>
        </section>'''

    def _render_recommendations(self, recommendations: List[Recommendation]) -> str:
        """Render recommendations section"""
        if not recommendations:
            return ''

        html = '''
        <section class="section" id="recommendations">
            <div class="section-header">
                <div class="section-icon success">&#128161;</div>
                <h2>Actionable Recommendations</h2>
            </div>
            <p class="section-intro">Prioritized actions with expected impact. Each recommendation includes confidence level and implementation details.</p>'''

        for rec in recommendations[:10]:
            changes_html = ''
            if rec.changes:
                changes_html = '<ul style="margin: 8px 0 0 20px;">'
                for change in rec.changes:
                    changes_html += f'<li>{change}</li>'
                changes_html += '</ul>'

            stats_html = ''
            if rec.stats:
                stats_html = '<div class="rec-stats">'
                for key, value in list(rec.stats.items())[:3]:
                    stats_html += f'''
                    <div class="rec-stat">
                        <div class="rec-stat-value">{value}</div>
                        <div class="rec-stat-label">{key.replace("_", " ").title()}</div>
                    </div>'''
                stats_html += '</div>'

            html += f'''
            <div class="rec-card">
                <div class="rec-header">
                    <div class="rec-priority">{rec.priority}</div>
                    <div>
                        <div class="rec-title">{rec.title}</div>
                        <div class="rec-subtitle">{rec.subtitle}</div>
                    </div>
                </div>
                <div class="rec-content">
                    {stats_html}
                    <div class="rec-details">
                        {f'<p><strong>Current:</strong> {rec.current_state}</p>' if rec.current_state else ''}
                        {f'<p><strong>Recommended:</strong> {rec.recommended_state}</p>' if rec.recommended_state else ''}
                        {f'<p><strong>Expected Lift:</strong> {rec.expected_lift}</p>' if rec.expected_lift else ''}
                        {f'<p><strong>Changes:</strong></p>{changes_html}' if changes_html else ''}
                    </div>
                </div>
            </div>'''

        html += '</section>'
        return html

    def _render_roadmap(self, phases: List[RoadmapPhase]) -> str:
        """Render implementation roadmap section"""
        if not phases:
            return ''

        html = '''
        <section class="section" id="roadmap">
            <div class="section-header">
                <div class="section-icon purple">&#128197;</div>
                <h2>Implementation Roadmap</h2>
            </div>
            <p class="section-intro">Phased approach starting with highest-impact fixes. Use checkboxes to track progress.</p>
            <div class="roadmap">'''

        for phase in phases:
            items_html = '<div class="roadmap-items">'
            for item in phase.items:
                checked = 'checked' if item.completed else ''
                items_html += f'<label class="roadmap-item"><input type="checkbox" {checked}> {item.task}</label>'
            items_html += '</div>'

            html += f'''
            <div class="roadmap-phase" style="border-left-color: {phase.color};">
                <h4>{phase.title}</h4>
                {items_html}
            </div>'''

        html += '</div></section>'
        return html

    def _render_roi_section(self, kpis: List[KPIRow], projections: List[ROIProjection]) -> str:
        """Render KPIs and ROI projections section"""
        if not kpis and not projections:
            return ''

        kpi_html = ''
        if kpis:
            kpi_html = '''
            <h3 style="font-size: 16px; margin-bottom: 16px; color: var(--dark);">KPIs to Track</h3>
            <table class="kpi-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Current</th>
                        <th>Target (30 days)</th>
                        <th>Target (90 days)</th>
                    </tr>
                </thead>
                <tbody>'''
            for kpi in kpis:
                kpi_html += f'''
                    <tr>
                        <td>{kpi.metric}</td>
                        <td class="{'kpi-current' if kpi.current_is_bad else ''}">{kpi.current}</td>
                        <td class="kpi-target">{kpi.target_30_days}</td>
                        <td class="kpi-target">{kpi.target_90_days}</td>
                    </tr>'''
            kpi_html += '</tbody></table>'

        roi_html = ''
        if projections:
            roi_html = '''
            <div class="roi-box">
                <h3>&#128200; ROI Projection</h3>
                <div class="roi-grid">'''
            for proj in projections:
                roi_html += f'''
                    <div class="roi-scenario">
                        <h4>{proj.title}</h4>'''
                for metric in proj.metrics:
                    roi_html += f'''
                        <div class="roi-metric">
                            <span>{metric.label}</span>
                            <span class="roi-value">{metric.value}</span>
                        </div>'''
                roi_html += '</div>'
            roi_html += '</div></div>'

        return f'''
        <section class="section" id="roi">
            <div class="section-header">
                <div class="section-icon success">&#128200;</div>
                <h2>Success Metrics & ROI</h2>
            </div>
            <p class="section-intro">KPI targets and projected return on implementing the recommendations.</p>
            {kpi_html}
            {roi_html}
        </section>'''

    def _render_ai_log(self, log_entries: List[AILogEntry]) -> str:
        """Render AI analysis log section"""
        if not log_entries:
            return ''

        html = '''
        <section class="section" id="ai-log">
            <div class="section-header">
                <div class="section-icon info">&#129302;</div>
                <h2>AI Analysis Log</h2>
            </div>
            <p class="section-intro">Transparency into the AI agents' decision-making process.</p>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Agent</th>
                        <th>Action</th>
                        <th>Result</th>
                    </tr>
                </thead>
                <tbody>'''

        for entry in log_entries[:20]:
            html += f'''
                    <tr>
                        <td><strong>{entry.agent}</strong></td>
                        <td>{entry.action}</td>
                        <td>{entry.result}</td>
                    </tr>'''

        html += '</tbody></table></section>'
        return html


def generate_business_report(report: BusinessReport) -> str:
    """Convenience function to generate a business insights report"""
    generator = BusinessReportGenerator()
    return generator.generate_report(report)
