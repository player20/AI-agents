"""
Competitor Tech Stack Scanner
Analyze competitor websites to detect their technology stack.

Usage:
    python tech_scanner.py --url https://competitor.com
    python tech_scanner.py --urls competitors.txt --output report.html
"""

import asyncio
import aiohttp
import re
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import ssl


class TechStackScanner:
    """Detect technology stacks from websites"""

    def __init__(self):
        # Technology detection patterns
        self.patterns = {
            # Frontend Frameworks
            'react': {
                'category': 'Frontend Framework',
                'patterns': [
                    r'react\.production\.min\.js',
                    r'react-dom',
                    r'__REACT_DEVTOOLS_GLOBAL_HOOK__',
                    r'data-reactroot',
                    r'data-reactid',
                    r'_reactRootContainer'
                ],
                'headers': [],
                'meta': []
            },
            'vue': {
                'category': 'Frontend Framework',
                'patterns': [
                    r'vue\.runtime\.min\.js',
                    r'vue\.min\.js',
                    r'__vue__',
                    r'data-v-[a-f0-9]+'
                ],
                'headers': [],
                'meta': [('generator', 'Vue')]
            },
            'angular': {
                'category': 'Frontend Framework',
                'patterns': [
                    r'angular\.min\.js',
                    r'ng-version',
                    r'ng-app',
                    r'ng-controller',
                    r'\[ngClass\]',
                    r'_ngcontent-'
                ],
                'headers': [],
                'meta': []
            },
            'svelte': {
                'category': 'Frontend Framework',
                'patterns': [
                    r'svelte',
                    r'__svelte'
                ],
                'headers': [],
                'meta': []
            },
            'next.js': {
                'category': 'Frontend Framework',
                'patterns': [
                    r'_next/static',
                    r'__NEXT_DATA__',
                    r'next/dist'
                ],
                'headers': [('x-powered-by', 'Next.js')],
                'meta': []
            },
            'nuxt': {
                'category': 'Frontend Framework',
                'patterns': [
                    r'_nuxt',
                    r'__NUXT__'
                ],
                'headers': [],
                'meta': []
            },

            # CSS Frameworks
            'tailwind': {
                'category': 'CSS Framework',
                'patterns': [
                    r'tailwindcss',
                    r'tw-',
                    r'class="[^"]*(?:flex|grid|p-\d|m-\d|text-\w+-\d{3})[^"]*"'
                ],
                'headers': [],
                'meta': []
            },
            'bootstrap': {
                'category': 'CSS Framework',
                'patterns': [
                    r'bootstrap\.min\.css',
                    r'bootstrap\.min\.js',
                    r'class="[^"]*(?:container|row|col-(?:sm|md|lg|xl))[^"]*"'
                ],
                'headers': [],
                'meta': []
            },
            'material-ui': {
                'category': 'CSS Framework',
                'patterns': [
                    r'MuiButton',
                    r'MuiTypography',
                    r'@material-ui',
                    r'@mui'
                ],
                'headers': [],
                'meta': []
            },

            # Backend/CMS
            'wordpress': {
                'category': 'CMS',
                'patterns': [
                    r'wp-content',
                    r'wp-includes',
                    r'wp-json'
                ],
                'headers': [],
                'meta': [('generator', 'WordPress')]
            },
            'shopify': {
                'category': 'E-commerce',
                'patterns': [
                    r'cdn\.shopify\.com',
                    r'Shopify\.theme'
                ],
                'headers': [('x-shopify-stage', '')],
                'meta': []
            },
            'wix': {
                'category': 'Website Builder',
                'patterns': [
                    r'wix\.com',
                    r'static\.wixstatic\.com'
                ],
                'headers': [],
                'meta': [('generator', 'Wix')]
            },
            'squarespace': {
                'category': 'Website Builder',
                'patterns': [
                    r'squarespace\.com',
                    r'sqsp'
                ],
                'headers': [],
                'meta': [('generator', 'Squarespace')]
            },
            'webflow': {
                'category': 'Website Builder',
                'patterns': [
                    r'webflow\.com',
                    r'wf-'
                ],
                'headers': [],
                'meta': [('generator', 'Webflow')]
            },

            # Analytics
            'google-analytics': {
                'category': 'Analytics',
                'patterns': [
                    r'google-analytics\.com',
                    r'gtag',
                    r'ga\(\'create\'',
                    r'googletagmanager\.com'
                ],
                'headers': [],
                'meta': []
            },
            'posthog': {
                'category': 'Analytics',
                'patterns': [
                    r'posthog',
                    r'app\.posthog\.com'
                ],
                'headers': [],
                'meta': []
            },
            'mixpanel': {
                'category': 'Analytics',
                'patterns': [
                    r'mixpanel\.com',
                    r'mixpanel\.track'
                ],
                'headers': [],
                'meta': []
            },
            'segment': {
                'category': 'Analytics',
                'patterns': [
                    r'segment\.com',
                    r'analytics\.js'
                ],
                'headers': [],
                'meta': []
            },
            'hotjar': {
                'category': 'Analytics',
                'patterns': [
                    r'hotjar\.com',
                    r'hj\('
                ],
                'headers': [],
                'meta': []
            },
            'amplitude': {
                'category': 'Analytics',
                'patterns': [
                    r'amplitude\.com',
                    r'amplitude\.getInstance'
                ],
                'headers': [],
                'meta': []
            },

            # Hosting/CDN
            'cloudflare': {
                'category': 'CDN/Security',
                'patterns': [
                    r'cloudflare'
                ],
                'headers': [('cf-ray', ''), ('server', 'cloudflare')],
                'meta': []
            },
            'vercel': {
                'category': 'Hosting',
                'patterns': [
                    r'vercel\.app'
                ],
                'headers': [('x-vercel-id', ''), ('server', 'Vercel')],
                'meta': []
            },
            'netlify': {
                'category': 'Hosting',
                'patterns': [
                    r'netlify'
                ],
                'headers': [('server', 'Netlify')],
                'meta': []
            },
            'aws': {
                'category': 'Hosting',
                'patterns': [
                    r'amazonaws\.com',
                    r'aws'
                ],
                'headers': [('server', 'AmazonS3'), ('x-amz-', '')],
                'meta': []
            },
            'heroku': {
                'category': 'Hosting',
                'patterns': [
                    r'herokuapp\.com'
                ],
                'headers': [('via', 'heroku')],
                'meta': []
            },

            # Payment
            'stripe': {
                'category': 'Payment',
                'patterns': [
                    r'stripe\.com',
                    r'Stripe\('
                ],
                'headers': [],
                'meta': []
            },
            'paypal': {
                'category': 'Payment',
                'patterns': [
                    r'paypal\.com',
                    r'paypalobjects'
                ],
                'headers': [],
                'meta': []
            },

            # Authentication
            'auth0': {
                'category': 'Authentication',
                'patterns': [
                    r'auth0\.com',
                    r'auth0-js'
                ],
                'headers': [],
                'meta': []
            },
            'firebase': {
                'category': 'Backend/Auth',
                'patterns': [
                    r'firebase',
                    r'firebaseapp\.com'
                ],
                'headers': [],
                'meta': []
            },
            'supabase': {
                'category': 'Backend/Auth',
                'patterns': [
                    r'supabase',
                    r'supabase\.co'
                ],
                'headers': [],
                'meta': []
            },

            # Chat/Support
            'intercom': {
                'category': 'Customer Support',
                'patterns': [
                    r'intercom\.io',
                    r'Intercom\('
                ],
                'headers': [],
                'meta': []
            },
            'zendesk': {
                'category': 'Customer Support',
                'patterns': [
                    r'zendesk\.com',
                    r'zdassets\.com'
                ],
                'headers': [],
                'meta': []
            },
            'crisp': {
                'category': 'Customer Support',
                'patterns': [
                    r'crisp\.chat'
                ],
                'headers': [],
                'meta': []
            },

            # Marketing
            'hubspot': {
                'category': 'Marketing',
                'patterns': [
                    r'hubspot\.com',
                    r'hs-scripts\.com',
                    r'hsforms\.com'
                ],
                'headers': [],
                'meta': []
            },
            'mailchimp': {
                'category': 'Marketing',
                'patterns': [
                    r'mailchimp\.com',
                    r'list-manage\.com'
                ],
                'headers': [],
                'meta': []
            },

            # Mobile
            'ionic': {
                'category': 'Mobile Framework',
                'patterns': [
                    r'ionic',
                    r'ion-'
                ],
                'headers': [],
                'meta': []
            },
            'capacitor': {
                'category': 'Mobile Framework',
                'patterns': [
                    r'capacitor'
                ],
                'headers': [],
                'meta': []
            },
        }

    async def scan_url(self, url: str) -> Dict[str, Any]:
        """Scan a URL for technology stack"""
        result = {
            'url': url,
            'scanned_at': datetime.now().isoformat(),
            'technologies': [],
            'categories': {},
            'success': False,
            'error': None
        }

        try:
            # Create SSL context that doesn't verify certificates (for scanning)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(url, allow_redirects=True) as response:
                    html = await response.text()
                    headers = dict(response.headers)

                    # Parse HTML
                    soup = BeautifulSoup(html, 'html.parser')

                    # Get meta tags
                    meta_tags = {}
                    for meta in soup.find_all('meta'):
                        name = meta.get('name', meta.get('property', ''))
                        content = meta.get('content', '')
                        if name and content:
                            meta_tags[name.lower()] = content.lower()

                    # Detect technologies
                    detected = set()

                    for tech_name, tech_info in self.patterns.items():
                        if self._detect_technology(tech_name, tech_info, html, headers, meta_tags):
                            detected.add(tech_name)
                            category = tech_info['category']
                            if category not in result['categories']:
                                result['categories'][category] = []
                            result['categories'][category].append(tech_name)

                    result['technologies'] = list(detected)
                    result['success'] = True

                    # Extract additional info
                    result['title'] = soup.title.string if soup.title else None
                    result['meta_description'] = meta_tags.get('description', None)

        except Exception as e:
            result['error'] = str(e)

        return result

    def _detect_technology(self, tech_name: str, tech_info: Dict, html: str, headers: Dict, meta_tags: Dict) -> bool:
        """Check if a technology is detected"""

        # Check HTML patterns
        for pattern in tech_info['patterns']:
            if re.search(pattern, html, re.IGNORECASE):
                return True

        # Check headers
        for header_name, header_value in tech_info['headers']:
            header_name_lower = header_name.lower()
            for h_name, h_value in headers.items():
                if header_name_lower in h_name.lower():
                    if not header_value or header_value.lower() in h_value.lower():
                        return True

        # Check meta tags
        for meta_name, meta_value in tech_info['meta']:
            if meta_name.lower() in meta_tags:
                if meta_value.lower() in meta_tags[meta_name.lower()]:
                    return True

        return False

    async def scan_batch(self, urls: List[str], concurrency: int = 5) -> List[Dict]:
        """Scan multiple URLs"""
        print(f"\nScanning {len(urls)} URLs for tech stacks...")
        print("-" * 50)

        semaphore = asyncio.Semaphore(concurrency)

        async def limited_scan(url):
            async with semaphore:
                print(f"  Scanning: {url}")
                return await self.scan_url(url)

        tasks = [limited_scan(url) for url in urls]
        results = await asyncio.gather(*tasks)

        return results

    def generate_report(self, results: List[Dict], output_path: str = "tech_stack_report.html") -> str:
        """Generate HTML comparison report"""

        # Aggregate technologies across all sites
        all_techs = {}
        for result in results:
            if result['success']:
                for tech in result['technologies']:
                    if tech not in all_techs:
                        all_techs[tech] = {'count': 0, 'sites': []}
                    all_techs[tech]['count'] += 1
                    all_techs[tech]['sites'].append(result['url'])

        # Sort by popularity
        sorted_techs = sorted(all_techs.items(), key=lambda x: x[1]['count'], reverse=True)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tech Stack Analysis Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f23; color: #fff; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 30px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #333; }}
        .header h1 {{ font-size: 28px; margin-bottom: 8px; color: #26a45a; }}
        .header p {{ color: #888; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; margin-bottom: 20px; }}
        .card {{ background: #1a1a2e; border-radius: 12px; padding: 20px; border: 1px solid #333; }}
        .card h3 {{ color: #26a45a; margin-bottom: 12px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }}
        .tech-list {{ list-style: none; }}
        .tech-list li {{ padding: 8px 0; border-bottom: 1px solid #333; display: flex; justify-content: space-between; }}
        .tech-list li:last-child {{ border-bottom: none; }}
        .tech-name {{ color: #fff; }}
        .tech-count {{ color: #26a45a; font-weight: bold; }}
        .site-card {{ background: #1a1a2e; border-radius: 12px; padding: 20px; margin-bottom: 16px; border: 1px solid #333; }}
        .site-card h3 {{ color: #fff; margin-bottom: 8px; word-break: break-all; }}
        .site-card .description {{ color: #888; font-size: 14px; margin-bottom: 12px; }}
        .tag {{ display: inline-block; background: #252542; color: #26a45a; padding: 4px 10px; border-radius: 20px; font-size: 12px; margin: 2px; }}
        .category {{ margin-bottom: 16px; }}
        .category-title {{ color: #888; font-size: 12px; text-transform: uppercase; margin-bottom: 8px; }}
        .summary-box {{ background: #252542; border-radius: 8px; padding: 16px; text-align: center; }}
        .summary-number {{ font-size: 36px; font-weight: bold; color: #26a45a; }}
        .summary-label {{ color: #888; font-size: 12px; }}
        .timestamp {{ color: #666; font-size: 12px; margin-top: 20px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Tech Stack Analysis Report</h1>
            <p>Analyzed {len(results)} websites for technology stack detection</p>
        </div>

        <div class="grid">
            <div class="summary-box">
                <div class="summary-number">{len(results)}</div>
                <div class="summary-label">Sites Analyzed</div>
            </div>
            <div class="summary-box">
                <div class="summary-number">{len(all_techs)}</div>
                <div class="summary-label">Technologies Detected</div>
            </div>
            <div class="summary-box">
                <div class="summary-number">{sorted_techs[0][0] if sorted_techs else 'N/A'}</div>
                <div class="summary-label">Most Common Tech</div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Most Used Technologies</h3>
                <ul class="tech-list">
                    {''.join(f'<li><span class="tech-name">{tech}</span><span class="tech-count">{info["count"]}/{len(results)}</span></li>' for tech, info in sorted_techs[:15])}
                </ul>
            </div>

            <div class="card">
                <h3>Technology Categories</h3>
                <ul class="tech-list">
                    {self._generate_category_summary(results)}
                </ul>
            </div>
        </div>

        <h2 style="margin: 20px 0; color: #26a45a;">Individual Site Analysis</h2>

        {''.join(self._generate_site_card(r) for r in results if r['success'])}

        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>"""

        with open(output_path, 'w') as f:
            f.write(html)

        print(f"\nReport saved to: {output_path}")
        return output_path

    def _generate_category_summary(self, results: List[Dict]) -> str:
        """Generate category summary"""
        categories = {}
        for result in results:
            if result['success']:
                for cat, techs in result.get('categories', {}).items():
                    if cat not in categories:
                        categories[cat] = 0
                    categories[cat] += 1

        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        return ''.join(f'<li><span class="tech-name">{cat}</span><span class="tech-count">{count}</span></li>' for cat, count in sorted_cats)

    def _generate_site_card(self, result: Dict) -> str:
        """Generate card for a single site"""
        categories_html = ''
        for cat, techs in result.get('categories', {}).items():
            tags = ''.join(f'<span class="tag">{tech}</span>' for tech in techs)
            categories_html += f'<div class="category"><div class="category-title">{cat}</div>{tags}</div>'

        return f"""
        <div class="site-card">
            <h3>{result['url']}</h3>
            <p class="description">{result.get('title', 'No title') or 'No title'}</p>
            {categories_html if categories_html else '<p style="color: #666;">No technologies detected</p>'}
        </div>"""

    def generate_json_report(self, results: List[Dict], output_path: str = "tech_stack_report.json") -> str:
        """Generate JSON report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_sites': len(results),
            'successful_scans': len([r for r in results if r['success']]),
            'results': results
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        return output_path


async def main():
    parser = argparse.ArgumentParser(description='Scan websites for technology stack')
    parser.add_argument('--url', type=str, help='Single URL to scan')
    parser.add_argument('--urls', type=str, help='File containing URLs (one per line)')
    parser.add_argument('--output', type=str, default='tech_stack_report.html', help='Output report path')
    parser.add_argument('--format', type=str, choices=['html', 'json', 'both'], default='html', help='Output format')
    parser.add_argument('--concurrency', type=int, default=5, help='Max concurrent scans')

    args = parser.parse_args()

    urls = []

    if args.url:
        urls = [args.url]
    elif args.urls:
        with open(args.urls, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    else:
        print("Error: Please provide --url or --urls")
        return

    scanner = TechStackScanner()
    results = await scanner.scan_batch(urls, concurrency=args.concurrency)

    if args.format in ['html', 'both']:
        scanner.generate_report(results, args.output if args.output.endswith('.html') else f"{args.output}.html")

    if args.format in ['json', 'both']:
        json_path = args.output.replace('.html', '.json') if args.output.endswith('.html') else f"{args.output}.json"
        scanner.generate_json_report(results, json_path)

    # Print summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    for result in results:
        if result['success']:
            print(f"\n{result['url']}")
            for cat, techs in result.get('categories', {}).items():
                print(f"  {cat}: {', '.join(techs)}")


if __name__ == "__main__":
    asyncio.run(main())
