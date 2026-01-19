"""
Accessibility Audit Script
Run comprehensive accessibility audits using axe-core via Playwright.

Usage:
    python accessibility_audit.py --url https://example.com --output report.html
    python accessibility_audit.py --urls urls.txt --output report.html
"""

import asyncio
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class A11yViolation:
    """Represents an accessibility violation"""
    id: str
    impact: str  # 'critical', 'serious', 'moderate', 'minor'
    description: str
    help: str
    help_url: str
    nodes: List[Dict] = field(default_factory=list)
    wcag_tags: List[str] = field(default_factory=list)


@dataclass
class A11yResult:
    """Results for a single URL"""
    url: str
    success: bool
    violations: List[A11yViolation] = field(default_factory=list)
    passes: int = 0
    incomplete: int = 0
    inapplicable: int = 0
    error: Optional[str] = None


class AccessibilityAuditor:
    """Run accessibility audits using axe-core"""

    # axe-core injection script
    AXE_CORE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.3/axe.min.js"

    # WCAG success criteria explanations
    WCAG_EXPLANATIONS = {
        'wcag2a': 'WCAG 2.0 Level A (Minimum)',
        'wcag2aa': 'WCAG 2.0 Level AA (Recommended)',
        'wcag2aaa': 'WCAG 2.0 Level AAA (Enhanced)',
        'wcag21a': 'WCAG 2.1 Level A',
        'wcag21aa': 'WCAG 2.1 Level AA',
        'wcag22aa': 'WCAG 2.2 Level AA',
        'best-practice': 'Best Practice (not WCAG)',
    }

    # Business impact descriptions
    IMPACT_BUSINESS = {
        'critical': {
            'description': 'Completely blocks access for some users',
            'affected': 'Users cannot complete critical tasks',
            'legal_risk': 'High - likely ADA/WCAG lawsuit risk',
            'priority': 'Fix immediately'
        },
        'serious': {
            'description': 'Causes significant difficulty',
            'affected': 'Users struggle to use features',
            'legal_risk': 'Medium - potential compliance issues',
            'priority': 'Fix within 1-2 weeks'
        },
        'moderate': {
            'description': 'Creates inconvenience',
            'affected': 'Some users need workarounds',
            'legal_risk': 'Low - should address',
            'priority': 'Fix within 1 month'
        },
        'minor': {
            'description': 'Slight inconvenience',
            'affected': 'Minor usability impact',
            'legal_risk': 'Minimal',
            'priority': 'Fix when convenient'
        }
    }

    def __init__(self, output_dir: str = "a11y_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results: List[A11yResult] = []

    async def audit_url(self, url: str, take_screenshot: bool = True) -> A11yResult:
        """Run accessibility audit on a single URL"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("Playwright not installed. Install with: pip install playwright && playwright install")
            return A11yResult(url=url, success=False, error="Playwright not installed")

        print(f"  Auditing: {url}")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720}
                )
                page = await context.new_page()

                # Navigate to URL
                await page.goto(url, wait_until='networkidle', timeout=30000)

                # Take screenshot
                if take_screenshot:
                    safe_url = url.replace('https://', '').replace('http://', '').replace('/', '_')[:50]
                    screenshot_path = self.output_dir / f"{safe_url}.png"
                    await page.screenshot(path=str(screenshot_path), full_page=True)

                # Inject axe-core
                await page.add_script_tag(url=self.AXE_CORE_CDN)
                await asyncio.sleep(0.5)  # Wait for axe to load

                # Run axe-core analysis
                axe_results = await page.evaluate("""
                    async () => {
                        try {
                            const results = await axe.run();
                            return {
                                violations: results.violations,
                                passes: results.passes.length,
                                incomplete: results.incomplete.length,
                                inapplicable: results.inapplicable.length
                            };
                        } catch (e) {
                            return { error: e.message };
                        }
                    }
                """)

                await browser.close()

                if 'error' in axe_results:
                    return A11yResult(url=url, success=False, error=axe_results['error'])

                # Parse violations
                violations = []
                for v in axe_results.get('violations', []):
                    wcag_tags = [t for t in v.get('tags', []) if 'wcag' in t or 'best-practice' in t]

                    violations.append(A11yViolation(
                        id=v['id'],
                        impact=v.get('impact', 'moderate'),
                        description=v['description'],
                        help=v['help'],
                        help_url=v['helpUrl'],
                        nodes=[{
                            'html': node.get('html', '')[:200],
                            'target': node.get('target', []),
                            'failure_summary': node.get('failureSummary', '')
                        } for node in v.get('nodes', [])[:5]],  # Limit nodes
                        wcag_tags=wcag_tags
                    ))

                return A11yResult(
                    url=url,
                    success=True,
                    violations=violations,
                    passes=axe_results.get('passes', 0),
                    incomplete=axe_results.get('incomplete', 0),
                    inapplicable=axe_results.get('inapplicable', 0)
                )

        except Exception as e:
            return A11yResult(url=url, success=False, error=str(e))

    async def audit_batch(self, urls: List[str], concurrency: int = 2) -> List[A11yResult]:
        """Audit multiple URLs with concurrency limit"""
        print(f"\nRunning accessibility audits on {len(urls)} URLs...")
        print("-" * 50)

        semaphore = asyncio.Semaphore(concurrency)

        async def limited_audit(url):
            async with semaphore:
                return await self.audit_url(url)

        tasks = [limited_audit(url) for url in urls]
        self.results = await asyncio.gather(*tasks)

        return self.results

    def generate_html_report(self, output_path: str = "a11y_report.html") -> str:
        """Generate HTML accessibility report"""

        # Calculate summary stats
        total_violations = sum(len(r.violations) for r in self.results if r.success)
        critical = sum(1 for r in self.results if r.success for v in r.violations if v.impact == 'critical')
        serious = sum(1 for r in self.results if r.success for v in r.violations if v.impact == 'serious')
        moderate = sum(1 for r in self.results if r.success for v in r.violations if v.impact == 'moderate')
        minor = sum(1 for r in self.results if r.success for v in r.violations if v.impact == 'minor')

        # Successful audits
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]

        # Collect all unique violations across all pages
        all_violations = {}
        for result in successful:
            for v in result.violations:
                if v.id not in all_violations:
                    all_violations[v.id] = {
                        'violation': v,
                        'pages': []
                    }
                all_violations[v.id]['pages'].append(result.url)

        # Build violations HTML
        violations_html = ""
        sorted_violations = sorted(
            all_violations.values(),
            key=lambda x: {'critical': 0, 'serious': 1, 'moderate': 2, 'minor': 3}.get(x['violation'].impact, 4)
        )

        for item in sorted_violations:
            v = item['violation']
            pages = item['pages']
            impact_info = self.IMPACT_BUSINESS.get(v.impact, {})

            impact_color = {
                'critical': '#dc3545',
                'serious': '#fd7e14',
                'moderate': '#ffc107',
                'minor': '#28a745'
            }.get(v.impact, '#6c757d')

            wcag_badges = ' '.join(
                f'<span class="wcag-badge">{tag}</span>'
                for tag in v.wcag_tags[:3]
            )

            nodes_html = ""
            for node in v.nodes[:3]:
                html_snippet = node['html'].replace('<', '&lt;').replace('>', '&gt;')
                nodes_html += f"""
                <div class="code-snippet">
                    <code>{html_snippet}</code>
                </div>
                """

            violations_html += f"""
            <div class="violation">
                <div class="violation-header">
                    <span class="impact-badge" style="background: {impact_color}">{v.impact.upper()}</span>
                    <span class="violation-id">{v.id}</span>
                    {wcag_badges}
                </div>
                <h3>{v.help}</h3>
                <p class="violation-desc">{v.description}</p>

                <div class="business-impact">
                    <strong>Business Impact:</strong> {impact_info.get('description', 'N/A')}<br>
                    <strong>Affected Users:</strong> {impact_info.get('affected', 'N/A')}<br>
                    <strong>Legal Risk:</strong> {impact_info.get('legal_risk', 'N/A')}<br>
                    <strong>Priority:</strong> {impact_info.get('priority', 'N/A')}
                </div>

                <div class="affected-pages">
                    <strong>Found on {len(pages)} page(s):</strong>
                    <ul>
                        {''.join(f'<li>{p}</li>' for p in pages[:5])}
                        {f'<li>...and {len(pages) - 5} more</li>' if len(pages) > 5 else ''}
                    </ul>
                </div>

                <div class="code-examples">
                    <strong>Example Elements:</strong>
                    {nodes_html}
                </div>

                <a href="{v.help_url}" target="_blank" class="learn-more">Learn how to fix this</a>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility Audit Report</title>
    <style>
        :root {{
            --critical: #dc3545;
            --serious: #fd7e14;
            --moderate: #ffc107;
            --minor: #28a745;
            --dark: #1e293b;
            --light: #f8fafc;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--light);
            color: var(--dark);
            line-height: 1.6;
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            padding: 40px;
            border-radius: 16px;
            margin-bottom: 24px;
        }}

        .header h1 {{
            font-size: 32px;
            margin-bottom: 8px;
        }}

        .header p {{
            opacity: 0.9;
        }}

        /* Summary Cards */
        .summary {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}

        .summary-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        .summary-card .number {{
            font-size: 36px;
            font-weight: 700;
        }}

        .summary-card .label {{
            color: #64748b;
            font-size: 12px;
            margin-top: 4px;
        }}

        .summary-card.critical .number {{ color: var(--critical); }}
        .summary-card.serious .number {{ color: var(--serious); }}
        .summary-card.moderate .number {{ color: var(--moderate); }}
        .summary-card.minor .number {{ color: var(--minor); }}

        /* Compliance Box */
        .compliance {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        .compliance h2 {{
            margin-bottom: 16px;
        }}

        .compliance-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }}

        .compliance-item {{
            padding: 16px;
            background: var(--light);
            border-radius: 8px;
            text-align: center;
        }}

        .compliance-status {{
            font-size: 24px;
            margin-bottom: 8px;
        }}

        .compliance-status.pass {{ color: var(--minor); }}
        .compliance-status.fail {{ color: var(--critical); }}

        /* Violations */
        .violations-section {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        .violations-section h2 {{
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--light);
        }}

        .violation {{
            background: var(--light);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }}

        .violation-header {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }}

        .impact-badge {{
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }}

        .violation-id {{
            background: var(--dark);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
        }}

        .wcag-badge {{
            background: #6366f1;
            color: white;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 10px;
        }}

        .violation h3 {{
            font-size: 18px;
            margin-bottom: 8px;
        }}

        .violation-desc {{
            color: #64748b;
            margin-bottom: 16px;
        }}

        .business-impact {{
            background: white;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 16px;
            font-size: 14px;
        }}

        .affected-pages {{
            margin-bottom: 16px;
            font-size: 14px;
        }}

        .affected-pages ul {{
            margin-top: 8px;
            padding-left: 20px;
        }}

        .code-examples {{
            margin-bottom: 16px;
        }}

        .code-snippet {{
            background: var(--dark);
            color: #e2e8f0;
            padding: 12px;
            border-radius: 8px;
            margin-top: 8px;
            overflow-x: auto;
        }}

        .code-snippet code {{
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 12px;
        }}

        .learn-more {{
            display: inline-block;
            color: #6366f1;
            text-decoration: none;
            font-weight: 500;
        }}

        .learn-more:hover {{
            text-decoration: underline;
        }}

        /* Failed audits */
        .failed-section {{
            margin-top: 24px;
            padding: 20px;
            background: #fef2f2;
            border-radius: 12px;
        }}

        .timestamp {{
            text-align: center;
            padding: 24px;
            color: #64748b;
            font-size: 14px;
        }}

        @media (max-width: 768px) {{
            .summary {{ grid-template-columns: repeat(2, 1fr); }}
            .compliance-grid {{ grid-template-columns: 1fr; }}
        }}

        @media print {{
            .violation {{ break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Accessibility Audit Report</h1>
            <p>{len(successful)} pages audited | {total_violations} issues found</p>
        </div>

        <div class="summary">
            <div class="summary-card">
                <div class="number">{total_violations}</div>
                <div class="label">Total Issues</div>
            </div>
            <div class="summary-card critical">
                <div class="number">{critical}</div>
                <div class="label">Critical</div>
            </div>
            <div class="summary-card serious">
                <div class="number">{serious}</div>
                <div class="label">Serious</div>
            </div>
            <div class="summary-card moderate">
                <div class="number">{moderate}</div>
                <div class="label">Moderate</div>
            </div>
            <div class="summary-card minor">
                <div class="number">{minor}</div>
                <div class="label">Minor</div>
            </div>
        </div>

        <div class="compliance">
            <h2>WCAG Compliance Status</h2>
            <div class="compliance-grid">
                <div class="compliance-item">
                    <div class="compliance-status {'fail' if critical > 0 or serious > 0 else 'pass'}">
                        {'FAIL' if critical > 0 or serious > 0 else 'PASS'}
                    </div>
                    <div>WCAG 2.1 Level A</div>
                </div>
                <div class="compliance-item">
                    <div class="compliance-status {'fail' if critical > 0 or serious > 0 or moderate > 3 else 'pass'}">
                        {'FAIL' if critical > 0 or serious > 0 or moderate > 3 else 'PASS'}
                    </div>
                    <div>WCAG 2.1 Level AA</div>
                </div>
                <div class="compliance-item">
                    <div class="compliance-status fail">
                        {'FAIL' if critical > 0 or serious > 0 or moderate > 0 else 'PASS'}
                    </div>
                    <div>WCAG 2.1 Level AAA</div>
                </div>
            </div>
        </div>

        <div class="violations-section">
            <h2>Issues Found ({len(all_violations)} unique issues)</h2>
            {violations_html if violations_html else '<p>No accessibility issues found!</p>'}
        </div>

        {f'''
        <div class="failed-section">
            <h3>Failed Audits ({len(failed)})</h3>
            <ul>
                {''.join(f"<li>{r.url}: {r.error}</li>" for r in failed)}
            </ul>
        </div>
        ''' if failed else ''}

        <div class="timestamp">
            Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\nReport saved to: {output_path}")
        return output_path

    def generate_json_report(self, output_path: str = "a11y_report.json") -> str:
        """Generate JSON report"""
        data = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_pages': len(self.results),
                'successful': len([r for r in self.results if r.success]),
                'total_violations': sum(len(r.violations) for r in self.results if r.success),
                'by_impact': {
                    'critical': sum(1 for r in self.results if r.success for v in r.violations if v.impact == 'critical'),
                    'serious': sum(1 for r in self.results if r.success for v in r.violations if v.impact == 'serious'),
                    'moderate': sum(1 for r in self.results if r.success for v in r.violations if v.impact == 'moderate'),
                    'minor': sum(1 for r in self.results if r.success for v in r.violations if v.impact == 'minor'),
                }
            },
            'results': [
                {
                    'url': r.url,
                    'success': r.success,
                    'violations': [
                        {
                            'id': v.id,
                            'impact': v.impact,
                            'help': v.help,
                            'description': v.description,
                            'help_url': v.help_url,
                            'wcag_tags': v.wcag_tags,
                            'affected_elements': len(v.nodes)
                        }
                        for v in r.violations
                    ],
                    'passes': r.passes,
                    'error': r.error
                }
                for r in self.results
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"JSON saved to: {output_path}")
        return output_path


async def main():
    parser = argparse.ArgumentParser(description='Run accessibility audits')
    parser.add_argument('--url', type=str, help='Single URL to audit')
    parser.add_argument('--urls', type=str, help='File with URLs (one per line)')
    parser.add_argument('--output', type=str, default='a11y_report.html', help='Output path')
    parser.add_argument('--format', type=str, choices=['html', 'json', 'both'], default='html')
    parser.add_argument('--concurrency', type=int, default=2, help='Max concurrent audits')

    args = parser.parse_args()

    urls = []

    if args.url:
        urls = [args.url]
    elif args.urls:
        with open(args.urls, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    else:
        print("Error: Provide --url or --urls")
        return

    auditor = AccessibilityAuditor()
    await auditor.audit_batch(urls, concurrency=args.concurrency)

    if args.format in ['html', 'both']:
        auditor.generate_html_report(args.output if args.output.endswith('.html') else f"{args.output}.html")

    if args.format in ['json', 'both']:
        json_path = args.output.replace('.html', '.json') if args.output.endswith('.html') else f"{args.output}.json"
        auditor.generate_json_report(json_path)

    # Summary
    print(f"\n{'='*50}")
    print("ACCESSIBILITY AUDIT SUMMARY")
    print(f"{'='*50}")

    successful = [r for r in auditor.results if r.success]
    total_violations = sum(len(r.violations) for r in successful)
    critical = sum(1 for r in successful for v in r.violations if v.impact == 'critical')
    serious = sum(1 for r in successful for v in r.violations if v.impact == 'serious')

    print(f"Pages audited: {len(auditor.results)}")
    print(f"Total issues: {total_violations}")
    print(f"Critical: {critical}")
    print(f"Serious: {serious}")

    if critical > 0 or serious > 0:
        print("\nWCAG AA Compliance: FAIL")
        print("Action required: Fix critical and serious issues")
    else:
        print("\nWCAG AA Compliance: LIKELY PASS")
        print("Continue monitoring for new issues")


if __name__ == "__main__":
    asyncio.run(main())
