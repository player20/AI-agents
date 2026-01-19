"""
Lighthouse Batch Runner
Run Lighthouse audits on multiple URLs and generate a combined report.

Usage:
    python lighthouse_batch.py --urls urls.txt --output report.html
    python lighthouse_batch.py --url https://example.com --output report.html
    python lighthouse_batch.py --sitemap https://example.com/sitemap.xml --output report.html
"""

import subprocess
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
import xml.etree.ElementTree as ET

class LighthouseBatchRunner:
    """Run Lighthouse audits on multiple URLs"""

    def __init__(self, output_dir: str = "lighthouse_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []

    async def run_lighthouse(self, url: str, categories: List[str] = None) -> Dict[str, Any]:
        """
        Run Lighthouse on a single URL

        Args:
            url: URL to audit
            categories: List of categories to audit (performance, accessibility, best-practices, seo, pwa)

        Returns:
            Lighthouse result dict
        """
        if categories is None:
            categories = ['performance', 'accessibility', 'best-practices', 'seo']

        # Generate output filename
        safe_url = url.replace('https://', '').replace('http://', '').replace('/', '_')[:50]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_output = self.output_dir / f"{safe_url}_{timestamp}.json"

        # Build Lighthouse command
        categories_arg = ','.join(categories)
        cmd = [
            'npx', 'lighthouse', url,
            '--output=json',
            f'--output-path={json_output}',
            f'--only-categories={categories_arg}',
            '--chrome-flags="--headless --no-sandbox"',
            '--quiet'
        ]

        print(f"  Auditing: {url}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0 and json_output.exists():
                with open(json_output, 'r') as f:
                    result = json.load(f)

                return {
                    'url': url,
                    'success': True,
                    'scores': {
                        'performance': self._get_score(result, 'performance'),
                        'accessibility': self._get_score(result, 'accessibility'),
                        'best-practices': self._get_score(result, 'best-practices'),
                        'seo': self._get_score(result, 'seo'),
                    },
                    'metrics': self._extract_metrics(result),
                    'audits': self._extract_failed_audits(result),
                    'json_path': str(json_output)
                }
            else:
                return {
                    'url': url,
                    'success': False,
                    'error': stderr.decode() if stderr else 'Unknown error'
                }

        except Exception as e:
            return {
                'url': url,
                'success': False,
                'error': str(e)
            }

    def _get_score(self, result: Dict, category: str) -> Optional[int]:
        """Extract score for a category"""
        try:
            score = result['categories'].get(category, {}).get('score')
            return int(score * 100) if score is not None else None
        except:
            return None

    def _extract_metrics(self, result: Dict) -> Dict[str, Any]:
        """Extract key performance metrics"""
        metrics = {}
        audits = result.get('audits', {})

        metric_keys = [
            'first-contentful-paint',
            'largest-contentful-paint',
            'total-blocking-time',
            'cumulative-layout-shift',
            'speed-index',
            'interactive'
        ]

        for key in metric_keys:
            if key in audits:
                metrics[key] = {
                    'value': audits[key].get('numericValue'),
                    'display': audits[key].get('displayValue'),
                    'score': audits[key].get('score')
                }

        return metrics

    def _extract_failed_audits(self, result: Dict) -> List[Dict]:
        """Extract failed audits for recommendations"""
        failed = []
        audits = result.get('audits', {})

        for audit_id, audit in audits.items():
            score = audit.get('score')
            if score is not None and score < 0.9:  # Not passing
                failed.append({
                    'id': audit_id,
                    'title': audit.get('title'),
                    'description': audit.get('description'),
                    'score': score,
                    'displayValue': audit.get('displayValue')
                })

        # Sort by score (worst first)
        failed.sort(key=lambda x: x.get('score', 1))
        return failed[:20]  # Top 20 issues

    async def run_batch(self, urls: List[str], concurrency: int = 3) -> List[Dict]:
        """
        Run Lighthouse on multiple URLs with concurrency limit

        Args:
            urls: List of URLs to audit
            concurrency: Max concurrent audits

        Returns:
            List of results
        """
        print(f"\nRunning Lighthouse audits on {len(urls)} URLs...")
        print(f"Concurrency: {concurrency}")
        print("-" * 50)

        semaphore = asyncio.Semaphore(concurrency)

        async def limited_audit(url):
            async with semaphore:
                return await self.run_lighthouse(url)

        tasks = [limited_audit(url) for url in urls]
        self.results = await asyncio.gather(*tasks)

        return self.results

    def generate_html_report(self, output_path: str = "lighthouse_report.html") -> str:
        """Generate an HTML report from results"""

        successful = [r for r in self.results if r.get('success')]
        failed = [r for r in self.results if not r.get('success')]

        # Calculate averages
        avg_scores = {}
        for category in ['performance', 'accessibility', 'best-practices', 'seo']:
            scores = [r['scores'][category] for r in successful if r['scores'].get(category) is not None]
            avg_scores[category] = round(sum(scores) / len(scores)) if scores else 0

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lighthouse Batch Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
        .header p {{ opacity: 0.9; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }}
        .score-card {{ background: white; border-radius: 12px; padding: 24px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .score-card .score {{ font-size: 48px; font-weight: bold; }}
        .score-card .label {{ color: #666; font-size: 14px; margin-top: 8px; }}
        .score-good {{ color: #0cce6b; }}
        .score-ok {{ color: #ffa400; }}
        .score-bad {{ color: #ff4e42; }}
        .results {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .results h2 {{ margin-bottom: 16px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f9f9f9; font-weight: 600; }}
        .url-cell {{ max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .score-cell {{ font-weight: 600; text-align: center; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
        .badge-good {{ background: #d4edda; color: #155724; }}
        .badge-ok {{ background: #fff3cd; color: #856404; }}
        .badge-bad {{ background: #f8d7da; color: #721c24; }}
        .failed-section {{ margin-top: 20px; }}
        .failed-item {{ background: #fff3f3; padding: 12px; border-radius: 8px; margin-bottom: 8px; }}
        .timestamp {{ color: #999; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Lighthouse Batch Report</h1>
            <p>{len(successful)} pages audited successfully, {len(failed)} failed</p>
        </div>

        <div class="summary">
            <div class="score-card">
                <div class="score {self._score_class(avg_scores['performance'])}">{avg_scores['performance']}</div>
                <div class="label">Performance</div>
            </div>
            <div class="score-card">
                <div class="score {self._score_class(avg_scores['accessibility'])}">{avg_scores['accessibility']}</div>
                <div class="label">Accessibility</div>
            </div>
            <div class="score-card">
                <div class="score {self._score_class(avg_scores['best-practices'])}">{avg_scores['best-practices']}</div>
                <div class="label">Best Practices</div>
            </div>
            <div class="score-card">
                <div class="score {self._score_class(avg_scores['seo'])}">{avg_scores['seo']}</div>
                <div class="label">SEO</div>
            </div>
        </div>

        <div class="results">
            <h2>Page Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>URL</th>
                        <th>Performance</th>
                        <th>Accessibility</th>
                        <th>Best Practices</th>
                        <th>SEO</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(self._generate_row(r) for r in successful)}
                </tbody>
            </table>

            {self._generate_failed_section(failed)}
        </div>

        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>"""

        with open(output_path, 'w') as f:
            f.write(html)

        print(f"\nReport saved to: {output_path}")
        return output_path

    def _score_class(self, score: int) -> str:
        if score >= 90:
            return 'score-good'
        elif score >= 50:
            return 'score-ok'
        else:
            return 'score-bad'

    def _badge_class(self, score: int) -> str:
        if score >= 90:
            return 'badge-good'
        elif score >= 50:
            return 'badge-ok'
        else:
            return 'badge-bad'

    def _generate_row(self, result: Dict) -> str:
        scores = result.get('scores', {})
        return f"""
        <tr>
            <td class="url-cell" title="{result['url']}">{result['url']}</td>
            <td class="score-cell"><span class="badge {self._badge_class(scores.get('performance', 0))}">{scores.get('performance', 'N/A')}</span></td>
            <td class="score-cell"><span class="badge {self._badge_class(scores.get('accessibility', 0))}">{scores.get('accessibility', 'N/A')}</span></td>
            <td class="score-cell"><span class="badge {self._badge_class(scores.get('best-practices', 0))}">{scores.get('best-practices', 'N/A')}</span></td>
            <td class="score-cell"><span class="badge {self._badge_class(scores.get('seo', 0))}">{scores.get('seo', 'N/A')}</span></td>
        </tr>"""

    def _generate_failed_section(self, failed: List[Dict]) -> str:
        if not failed:
            return ""

        items = ''.join(f"""
        <div class="failed-item">
            <strong>{r['url']}</strong><br>
            <small>{r.get('error', 'Unknown error')}</small>
        </div>""" for r in failed)

        return f"""
        <div class="failed-section">
            <h3>Failed Audits ({len(failed)})</h3>
            {items}
        </div>"""

    def generate_json_report(self, output_path: str = "lighthouse_report.json") -> str:
        """Generate a JSON report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_urls': len(self.results),
            'successful': len([r for r in self.results if r.get('success')]),
            'failed': len([r for r in self.results if not r.get('success')]),
            'results': self.results
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        return output_path


async def fetch_sitemap_urls(sitemap_url: str) -> List[str]:
    """Fetch URLs from a sitemap"""
    async with aiohttp.ClientSession() as session:
        async with session.get(sitemap_url) as response:
            content = await response.text()

    root = ET.fromstring(content)
    # Handle namespace
    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    urls = []
    for url in root.findall('.//sm:loc', ns):
        urls.append(url.text)

    # Also try without namespace
    if not urls:
        for url in root.findall('.//loc'):
            urls.append(url.text)

    return urls


async def main():
    parser = argparse.ArgumentParser(description='Run Lighthouse audits on multiple URLs')
    parser.add_argument('--url', type=str, help='Single URL to audit')
    parser.add_argument('--urls', type=str, help='File containing URLs (one per line)')
    parser.add_argument('--sitemap', type=str, help='Sitemap URL to extract pages from')
    parser.add_argument('--output', type=str, default='lighthouse_report.html', help='Output report path')
    parser.add_argument('--format', type=str, choices=['html', 'json', 'both'], default='html', help='Output format')
    parser.add_argument('--concurrency', type=int, default=3, help='Max concurrent audits')
    parser.add_argument('--limit', type=int, default=50, help='Max URLs to audit (for sitemaps)')

    args = parser.parse_args()

    urls = []

    if args.url:
        urls = [args.url]
    elif args.urls:
        with open(args.urls, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    elif args.sitemap:
        print(f"Fetching URLs from sitemap: {args.sitemap}")
        urls = await fetch_sitemap_urls(args.sitemap)
        print(f"Found {len(urls)} URLs in sitemap")
        if len(urls) > args.limit:
            print(f"Limiting to first {args.limit} URLs")
            urls = urls[:args.limit]
    else:
        print("Error: Please provide --url, --urls, or --sitemap")
        sys.exit(1)

    if not urls:
        print("No URLs to audit")
        sys.exit(1)

    runner = LighthouseBatchRunner()
    await runner.run_batch(urls, concurrency=args.concurrency)

    if args.format in ['html', 'both']:
        runner.generate_html_report(args.output if args.output.endswith('.html') else f"{args.output}.html")

    if args.format in ['json', 'both']:
        json_path = args.output.replace('.html', '.json') if args.output.endswith('.html') else f"{args.output}.json"
        runner.generate_json_report(json_path)

    # Print summary
    successful = [r for r in runner.results if r.get('success')]
    print(f"\n{'='*50}")
    print(f"SUMMARY")
    print(f"{'='*50}")
    print(f"Total URLs: {len(runner.results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(runner.results) - len(successful)}")

    if successful:
        avg_perf = sum(r['scores']['performance'] for r in successful if r['scores'].get('performance')) / len(successful)
        avg_a11y = sum(r['scores']['accessibility'] for r in successful if r['scores'].get('accessibility')) / len(successful)
        print(f"\nAverage Performance: {avg_perf:.0f}")
        print(f"Average Accessibility: {avg_a11y:.0f}")


if __name__ == "__main__":
    asyncio.run(main())
