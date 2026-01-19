"""
Before/After Prototype Generator
Create interactive visual prototypes showing proposed changes to clients.

This is the MOST IMPORTANT tool for client presentations.
Clients want to SEE what will change BEFORE development starts.

Usage:
    python prototype_generator.py --config prototype.json --output client_prototype.html
    python prototype_generator.py --template --output my_prototype.json  # Generate template

Example config (prototype.json):
{
    "app_name": "JuiceNet",
    "client_name": "Acme Corp",
    "screens": [
        {
            "id": "landing",
            "name": "Landing Page",
            "before": {
                "description": "Generic landing with no clear value prop",
                "screenshot": "before/landing.png",  # Optional
                "issues": ["No clear CTA", "Missing trust signals"]
            },
            "after": {
                "description": "Clear role selection with earnings preview",
                "screenshot": "after/landing.png",  # Optional
                "changes": ["Added role selection cards", "Added earnings preview"]
            }
        }
    ]
}
"""

import json
import argparse
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Screen:
    """A single screen comparison"""
    id: str
    name: str
    before_description: str
    after_description: str
    before_screenshot: Optional[str] = None
    after_screenshot: Optional[str] = None
    before_issues: List[str] = field(default_factory=list)
    after_changes: List[str] = field(default_factory=list)
    before_html: Optional[str] = None  # Inline HTML mockup
    after_html: Optional[str] = None   # Inline HTML mockup


