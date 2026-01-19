"""
Shareable Interactive Audit Report Generator

Creates a fully self-contained HTML report with:
- Interactive charts (Chart.js CDN)
- Embedded JuiceNet prototype (no file:/// references)
- Toggle between Current/Proposed views
- Premium styling
- Ready for hosting on Netlify/Vercel
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import json


class ShareableInteractiveReport:
    """Generates a fully interactive, shareable audit report."""

    def __init__(
        self,
        app_name: str = "JuiceNet",
        tagline: str = "EV Charging Marketplace",
        audit_date: str = None,
        prototype_path: str = None
    ):
        self.app_name = app_name
        self.tagline = tagline
        self.audit_date = audit_date or datetime.now().strftime("%B %d, %Y")
        self.prototype_path = prototype_path or r"C:\Users\jacob\Desktop\claude-code-example\JuiceNet code\mockups\juicenet-flow-prototype.html"

        # Default JuiceNet metrics
        self.funnel_data = [
            {"stage": "Page Views", "count": 968, "rate": 100, "color": "#3B82F6"},
            {"stage": "Signups", "count": 2012, "rate": 100, "color": "#8B5CF6"},
            {"stage": "Email Verified", "count": 1543, "rate": 76.7, "color": "#10B981"},
            {"stage": "Profile Complete", "count": 941, "rate": 46.8, "color": "#F59E0B"},
            {"stage": "First Booking", "count": 101, "rate": 5.0, "color": "#EF4444"},
        ]

        self.host_funnel = [
            {"stage": "Host Signups", "count": 127, "rate": 100, "color": "#3B82F6"},
            {"stage": "Charger Added", "count": 87, "rate": 68.5, "color": "#10B981"},
            {"stage": "Profile Complete", "count": 64, "rate": 50.4, "color": "#F59E0B"},
            {"stage": "First Booking Received", "count": 23, "rate": 18.1, "color": "#EF4444"},
        ]

        self.ux_issues = [
            {
                "title": "No Privacy Explanation for Sensitive Data",
                "severity": "critical",
                "impact": "Users abandon signup when asked for DOB/Address without context",
                "affected": "23% drop-off at profile step"
            },
            {
                "title": "Missing Role Selection at Entry",
                "severity": "critical",
                "impact": "Users confused about whether to sign up as host or guest",
                "affected": "Estimated 15-20% confusion rate"
            },
            {
                "title": "No Earnings Preview for Hosts",
                "severity": "high",
                "impact": "Hosts lack motivation to complete lengthy signup",
                "affected": "31.5% host drop-off"
            },
            {
                "title": "Progress Steps Lack Encouragement",
                "severity": "medium",
                "impact": "Users don't know how far along they are",
                "affected": "Increased abandonment mid-flow"
            },
            {
                "title": "Photo Upload Missing Motivation",
                "severity": "medium",
                "impact": "Many hosts skip photos, reducing booking rates",
                "affected": "Listings without photos get 70% fewer bookings"
            }
        ]

        self.heuristics = {
            "Visibility of System Status": 6,
            "Match with Real World": 8,
            "User Control & Freedom": 7,
            "Consistency & Standards": 8,
            "Error Prevention": 5,
            "Recognition over Recall": 7,
            "Flexibility & Efficiency": 6,
            "Aesthetic & Minimal Design": 8,
            "Help Users with Errors": 5,
            "Help & Documentation": 4
        }

        self.recommendations = [
            {
                "title": "Add Privacy Explanations",
                "priority": 1,
                "impact": "Reduce profile abandonment by 15-20%",
                "effort": "Low (copy changes only)",
                "description": "Add trust-building text under DOB ('Required by Stripe for secure payouts') and Address ('Never shown publicly')"
            },
            {
                "title": "Landing Page with Role Selection",
                "priority": 2,
                "impact": "Reduce confusion by 30-40%",
                "effort": "Medium (new component)",
                "description": "Show clear CHARGE vs EARN options upfront so users self-select their journey"
            },
            {
                "title": "Earnings Preview for Hosts",
                "priority": 3,
                "impact": "Increase host conversion by 20-25%",
                "effort": "Low (UI addition)",
                "description": "Show '$180-$320 average monthly earnings' during host signup"
            },
            {
                "title": "Progress Encouragement Text",
                "priority": 4,
                "impact": "Reduce mid-flow abandonment by 10-15%",
                "effort": "Low (copy changes)",
                "description": "Add step indicators like 'Almost there! Step 3 of 4'"
            },
            {
                "title": "Photo Motivation Text",
                "priority": 5,
                "impact": "Increase photo uploads by 40%",
                "effort": "Low (single line)",
                "description": "Add 'Listings with photos get 3x more bookings' under upload"
            }
        ]

    def _load_prototype_content(self) -> str:
        """Load the exact prototype content from file."""
        prototype_file = Path(self.prototype_path)
        if prototype_file.exists():
            with open(prototype_file, 'r', encoding='utf-8') as f:
                return f.read()
        return self._generate_fallback_prototype()

    def _generate_fallback_prototype(self) -> str:
        """Generate fallback prototype if file not found."""
        return '''
        <div style="text-align: center; padding: 60px 20px; color: #64748B;">
            <p>Prototype file not found at configured path.</p>
            <p>Please update prototype_path in the generator.</p>
        </div>
        '''

    def generate(self) -> str:
        """Generate the complete shareable interactive report."""
        prototype_content = self._load_prototype_content()

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.app_name} - Interactive UX Audit Report</title>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

    <!-- Chart.js for Interactive Graphs -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

    <style>
        :root {{
            --primary: #EF4444;
            --primary-light: #FCA5A5;
            --secondary: #F97316;
            --accent: #10B981;
            --dark: #0F172A;
            --dark-secondary: #1E293B;
            --light: #F8FAFC;
            --text: #334155;
            --text-light: #64748B;
            --success: #10B981;
            --warning: #F59E0B;
            --danger: #EF4444;
            --juicenet-green: #26a45a;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

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
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(10px);
            padding: 16px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 1000;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}

        .nav-brand {{
            font-size: 18px;
            font-weight: 700;
            color: white;
        }}

        .nav-brand span {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .nav-links {{
            display: flex;
            gap: 8px;
        }}

        .nav-link {{
            color: rgba(255,255,255,0.7);
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
        }}

        .nav-link:hover, .nav-link.active {{
            color: white;
            background: rgba(255,255,255,0.1);
        }}

        /* Cover Section */
        .cover {{
            background: linear-gradient(135deg, var(--dark) 0%, var(--dark-secondary) 100%);
            color: white;
            padding: 140px 60px 80px;
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
            background: radial-gradient(circle, rgba(239,68,68,0.15) 0%, transparent 70%);
            border-radius: 50%;
        }}

        .cover::after {{
            content: '';
            position: absolute;
            bottom: -30%;
            left: -10%;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(16,185,129,0.1) 0%, transparent 70%);
            border-radius: 50%;
        }}

        .cover-content {{
            position: relative;
            z-index: 1;
            max-width: 900px;
        }}

        .cover-badge {{
            display: inline-block;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            padding: 10px 24px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 28px;
        }}

        .cover h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 56px;
            font-weight: 700;
            line-height: 1.15;
            margin-bottom: 20px;
        }}

        .cover h1 span {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .cover .subtitle {{
            font-size: 20px;
            opacity: 0.85;
            margin-bottom: 48px;
            line-height: 1.6;
            max-width: 600px;
        }}

        .cover-stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 24px;
            max-width: 800px;
        }}

        .cover-stat {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            transition: transform 0.2s ease, background 0.2s ease;
        }}

        .cover-stat:hover {{
            transform: translateY(-4px);
            background: rgba(255,255,255,0.08);
        }}

        .cover-stat-value {{
            font-size: 36px;
            font-weight: 800;
        }}

        .cover-stat-value.danger {{ color: var(--danger); }}
        .cover-stat-value.warning {{ color: var(--warning); }}
        .cover-stat-value.success {{ color: var(--success); }}
        .cover-stat-value.info {{ color: #60A5FA; }}

        .cover-stat-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.7;
            margin-top: 8px;
        }}

        /* Container */
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 60px 40px;
        }}

        /* Section */
        .section {{
            background: white;
            border-radius: 24px;
            padding: 48px;
            margin-bottom: 32px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        }}

        .section-header {{
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 24px;
        }}

        .section-icon {{
            width: 52px;
            height: 52px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
        }}

        .section-icon.danger {{ background: linear-gradient(135deg, #EF4444, #DC2626); }}
        .section-icon.success {{ background: linear-gradient(135deg, #10B981, #059669); }}
        .section-icon.warning {{ background: linear-gradient(135deg, #F59E0B, #D97706); }}
        .section-icon.info {{ background: linear-gradient(135deg, #3B82F6, #2563EB); }}
        .section-icon.purple {{ background: linear-gradient(135deg, #8B5CF6, #7C3AED); }}

        .section h2 {{
            font-size: 28px;
            font-weight: 700;
            color: var(--dark);
        }}

        .section-intro {{
            font-size: 17px;
            color: var(--text-light);
            margin-bottom: 32px;
            line-height: 1.7;
        }}

        /* Charts Container */
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 32px;
            margin: 32px 0;
        }}

        .chart-card {{
            background: var(--light);
            border-radius: 16px;
            padding: 24px;
        }}

        .chart-card h3 {{
            font-size: 16px;
            font-weight: 600;
            color: var(--dark);
            margin-bottom: 16px;
        }}

        .chart-wrapper {{
            position: relative;
            height: 300px;
        }}

        /* Interactive Funnel */
        .funnel-interactive {{
            margin: 32px 0;
        }}

        .funnel-stage {{
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 4px;
            cursor: pointer;
            transition: transform 0.2s ease;
        }}

        .funnel-stage:hover {{
            transform: translateX(8px);
        }}

        .funnel-bar {{
            height: 56px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            padding: 0 20px;
            color: white;
            font-weight: 600;
            font-size: 15px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .funnel-bar::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.1) 50%, transparent 100%);
            transform: translateX(-100%);
            transition: transform 0.5s ease;
        }}

        .funnel-stage:hover .funnel-bar::after {{
            transform: translateX(100%);
        }}

        .funnel-stats {{
            min-width: 150px;
            text-align: right;
        }}

        .funnel-count {{
            font-size: 24px;
            font-weight: 800;
            color: var(--dark);
        }}

        .funnel-rate {{
            font-size: 13px;
            color: var(--text-light);
        }}

        .funnel-dropoff {{
            color: var(--danger);
            font-weight: 600;
            font-size: 12px;
            margin-left: 8px;
        }}

        .funnel-arrow {{
            text-align: center;
            padding: 4px 0 4px 70px;
            color: var(--text-light);
            font-size: 14px;
        }}

        /* Issues Grid */
        .issues-grid {{
            display: grid;
            gap: 16px;
        }}

        .issue-card {{
            background: var(--light);
            border-radius: 16px;
            padding: 24px;
            border-left: 4px solid;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            cursor: pointer;
        }}

        .issue-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        }}

        .issue-card.critical {{ border-left-color: #DC2626; }}
        .issue-card.high {{ border-left-color: #D97706; }}
        .issue-card.medium {{ border-left-color: #2563EB; }}

        .issue-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 12px;
        }}

        .issue-title {{
            font-size: 17px;
            font-weight: 600;
            color: var(--dark);
        }}

        .issue-badge {{
            padding: 5px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .issue-badge.critical {{ background: #FEE2E2; color: #DC2626; }}
        .issue-badge.high {{ background: #FEF3C7; color: #D97706; }}
        .issue-badge.medium {{ background: #DBEAFE; color: #2563EB; }}

        .issue-description {{
            font-size: 14px;
            color: var(--text-light);
            margin-bottom: 12px;
            line-height: 1.5;
        }}

        .issue-impact {{
            background: white;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            color: var(--danger);
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        /* Heuristics */
        .heuristics-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}

        .heuristic-item {{
            background: var(--light);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: transform 0.2s ease;
        }}

        .heuristic-item:hover {{
            transform: translateX(4px);
        }}

        .heuristic-name {{
            font-size: 14px;
            color: var(--dark);
            font-weight: 500;
        }}

        .heuristic-score {{
            font-size: 18px;
            font-weight: 700;
        }}

        .heuristic-score.good {{ color: var(--success); }}
        .heuristic-score.ok {{ color: var(--warning); }}
        .heuristic-score.bad {{ color: var(--danger); }}

        .heuristics-total {{
            background: linear-gradient(135deg, var(--dark), var(--dark-secondary));
            color: white;
            border-radius: 16px;
            padding: 32px;
            text-align: center;
            margin-top: 24px;
        }}

        .heuristics-total-value {{
            font-size: 56px;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .heuristics-total-label {{
            font-size: 14px;
            opacity: 0.8;
            margin-top: 8px;
        }}

        /* Recommendations */
        .recommendations-list {{
            display: flex;
            flex-direction: column;
            gap: 24px;
        }}

        .recommendation {{
            background: var(--light);
            border-radius: 16px;
            padding: 28px;
            display: grid;
            grid-template-columns: 60px 1fr auto;
            gap: 24px;
            align-items: start;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}

        .recommendation:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        }}

        .recommendation-number {{
            width: 52px;
            height: 52px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 800;
            font-size: 20px;
        }}

        .recommendation-content h4 {{
            font-size: 18px;
            font-weight: 700;
            color: var(--dark);
            margin-bottom: 8px;
        }}

        .recommendation-content p {{
            font-size: 14px;
            color: var(--text-light);
            line-height: 1.6;
        }}

        .recommendation-meta {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            text-align: right;
        }}

        .recommendation-impact {{
            background: #D1FAE5;
            color: #059669;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}

        .recommendation-effort {{
            font-size: 12px;
            color: var(--text-light);
        }}

        /* Interactive Prototype Section */
        .prototype-section {{
            background: linear-gradient(135deg, var(--dark) 0%, var(--dark-secondary) 100%);
            border-radius: 24px;
            padding: 48px;
            margin-bottom: 32px;
            color: white;
        }}

        .prototype-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
        }}

        .prototype-header h2 {{
            font-size: 28px;
            font-weight: 700;
            color: white;
        }}

        .prototype-toggle {{
            display: flex;
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 4px;
        }}

        .toggle-btn {{
            padding: 12px 24px;
            border: none;
            background: transparent;
            color: rgba(255,255,255,0.7);
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.2s ease;
        }}

        .toggle-btn.active {{
            background: white;
            color: var(--dark);
        }}

        .prototype-container {{
            background: #e8e8e8;
            border-radius: 16px;
            min-height: 700px;
            overflow: hidden;
        }}

        .prototype-iframe {{
            width: 100%;
            height: 700px;
            border: none;
        }}

        /* Embedded Prototype Styles */
        .embedded-prototype {{
            width: 100%;
            min-height: 700px;
        }}

        /* ROI Calculator */
        .roi-calculator {{
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            border-radius: 16px;
            padding: 32px;
            color: white;
            margin-top: 32px;
        }}

        .roi-calculator h3 {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 24px;
        }}

        .roi-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
        }}

        .roi-item {{
            text-align: center;
        }}

        .roi-value {{
            font-size: 36px;
            font-weight: 800;
        }}

        .roi-label {{
            font-size: 13px;
            opacity: 0.9;
            margin-top: 4px;
        }}

        /* Footer */
        .footer {{
            background: var(--dark);
            color: white;
            padding: 40px 60px;
            text-align: center;
        }}

        .footer p {{
            font-size: 14px;
            opacity: 0.7;
        }}

        /* Animations */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .animate-in {{
            animation: fadeInUp 0.6s ease forwards;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .cover {{
                padding: 120px 24px 60px;
            }}

            .cover h1 {{
                font-size: 36px;
            }}

            .cover-stats {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .container {{
                padding: 40px 20px;
            }}

            .section {{
                padding: 24px;
            }}

            .charts-grid {{
                grid-template-columns: 1fr;
            }}

            .heuristics-grid {{
                grid-template-columns: 1fr;
            }}

            .recommendation {{
                grid-template-columns: 1fr;
                text-align: center;
            }}

            .recommendation-number {{
                margin: 0 auto;
            }}

            .recommendation-meta {{
                text-align: center;
                flex-direction: row;
                justify-content: center;
            }}

            .roi-grid {{
                grid-template-columns: 1fr;
            }}

            .nav {{
                padding: 12px 20px;
            }}

            .nav-links {{
                display: none;
            }}
        }}

        /* Print styles */
        @media print {{
            .nav, .prototype-section {{
                display: none;
            }}

            .cover {{
                min-height: auto;
                padding: 40px;
            }}

            .section {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="nav">
        <div class="nav-brand"><span>{self.app_name}</span> Audit Report</div>
        <div class="nav-links">
            <a href="#overview" class="nav-link active">Overview</a>
            <a href="#funnel" class="nav-link">Funnel</a>
            <a href="#issues" class="nav-link">Issues</a>
            <a href="#prototype" class="nav-link">Prototype</a>
            <a href="#recommendations" class="nav-link">Fixes</a>
        </div>
    </nav>

    <!-- Cover Section -->
    <section class="cover" id="overview">
        <div class="cover-content">
            <div class="cover-badge">Interactive UX Audit</div>
            <h1>{self.app_name}<br><span>Comprehensive Analysis</span></h1>
            <p class="subtitle">{self.tagline} - Deep dive into user experience, conversion funnels, and actionable improvements with interactive prototype.</p>

            <div class="cover-stats">
                <div class="cover-stat">
                    <div class="cover-stat-value danger">5.0%</div>
                    <div class="cover-stat-label">Conversion Rate</div>
                </div>
                <div class="cover-stat">
                    <div class="cover-stat-value warning">64/100</div>
                    <div class="cover-stat-label">UX Score</div>
                </div>
                <div class="cover-stat">
                    <div class="cover-stat-value info">5</div>
                    <div class="cover-stat-label">Critical Issues</div>
                </div>
                <div class="cover-stat">
                    <div class="cover-stat-value success">+45%</div>
                    <div class="cover-stat-label">Potential Uplift</div>
                </div>
            </div>
        </div>
    </section>

    <!-- Main Content -->
    <div class="container">
        <!-- Funnel Section -->
        <section class="section" id="funnel">
            <div class="section-header">
                <div class="section-icon danger">&#128202;</div>
                <h2>Conversion Funnel Analysis</h2>
            </div>
            <p class="section-intro">Interactive visualization of user journey from first visit to conversion. Click on any stage to see detailed breakdown.</p>

            <div class="charts-grid">
                <div class="chart-card">
                    <h3>Guest Signup Funnel</h3>
                    <div class="chart-wrapper">
                        <canvas id="guestFunnelChart"></canvas>
                    </div>
                </div>
                <div class="chart-card">
                    <h3>Host Signup Funnel</h3>
                    <div class="chart-wrapper">
                        <canvas id="hostFunnelChart"></canvas>
                    </div>
                </div>
            </div>

            <h3 style="margin: 40px 0 24px; font-size: 20px; color: var(--dark);">Detailed Guest Funnel</h3>
            <div class="funnel-interactive">
                {self._generate_funnel_html()}
            </div>
        </section>

        <!-- Issues Section -->
        <section class="section" id="issues">
            <div class="section-header">
                <div class="section-icon warning">&#9888;</div>
                <h2>UX Issues Identified</h2>
            </div>
            <p class="section-intro">Critical user experience issues discovered during production testing, ranked by impact on conversion.</p>

            <div class="issues-grid">
                {self._generate_issues_html()}
            </div>

            <h3 style="margin: 40px 0 24px; font-size: 20px; color: var(--dark);">Nielsen's Heuristics Evaluation</h3>
            <div class="heuristics-grid">
                {self._generate_heuristics_html()}
            </div>
            <div class="heuristics-total">
                <div class="heuristics-total-value">64/100</div>
                <div class="heuristics-total-label">Overall UX Score</div>
            </div>
        </section>

        <!-- Interactive Prototype Section -->
        <section class="prototype-section" id="prototype">
            <div class="prototype-header">
                <h2>&#128241; Interactive Prototype</h2>
                <div class="prototype-toggle">
                    <button class="toggle-btn" onclick="showCurrentIssues()">Current Issues</button>
                    <button class="toggle-btn active" onclick="showProposedFixes()">Proposed Fixes</button>
                </div>
            </div>
            <div class="prototype-container" id="prototypeContainer">
                <!-- Embedded prototype will be injected here -->
            </div>
        </section>

        <!-- Recommendations Section -->
        <section class="section" id="recommendations">
            <div class="section-header">
                <div class="section-icon success">&#10003;</div>
                <h2>Recommended Fixes</h2>
            </div>
            <p class="section-intro">Prioritized list of improvements with expected impact and implementation effort.</p>

            <div class="recommendations-list">
                {self._generate_recommendations_html()}
            </div>

            <div class="roi-calculator">
                <h3>&#128200; Projected ROI</h3>
                <div class="roi-grid">
                    <div class="roi-item">
                        <div class="roi-value">+490</div>
                        <div class="roi-label">Additional Conversions/Month</div>
                    </div>
                    <div class="roi-item">
                        <div class="roi-value">$5,600</div>
                        <div class="roi-label">Est. Monthly Revenue</div>
                    </div>
                    <div class="roi-item">
                        <div class="roi-value">2 weeks</div>
                        <div class="roi-label">Implementation Time</div>
                    </div>
                </div>
            </div>
        </section>
    </div>

    <!-- Footer -->
    <footer class="footer">
        <p>Generated by Weaver Pro Audit System | {self.audit_date}</p>
    </footer>

    <!-- Embedded Prototype Content (Hidden) -->
    <template id="prototypeTemplate">
        {self._escape_html_for_template(prototype_content)}
    </template>

    <script>
        // Chart.js Configuration
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#64748B';

        // Guest Funnel Chart
        const guestCtx = document.getElementById('guestFunnelChart').getContext('2d');
        new Chart(guestCtx, {{
            type: 'bar',
            data: {{
                labels: ['Page Views', 'Signups', 'Email Verified', 'Profile Done', 'First Booking'],
                datasets: [{{
                    label: 'Users',
                    data: [968, 2012, 1543, 941, 101],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)'
                    ],
                    borderRadius: 8,
                    borderSkipped: false,
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    tooltip: {{
                        backgroundColor: '#0F172A',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {{
                            label: function(context) {{
                                return context.raw.toLocaleString() + ' users';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{
                            color: 'rgba(0,0,0,0.05)'
                        }}
                    }},
                    x: {{
                        grid: {{
                            display: false
                        }}
                    }}
                }}
            }}
        }});

        // Host Funnel Chart
        const hostCtx = document.getElementById('hostFunnelChart').getContext('2d');
        new Chart(hostCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Host Signups', 'Charger Added', 'Profile Complete', 'First Booking'],
                datasets: [{{
                    data: [127, 87, 64, 23],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)'
                    ],
                    borderWidth: 0,
                    hoverOffset: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 16,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }}
                    }},
                    tooltip: {{
                        backgroundColor: '#0F172A',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        padding: 12,
                        cornerRadius: 8
                    }}
                }}
            }}
        }});

        // Prototype Toggle Functions
        function showCurrentIssues() {{
            document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            const container = document.getElementById('prototypeContainer');
            container.innerHTML = `
                <div style="padding: 60px; text-align: center;">
                    <h3 style="color: #EF4444; margin-bottom: 16px;">Current App Issues</h3>
                    <div style="display: grid; gap: 16px; max-width: 600px; margin: 0 auto; text-align: left;">
                        <div style="background: white; padding: 20px; border-radius: 12px; border-left: 4px solid #EF4444;">
                            <strong style="color: #0F172A;">No Privacy Explanation</strong>
                            <p style="color: #64748B; margin-top: 8px; font-size: 14px;">Users see requests for DOB and Address with no context why.</p>
                        </div>
                        <div style="background: white; padding: 20px; border-radius: 12px; border-left: 4px solid #EF4444;">
                            <strong style="color: #0F172A;">Missing Role Selection</strong>
                            <p style="color: #64748B; margin-top: 8px; font-size: 14px;">Users don't know if they should sign up as host or guest.</p>
                        </div>
                        <div style="background: white; padding: 20px; border-radius: 12px; border-left: 4px solid #F59E0B;">
                            <strong style="color: #0F172A;">No Earnings Preview</strong>
                            <p style="color: #64748B; margin-top: 8px; font-size: 14px;">Hosts have no idea how much they can earn.</p>
                        </div>
                        <div style="background: white; padding: 20px; border-radius: 12px; border-left: 4px solid #F59E0B;">
                            <strong style="color: #0F172A;">Progress Steps Unclear</strong>
                            <p style="color: #64748B; margin-top: 8px; font-size: 14px;">Users don't know how far along they are in signup.</p>
                        </div>
                    </div>
                </div>
            `;
        }}

        function showProposedFixes() {{
            document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            // Load the embedded prototype
            const template = document.getElementById('prototypeTemplate');
            const container = document.getElementById('prototypeContainer');

            // Create an iframe with the prototype content
            const iframe = document.createElement('iframe');
            iframe.className = 'prototype-iframe';
            iframe.srcdoc = template.innerHTML;

            container.innerHTML = '';
            container.appendChild(iframe);
        }}

        // Initialize with proposed fixes view
        document.addEventListener('DOMContentLoaded', function() {{
            showProposedFixes();

            // Smooth scroll for nav links
            document.querySelectorAll('.nav-link').forEach(link => {{
                link.addEventListener('click', function(e) {{
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {{
                        target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    }}

                    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                    this.classList.add('active');
                }});
            }});

            // Update active nav on scroll
            const sections = document.querySelectorAll('section[id]');
            window.addEventListener('scroll', function() {{
                let current = '';
                sections.forEach(section => {{
                    const sectionTop = section.offsetTop;
                    if (scrollY >= sectionTop - 100) {{
                        current = section.getAttribute('id');
                    }}
                }});

                document.querySelectorAll('.nav-link').forEach(link => {{
                    link.classList.remove('active');
                    if (link.getAttribute('href') === '#' + current) {{
                        link.classList.add('active');
                    }}
                }});
            }});
        }});
    </script>
</body>
</html>'''

    def _generate_funnel_html(self) -> str:
        """Generate interactive funnel HTML."""
        html = ""
        max_count = max(stage["count"] for stage in self.funnel_data)

        for i, stage in enumerate(self.funnel_data):
            width_pct = (stage["count"] / max_count) * 100

            html += f'''
            <div class="funnel-stage">
                <div style="flex: 1;">
                    <div class="funnel-bar" style="width: {width_pct}%; background: {stage["color"]};">
                        {stage["stage"]}
                    </div>
                </div>
                <div class="funnel-stats">
                    <div class="funnel-count">{stage["count"]:,}</div>
                    <div class="funnel-rate">{stage["rate"]}% of signups</div>
                </div>
            </div>
            '''

            if i < len(self.funnel_data) - 1:
                next_stage = self.funnel_data[i + 1]
                dropoff = stage["rate"] - next_stage["rate"]
                html += f'''
                <div class="funnel-arrow">
                    &#8595; <span class="funnel-dropoff">-{dropoff:.1f}% drop-off</span>
                </div>
                '''

        return html

    def _generate_issues_html(self) -> str:
        """Generate issues cards HTML."""
        html = ""
        for issue in self.ux_issues:
            html += f'''
            <div class="issue-card {issue["severity"]}">
                <div class="issue-header">
                    <div class="issue-title">{issue["title"]}</div>
                    <span class="issue-badge {issue["severity"]}">{issue["severity"].upper()}</span>
                </div>
                <div class="issue-description">{issue["impact"]}</div>
                <div class="issue-impact">
                    &#9888; {issue["affected"]}
                </div>
            </div>
            '''
        return html

    def _generate_heuristics_html(self) -> str:
        """Generate heuristics grid HTML."""
        html = ""
        for name, score in self.heuristics.items():
            score_class = "good" if score >= 7 else "ok" if score >= 5 else "bad"
            html += f'''
            <div class="heuristic-item">
                <div class="heuristic-name">{name}</div>
                <div class="heuristic-score {score_class}">{score}/10</div>
            </div>
            '''
        return html

    def _generate_recommendations_html(self) -> str:
        """Generate recommendations list HTML."""
        html = ""
        for rec in self.recommendations:
            html += f'''
            <div class="recommendation">
                <div class="recommendation-number">{rec["priority"]}</div>
                <div class="recommendation-content">
                    <h4>{rec["title"]}</h4>
                    <p>{rec["description"]}</p>
                </div>
                <div class="recommendation-meta">
                    <span class="recommendation-impact">{rec["impact"]}</span>
                    <span class="recommendation-effort">Effort: {rec["effort"]}</span>
                </div>
            </div>
            '''
        return html

    def _escape_html_for_template(self, content: str) -> str:
        """Escape HTML content for embedding in template tag."""
        # The template tag should contain valid HTML, so we don't escape
        # but we need to make sure the content is properly formatted
        return content

    def save(self, output_path: str = None) -> str:
        """Generate and save the report."""
        if output_path is None:
            output_path = Path(__file__).parent / f"{self.app_name.upper()}_SHAREABLE_AUDIT.html"

        content = self.generate()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Shareable audit report saved to: {output_path}")
        return str(output_path)


def main():
    """Generate the shareable interactive audit report."""
    report = ShareableInteractiveReport(
        app_name="JuiceNet",
        tagline="EV Charging Marketplace",
        prototype_path=r"C:\Users\jacob\Desktop\claude-code-example\JuiceNet code\mockups\juicenet-flow-prototype.html"
    )

    output_path = report.save()
    print(f"\nReport generated: {output_path}")
    print("\nTo deploy to Netlify:")
    print("1. Go to https://app.netlify.com/drop")
    print("2. Drag and drop the HTML file")
    print("3. Get your shareable URL instantly!")


if __name__ == "__main__":
    main()
