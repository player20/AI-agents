#!/usr/bin/env python3
"""
Weaver Pro CLI - Audit, Optimize, Build

Usage:
    weaver audit <url>                    # Quick audit
    weaver audit <url> --full             # Comprehensive audit
    weaver audit <url> -f html -o ./out   # HTML report output
"""

import click
import json
import asyncio
import sys
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

# Version
__version__ = "1.0.0"


def validate_url(url: str) -> tuple[bool, str]:
    """
    Validate URL format and return (is_valid, error_message).
    Returns (True, "") if valid, (False, "error message") if invalid.
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"

    url = url.strip()

    # Check for valid URL scheme
    if not url.startswith(('http://', 'https://')):
        return False, "URL must start with http:// or https://"

    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return False, "URL must include a domain (e.g., example.com)"

        # Basic domain validation
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$', parsed.netloc.split(':')[0]):
            return False, f"Invalid domain: {parsed.netloc}"

        return True, ""
    except Exception as e:
        return False, f"Invalid URL format: {str(e)[:50]}"


def get_timestamp():
    """Get ISO timestamp for filenames"""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _has_valid_metrics(analytics_data) -> bool:
    """Check if analytics data has valid metrics (no error key)"""
    if not analytics_data:
        return False
    metrics = getattr(analytics_data, 'metrics', {})
    return 'error' not in metrics and bool(metrics)


def calculate_confidence(analytics_data, full_mode: bool, user_count: int) -> dict:
    """
    Calculate confidence level based on data sources.

    Returns dict with score (0-100), level (High/Medium/Low/Very Low),
    color (green/yellow/orange/red), and has_real_data flag.
    """
    confidence = 40  # Base: simulation only
    has_valid_data = _has_valid_metrics(analytics_data)

    # Boost from real data sources (only if metrics are valid)
    if analytics_data and has_valid_data:
        source_boosts = {
            'lighthouse': 35,
            'ga4': 30,
            'search_console': 20,
            'firebase': 20,
        }
        confidence += source_boosts.get(analytics_data.source, 10)

    # Boost from audit configuration
    if full_mode:
        confidence += 10
    if user_count >= 5:
        confidence += 5

    confidence = min(100, confidence)  # Cap at 100%

    # Determine level and color
    if confidence >= 85:
        level, color = "High", "green"
    elif confidence >= 65:
        level, color = "Medium", "yellow"
    elif confidence >= 40:
        level, color = "Low", "orange"
    else:
        level, color = "Very Low", "red"

    return {
        "score": confidence,
        "level": level,
        "color": color,
        "has_real_data": has_valid_data
    }


@click.group()
@click.version_option(version=__version__, prog_name="weaver")
def cli():
    """Weaver Pro - Audit, Optimize, Build platforms"""
    pass


@cli.command()
@click.argument("url")
@click.option("--output", "-o", type=click.Path(), default="./weaver-output",
              help="Output directory for results")
@click.option("--format", "-f", "output_format",
              type=click.Choice(["json", "html", "pdf"]), default="json",
              help="Output format (default: json)")
@click.option("--full", is_flag=True,
              help="Run comprehensive audit (includes screenshots, accessibility)")
@click.option("--users", "-u", type=int, default=3,
              help="Number of simulated user sessions (default: 3)")
@click.option("--analytics", "-a", type=click.Path(exists=True),
              help="Path to analytics export (GA4 CSV, Lighthouse JSON, Firebase JSON)")
@click.option("--quiet", "-q", is_flag=True,
              help="Minimal output (just results)")
def audit(url, output, output_format, full, users, analytics, quiet):
    """
    Audit a web application for issues and opportunities.

    Examples:
        weaver audit https://example.com
        weaver audit https://myapp.com --full -f html -o ./reports
        weaver audit https://myapp.com -a ./ga4-export.csv
        weaver audit https://myapp.com -a ./lighthouse-report.json
    """
    # Validate URL first
    is_valid, error_msg = validate_url(url)
    if not is_valid:
        click.echo(f"[ERROR] {error_msg}", err=True)
        click.echo("Usage: weaver audit <url>", err=True)
        click.echo("Example: weaver audit https://example.com", err=True)
        sys.exit(1)

    # Lazy imports for faster startup
    from core.audit_mode import AuditModeAnalyzer

    if not quiet:
        click.echo(f"\n{'='*60}")
        click.echo(f"  WEAVER PRO AUDIT")
        click.echo(f"  Target: {url}")
        click.echo(f"  Mode: {'Comprehensive' if full else 'Quick'}")
        click.echo(f"{'='*60}\n")

    # Create output directory
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize analyzer
    analyzer = AuditModeAnalyzer([], {})

    results = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "mode": "comprehensive" if full else "quick",
        "scores": {},
        "issues": [],
        "recommendations": [],
        "sdk_detected": [],
        "funnel_analysis": None,
        "analytics": None
    }

    # Step 0: Load analytics data if provided
    analytics_data = None
    if analytics:
        if not quiet:
            click.echo(f"Loading analytics from {analytics}...")

        try:
            from core.analytics_parser import parse_analytics_file

            with open(analytics, 'rb') as f:
                analytics_data = parse_analytics_file(f.read(), analytics)

            if analytics_data:
                results["analytics"] = analytics_data.to_dict()
                if not quiet:
                    click.echo(f"   [OK] Loaded {analytics_data.source} data")

                    # Show key metrics based on source
                    if analytics_data.source == 'ga4':
                        m = analytics_data.metrics
                        click.echo(f"   Users: {m.get('total_users', 0):,} | Sessions: {m.get('total_sessions', 0):,}")
                    elif analytics_data.source == 'lighthouse':
                        m = analytics_data.metrics
                        click.echo(f"   Performance: {m.get('performance', 0):.0f} | Accessibility: {m.get('accessibility', 0):.0f}")
                    elif analytics_data.source == 'search_console':
                        m = analytics_data.metrics
                        click.echo(f"   Clicks: {m.get('total_clicks', 0):,} | Impressions: {m.get('total_impressions', 0):,}")
            else:
                if not quiet:
                    click.echo("   [--] Unknown analytics format", err=True)

        except Exception as e:
            if not quiet:
                click.echo(f"   [!!] Failed to load analytics: {str(e)[:50]}", err=True)

    # Step 1: Crawl and analyze user flows
    if not quiet:
        click.echo(f"🔍 Crawling {url}...")

    async def crawl_with_timeout():
        """Wrapper to add timeout to crawl operation"""
        return await asyncio.wait_for(
            analyzer.crawl_app_flows(
                base_url=url,
                test_credentials=None,
                simulate_users=users
            ),
            timeout=120.0  # 2 minute timeout
        )

    try:
        sessions = asyncio.run(crawl_with_timeout())

        if not quiet:
            click.echo(f"   ✅ Simulated {len(sessions)} user sessions")

        # Analyze funnel
        funnel_analysis = analyzer.analyze_sessions(sessions)
        results["funnel_analysis"] = funnel_analysis

        completion_rate = funnel_analysis.get("completion_rate", 0)
        if not quiet:
            click.echo(f"   📊 Completion rate: {completion_rate}%")

        biggest_drop = funnel_analysis.get("biggest_drop_off", {})
        if biggest_drop.get("percentage", 0) > 30:
            if not quiet:
                click.echo(
                    f"   ⚠️  Drop-off: {biggest_drop.get('percentage', 0)}% "
                    f"at {biggest_drop.get('step', 'unknown')}"
                )

    except Exception as e:
        if not quiet:
            click.echo(f"   ❌ Crawl failed: {str(e)[:100]}", err=True)
        results["errors"] = [str(e)]

    # Step 2: Full audit (optional)
    if full:
        if not quiet:
            click.echo("\n📸 Running comprehensive checks...")

        async def capture_url_data(target_url: str) -> dict:
            """Capture screenshots and console errors from a URL using Playwright."""
            from playwright.async_api import async_playwright

            ui_results = {
                "screenshots": [],
                "console_errors": [],
                "performance_metrics": {}
            }

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                # Capture console errors
                console_errors = []
                page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

                try:
                    # Navigate and capture desktop screenshot
                    await page.goto(target_url, wait_until="networkidle", timeout=30000)
                    ui_results["screenshots"].append({
                        "viewport": "desktop",
                        "width": 1280,
                        "height": 720
                    })

                    # Mobile viewport
                    await page.set_viewport_size({"width": 375, "height": 812})
                    await page.wait_for_timeout(500)
                    ui_results["screenshots"].append({
                        "viewport": "mobile",
                        "width": 375,
                        "height": 812
                    })

                    ui_results["console_errors"] = console_errors

                except Exception as e:
                    ui_results["error"] = str(e)[:100]

                finally:
                    await browser.close()

            return ui_results

        try:
            ui_results = asyncio.run(capture_url_data(url))

            if ui_results:
                results["screenshots"] = ui_results.get("screenshots", [])
                results["console_errors"] = ui_results.get("console_errors", [])
                results["performance"] = ui_results.get("performance_metrics", {})

                if not quiet:
                    click.echo(f"   ✅ Captured {len(results.get('screenshots', []))} screenshots")
                    if results.get("console_errors"):
                        click.echo(f"   ⚠️  Found {len(results['console_errors'])} JS errors")

        except ImportError:
            if not quiet:
                click.echo("   ⚠️  Full audit requires Playwright (pip install playwright)")
        except Exception as e:
            if not quiet:
                click.echo(f"   ⚠️  Full audit partial: {str(e)[:50]}")

    # Step 3: Generate recommendations
    if not quiet:
        click.echo("\n💡 Generating recommendations...")

    try:
        recommendations = analyzer.generate_recommendations(
            results.get("funnel_analysis", {}),
            {},  # No SDK detection without code
            {}   # No code files
        )
        results["recommendations"] = recommendations

        if not quiet:
            click.echo(f"   ✅ Generated {len(recommendations)} action items")

    except Exception as e:
        if not quiet:
            click.echo(f"   ⚠️  Recommendation generation partial: {str(e)[:50]}")

    # Step 4: Calculate scores (use real data when available)
    funnel = results.get("funnel_analysis", {})

    # Default scores from simulated data
    ux_score = min(10, max(0, funnel.get("completion_rate", 50) / 10))
    performance_score = 7.0
    accessibility_score = 7.0
    seo_score = 7.0

    # Override with real analytics data when available (only if valid)
    if analytics_data and _has_valid_metrics(analytics_data):
        if analytics_data.source == 'lighthouse':
            m = analytics_data.metrics
            performance_score = m.get('performance', 70) / 10
            accessibility_score = m.get('accessibility', 70) / 10
            seo_score = m.get('seo', 70) / 10

        elif analytics_data.source == 'ga4':
            m = analytics_data.metrics
            # Calculate UX score from bounce rate and session duration
            bounce_rate = m.get('bounce_rate', 50)
            # Lower bounce rate = better UX (inverse relationship)
            bounce_score = max(0, min(10, (100 - bounce_rate) / 10))
            # Weight real data higher (70%) vs simulated (30%)
            ux_score = (ux_score * 0.3) + (bounce_score * 0.7)

        elif analytics_data.source == 'search_console':
            m = analytics_data.metrics
            # CTR and position indicate SEO health
            avg_ctr = m.get('avg_ctr', 3)
            avg_position = max(1, m.get('avg_position', 20))  # Ensure min 1
            # Position 1 = 10, Position 10 = 8, Position 50 = 1
            position_score = max(1, min(10, 10 - (avg_position - 1) / 5.5))
            ctr_score = min(10, avg_ctr * 2)  # 5% CTR = 10
            seo_score = (position_score + ctr_score) / 2

    results["scores"] = {
        "ux": round(ux_score, 1),
        "performance": round(performance_score, 1),
        "accessibility": round(accessibility_score, 1),
        "seo": round(seo_score, 1)
    }

    # Step 4b: Calculate confidence level
    results["confidence"] = calculate_confidence(analytics_data, full, users)

    # Step 5: Save results
    timestamp = get_timestamp()
    base_filename = f"audit_{timestamp}"

    if output_format == "json":
        output_file = output_path / f"{base_filename}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        if not quiet:
            click.echo(f"\n📄 Results saved: {output_file}")

    elif output_format == "html":
        output_file = output_path / f"{base_filename}.html"
        html_content = generate_html_report(results)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        if not quiet:
            click.echo(f"\n📄 Report saved: {output_file}")

    elif output_format == "pdf":
        # For now, generate HTML and note PDF requires extra deps
        output_file = output_path / f"{base_filename}.html"
        html_content = generate_html_report(results)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        if not quiet:
            click.echo(f"\n📄 Report saved: {output_file}")
            click.echo("   (PDF export coming soon - saved as HTML)")

    # Summary
    if not quiet:
        conf = results["confidence"]
        click.echo(f"\n{'='*60}")
        click.echo("  AUDIT COMPLETE")
        click.echo(f"  UX Score: {results['scores']['ux']:.1f}/10")
        click.echo(f"  Performance: {results['scores']['performance']:.1f}/10")
        click.echo(f"  Confidence: {conf['level']} ({conf['score']}%)")
        if analytics_data:
            click.echo(f"  (Scores include real {analytics_data.source.upper()} data)")
        elif conf['score'] < 65:
            click.echo("  [TIP] Add -a <file> for higher confidence with real data")
        click.echo(f"  Issues: {len(results.get('issues', []))}")
        click.echo(f"  Recommendations: {len(results.get('recommendations', []))}")
        click.echo(f"{'='*60}\n")

    # Return non-zero if critical issues found
    if results["scores"]["ux"] < 5:
        sys.exit(1)


def _generate_analytics_section(analytics: dict) -> str:
    """Generate HTML section for analytics data if present"""
    if not analytics:
        return ""

    source = analytics.get('source', 'unknown').upper()
    metrics = analytics.get('metrics', {})

    rows = ""
    if source == 'GA4':
        rows = f"""
            <p><strong>Total Users:</strong> {metrics.get('total_users', 0):,}</p>
            <p><strong>Total Sessions:</strong> {metrics.get('total_sessions', 0):,}</p>
            <p><strong>Bounce Rate:</strong> {metrics.get('bounce_rate', 0):.1f}%</p>
            <p><strong>Avg Session Duration:</strong> {metrics.get('avg_session_duration', 0):.1f}s</p>
        """
    elif source == 'LIGHTHOUSE':
        rows = f"""
            <p><strong>Performance:</strong> {metrics.get('performance', 0):.0f}/100</p>
            <p><strong>Accessibility:</strong> {metrics.get('accessibility', 0):.0f}/100</p>
            <p><strong>Best Practices:</strong> {metrics.get('best_practices', 0):.0f}/100</p>
            <p><strong>SEO:</strong> {metrics.get('seo', 0):.0f}/100</p>
            <p><strong>LCP:</strong> {metrics.get('lcp_ms', 0):.0f}ms</p>
            <p><strong>CLS:</strong> {metrics.get('cls', 0):.3f}</p>
        """
    elif source == 'SEARCH_CONSOLE':
        rows = f"""
            <p><strong>Total Clicks:</strong> {metrics.get('total_clicks', 0):,}</p>
            <p><strong>Total Impressions:</strong> {metrics.get('total_impressions', 0):,}</p>
            <p><strong>Avg CTR:</strong> {metrics.get('avg_ctr', 0):.1f}%</p>
            <p><strong>Avg Position:</strong> {metrics.get('avg_position', 0):.1f}</p>
        """
    elif source == 'FIREBASE':
        rows = f"""
            <p><strong>Total Events:</strong> {metrics.get('total_events', 0):,}</p>
            <p><strong>Unique Users:</strong> {metrics.get('user_count', 0):,}</p>
        """

    return f"""
        <div class="section">
            <h2 class="section-title">Real Analytics Data ({source})</h2>
            <div class="score-card" style="text-align: left;">
                {rows}
            </div>
        </div>
    """


def _generate_confidence_badge(confidence: dict) -> str:
    """Generate HTML confidence badge indicator"""
    if not confidence:
        return ""

    # WCAG AA compliant colors (4.5:1+ contrast on #0a0a0a background)
    colors = {
        "green": "#34d399",   # Lighter green for better contrast
        "yellow": "#fbbf24",  # Brighter yellow for 4.5:1+
        "orange": "#fb923c",  # Lighter orange for 4.5:1+
        "red": "#f87171"      # Lighter red for better contrast
    }
    icons = {
        "High": "●",
        "Medium": "●",
        "Low": "●",
        "Very Low": "●"
    }

    color = colors.get(confidence.get('color', 'orange'), '#737373')
    level = confidence.get('level', 'Low')
    score = confidence.get('score', 40)
    has_real_data = confidence.get('has_real_data', False)

    tip_text = ""
    if not has_real_data:
        tip_text = '<p style="margin: 8px 0 0 0; font-size: 0.75rem; color: #a3a3a3;">TIP: Upload GA4 or Lighthouse data for higher confidence</p>'

    return f'''
        <div class="confidence-badge" style="
            display: flex; flex-direction: column; align-items: center;
            padding: 16px 24px; border-radius: 12px;
            background: {color}25; border: 2px solid {color};
            margin-bottom: 24px; text-align: center;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.5rem; color: {color};">{icons.get(level, "●")}</span>
                <span style="color: {color}; font-weight: 700; font-size: 1.25rem;">
                    {level} Confidence
                </span>
                <span style="color: {color}; font-weight: 600; font-size: 1rem;">
                    ({score}%)
                </span>
            </div>
            {tip_text}
        </div>
    '''


def generate_html_report(results: dict) -> str:
    """Generate a simple HTML report from audit results"""
    scores = results.get("scores", {})
    recommendations = results.get("recommendations", [])
    funnel = results.get("funnel_analysis", {})

    recs_html = ""
    for i, rec in enumerate(recommendations[:10], 1):
        title = rec.get("title", rec.get("recommendation", "Recommendation"))
        priority = rec.get("priority", "medium")
        recs_html += f"""
        <div class="rec rec-{priority}">
            <span class="rec-num">{i}</span>
            <span class="rec-title">{title}</span>
            <span class="rec-priority">{priority.upper()}</span>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weaver Pro Audit Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0a0a0a;
            color: #fafafa;
            padding: 40px;
            line-height: 1.6;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{
            font-size: 2rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .subtitle {{ color: #737373; margin-bottom: 32px; }}
        .scores {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-bottom: 40px;
        }}
        .score-card {{
            background: #171717;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        .score-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
        }}
        .score-label {{ color: #a3a3a3; font-size: 0.875rem; }}
        .section {{ margin-bottom: 32px; }}
        .section-title {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 16px;
            color: #fafafa;
        }}
        .rec {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            background: #171717;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 3px solid #667eea;
        }}
        .rec-high {{ border-left-color: #ef4444; }}
        .rec-medium {{ border-left-color: #f59e0b; }}
        .rec-low {{ border-left-color: #10b981; }}
        .rec-num {{
            background: rgba(102, 126, 234, 0.2);
            color: #667eea;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .rec-title {{ flex: 1; }}
        .rec-priority {{
            font-size: 0.625rem;
            padding: 2px 8px;
            border-radius: 4px;
            background: rgba(255,255,255,0.1);
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
            color: #525252;
            font-size: 0.875rem;
            text-align: center;
        }}
        /* Focus states for keyboard accessibility */
        a:focus, button:focus {{
            outline: 2px solid #667eea;
            outline-offset: 2px;
            border-radius: 2px;
        }}
        a:focus-visible, button:focus-visible {{
            outline: 2px solid #667eea;
            outline-offset: 2px;
            border-radius: 2px;
        }}
        /* Remove outline for mouse users, keep for keyboard */
        a:focus:not(:focus-visible), button:focus:not(:focus-visible) {{
            outline: none;
        }}
        /* Interactive card hover/focus states */
        .score-card:focus-within, .rec:focus-within {{
            outline: 2px solid #667eea;
            outline-offset: 2px;
        }}
        /* Link styling */
        a {{
            color: #667eea;
            text-decoration: none;
            transition: color 0.2s ease;
        }}
        a:hover {{
            color: #764ba2;
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Weaver Pro Audit Report</h1>
        <p class="subtitle">{results.get('url', 'Unknown URL')} - {results.get('timestamp', '')[:10]}</p>

        {_generate_confidence_badge(results.get('confidence'))}

        <div class="scores">
            <div class="score-card">
                <div class="score-value">{scores.get('ux', 0):.1f}</div>
                <div class="score-label">UX Score</div>
            </div>
            <div class="score-card">
                <div class="score-value">{scores.get('performance', 0):.1f}</div>
                <div class="score-label">Performance</div>
            </div>
            <div class="score-card">
                <div class="score-value">{scores.get('accessibility', 0):.1f}</div>
                <div class="score-label">Accessibility</div>
            </div>
            <div class="score-card">
                <div class="score-value">{scores.get('seo', 0):.1f}</div>
                <div class="score-label">SEO</div>
            </div>
        </div>

        {_generate_analytics_section(results.get('analytics'))}

        <div class="section">
            <h2 class="section-title">Funnel Analysis</h2>
            <div class="score-card" style="text-align: left;">
                <p><strong>Completion Rate:</strong> {funnel.get('completion_rate', 0)}%</p>
                <p><strong>Biggest Drop-off:</strong> {funnel.get('biggest_drop_off', {}).get('step', 'N/A')} ({funnel.get('biggest_drop_off', {}).get('percentage', 0)}%)</p>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">Recommendations</h2>
            {recs_html if recs_html else '<p style="color: #737373;">No recommendations generated.</p>'}
        </div>

        <div class="footer">
            Generated by Weaver Pro CLI v{__version__}
        </div>
    </div>
</body>
</html>"""


@cli.command()
@click.argument("audit_file", type=click.Path(exists=True))
@click.option("--format", "-f", "output_format",
              type=click.Choice(["html", "pdf"]), default="html",
              help="Output format")
@click.option("--output", "-o", type=click.Path(),
              help="Output file path")
def report(audit_file, output_format, output):
    """
    Generate a report from a saved audit JSON file.

    Example:
        weaver report ./audit-2026-01-18.json -f html
    """
    with open(audit_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    if output:
        output_path = Path(output)
    else:
        output_path = Path(audit_file).with_suffix(f".{output_format}")

    if output_format == "html":
        html_content = generate_html_report(results)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        click.echo(f"📄 Report saved: {output_path}")

    elif output_format == "pdf":
        # Generate HTML for now
        html_content = generate_html_report(results)
        html_path = output_path.with_suffix(".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        click.echo(f"📄 Report saved: {html_path}")
        click.echo("   (PDF export coming soon)")


@cli.command()
def info():
    """Show system information and configuration"""
    click.echo(f"\nWeaver Pro CLI v{__version__}")
    click.echo(f"Python: {sys.version.split()[0]}")
    click.echo(f"Platform: {sys.platform}")

    # Check dependencies
    click.echo("\nDependencies:")

    deps = [
        ("click", "CLI framework"),
        ("playwright", "Browser automation"),
        ("anthropic", "Claude API"),
    ]

    for pkg, desc in deps:
        try:
            __import__(pkg)
            click.echo(f"  [OK] {pkg} - {desc}")
        except ImportError:
            click.echo(f"  [--] {pkg} - {desc} (not installed)")


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()