class PrototypeGenerator:
    """Generate before/after comparison prototypes"""

    def __init__(self):
        self.screens: List[Screen] = []
        self.app_name = ""
        self.client_name = ""

    def load_config(self, config_path: str) -> None:
        """Load prototype configuration from JSON"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.app_name = config.get('app_name', 'App')
        self.client_name = config.get('client_name', 'Client')

        for screen_data in config.get('screens', []):
            before = screen_data.get('before', {})
            after = screen_data.get('after', {})

            screen = Screen(
                id=screen_data.get('id', 'screen'),
                name=screen_data.get('name', 'Screen'),
                before_description=before.get('description', ''),
                after_description=after.get('description', ''),
                before_screenshot=before.get('screenshot'),
                after_screenshot=after.get('screenshot'),
                before_issues=before.get('issues', []),
                after_changes=after.get('changes', []),
                before_html=before.get('html'),
                after_html=after.get('html')
            )
            self.screens.append(screen)

    def _encode_image(self, image_path: str) -> Optional[str]:
        """Encode image to base64"""
        path = Path(image_path)
        if not path.exists():
            return None

        with open(path, 'rb') as f:
            data = base64.b64encode(f.read()).decode()

        ext = path.suffix.lower()
        mime = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }.get(ext, 'image/png')

        return f"data:{mime};base64,{data}"

    def generate_html(self, output_path: str = "prototype.html") -> str:
        """Generate the interactive HTML prototype"""

        # Build navigation tabs
        nav_tabs = ""
        for i, screen in enumerate(self.screens):
            active = "active" if i == 0 else ""
            nav_tabs += f"""
            <button class="nav-tab {active}" onclick="showScreen('{screen.id}')" data-screen="{screen.id}">
                {screen.name}
            </button>
            """

        # Build screen panels
        screens_html = ""
        for i, screen in enumerate(self.screens):
            display = "flex" if i == 0 else "none"

            # Before content
            before_content = ""
            if screen.before_screenshot:
                img_data = self._encode_image(screen.before_screenshot)
                if img_data:
                    before_content = f'<img src="{img_data}" alt="Before" class="screen-image">'
                else:
                    before_content = f'<div class="placeholder">Screenshot: {screen.before_screenshot}</div>'
            elif screen.before_html:
                before_content = f'<div class="inline-mockup">{screen.before_html}</div>'
            else:
                before_content = f'<div class="description-placeholder">{screen.before_description}</div>'

            # After content
            after_content = ""
            if screen.after_screenshot:
                img_data = self._encode_image(screen.after_screenshot)
                if img_data:
                    after_content = f'<img src="{img_data}" alt="After" class="screen-image">'
                else:
                    after_content = f'<div class="placeholder">Screenshot: {screen.after_screenshot}</div>'
            elif screen.after_html:
                after_content = f'<div class="inline-mockup">{screen.after_html}</div>'
            else:
                after_content = f'<div class="description-placeholder">{screen.after_description}</div>'

            # Issues list
            issues_html = ""
            if screen.before_issues:
                issues_html = '<ul class="issues-list">' + \
                    ''.join(f'<li>{issue}</li>' for issue in screen.before_issues) + \
                    '</ul>'

            # Changes list
            changes_html = ""
            if screen.after_changes:
                changes_html = '<ul class="changes-list">' + \
                    ''.join(f'<li>{change}</li>' for change in screen.after_changes) + \
                    '</ul>'

            screens_html += f"""
            <div class="screen-panel" id="screen-{screen.id}" style="display: {display}">
                <h2 class="screen-title">{screen.name}</h2>

                <div class="comparison-container">
                    <!-- Before -->
                    <div class="comparison-side before">
                        <div class="side-header">
                            <span class="badge badge-before">CURRENT</span>
                        </div>
                        <div class="phone-frame">
                            <div class="phone-notch"></div>
                            <div class="phone-content">
                                {before_content}
                            </div>
                        </div>
                        <div class="side-description">
                            <p>{screen.before_description}</p>
                            {issues_html}
                        </div>
                    </div>

                    <!-- Arrow -->
                    <div class="comparison-arrow">
                        <svg viewBox="0 0 24 24" width="48" height="48" fill="currentColor">
                            <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8-8-8z"/>
                        </svg>
                    </div>

                    <!-- After -->
                    <div class="comparison-side after">
                        <div class="side-header">
                            <span class="badge badge-after">PROPOSED</span>
                        </div>
                        <div class="phone-frame">
                            <div class="phone-notch"></div>
                            <div class="phone-content">
                                {after_content}
                            </div>
                        </div>
                        <div class="side-description">
                            <p>{screen.after_description}</p>
                            {changes_html}
                        </div>
                    </div>
                </div>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.app_name} - Proposed Changes | {self.client_name}</title>
    <style>
        :root {{
            --primary: #6366f1;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --dark: #0f172a;
            --light: #f1f5f9;
            --before-color: #64748b;
            --after-color: #10b981;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            color: white;
        }}

        /* Header */
        .header {{
            padding: 40px 20px 20px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}

        .header h1 {{
            font-size: 32px;
            margin-bottom: 8px;
        }}

        .header .subtitle {{
            color: #94a3b8;
            font-size: 16px;
        }}

        /* Navigation */
        .nav {{
            display: flex;
            justify-content: center;
            gap: 8px;
            padding: 20px;
            flex-wrap: wrap;
            background: rgba(0,0,0,0.2);
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(10px);
        }}

        .nav-tab {{
            background: rgba(255,255,255,0.1);
            border: none;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }}

        .nav-tab:hover {{
            background: rgba(255,255,255,0.2);
        }}

        .nav-tab.active {{
            background: var(--primary);
        }}

        /* Screen Panel */
        .screen-panel {{
            padding: 40px 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}

        .screen-title {{
            text-align: center;
            font-size: 28px;
            margin-bottom: 40px;
        }}

        /* Comparison Container */
        .comparison-container {{
            display: flex;
            align-items: flex-start;
            justify-content: center;
            gap: 40px;
            flex-wrap: wrap;
        }}

        .comparison-side {{
            flex: 1;
            max-width: 400px;
            min-width: 300px;
        }}

        .comparison-arrow {{
            display: flex;
            align-items: center;
            padding-top: 200px;
            color: var(--primary);
        }}

        @media (max-width: 900px) {{
            .comparison-arrow {{
                transform: rotate(90deg);
                padding: 20px 0;
            }}
        }}

        /* Side Header */
        .side-header {{
            text-align: center;
            margin-bottom: 16px;
        }}

        .badge {{
            display: inline-block;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 1px;
        }}

        .badge-before {{
            background: rgba(100, 116, 139, 0.3);
            color: #94a3b8;
        }}

        .badge-after {{
            background: rgba(16, 185, 129, 0.2);
            color: var(--success);
        }}

        /* Phone Frame */
        .phone-frame {{
            background: #000;
            border-radius: 40px;
            padding: 12px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.5);
            position: relative;
        }}

        .phone-notch {{
            width: 150px;
            height: 30px;
            background: #000;
            border-radius: 0 0 20px 20px;
            position: absolute;
            top: 12px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10;
        }}

        .phone-content {{
            background: white;
            border-radius: 32px;
            min-height: 600px;
            overflow: hidden;
            position: relative;
        }}

        .screen-image {{
            width: 100%;
            height: auto;
            display: block;
        }}

        .placeholder, .description-placeholder {{
            padding: 60px 20px;
            text-align: center;
            color: #64748b;
            font-style: italic;
            background: #f8fafc;
            min-height: 600px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .inline-mockup {{
            min-height: 600px;
        }}

        /* Description */
        .side-description {{
            margin-top: 24px;
            padding: 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
        }}

        .side-description p {{
            color: #cbd5e1;
            margin-bottom: 12px;
            line-height: 1.6;
        }}

        /* Issues List (Before) */
        .issues-list {{
            list-style: none;
            padding: 0;
        }}

        .issues-list li {{
            position: relative;
            padding-left: 24px;
            margin-bottom: 8px;
            color: #f87171;
            font-size: 14px;
        }}

        .issues-list li::before {{
            content: "!";
            position: absolute;
            left: 0;
            width: 16px;
            height: 16px;
            background: #dc2626;
            color: white;
            border-radius: 50%;
            font-size: 11px;
            font-weight: bold;
            text-align: center;
            line-height: 16px;
        }}

        /* Changes List (After) */
        .changes-list {{
            list-style: none;
            padding: 0;
        }}

        .changes-list li {{
            position: relative;
            padding-left: 24px;
            margin-bottom: 8px;
            color: #4ade80;
            font-size: 14px;
        }}

        .changes-list li::before {{
            content: "+";
            position: absolute;
            left: 0;
            width: 16px;
            height: 16px;
            background: #22c55e;
            color: white;
            border-radius: 50%;
            font-size: 14px;
            font-weight: bold;
            text-align: center;
            line-height: 16px;
        }}

        /* Toggle View */
        .toggle-container {{
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 8px;
            background: rgba(0,0,0,0.8);
            padding: 8px;
            border-radius: 12px;
            backdrop-filter: blur(10px);
            z-index: 100;
        }}

        .toggle-btn {{
            background: rgba(255,255,255,0.1);
            border: none;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }}

        .toggle-btn:hover, .toggle-btn.active {{
            background: var(--primary);
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 40px;
            color: #64748b;
            font-size: 12px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}

        /* Summary Stats */
        .summary-stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            padding: 30px;
            background: rgba(255,255,255,0.02);
            margin-bottom: 20px;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 36px;
            font-weight: 700;
            color: var(--primary);
        }}

        .stat-label {{
            font-size: 14px;
            color: #64748b;
        }}

        /* Slider view (alternative) */
        .slider-view {{
            display: none;
        }}

        .slider-view.active {{
            display: block;
        }}

        .comparison-view {{
            display: flex;
        }}

        .comparison-view.hidden {{
            display: none;
        }}

        /* Image Overlay Slider */
        .slider-container {{
            position: relative;
            max-width: 400px;
            margin: 0 auto;
        }}

        .slider-container .phone-frame {{
            position: relative;
        }}

        .slider-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            width: 50%;
            height: 100%;
            overflow: hidden;
        }}

        .slider-handle {{
            position: absolute;
            top: 0;
            bottom: 0;
            width: 4px;
            background: var(--primary);
            cursor: ew-resize;
            left: 50%;
            transform: translateX(-50%);
        }}

        .slider-handle::after {{
            content: "";
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 40px;
            height: 40px;
            background: var(--primary);
            border-radius: 50%;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}

        @media print {{
            body {{
                background: white;
                color: black;
            }}
            .nav, .toggle-container {{ display: none; }}
            .screen-panel {{ display: block !important; page-break-after: always; }}
            .phone-frame {{ box-shadow: 0 0 0 2px #ddd; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{self.app_name}</h1>
        <p class="subtitle">Proposed UX Improvements for {self.client_name}</p>
    </div>

    <div class="summary-stats">
        <div class="stat">
            <div class="stat-value">{len(self.screens)}</div>
            <div class="stat-label">Screens Updated</div>
        </div>
        <div class="stat">
            <div class="stat-value">{sum(len(s.after_changes) for s in self.screens)}</div>
            <div class="stat-label">Improvements</div>
        </div>
        <div class="stat">
            <div class="stat-value">{sum(len(s.before_issues) for s in self.screens)}</div>
            <div class="stat-label">Issues Addressed</div>
        </div>
    </div>

    <nav class="nav">
        {nav_tabs}
    </nav>

    <main>
        {screens_html}
    </main>

    <div class="toggle-container">
        <button class="toggle-btn active" onclick="setView('comparison')">Side by Side</button>
        <button class="toggle-btn" onclick="setView('slider')">Slider</button>
    </div>

    <footer class="footer">
        <p>This prototype shows proposed changes. Actual implementation may vary slightly.</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d')} | Confidential - For {self.client_name} Only</p>
    </footer>

    <script>
        function showScreen(screenId) {{
            // Hide all screens
            document.querySelectorAll('.screen-panel').forEach(panel => {{
                panel.style.display = 'none';
            }});

            // Show selected screen
            document.getElementById('screen-' + screenId).style.display = 'flex';

            // Update active tab
            document.querySelectorAll('.nav-tab').forEach(tab => {{
                tab.classList.remove('active');
                if (tab.dataset.screen === screenId) {{
                    tab.classList.add('active');
                }}
            }});
        }}

        function setView(view) {{
            document.querySelectorAll('.toggle-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');

            // Toggle view mode (comparison vs slider)
            // This is a placeholder - would need more implementation for slider view
        }}

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            const tabs = Array.from(document.querySelectorAll('.nav-tab'));
            const activeTab = document.querySelector('.nav-tab.active');
            const currentIndex = tabs.indexOf(activeTab);

            if (e.key === 'ArrowRight' && currentIndex < tabs.length - 1) {{
                tabs[currentIndex + 1].click();
            }} else if (e.key === 'ArrowLeft' && currentIndex > 0) {{
                tabs[currentIndex - 1].click();
            }}
        }});
    </script>
</body>
</html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"Prototype saved to: {output_path}")
        return output_path

    @staticmethod
    def generate_template(output_path: str = "prototype_template.json") -> str:
        """Generate a template configuration file"""
        template = {
            "app_name": "MyApp",
            "client_name": "Client Company",
            "screens": [
                {
                    "id": "landing",
                    "name": "Landing Page",
                    "before": {
                        "description": "Current landing page with generic messaging",
                        "screenshot": "screenshots/before/landing.png",
                        "issues": [
                            "No clear value proposition",
                            "Missing trust signals",
                            "Confusing navigation"
                        ]
                    },
                    "after": {
                        "description": "Improved landing with clear CTA and social proof",
                        "screenshot": "screenshots/after/landing.png",
                        "changes": [
                            "Added clear value proposition headline",
                            "Added customer testimonials",
                            "Simplified navigation to key actions"
                        ]
                    }
                },
                {
                    "id": "signup",
                    "name": "Sign Up Flow",
                    "before": {
                        "description": "Long form with too many required fields",
                        "screenshot": "screenshots/before/signup.png",
                        "issues": [
                            "Too many form fields",
                            "No progress indicator",
                            "Missing privacy explanations"
                        ]
                    },
                    "after": {
                        "description": "Streamlined signup with progressive disclosure",
                        "screenshot": "screenshots/after/signup.png",
                        "changes": [
                            "Reduced to essential fields only",
                            "Added step indicator",
                            "Added trust badges and privacy text"
                        ]
                    }
                },
                {
                    "id": "dashboard",
                    "name": "User Dashboard",
                    "before": {
                        "description": "Cluttered dashboard with poor information hierarchy",
                        "screenshot": "screenshots/before/dashboard.png",
                        "issues": [
                            "Information overload",
                            "Key metrics hard to find",
                            "No clear next actions"
                        ]
                    },
                    "after": {
                        "description": "Clean dashboard focused on key metrics",
                        "screenshot": "screenshots/after/dashboard.png",
                        "changes": [
                            "Prominent key metrics cards",
                            "Clear action buttons",
                            "Improved visual hierarchy"
                        ]
                    }
                }
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(template, f, indent=2)

        print(f"Template saved to: {output_path}")
        print("\nEdit this file with your app's screens, then run:")
        print(f"  python prototype_generator.py --config {output_path} --output prototype.html")

        return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Generate before/after comparison prototypes for client presentations'
    )
    parser.add_argument('--config', type=str, help='Path to prototype config JSON')
    parser.add_argument('--output', type=str, default='prototype.html', help='Output HTML path')
    parser.add_argument('--template', action='store_true', help='Generate a template config file')

    args = parser.parse_args()

    if args.template:
        output = args.output if args.output.endswith('.json') else 'prototype_template.json'
        PrototypeGenerator.generate_template(output)
        return

    if not args.config:
        print("Error: Provide --config or use --template to generate a config file")
        return

    generator = PrototypeGenerator()
    generator.load_config(args.config)
    generator.generate_html(args.output)

    print(f"\nGenerated prototype with {len(generator.screens)} screens")
    print(f"Open {args.output} in a browser to view")


if __name__ == "__main__":
    main()
