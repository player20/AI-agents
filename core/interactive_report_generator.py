"""
Interactive HTML Report Generator for Code Weaver Pro

Generates stunning, interactive HTML reports for different customer types:
- New App Concept: For startups who need app visualization
- Modernization Audit: For businesses modernizing legacy systems
- Optimization Analysis: For businesses improving existing apps

Features:
- Interactive Chart.js charts (funnels, bar, doughnut)
- Clickable prototype embeds with toggle views
- Scroll-triggered animations
- Discoverable elements (expandable sections, hover reveals)
- Print-friendly PDF export
"""

from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, BaseLoader
import json
import base64


class ReportType(Enum):
    """Types of reports that can be generated."""
    NEW_APP_CONCEPT = "new_app"
    MODERNIZATION_AUDIT = "modernization"
    OPTIMIZATION_ANALYSIS = "optimization"


class InteractiveReportGenerator:
    """
    Generates interactive HTML reports based on customer type.

    Each report includes:
    - Animated cover page with key stats
    - Interactive Chart.js visualizations
    - Prototype toggles (Current vs Proposed)
    - Scroll-triggered animations
    - Print-friendly styling
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the report generator.

        Args:
            output_dir: Directory to save generated reports
        """
        self.output_dir = output_dir or Path("reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Template directory is relative to this file
        self.template_dir = Path(__file__).parent / "reports" / "templates"
        self.assets_dir = Path(__file__).parent / "reports" / "assets"

        # Initialize Jinja2 environment with string loader fallback
        if self.template_dir.exists():
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=True
            )
        else:
            # Use string-based templates if no template dir
            self.env = Environment(autoescape=True)

        # Register custom filters
        self.env.filters['tojson'] = lambda x: json.dumps(x)
        self.env.filters['format_number'] = lambda x: f"{x:,}" if isinstance(x, (int, float)) else x
        self.env.filters['format_percent'] = lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) else x

    def generate(
        self,
        report_type: ReportType,
        data: Dict[str, Any],
        output_name: Optional[str] = None
    ) -> Path:
        """
        Generate an interactive HTML report.

        Args:
            report_type: Type of report to generate
            data: Report data (varies by type)
            output_name: Custom output filename

        Returns:
            Path to the generated HTML file
        """
        # Try to load from file, fall back to embedded template
        template_content = self._get_template_content(report_type)
        template = self.env.from_string(template_content)

        # Add common data
        render_data = {
            "data": data,
            "report_type": report_type.value,
            "report_type_display": self._get_display_name(report_type),
            "generated_at": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "generated_timestamp": datetime.now().isoformat(),
        }

        html = template.render(**render_data)

        # Save the report
        output_name = output_name or f"{report_type.value}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        output_path = self.output_dir / output_name
        output_path.write_text(html, encoding="utf-8")

        return output_path

    def _get_display_name(self, report_type: ReportType) -> str:
        """Get human-readable name for report type."""
        names = {
            ReportType.NEW_APP_CONCEPT: "New App Concept",
            ReportType.MODERNIZATION_AUDIT: "Modernization Audit",
            ReportType.OPTIMIZATION_ANALYSIS: "Optimization Analysis",
        }
        return names.get(report_type, report_type.value)

    def _get_template_content(self, report_type: ReportType) -> str:
        """Get template content for report type."""
        template_map = {
            ReportType.NEW_APP_CONCEPT: "new_app.html",
            ReportType.MODERNIZATION_AUDIT: "modernization.html",
            ReportType.OPTIMIZATION_ANALYSIS: "optimization.html",
        }

        template_name = template_map.get(report_type)
        template_path = self.template_dir / template_name

        if template_path.exists():
            return template_path.read_text(encoding="utf-8")

        # Fall back to embedded templates
        return self._get_embedded_template(report_type)

    def _get_embedded_template(self, report_type: ReportType) -> str:
        """Get embedded template for report type."""
        # Base template components
        base_css = self._get_base_css()
        base_js = self._get_base_js()

        if report_type == ReportType.OPTIMIZATION_ANALYSIS:
            return self._get_optimization_template(base_css, base_js)
        elif report_type == ReportType.NEW_APP_CONCEPT:
            return self._get_new_app_template(base_css, base_js)
        elif report_type == ReportType.MODERNIZATION_AUDIT:
            return self._get_modernization_template(base_css, base_js)

        return "<html><body>Template not found</body></html>"

    def _get_base_css(self) -> str:
        """Get base CSS styles."""
        return '''
        :root {
            --primary: #667eea;
            --primary-dark: #5a6fd6;
            --secondary: #764ba2;
            --accent: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --bg-dark: #1a1d29;
            --bg-card: #2d3748;
            --text-primary: #ffffff;
            --text-secondary: #b8c4d4;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
        }

        /* Header / Cover */
        .report-header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            padding: 80px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .report-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
            opacity: 0.5;
        }

        .report-header h1 {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 16px;
            position: relative;
            z-index: 1;
        }

        .report-header .tagline {
            font-size: 1.25rem;
            opacity: 0.9;
            margin-bottom: 40px;
            position: relative;
            z-index: 1;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 24px;
            max-width: 800px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 24px;
            text-align: center;
        }

        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            display: block;
        }

        .stat-label {
            font-size: 0.875rem;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Navigation */
        .nav-sticky {
            position: sticky;
            top: 0;
            background: rgba(26, 29, 41, 0.95);
            backdrop-filter: blur(10px);
            padding: 16px 40px;
            z-index: 100;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .nav-links {
            display: flex;
            gap: 32px;
            justify-content: center;
            list-style: none;
        }

        .nav-links a {
            color: var(--text-secondary);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
        }

        .nav-links a:hover {
            color: var(--primary);
        }

        /* Sections */
        .section {
            padding: 80px 40px;
            max-width: 1200px;
            margin: 0 auto;
        }

        .section-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 16px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .section-subtitle {
            color: var(--text-secondary);
            font-size: 1.125rem;
            margin-bottom: 40px;
        }

        /* Cards */
        .card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        }

        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 12px;
        }

        /* Severity Badges */
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .badge-high { background: var(--danger); }
        .badge-medium { background: var(--warning); color: #000; }
        .badge-low { background: var(--accent); }

        /* Charts Container */
        .chart-container {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }

        .chart-title {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 16px;
            text-align: center;
        }

        /* Score Circles */
        .score-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 24px;
            margin-bottom: 40px;
        }

        .score-circle {
            text-align: center;
        }

        .score-ring {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: conic-gradient(var(--primary) var(--score-percent), rgba(255,255,255,0.1) 0);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 12px;
            position: relative;
        }

        .score-ring::before {
            content: '';
            position: absolute;
            width: 80px;
            height: 80px;
            background: var(--bg-dark);
            border-radius: 50%;
        }

        .score-value {
            position: relative;
            font-size: 1.5rem;
            font-weight: 700;
        }

        .score-label {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        /* Toggle Buttons */
        .toggle-group {
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
            background: rgba(255, 255, 255, 0.05);
            padding: 4px;
            border-radius: 8px;
            width: fit-content;
        }

        .toggle-btn {
            padding: 10px 24px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.2s;
        }

        .toggle-btn.active {
            background: var(--primary);
            color: white;
        }

        /* Recommendations */
        .recommendation {
            display: flex;
            gap: 16px;
            padding: 20px;
            background: var(--bg-card);
            border-radius: 12px;
            margin-bottom: 16px;
            border-left: 4px solid var(--primary);
        }

        .recommendation-icon {
            font-size: 1.5rem;
        }

        .recommendation-content {
            flex: 1;
        }

        .recommendation-title {
            font-weight: 600;
            margin-bottom: 8px;
        }

        .recommendation-meta {
            display: flex;
            gap: 16px;
            margin-top: 12px;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        /* Issues List */
        .issue-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            border-left: 4px solid var(--danger);
        }

        .issue-card.medium { border-left-color: var(--warning); }
        .issue-card.low { border-left-color: var(--accent); }

        .issue-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }

        .issue-category {
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Expandable Sections */
        .expandable {
            cursor: pointer;
        }

        .expandable-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }

        .expandable.open .expandable-content {
            max-height: 1000px;
        }

        .expand-icon {
            transition: transform 0.3s;
        }

        .expandable.open .expand-icon {
            transform: rotate(180deg);
        }

        /* Animations */
        .fade-in-up {
            opacity: 0;
            transform: translateY(30px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }

        .fade-in-up.visible {
            opacity: 1;
            transform: translateY(0);
        }

        /* Counter Animation */
        @keyframes countUp {
            from { opacity: 0; transform: scale(0.5); }
            to { opacity: 1; transform: scale(1); }
        }

        .animate-count {
            animation: countUp 0.6s ease forwards;
        }

        /* Print Styles */
        @media print {
            .nav-sticky { display: none; }
            .no-print { display: none; }
            body { background: white; color: black; }
            .section { padding: 40px 20px; }
            .page-break { page-break-before: always; }
        }

        /* Responsive */
        @media (max-width: 768px) {
            .report-header { padding: 60px 20px; }
            .report-header h1 { font-size: 2rem; }
            .section { padding: 40px 20px; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .nav-links { flex-wrap: wrap; gap: 16px; }
        }
        '''

    def _get_base_js(self) -> str:
        """Get base JavaScript."""
        return '''
        // Intersection Observer for fade-in animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, observerOptions);

        document.querySelectorAll('.fade-in-up').forEach(el => observer.observe(el));

        // Animated counter
        function animateCounter(el, target, duration = 1500) {
            const start = 0;
            const startTime = performance.now();

            function update(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3);
                const current = Math.floor(start + (target - start) * eased);
                el.textContent = current.toLocaleString();

                if (progress < 1) {
                    requestAnimationFrame(update);
                }
            }

            requestAnimationFrame(update);
        }

        // Initialize counters when visible
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const target = parseInt(entry.target.dataset.target);
                    animateCounter(entry.target, target);
                    counterObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        document.querySelectorAll('[data-counter]').forEach(el => counterObserver.observe(el));

        // Toggle functionality
        function toggleView(btn, viewId) {
            // Update buttons
            btn.closest('.toggle-group').querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update views
            const container = document.getElementById(viewId + '-container');
            container.querySelectorAll('.toggle-view').forEach(v => v.style.display = 'none');
            document.getElementById(viewId).style.display = 'block';
        }

        // Expandable sections
        document.querySelectorAll('.expandable').forEach(el => {
            el.querySelector('.expandable-header')?.addEventListener('click', () => {
                el.classList.toggle('open');
            });
        });

        // Smooth scroll for nav links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
        '''

    def _get_optimization_template(self, css: str, js: str) -> str:
        """Get optimization analysis template."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{{{ data.client_name }}}} - Optimization Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>{css}</style>
</head>
<body>
    <!-- Header -->
    <header class="report-header">
        <h1>Optimization Analysis</h1>
        <p class="tagline">{{{{ data.client_name }}}} | {{{{ data.url }}}}</p>

        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-number" data-counter data-target="{{{{ data.scores.overall or 0 }}}}">0</span>
                <span class="stat-label">Overall Score</span>
            </div>
            <div class="stat-card">
                <span class="stat-number" data-counter data-target="{{{{ data.issues|length }}}}">0</span>
                <span class="stat-label">Issues Found</span>
            </div>
            <div class="stat-card">
                <span class="stat-number" data-counter data-target="{{{{ data.recommendations|length }}}}">0</span>
                <span class="stat-label">Recommendations</span>
            </div>
        </div>
    </header>

    <!-- Navigation -->
    <nav class="nav-sticky">
        <ul class="nav-links">
            <li><a href="#scores">Scores</a></li>
            <li><a href="#funnel">User Funnel</a></li>
            <li><a href="#issues">Issues</a></li>
            <li><a href="#recommendations">Recommendations</a></li>
        </ul>
    </nav>

    <!-- Scores Section -->
    <section id="scores" class="section">
        <h2 class="section-title fade-in-up">Performance Scores</h2>
        <p class="section-subtitle fade-in-up">Comprehensive analysis across key metrics</p>

        <div class="score-grid fade-in-up">
            {{% for metric, score in data.scores.items() %}}
            <div class="score-circle">
                <div class="score-ring" style="--score-percent: {{{{ score }}}}%">
                    <span class="score-value">{{{{ score }}}}</span>
                </div>
                <span class="score-label">{{{{ metric|replace('_', ' ')|title }}}}</span>
            </div>
            {{% endfor %}}
        </div>

        <div class="chart-container fade-in-up">
            <h3 class="chart-title">Score Breakdown</h3>
            <canvas id="scoresChart" height="200"></canvas>
        </div>
    </section>

    <!-- Funnel Section -->
    {{% if data.funnel %}}
    <section id="funnel" class="section">
        <h2 class="section-title fade-in-up">User Conversion Funnel</h2>
        <p class="section-subtitle fade-in-up">Track where users drop off in your flow</p>

        <div class="chart-container fade-in-up">
            <canvas id="funnelChart" height="300"></canvas>
        </div>
    </section>
    {{% endif %}}

    <!-- Issues Section -->
    <section id="issues" class="section">
        <h2 class="section-title fade-in-up">Issues Found</h2>
        <p class="section-subtitle fade-in-up">Prioritized list of improvements</p>

        {{% for issue in data.issues %}}
        <div class="issue-card {{{{ issue.severity }}}} fade-in-up">
            <div class="issue-header">
                <div>
                    <span class="issue-category">{{{{ issue.category }}}}</span>
                    <h3 class="card-title">{{{{ issue.title }}}}</h3>
                </div>
                <span class="badge badge-{{{{ issue.severity }}}}">{{{{ issue.severity }}}}</span>
            </div>
            <p>{{{{ issue.description }}}}</p>
            {{% if issue.recommendation %}}
            <div class="recommendation-meta">
                <span>💡 {{{{ issue.recommendation }}}}</span>
            </div>
            {{% endif %}}
        </div>
        {{% endfor %}}
    </section>

    <!-- Recommendations Section -->
    <section id="recommendations" class="section">
        <h2 class="section-title fade-in-up">Recommendations</h2>
        <p class="section-subtitle fade-in-up">Prioritized actions to improve your application</p>

        {{% for rec in data.recommendations %}}
        <div class="recommendation fade-in-up">
            <span class="recommendation-icon">
                {{% if rec.impact == 'high' %}}🚀{{% elif rec.impact == 'medium' %}}⚡{{% else %}}✨{{% endif %}}
            </span>
            <div class="recommendation-content">
                <h3 class="recommendation-title">{{{{ rec.title }}}}</h3>
                <p>{{{{ rec.description }}}}</p>
                <div class="recommendation-meta">
                    <span>Impact: <strong>{{{{ rec.impact|title }}}}</strong></span>
                    <span>Effort: <strong>{{{{ rec.effort|title }}}}</strong></span>
                </div>
            </div>
        </div>
        {{% endfor %}}
    </section>

    <!-- Footer -->
    <footer class="section" style="text-align: center; padding: 40px;">
        <p style="color: var(--text-secondary);">
            Generated by Code Weaver Pro | {{{{ generated_at }}}}
        </p>
    </footer>

    <script>
        {js}

        // Initialize Charts
        document.addEventListener('DOMContentLoaded', function() {{
            // Scores Chart
            const scoresCtx = document.getElementById('scoresChart');
            if (scoresCtx) {{
                const scoresData = {{{{ data.scores | tojson }}}};
                new Chart(scoresCtx, {{
                    type: 'bar',
                    data: {{
                        labels: Object.keys(scoresData).map(k => k.replace('_', ' ').replace(/\\b\\w/g, l => l.toUpperCase())),
                        datasets: [{{
                            label: 'Score',
                            data: Object.values(scoresData),
                            backgroundColor: Object.values(scoresData).map(v =>
                                v >= 80 ? '#10b981' : v >= 60 ? '#f59e0b' : '#ef4444'
                            ),
                            borderRadius: 8,
                        }}]
                    }},
                    options: {{
                        indexAxis: 'y',
                        scales: {{
                            x: {{ max: 100, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
                            y: {{ grid: {{ display: false }} }}
                        }},
                        plugins: {{
                            legend: {{ display: false }},
                            tooltip: {{
                                callbacks: {{
                                    label: (ctx) => ctx.raw + '/100'
                                }}
                            }}
                        }}
                    }}
                }});
            }}

            // Funnel Chart
            const funnelCtx = document.getElementById('funnelChart');
            if (funnelCtx) {{
                const funnelData = {{{{ data.funnel | tojson }}}};
                new Chart(funnelCtx, {{
                    type: 'bar',
                    data: {{
                        labels: funnelData.labels,
                        datasets: [{{
                            label: 'Users',
                            data: funnelData.values,
                            backgroundColor: ['#8B5CF6', '#10B981', '#F59E0B', '#EF4444', '#3B82F6'],
                            borderRadius: 8,
                        }}]
                    }},
                    options: {{
                        scales: {{
                            y: {{ beginAtZero: true, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
                            x: {{ grid: {{ display: false }} }}
                        }},
                        plugins: {{
                            legend: {{ display: false }},
                            tooltip: {{
                                callbacks: {{
                                    label: (ctx) => ctx.raw.toLocaleString() + ' users'
                                }}
                            }}
                        }}
                    }}
                }});
            }}
        }});
    </script>
</body>
</html>'''

    def _get_new_app_template(self, css: str, js: str) -> str:
        """Get new app concept template."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{{{ data.project_name }}}} - App Concept</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        {css}

        .persona-card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }}

        .persona-header {{
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 16px;
        }}

        .persona-avatar {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }}

        .feature-priority {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .priority-must_have {{ background: var(--danger); }}
        .priority-should_have {{ background: var(--warning); color: #000; }}
        .priority-nice_to_have {{ background: var(--accent); }}

        .timeline-phase {{
            display: flex;
            gap: 24px;
            padding: 24px;
            background: var(--bg-card);
            border-radius: 12px;
            margin-bottom: 16px;
            border-left: 4px solid var(--primary);
        }}

        .phase-number {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: var(--primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            font-weight: 700;
            flex-shrink: 0;
        }}

        .phase-content {{
            flex: 1;
        }}

        .phase-duration {{
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}

        .deliverable {{
            display: inline-block;
            background: rgba(102, 126, 234, 0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.875rem;
            margin: 4px 4px 0 0;
        }}

        .cost-breakdown {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }}

        .cost-item {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}

        .cost-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent);
        }}
    </style>
</head>
<body>
    <!-- Header -->
    <header class="report-header">
        <h1>{{{{ data.project_name }}}}</h1>
        <p class="tagline">{{{{ data.tagline }}}}</p>

        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-number">{{{{ data.market_analysis.market_size }}}}</span>
                <span class="stat-label">Market Size</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{{{{ data.market_analysis.growth_rate }}}}</span>
                <span class="stat-label">Growth Rate</span>
            </div>
            <div class="stat-card">
                <span class="stat-number" data-counter data-target="{{{{ data.proposed_features|length }}}}">0</span>
                <span class="stat-label">Features</span>
            </div>
        </div>
    </header>

    <!-- Navigation -->
    <nav class="nav-sticky">
        <ul class="nav-links">
            <li><a href="#market">Market</a></li>
            <li><a href="#personas">Users</a></li>
            <li><a href="#features">Features</a></li>
            <li><a href="#timeline">Timeline</a></li>
            <li><a href="#cost">Investment</a></li>
        </ul>
    </nav>

    <!-- Market Analysis -->
    <section id="market" class="section">
        <h2 class="section-title fade-in-up">Market Analysis</h2>
        <p class="section-subtitle fade-in-up">Understanding the competitive landscape</p>

        <div class="chart-container fade-in-up">
            <h3 class="chart-title">Competitive Landscape</h3>
            <canvas id="competitorChart" height="200"></canvas>
        </div>

        <h3 class="card-title fade-in-up" style="margin-top: 40px; margin-bottom: 24px;">Key Competitors</h3>
        {{% for comp in data.market_analysis.competitors %}}
        <div class="card fade-in-up">
            <h4 class="card-title">{{{{ comp.name }}}}</h4>
            <p><strong style="color: var(--accent);">Strength:</strong> {{{{ comp.strength }}}}</p>
            <p><strong style="color: var(--danger);">Weakness:</strong> {{{{ comp.weakness }}}}</p>
        </div>
        {{% endfor %}}
    </section>

    <!-- User Personas -->
    <section id="personas" class="section">
        <h2 class="section-title fade-in-up">Target Users</h2>
        <p class="section-subtitle fade-in-up">Understanding who we're building for</p>

        {{% for persona in data.user_personas %}}
        <div class="persona-card fade-in-up">
            <div class="persona-header">
                <div class="persona-avatar">👤</div>
                <div>
                    <h3 class="card-title" style="margin: 0;">{{{{ persona.name }}}}</h3>
                    <p style="color: var(--text-secondary); margin: 0;">{{{{ persona.role }}}}</p>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
                <div>
                    <h4 style="color: var(--accent); margin-bottom: 8px;">Goals</h4>
                    <ul style="margin: 0; padding-left: 20px;">
                        {{% for goal in persona.goals %}}<li>{{{{ goal }}}}</li>{{% endfor %}}
                    </ul>
                </div>
                <div>
                    <h4 style="color: var(--danger); margin-bottom: 8px;">Pain Points</h4>
                    <ul style="margin: 0; padding-left: 20px;">
                        {{% for pain in persona.pain_points %}}<li>{{{{ pain }}}}</li>{{% endfor %}}
                    </ul>
                </div>
            </div>
        </div>
        {{% endfor %}}
    </section>

    <!-- Features -->
    <section id="features" class="section">
        <h2 class="section-title fade-in-up">Proposed Features</h2>
        <p class="section-subtitle fade-in-up">Prioritized feature roadmap</p>

        {{% for feature in data.proposed_features %}}
        <div class="card fade-in-up">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h3 class="card-title">{{{{ feature.name }}}}</h3>
                    <p>{{{{ feature.description }}}}</p>
                </div>
                <span class="feature-priority priority-{{{{ feature.priority }}}}">{{{{ feature.priority|replace('_', ' ')|title }}}}</span>
            </div>
        </div>
        {{% endfor %}}
    </section>

    <!-- Timeline -->
    <section id="timeline" class="section">
        <h2 class="section-title fade-in-up">Development Timeline</h2>
        <p class="section-subtitle fade-in-up">Phased approach to delivery</p>

        {{% for phase in data.timeline.phases %}}
        <div class="timeline-phase fade-in-up">
            <div class="phase-number">{{{{ loop.index }}}}</div>
            <div class="phase-content">
                <h3 class="card-title" style="margin-bottom: 4px;">{{{{ phase.name }}}}</h3>
                <p class="phase-duration">Duration: {{{{ phase.duration }}}}</p>
                <div style="margin-top: 12px;">
                    {{% for d in phase.deliverables %}}<span class="deliverable">{{{{ d }}}}</span>{{% endfor %}}
                </div>
            </div>
        </div>
        {{% endfor %}}
    </section>

    <!-- Cost Estimate -->
    <section id="cost" class="section">
        <h2 class="section-title fade-in-up">Investment Estimate</h2>
        <p class="section-subtitle fade-in-up">Transparent cost breakdown</p>

        <div class="card fade-in-up" style="text-align: center; padding: 40px;">
            <h3 style="color: var(--text-secondary); margin-bottom: 8px;">Total Investment</h3>
            <p style="font-size: 3rem; font-weight: 700; background: linear-gradient(135deg, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                {{{{ data.cost_estimate.total }}}}
            </p>
        </div>

        <div class="cost-breakdown fade-in-up">
            {{% for item in data.cost_estimate.breakdown %}}
            <div class="cost-item">
                <p style="color: var(--text-secondary); margin-bottom: 8px;">{{{{ item.item }}}}</p>
                <p class="cost-value">{{{{ item.cost }}}}</p>
            </div>
            {{% endfor %}}
        </div>
    </section>

    <!-- Footer -->
    <footer class="section" style="text-align: center; padding: 40px;">
        <p style="color: var(--text-secondary);">
            Generated by Code Weaver Pro | {{{{ generated_at }}}}
        </p>
    </footer>

    <script>
        {js}

        // Competitor Chart
        document.addEventListener('DOMContentLoaded', function() {{
            const ctx = document.getElementById('competitorChart');
            if (ctx) {{
                const competitors = {{{{ data.market_analysis.competitors | tojson }}}};
                new Chart(ctx, {{
                    type: 'radar',
                    data: {{
                        labels: ['Market Share', 'Features', 'UX', 'Pricing', 'Support'],
                        datasets: competitors.map((c, i) => ({{
                            label: c.name,
                            data: [Math.random() * 40 + 60, Math.random() * 40 + 60, Math.random() * 40 + 60, Math.random() * 40 + 60, Math.random() * 40 + 60],
                            borderColor: ['#667eea', '#10b981', '#f59e0b'][i],
                            backgroundColor: ['rgba(102, 126, 234, 0.2)', 'rgba(16, 185, 129, 0.2)', 'rgba(245, 158, 11, 0.2)'][i],
                        }}))
                    }},
                    options: {{
                        scales: {{
                            r: {{
                                beginAtZero: true,
                                max: 100,
                                grid: {{ color: 'rgba(255,255,255,0.1)' }},
                                angleLines: {{ color: 'rgba(255,255,255,0.1)' }},
                                pointLabels: {{ color: '#fff' }}
                            }}
                        }},
                        plugins: {{
                            legend: {{ labels: {{ color: '#fff' }} }}
                        }}
                    }}
                }});
            }}
        }});
    </script>
</body>
</html>'''

    def _get_modernization_template(self, css: str, js: str) -> str:
        """Get modernization audit template."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{{{ data.system_name }}}} - Modernization Audit</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        {css}

        .tech-stack {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 12px;
        }}

        .tech-badge {{
            background: rgba(102, 126, 234, 0.2);
            border: 1px solid var(--primary);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.875rem;
        }}

        .tech-badge.old {{
            background: rgba(239, 68, 68, 0.2);
            border-color: var(--danger);
        }}

        .tech-badge.new {{
            background: rgba(16, 185, 129, 0.2);
            border-color: var(--accent);
        }}

        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 40px;
        }}

        .comparison-card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 24px;
        }}

        .comparison-card.before {{
            border-left: 4px solid var(--danger);
        }}

        .comparison-card.after {{
            border-left: 4px solid var(--accent);
        }}

        .improvement-badge {{
            display: inline-block;
            background: var(--accent);
            color: #000;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-left: 8px;
        }}

        .debt-meter {{
            height: 24px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            overflow: hidden;
            margin: 16px 0;
        }}

        .debt-fill {{
            height: 100%;
            border-radius: 12px;
            transition: width 1s ease;
        }}

        .roadmap-phase {{
            position: relative;
            padding: 24px;
            padding-left: 60px;
            margin-bottom: 24px;
        }}

        .roadmap-phase::before {{
            content: '';
            position: absolute;
            left: 20px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(to bottom, var(--primary), var(--secondary));
        }}

        .phase-marker {{
            position: absolute;
            left: 8px;
            top: 24px;
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: var(--primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.875rem;
        }}

        .risk-tag {{
            display: inline-block;
            background: rgba(239, 68, 68, 0.2);
            color: var(--danger);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            margin: 4px 4px 0 0;
        }}
    </style>
</head>
<body>
    <!-- Header -->
    <header class="report-header">
        <h1>Modernization Audit</h1>
        <p class="tagline">{{{{ data.system_name }}}} | {{{{ data.client_name }}}}</p>

        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-number" style="color: {{{{ '#ef4444' if data.tech_debt.score < 50 else '#f59e0b' if data.tech_debt.score < 75 else '#10b981' }}}}">{{{{ data.tech_debt.score }}}}</span>
                <span class="stat-label">Health Score</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{{{{ data.roi_projection.projected_savings }}}}</span>
                <span class="stat-label">Monthly Savings</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{{{{ data.roi_projection.payback_period }}}}</span>
                <span class="stat-label">Payback Period</span>
            </div>
        </div>
    </header>

    <!-- Navigation -->
    <nav class="nav-sticky">
        <ul class="nav-links">
            <li><a href="#stack">Tech Stack</a></li>
            <li><a href="#debt">Tech Debt</a></li>
            <li><a href="#comparison">Before/After</a></li>
            <li><a href="#roadmap">Roadmap</a></li>
            <li><a href="#roi">ROI</a></li>
        </ul>
    </nav>

    <!-- Tech Stack -->
    <section id="stack" class="section">
        <h2 class="section-title fade-in-up">Technology Stack</h2>
        <p class="section-subtitle fade-in-up">Current vs Proposed Architecture</p>

        <div class="toggle-group fade-in-up">
            <button class="toggle-btn active" onclick="toggleView(this, 'current-stack')">Current Stack</button>
            <button class="toggle-btn" onclick="toggleView(this, 'proposed-stack')">Proposed Stack</button>
        </div>

        <div id="stack-container">
            <div id="current-stack" class="toggle-view card fade-in-up">
                <h3 class="card-title" style="color: var(--danger);">Current Stack (Legacy)</h3>
                <div class="tech-stack">
                    {{% for tech in data.current_stack %}}<span class="tech-badge old">{{{{ tech }}}}</span>{{% endfor %}}
                </div>
            </div>
            <div id="proposed-stack" class="toggle-view card fade-in-up" style="display: none;">
                <h3 class="card-title" style="color: var(--accent);">Proposed Stack (Modern)</h3>
                <div class="tech-stack">
                    {{% for tech in data.proposed_stack %}}<span class="tech-badge new">{{{{ tech }}}}</span>{{% endfor %}}
                </div>
            </div>
        </div>
    </section>

    <!-- Tech Debt -->
    <section id="debt" class="section">
        <h2 class="section-title fade-in-up">Technical Debt Analysis</h2>
        <p class="section-subtitle fade-in-up">Understanding the current system health</p>

        <div class="card fade-in-up">
            <h3 class="card-title">System Health Score</h3>
            <div class="debt-meter">
                <div class="debt-fill" style="width: {{{{ data.tech_debt.score }}}}%; background: linear-gradient(90deg, var(--danger), var(--warning), var(--accent));"></div>
            </div>
            <p style="text-align: center; font-size: 2rem; font-weight: 700;">{{{{ data.tech_debt.score }}}}/100</p>
        </div>

        {{% for category in data.tech_debt.categories %}}
        <div class="issue-card {{{{ category.severity }}}} fade-in-up">
            <div class="issue-header">
                <h3 class="card-title">{{{{ category.name }}}}</h3>
                <span class="badge badge-{{{{ 'high' if category.severity == 'critical' else category.severity }}}}">{{{{ category.severity }}}}</span>
            </div>
            <ul style="margin: 0; padding-left: 20px;">
                {{% for issue in category.issues %}}<li>{{{{ issue }}}}</li>{{% endfor %}}
            </ul>
        </div>
        {{% endfor %}}
    </section>

    <!-- Before/After Comparison -->
    <section id="comparison" class="section">
        <h2 class="section-title fade-in-up">Before & After</h2>
        <p class="section-subtitle fade-in-up">Expected improvements after modernization</p>

        {{% for comp in data.before_after %}}
        <div class="card fade-in-up">
            <h3 class="card-title">{{{{ comp.area }}}}<span class="improvement-badge">{{{{ comp.improvement }}}}</span></h3>
            <div class="comparison-grid" style="margin-top: 16px;">
                <div class="comparison-card before">
                    <span style="color: var(--danger); font-weight: 600;">Before</span>
                    <p style="font-size: 1.5rem; font-weight: 700; margin-top: 8px;">{{{{ comp.before }}}}</p>
                </div>
                <div class="comparison-card after">
                    <span style="color: var(--accent); font-weight: 600;">After</span>
                    <p style="font-size: 1.5rem; font-weight: 700; margin-top: 8px;">{{{{ comp.after }}}}</p>
                </div>
            </div>
        </div>
        {{% endfor %}}
    </section>

    <!-- Migration Roadmap -->
    <section id="roadmap" class="section">
        <h2 class="section-title fade-in-up">Migration Roadmap</h2>
        <p class="section-subtitle fade-in-up">Phased approach to modernization</p>

        {{% for phase in data.migration_roadmap.phases %}}
        <div class="roadmap-phase fade-in-up">
            <div class="phase-marker">{{{{ loop.index }}}}</div>
            <div class="card" style="margin: 0;">
                <h3 class="card-title">{{{{ phase.name }}}}</h3>
                <p style="color: var(--text-secondary);">Duration: {{{{ phase.duration }}}}</p>

                <h4 style="margin-top: 16px; margin-bottom: 8px; font-size: 0.875rem; color: var(--accent);">Milestones</h4>
                <ul style="margin: 0; padding-left: 20px;">
                    {{% for m in phase.milestones %}}<li>{{{{ m }}}}</li>{{% endfor %}}
                </ul>

                {{% if phase.risks %}}
                <h4 style="margin-top: 16px; margin-bottom: 8px; font-size: 0.875rem; color: var(--danger);">Risks</h4>
                <div>{{% for r in phase.risks %}}<span class="risk-tag">⚠️ {{{{ r }}}}</span>{{% endfor %}}</div>
                {{% endif %}}
            </div>
        </div>
        {{% endfor %}}
    </section>

    <!-- ROI Projection -->
    <section id="roi" class="section">
        <h2 class="section-title fade-in-up">ROI Projection</h2>
        <p class="section-subtitle fade-in-up">Financial impact of modernization</p>

        <div class="stats-grid fade-in-up" style="margin-bottom: 40px;">
            <div class="card" style="text-align: center;">
                <p style="color: var(--text-secondary);">Current Monthly Cost</p>
                <p style="font-size: 1.5rem; font-weight: 700; color: var(--danger);">{{{{ data.roi_projection.current_costs }}}}</p>
            </div>
            <div class="card" style="text-align: center;">
                <p style="color: var(--text-secondary);">Projected Savings</p>
                <p style="font-size: 1.5rem; font-weight: 700; color: var(--accent);">{{{{ data.roi_projection.projected_savings }}}}/mo</p>
            </div>
            <div class="card" style="text-align: center;">
                <p style="color: var(--text-secondary);">Payback Period</p>
                <p style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">{{{{ data.roi_projection.payback_period }}}}</p>
            </div>
        </div>

        <div class="chart-container fade-in-up">
            <h3 class="chart-title">Cost Projection Over Time</h3>
            <canvas id="roiChart" height="250"></canvas>
        </div>
    </section>

    <!-- Footer -->
    <footer class="section" style="text-align: center; padding: 40px;">
        <p style="color: var(--text-secondary);">
            Generated by Code Weaver Pro | {{{{ generated_at }}}}
        </p>
    </footer>

    <script>
        {js}

        // ROI Chart
        document.addEventListener('DOMContentLoaded', function() {{
            const ctx = document.getElementById('roiChart');
            if (ctx) {{
                const roiData = {{{{ data.roi_projection.chart_data | tojson }}}};
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: roiData.labels,
                        datasets: [
                            {{
                                label: 'Current Costs',
                                data: roiData.current,
                                borderColor: '#ef4444',
                                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                fill: true,
                                tension: 0.4,
                            }},
                            {{
                                label: 'With Modernization',
                                data: roiData.projected,
                                borderColor: '#10b981',
                                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                                fill: true,
                                tension: 0.4,
                            }}
                        ]
                    }},
                    options: {{
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                grid: {{ color: 'rgba(255,255,255,0.1)' }},
                                ticks: {{
                                    callback: (value) => '$' + value.toLocaleString()
                                }}
                            }},
                            x: {{ grid: {{ display: false }} }}
                        }},
                        plugins: {{
                            legend: {{ labels: {{ color: '#fff' }} }},
                            tooltip: {{
                                callbacks: {{
                                    label: (ctx) => ctx.dataset.label + ': $' + ctx.raw.toLocaleString()
                                }}
                            }}
                        }}
                    }}
                }});
            }}
        }});
    </script>
</body>
</html>'''

    def encode_image(self, image_path: str) -> Optional[str]:
        """
        Encode an image as base64 for embedding in HTML.

        Args:
            image_path: Path to the image file

        Returns:
            Base64-encoded data URL or None if file doesn't exist
        """
        path = Path(image_path)
        if not path.exists():
            return None

        suffix = path.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(suffix, "image/png")

        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        return f"data:{mime_type};base64,{b64}"


# Convenience functions for each report type

def generate_optimization_report(
    data: Dict[str, Any],
    output_dir: Optional[Path] = None,
    output_name: Optional[str] = None
) -> Path:
    """Generate an Optimization Analysis report."""
    generator = InteractiveReportGenerator(output_dir)
    return generator.generate(ReportType.OPTIMIZATION_ANALYSIS, data, output_name)


def generate_new_app_report(
    data: Dict[str, Any],
    output_dir: Optional[Path] = None,
    output_name: Optional[str] = None
) -> Path:
    """Generate a New App Concept report for startups."""
    generator = InteractiveReportGenerator(output_dir)
    return generator.generate(ReportType.NEW_APP_CONCEPT, data, output_name)


def generate_modernization_report(
    data: Dict[str, Any],
    output_dir: Optional[Path] = None,
    output_name: Optional[str] = None
) -> Path:
    """Generate a Modernization Audit report."""
    generator = InteractiveReportGenerator(output_dir)
    return generator.generate(ReportType.MODERNIZATION_AUDIT, data, output_name)


# Sample data generators for testing

def get_sample_optimization_data() -> Dict[str, Any]:
    """Generate sample data for an optimization report."""
    return {
        "client_name": "TechStartup Inc.",
        "url": "https://example.com",
        "scores": {
            "performance": 72,
            "accessibility": 85,
            "seo": 90,
            "best_practices": 88,
            "overall": 84
        },
        "funnel": {
            "labels": ["Visitors", "Signups", "Active Users", "Paid Customers"],
            "values": [10000, 2500, 800, 150]
        },
        "issues": [
            {
                "title": "Large Contentful Paint (LCP) too slow",
                "severity": "high",
                "category": "Performance",
                "description": "LCP is 4.2s, which exceeds the recommended 2.5s threshold",
                "recommendation": "Optimize images, implement lazy loading, and consider CDN"
            },
            {
                "title": "Missing alt text on images",
                "severity": "medium",
                "category": "Accessibility",
                "description": "12 images are missing alt text attributes",
                "recommendation": "Add descriptive alt text to all images"
            },
            {
                "title": "Touch targets too small on mobile",
                "severity": "medium",
                "category": "Mobile UX",
                "description": "Several buttons are smaller than 44x44px",
                "recommendation": "Increase button sizes to meet WCAG guidelines"
            }
        ],
        "screenshots": {
            "desktop": None,
            "mobile": None,
            "tablet": None
        },
        "recommendations": [
            {
                "title": "Implement Image Optimization Pipeline",
                "description": "Set up automatic image compression and WebP conversion",
                "impact": "high",
                "effort": "medium"
            },
            {
                "title": "Add Caching Headers",
                "description": "Configure proper cache-control headers for static assets",
                "impact": "medium",
                "effort": "low"
            },
            {
                "title": "Refactor CSS for Critical Path",
                "description": "Inline critical CSS and defer non-critical styles",
                "impact": "medium",
                "effort": "high"
            }
        ]
    }


def get_sample_new_app_data() -> Dict[str, Any]:
    """Generate sample data for a new app concept report."""
    return {
        "client_name": "InnovateCo",
        "project_name": "TaskFlow Pro",
        "tagline": "Streamline your team's productivity",
        "market_analysis": {
            "market_size": "$2.4B",
            "growth_rate": "15% YoY",
            "competitors": [
                {"name": "Asana", "strength": "Enterprise features", "weakness": "Complex pricing"},
                {"name": "Trello", "strength": "Simple interface", "weakness": "Limited automation"},
                {"name": "Monday.com", "strength": "Customizable", "weakness": "Learning curve"}
            ]
        },
        "user_personas": [
            {
                "name": "Project Manager Paula",
                "role": "Senior Project Manager",
                "goals": ["Track team progress", "Reduce meeting overhead", "Automate reporting"],
                "pain_points": ["Too many tools", "Manual status updates", "Poor visibility"]
            },
            {
                "name": "Developer Dave",
                "role": "Full-Stack Developer",
                "goals": ["Focus on coding", "Clear task priorities", "Quick updates"],
                "pain_points": ["Context switching", "Unclear requirements", "Notification overload"]
            }
        ],
        "proposed_features": [
            {"name": "Smart Task Assignment", "description": "AI-powered task distribution based on skills and workload", "priority": "must_have"},
            {"name": "Real-time Collaboration", "description": "Live editing and commenting on tasks", "priority": "must_have"},
            {"name": "Automated Standups", "description": "Daily progress reports generated automatically", "priority": "should_have"},
            {"name": "Integration Hub", "description": "Connect with 50+ popular tools", "priority": "should_have"},
            {"name": "Voice Commands", "description": "Create and update tasks via voice", "priority": "nice_to_have"}
        ],
        "prototype_screens": [],
        "user_flow": {
            "steps": [
                {"name": "Onboarding", "description": "Quick 3-step setup wizard"},
                {"name": "Dashboard", "description": "Personalized task overview"},
                {"name": "Task Creation", "description": "Smart form with AI suggestions"},
                {"name": "Collaboration", "description": "Real-time team interaction"},
                {"name": "Reporting", "description": "Automated insights and analytics"}
            ]
        },
        "timeline": {
            "phases": [
                {"name": "Discovery & Design", "duration": "4 weeks", "deliverables": ["User research", "Wireframes", "Design system"]},
                {"name": "MVP Development", "duration": "8 weeks", "deliverables": ["Core features", "Basic integrations", "Beta testing"]},
                {"name": "Launch & Iterate", "duration": "4 weeks", "deliverables": ["Public launch", "User feedback", "Quick wins"]}
            ]
        },
        "cost_estimate": {
            "total": "$85,000 - $120,000",
            "breakdown": [
                {"item": "Design & UX", "cost": "$15,000 - $20,000"},
                {"item": "Frontend Development", "cost": "$25,000 - $35,000"},
                {"item": "Backend Development", "cost": "$30,000 - $45,000"},
                {"item": "QA & Testing", "cost": "$10,000 - $15,000"},
                {"item": "DevOps & Launch", "cost": "$5,000 - $5,000"}
            ]
        }
    }


def get_sample_modernization_data() -> Dict[str, Any]:
    """Generate sample data for a modernization report."""
    return {
        "client_name": "LegacyCorp",
        "system_name": "Customer Portal v1.0",
        "current_stack": ["jQuery 1.x", "PHP 5.6", "MySQL 5.5", "Apache", "Monolithic architecture"],
        "proposed_stack": ["React 18", "Node.js 20", "PostgreSQL 16", "Docker/K8s", "Microservices"],
        "tech_debt": {
            "score": 35,
            "categories": [
                {
                    "name": "Security Vulnerabilities",
                    "severity": "critical",
                    "issues": ["Unsupported PHP version", "SQL injection risks", "No HTTPS enforcement"]
                },
                {
                    "name": "Performance Bottlenecks",
                    "severity": "high",
                    "issues": ["No caching layer", "Synchronous processing", "Unoptimized queries"]
                },
                {
                    "name": "Maintainability",
                    "severity": "medium",
                    "issues": ["No test coverage", "Mixed business logic", "Poor documentation"]
                }
            ]
        },
        "before_after": [
            {"area": "Page Load Time", "before": "8.5s", "after": "1.2s", "improvement": "86% faster"},
            {"area": "API Response", "before": "2.1s", "after": "120ms", "improvement": "94% faster"},
            {"area": "Uptime", "before": "97.5%", "after": "99.95%", "improvement": "2.45% increase"},
            {"area": "Deploy Frequency", "before": "Monthly", "after": "Daily", "improvement": "30x more frequent"}
        ],
        "migration_roadmap": {
            "phases": [
                {
                    "name": "Phase 1: Foundation",
                    "duration": "6 weeks",
                    "milestones": ["Set up new infrastructure", "Create API gateway", "Database migration plan"],
                    "risks": ["Data integrity during migration", "Team learning curve"]
                },
                {
                    "name": "Phase 2: Core Services",
                    "duration": "10 weeks",
                    "milestones": ["Auth microservice", "User management", "Core business logic"],
                    "risks": ["API compatibility", "Performance benchmarking"]
                },
                {
                    "name": "Phase 3: Frontend",
                    "duration": "8 weeks",
                    "milestones": ["React component library", "New UI implementation", "A/B testing"],
                    "risks": ["User adoption", "Feature parity"]
                },
                {
                    "name": "Phase 4: Cutover",
                    "duration": "4 weeks",
                    "milestones": ["Final data migration", "Traffic switch", "Legacy decommission"],
                    "risks": ["Rollback planning", "Zero-downtime switch"]
                }
            ]
        },
        "roi_projection": {
            "current_costs": "$45,000/month",
            "projected_savings": "$18,000/month",
            "payback_period": "14 months",
            "chart_data": {
                "labels": ["Q1", "Q2", "Q3", "Q4", "Q1 Y2", "Q2 Y2"],
                "current": [45000, 46000, 47000, 48000, 49000, 50000],
                "projected": [65000, 55000, 35000, 28000, 27000, 27000]
            }
        }
    }


if __name__ == "__main__":
    # Test report generation
    from pathlib import Path

    print("Generating sample interactive reports...")

    output_dir = Path("C:/Users/jacob/MultiAgentTeam/test_reports")
    generator = InteractiveReportGenerator(output_dir)

    # Generate each report type
    opt_path = generator.generate(
        ReportType.OPTIMIZATION_ANALYSIS,
        get_sample_optimization_data(),
        "sample_optimization.html"
    )
    print(f"  Optimization report: {opt_path}")

    new_app_path = generator.generate(
        ReportType.NEW_APP_CONCEPT,
        get_sample_new_app_data(),
        "sample_new_app.html"
    )
    print(f"  New App Concept report: {new_app_path}")

    mod_path = generator.generate(
        ReportType.MODERNIZATION_AUDIT,
        get_sample_modernization_data(),
        "sample_modernization.html"
    )
    print(f"  Modernization report: {mod_path}")

    print(f"\nDone! Open the HTML files in a browser to preview:")
    print(f"  file:///{output_dir.as_posix()}")
