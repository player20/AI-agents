"""
Business Digitization Report Generator
Creates professional client-ready reports alongside prototypes.

Generates:
- Executive Summary
- Business Analysis
- Feature Recommendations (with justification)
- Design System (colors, fonts, mood)
- Screen Breakdown
- Implementation Roadmap
- Investment Estimate
- Next Steps
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    company_name: str = "Your Agency"
    company_tagline: str = "Digital Transformation Specialists"
    contact_email: str = "hello@youragency.com"
    contact_phone: str = "(555) 123-4567"


class BusinessReport:
    """Generate professional business digitization reports"""

    # Pricing estimates by feature complexity
    FEATURE_COSTS = {
        'high': {'min': 8000, 'max': 15000, 'time': '3-4 weeks'},
        'medium': {'min': 4000, 'max': 8000, 'time': '2-3 weeks'},
        'low': {'min': 1500, 'max': 4000, 'time': '1-2 weeks'}
    }

    # Industry insights
    INDUSTRY_INSIGHTS = {
        'restaurant': {
            'market_size': '$899 billion (US food service)',
            'digital_adoption': '67% of consumers prefer mobile ordering',
            'key_trend': 'Contactless ordering increased 300% since 2020',
            'competitor_apps': ['Toast', 'Square', 'ChowNow', 'Olo'],
            'success_metric': 'Average 23% increase in order value with mobile apps'
        },
        'fitness': {
            'market_size': '$96 billion (US fitness industry)',
            'digital_adoption': '72% of gym members want mobile booking',
            'key_trend': 'Hybrid fitness (in-person + digital) is the new standard',
            'competitor_apps': ['Mindbody', 'ClassPass', 'Gympass', 'Wodify'],
            'success_metric': 'Studios with apps see 34% higher retention'
        },
        'retail': {
            'market_size': '$5.5 trillion (US retail)',
            'digital_adoption': '85% of consumers research online before buying',
            'key_trend': 'Omnichannel experience is expected, not optional',
            'competitor_apps': ['Shopify', 'Square', 'Lightspeed'],
            'success_metric': 'Mobile commerce growing 25% year-over-year'
        },
        'service': {
            'market_size': '$1.2 trillion (US home services)',
            'digital_adoption': '78% prefer online booking over phone calls',
            'key_trend': 'Real-time tracking is now expected (like Uber)',
            'competitor_apps': ['Housecall Pro', 'Jobber', 'ServiceTitan'],
            'success_metric': 'Businesses with apps close 40% more jobs'
        },
        'healthcare': {
            'market_size': '$4.3 trillion (US healthcare)',
            'digital_adoption': '76% want telehealth options',
            'key_trend': 'Patient portals are now standard expectation',
            'competitor_apps': ['Zocdoc', 'Healthgrades', 'MyChart'],
            'success_metric': 'Digital scheduling reduces no-shows by 38%'
        },
        'beauty': {
            'market_size': '$63 billion (US beauty services)',
            'digital_adoption': '82% book appointments online',
            'key_trend': 'Instagram-worthy experiences drive bookings',
            'competitor_apps': ['Vagaro', 'Fresha', 'Boulevard', 'GlossGenius'],
            'success_metric': 'Salons with apps see 45% more repeat bookings'
        },
        'education': {
            'market_size': '$76 billion (US tutoring/supplemental)',
            'digital_adoption': '89% prefer online learning options',
            'key_trend': 'Hybrid learning is permanent, not temporary',
            'competitor_apps': ['Teachable', 'Thinkific', 'Outschool'],
            'success_metric': 'Online course completion 60% higher with apps'
        },
        'realestate': {
            'market_size': '$226 billion (US real estate services)',
            'digital_adoption': '97% of home buyers search online',
            'key_trend': 'Virtual tours are now expected, not a novelty',
            'competitor_apps': ['Zillow', 'Redfin', 'Realtor.com'],
            'success_metric': 'Agents with apps close 28% more deals'
        }
    }

    def __init__(self, config: ReportConfig = None):
        self.config = config or ReportConfig()

    def generate_report(self, plan, output_path: str = None) -> str:
        """Generate a complete business report"""

        if not output_path:
            safe_name = plan.business_name.lower().replace(' ', '_')[:20]
            output_path = f"{safe_name}_report.html"

        # Get industry insights
        insights = self.INDUSTRY_INSIGHTS.get(plan.industry, self.INDUSTRY_INSIGHTS['service'])

        # Calculate costs
        total_min = 0
        total_max = 0
        feature_breakdown = []

        for feature in plan.core_features:
            priority = feature.get('priority', 'medium')
            costs = self.FEATURE_COSTS.get(priority, self.FEATURE_COSTS['medium'])
            total_min += costs['min']
            total_max += costs['max']
            feature_breakdown.append({
                'name': feature['name'],
                'description': feature['description'],
                'priority': priority,
                'cost_range': f"${costs['min']:,} - ${costs['max']:,}",
                'timeline': costs['time']
            })

        # Build deliberation log HTML
        deliberation_html = ""
        for thought in plan.deliberation_log:
            if thought.decision:
                deliberation_html += f"""
                <div class="deliberation-item">
                    <span class="agent-badge">{thought.agent}</span>
                    <p>{thought.decision}</p>
                </div>
                """

        # Build features HTML
        features_html = ""
        for f in feature_breakdown:
            priority_class = f['priority']
            features_html += f"""
            <tr>
                <td><strong>{f['name']}</strong><br><small>{f['description']}</small></td>
                <td><span class="priority-badge {priority_class}">{f['priority'].upper()}</span></td>
                <td>{f['cost_range']}</td>
                <td>{f['timeline']}</td>
            </tr>
            """

        # Build screens HTML
        screens_html = ""
        for i, screen in enumerate(plan.screens, 1):
            screens_html += f"""
            <div class="screen-card">
                <div class="screen-number">{i}</div>
                <div class="screen-info">
                    <h4>{screen['name']}</h4>
                    <p>{screen['description']}</p>
                </div>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{plan.business_name} - Digital Transformation Proposal</title>
    <style>
        :root {{
            --primary: {plan.primary_color};
            --secondary: {plan.secondary_color};
            --accent: {plan.accent_color};
            --dark: #1e293b;
            --light: #f8fafc;
            --text: #334155;
            --muted: #64748b;
        }}

        @page {{
            margin: 0.5in;
            size: letter;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: white;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px;
        }}

        /* Cover Page */
        .cover {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 80px 60px;
            margin: -40px -40px 40px -40px;
            text-align: center;
            page-break-after: always;
        }}

        .cover h1 {{
            font-size: 42px;
            margin-bottom: 16px;
            font-weight: 700;
        }}

        .cover .subtitle {{
            font-size: 24px;
            opacity: 0.9;
            margin-bottom: 40px;
        }}

        .cover .meta {{
            font-size: 14px;
            opacity: 0.8;
        }}

        .cover .date {{
            margin-top: 60px;
            font-size: 16px;
        }}

        /* Section Styling */
        .section {{
            margin-bottom: 40px;
            page-break-inside: avoid;
        }}

        .section-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 3px solid var(--primary);
        }}

        .section-number {{
            background: var(--primary);
            color: white;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 18px;
        }}

        .section-header h2 {{
            font-size: 24px;
            color: var(--dark);
        }}

        /* Executive Summary */
        .exec-summary {{
            background: var(--light);
            padding: 30px;
            border-radius: 12px;
            border-left: 4px solid var(--primary);
        }}

        .exec-summary h3 {{
            color: var(--primary);
            margin-bottom: 16px;
        }}

        .exec-summary p {{
            margin-bottom: 12px;
        }}

        .highlight-box {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            text-align: center;
        }}

        .highlight-item .value {{
            font-size: 28px;
            font-weight: 700;
            color: var(--primary);
        }}

        .highlight-item .label {{
            font-size: 12px;
            color: var(--muted);
            margin-top: 4px;
        }}

        /* Industry Insights */
        .insight-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}

        .insight-card {{
            background: var(--light);
            padding: 20px;
            border-radius: 8px;
        }}

        .insight-card .label {{
            font-size: 12px;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}

        .insight-card .value {{
            font-size: 16px;
            font-weight: 600;
            color: var(--dark);
        }}

        .trend-callout {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            padding: 24px;
            border-radius: 12px;
            margin-top: 20px;
        }}

        .trend-callout .label {{
            opacity: 0.8;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .trend-callout .value {{
            font-size: 20px;
            font-weight: 600;
            margin-top: 8px;
        }}

        /* Design System */
        .design-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }}

        .color-palette {{
            display: flex;
            gap: 12px;
        }}

        .color-swatch {{
            width: 60px;
            height: 60px;
            border-radius: 12px;
            display: flex;
            align-items: flex-end;
            justify-content: center;
            padding-bottom: 8px;
            font-size: 10px;
            color: white;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }}

        .font-preview {{
            background: var(--light);
            padding: 20px;
            border-radius: 8px;
        }}

        .font-preview .font-name {{
            font-size: 14px;
            color: var(--muted);
            margin-bottom: 8px;
        }}

        .font-preview .font-sample {{
            font-size: 24px;
            color: var(--dark);
        }}

        .mood-tags {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 16px;
        }}

        .mood-tag {{
            background: var(--primary);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
        }}

        /* Features Table */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }}

        th, td {{
            padding: 14px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}

        th {{
            background: var(--light);
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--muted);
        }}

        .priority-badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }}

        .priority-badge.high {{
            background: #fee2e2;
            color: #dc2626;
        }}

        .priority-badge.medium {{
            background: #fef3c7;
            color: #d97706;
        }}

        .priority-badge.low {{
            background: #d1fae5;
            color: #059669;
        }}

        /* Screens */
        .screens-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}

        .screen-card {{
            display: flex;
            gap: 16px;
            background: var(--light);
            padding: 20px;
            border-radius: 8px;
        }}

        .screen-number {{
            width: 40px;
            height: 40px;
            background: var(--primary);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            flex-shrink: 0;
        }}

        .screen-info h4 {{
            color: var(--dark);
            margin-bottom: 4px;
        }}

        .screen-info p {{
            font-size: 14px;
            color: var(--muted);
        }}

        /* Timeline */
        .timeline {{
            position: relative;
            padding-left: 30px;
        }}

        .timeline::before {{
            content: '';
            position: absolute;
            left: 8px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: var(--primary);
        }}

        .timeline-item {{
            position: relative;
            padding-bottom: 24px;
        }}

        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -26px;
            top: 4px;
            width: 14px;
            height: 14px;
            background: var(--primary);
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 0 0 2px var(--primary);
        }}

        .timeline-item .phase {{
            font-size: 12px;
            color: var(--primary);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .timeline-item h4 {{
            margin: 4px 0 8px;
            color: var(--dark);
        }}

        .timeline-item p {{
            font-size: 14px;
            color: var(--muted);
        }}

        /* Investment */
        .investment-box {{
            background: linear-gradient(135deg, var(--dark), #334155);
            color: white;
            padding: 40px;
            border-radius: 16px;
            text-align: center;
        }}

        .investment-box .label {{
            font-size: 14px;
            opacity: 0.8;
            margin-bottom: 8px;
        }}

        .investment-box .amount {{
            font-size: 48px;
            font-weight: 700;
        }}

        .investment-box .note {{
            font-size: 14px;
            opacity: 0.7;
            margin-top: 16px;
        }}

        .roi-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 24px;
        }}

        .roi-item {{
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 8px;
        }}

        .roi-item .value {{
            font-size: 24px;
            font-weight: 700;
        }}

        .roi-item .label {{
            font-size: 12px;
            opacity: 0.8;
            margin-top: 4px;
        }}

        /* Deliberation Log */
        .deliberation-item {{
            display: flex;
            gap: 12px;
            padding: 12px;
            background: var(--light);
            border-radius: 8px;
            margin-bottom: 8px;
        }}

        .agent-badge {{
            background: var(--primary);
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
            height: fit-content;
        }}

        .deliberation-item p {{
            font-size: 14px;
            color: var(--text);
        }}

        /* Next Steps */
        .next-steps {{
            background: var(--light);
            padding: 30px;
            border-radius: 12px;
        }}

        .step-item {{
            display: flex;
            gap: 16px;
            margin-bottom: 20px;
        }}

        .step-number {{
            width: 32px;
            height: 32px;
            background: var(--primary);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            flex-shrink: 0;
        }}

        .step-content h4 {{
            color: var(--dark);
            margin-bottom: 4px;
        }}

        .step-content p {{
            font-size: 14px;
            color: var(--muted);
        }}

        /* Footer */
        .footer {{
            margin-top: 60px;
            padding-top: 30px;
            border-top: 2px solid var(--light);
            text-align: center;
        }}

        .footer .company {{
            font-size: 20px;
            font-weight: 700;
            color: var(--primary);
        }}

        .footer .tagline {{
            color: var(--muted);
            margin: 8px 0 16px;
        }}

        .footer .contact {{
            font-size: 14px;
            color: var(--text);
        }}

        /* Print Styles */
        @media print {{
            .cover {{
                margin: -0.5in;
                padding: 1in;
            }}
            .section {{
                page-break-inside: avoid;
            }}
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Cover Page -->
        <div class="cover">
            <h1>{plan.business_name}</h1>
            <p class="subtitle">Digital Transformation Proposal</p>
            <p class="meta">
                Prepared exclusively for {plan.business_name}<br>
                by {self.config.company_name}
            </p>
            <p class="date">{datetime.now().strftime('%B %d, %Y')}</p>
        </div>

        <!-- Executive Summary -->
        <div class="section">
            <div class="section-header">
                <div class="section-number">1</div>
                <h2>Executive Summary</h2>
            </div>
            <div class="exec-summary">
                <h3>The Opportunity</h3>
                <p>
                    <strong>{plan.business_name}</strong> has the opportunity to transform customer experience
                    and drive significant growth through a custom mobile application. Based on our analysis
                    of the {plan.industry} industry, businesses with mobile apps see measurable improvements
                    in customer engagement, retention, and revenue.
                </p>
                <p>
                    Our AI-powered analysis has identified the optimal features, design direction, and
                    implementation strategy tailored specifically for your business.
                </p>
                <div class="highlight-box">
                    <div class="highlight-item">
                        <div class="value">{len(plan.core_features)}</div>
                        <div class="label">Core Features</div>
                    </div>
                    <div class="highlight-item">
                        <div class="value">{len(plan.screens)}</div>
                        <div class="label">App Screens</div>
                    </div>
                    <div class="highlight-item">
                        <div class="value">${total_min//1000}K-${total_max//1000}K</div>
                        <div class="label">Investment Range</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Industry Insights -->
        <div class="section">
            <div class="section-header">
                <div class="section-number">2</div>
                <h2>Industry Insights</h2>
            </div>
            <div class="insight-grid">
                <div class="insight-card">
                    <div class="label">Market Size</div>
                    <div class="value">{insights['market_size']}</div>
                </div>
                <div class="insight-card">
                    <div class="label">Digital Adoption</div>
                    <div class="value">{insights['digital_adoption']}</div>
                </div>
                <div class="insight-card">
                    <div class="label">Success Metric</div>
                    <div class="value">{insights['success_metric']}</div>
                </div>
                <div class="insight-card">
                    <div class="label">Competitors</div>
                    <div class="value">{', '.join(insights['competitor_apps'][:3])}</div>
                </div>
            </div>
            <div class="trend-callout">
                <div class="label">Key Industry Trend</div>
                <div class="value">{insights['key_trend']}</div>
            </div>
        </div>

        <!-- Design System -->
        <div class="section">
            <div class="section-header">
                <div class="section-number">3</div>
                <h2>Design System</h2>
            </div>
            <p style="margin-bottom: 20px; color: var(--muted);">
                Based on {plan.industry} industry best practices and your brand personality,
                we recommend a <strong>{plan.style_mood}</strong> visual direction.
            </p>
            <div class="design-grid">
                <div>
                    <h4 style="margin-bottom: 12px; color: var(--dark);">Color Palette</h4>
                    <div class="color-palette">
                        <div class="color-swatch" style="background: {plan.primary_color}">{plan.primary_color}</div>
                        <div class="color-swatch" style="background: {plan.secondary_color}">{plan.secondary_color}</div>
                        <div class="color-swatch" style="background: {plan.accent_color}">{plan.accent_color}</div>
                    </div>
                </div>
                <div>
                    <h4 style="margin-bottom: 12px; color: var(--dark);">Typography</h4>
                    <div class="font-preview">
                        <div class="font-name">Headings: {plan.heading_font}</div>
                        <div class="font-sample" style="font-family: '{plan.heading_font}', sans-serif;">Aa Bb Cc 123</div>
                    </div>
                    <div class="font-preview" style="margin-top: 12px;">
                        <div class="font-name">Body: {plan.body_font}</div>
                        <div class="font-sample" style="font-family: '{plan.body_font}', sans-serif; font-size: 18px;">Aa Bb Cc 123</div>
                    </div>
                </div>
            </div>
            <div class="mood-tags">
                <span class="mood-tag">{plan.style_mood}</span>
            </div>
        </div>

        <!-- Recommended Features -->
        <div class="section">
            <div class="section-header">
                <div class="section-number">4</div>
                <h2>Recommended Features</h2>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Feature</th>
                        <th>Priority</th>
                        <th>Investment</th>
                        <th>Timeline</th>
                    </tr>
                </thead>
                <tbody>
                    {features_html}
                </tbody>
            </table>
        </div>

        <!-- App Screens -->
        <div class="section">
            <div class="section-header">
                <div class="section-number">5</div>
                <h2>App Screens</h2>
            </div>
            <div class="screens-grid">
                {screens_html}
            </div>
        </div>

        <!-- Implementation Timeline -->
        <div class="section">
            <div class="section-header">
                <div class="section-number">6</div>
                <h2>Implementation Timeline</h2>
            </div>
            <div class="timeline">
                <div class="timeline-item">
                    <div class="phase">Phase 1 - Week 1-2</div>
                    <h4>Discovery & Design</h4>
                    <p>Finalize requirements, create detailed wireframes, and establish design system</p>
                </div>
                <div class="timeline-item">
                    <div class="phase">Phase 2 - Week 3-6</div>
                    <h4>Development - MVP Features</h4>
                    <p>Build core functionality: {', '.join([f['name'] for f in plan.core_features[:3]])}</p>
                </div>
                <div class="timeline-item">
                    <div class="phase">Phase 3 - Week 7-8</div>
                    <h4>Testing & Refinement</h4>
                    <p>Quality assurance, user testing, and performance optimization</p>
                </div>
                <div class="timeline-item">
                    <div class="phase">Phase 4 - Week 9-10</div>
                    <h4>Launch & Support</h4>
                    <p>App store submission, launch support, and initial user onboarding</p>
                </div>
            </div>
        </div>

        <!-- Investment -->
        <div class="section">
            <div class="section-header">
                <div class="section-number">7</div>
                <h2>Investment</h2>
            </div>
            <div class="investment-box">
                <div class="label">Total Project Investment</div>
                <div class="amount">${total_min:,} - ${total_max:,}</div>
                <div class="note">Includes design, development, testing, and launch support</div>
                <div class="roi-grid">
                    <div class="roi-item">
                        <div class="value">10-20%</div>
                        <div class="label">Expected Revenue Increase</div>
                    </div>
                    <div class="roi-item">
                        <div class="value">30-40%</div>
                        <div class="label">Customer Retention Boost</div>
                    </div>
                    <div class="roi-item">
                        <div class="value">6-12 mo</div>
                        <div class="label">Typical ROI Timeline</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- AI Analysis -->
        <div class="section">
            <div class="section-header">
                <div class="section-number">8</div>
                <h2>AI Analysis Log</h2>
            </div>
            <p style="margin-bottom: 16px; color: var(--muted);">
                Our AI agents analyzed your business and made these recommendations:
            </p>
            {deliberation_html}
        </div>

        <!-- Next Steps -->
        <div class="section">
            <div class="section-header">
                <div class="section-number">9</div>
                <h2>Next Steps</h2>
            </div>
            <div class="next-steps">
                <div class="step-item">
                    <div class="step-number">1</div>
                    <div class="step-content">
                        <h4>Review This Proposal</h4>
                        <p>Take time to review the prototype and this document. Note any questions or changes.</p>
                    </div>
                </div>
                <div class="step-item">
                    <div class="step-number">2</div>
                    <div class="step-content">
                        <h4>Schedule Discovery Call</h4>
                        <p>Let's discuss your vision, answer questions, and refine the approach together.</p>
                    </div>
                </div>
                <div class="step-item">
                    <div class="step-number">3</div>
                    <div class="step-content">
                        <h4>Finalize Scope & Agreement</h4>
                        <p>We'll create a detailed project plan and move forward with development.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="company">{self.config.company_name}</div>
            <div class="tagline">{self.config.company_tagline}</div>
            <div class="contact">
                {self.config.contact_email} | {self.config.contact_phone}
            </div>
        </div>
    </div>
</body>
</html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"[REPORT] Saved to: {output_path}")
        return output_path
