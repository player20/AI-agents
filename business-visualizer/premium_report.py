"""
Premium Client Report Generator
Creates impressive, detailed reports that wow clients every time.

Features:
- Fun facts and industry insights
- Psychology behind recommendations
- Case studies and success stories
- Embedded interactive prototype
- Works for both BUILD (new apps) and AUDIT (existing apps)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ReportConfig:
    """Agency branding configuration"""
    company_name: str = "Digital Ventures"
    company_tagline: str = "Transforming Ideas Into Reality"
    contact_email: str = "hello@digitalventures.com"
    contact_phone: str = "(555) 123-4567"
    website: str = "www.digitalventures.com"


class PremiumReport:
    """Generate impressive, detailed client reports"""

    # Fun facts and insights by industry
    INDUSTRY_INSIGHTS = {
        'restaurant': {
            'fun_facts': [
                "Mobile orders have 20% higher average ticket size than in-person orders",
                "67% of customers prefer to order ahead rather than wait in line",
                "Restaurants with loyalty apps see 35% higher customer retention",
                "The average American checks their phone 96 times per day - be one of those checks",
                "Digital menus with photos increase orders by 30%",
            ],
            'psychology': [
                {
                    'principle': "The Paradox of Choice",
                    'insight': "Too many menu options cause decision paralysis. We recommend highlighting 'Popular' and 'Staff Picks' to guide users.",
                    'source': "Barry Schwartz, Columbia Business School"
                },
                {
                    'principle': "Social Proof",
                    'insight': "Showing order counts ('2.3k orders') triggers herd mentality - if others love it, it must be good.",
                    'source': "Robert Cialdini, Influence"
                },
                {
                    'principle': "Loss Aversion",
                    'insight': "Limited-time offers ('Today only!') create urgency. People fear missing out more than they enjoy gaining.",
                    'source': "Kahneman & Tversky, Prospect Theory"
                },
            ],
            'case_studies': [
                {
                    'company': "Sweetgreen",
                    'result': "50% of orders now come through their app",
                    'insight': "They focused on speed - order in under 30 seconds"
                },
                {
                    'company': "Starbucks",
                    'result': "Mobile orders = 26% of all transactions",
                    'insight': "Rewards program drives 53% of spending"
                },
                {
                    'company': "Chipotle",
                    'result': "Digital sales grew 81% year-over-year",
                    'insight': "Pickup shelves + order tracking reduced friction"
                },
            ],
            'market_stats': {
                'market_size': '$899 Billion',
                'growth_rate': '4.1% annually',
                'mobile_adoption': '67% prefer mobile ordering',
                'avg_roi': '300-400% on app investment',
            },
        },
        'fitness': {
            'fun_facts': [
                "Members who book classes via app attend 40% more sessions",
                "Push notifications increase class attendance by 25%",
                "Studios with apps see 34% higher member retention",
                "The best time to send workout reminders is 6 AM and 5 PM",
                "Social features (sharing workouts) increase engagement by 50%",
            ],
            'psychology': [
                {
                    'principle': "Commitment & Consistency",
                    'insight': "Once someone books a class, they're 80% more likely to show up. The app creates a public commitment.",
                    'source': "Robert Cialdini, Influence"
                },
                {
                    'principle': "Variable Rewards",
                    'insight': "Streak counters and badges trigger dopamine. Users become addicted to maintaining their streak.",
                    'source': "Nir Eyal, Hooked"
                },
                {
                    'principle': "Social Comparison",
                    'insight': "Leaderboards and shared achievements tap into competitive instincts - 'If they can do it, so can I'",
                    'source': "Leon Festinger, Social Comparison Theory"
                },
            ],
            'case_studies': [
                {
                    'company': "Peloton",
                    'result': "92% member retention rate",
                    'insight': "Leaderboards + live classes create community"
                },
                {
                    'company': "ClassPass",
                    'result': "30M+ classes booked",
                    'insight': "Credits system gamifies fitness exploration"
                },
                {
                    'company': "Orange Theory",
                    'result': "1M+ active members",
                    'insight': "Heart rate tracking makes every workout measurable"
                },
            ],
            'market_stats': {
                'market_size': '$96 Billion',
                'growth_rate': '7.2% annually',
                'mobile_adoption': '72% want mobile booking',
                'avg_roi': '250-350% on app investment',
            },
        },
        'retail': {
            'fun_facts': [
                "Mobile commerce will hit $710 billion by 2025",
                "Apps convert 3x better than mobile websites",
                "Push notifications have 7x higher engagement than email",
                "Wishlist features increase purchase intent by 40%",
                "AR try-on features reduce returns by 25%",
            ],
            'psychology': [
                {
                    'principle': "Scarcity",
                    'insight': "'Only 3 left!' creates urgency. Limited availability increases perceived value.",
                    'source': "Robert Cialdini, Influence"
                },
                {
                    'principle': "Reciprocity",
                    'insight': "Free shipping thresholds ('$15 more for free shipping!') feel like gifts - triggering reciprocal purchases.",
                    'source': "Robert Cialdini, Influence"
                },
                {
                    'principle': "Anchoring",
                    'insight': "Showing original price crossed out makes the sale price feel like a steal, even if it's the 'real' price.",
                    'source': "Dan Ariely, Predictably Irrational"
                },
            ],
            'case_studies': [
                {
                    'company': "SHEIN",
                    'result': "Most downloaded shopping app globally",
                    'insight': "Gamification + daily new arrivals = addiction"
                },
                {
                    'company': "Nike",
                    'result': "30% of revenue from digital",
                    'insight': "Exclusive app-only drops create FOMO"
                },
                {
                    'company': "Sephora",
                    'result': "80% of sales influenced by digital",
                    'insight': "AR try-on removes purchase hesitation"
                },
            ],
            'market_stats': {
                'market_size': '$5.5 Trillion',
                'growth_rate': '10.4% annually',
                'mobile_adoption': '85% research online first',
                'avg_roi': '400-600% on app investment',
            },
        },
        'service': {
            'fun_facts': [
                "78% of customers prefer online booking over phone calls",
                "Businesses with apps close 40% more jobs",
                "Real-time tracking reduces 'where are you?' calls by 80%",
                "Photo upload features reduce misquotes by 60%",
                "Same-day booking requests have increased 200% since 2020",
            ],
            'psychology': [
                {
                    'principle': "Uncertainty Reduction",
                    'insight': "Real-time tracking eliminates the #1 frustration: not knowing when they'll arrive. Certainty = comfort.",
                    'source': "Uber Effect Research"
                },
                {
                    'principle': "Trust Through Transparency",
                    'insight': "Upfront pricing removes fear of surprise charges. Trust = conversion.",
                    'source': "Harvard Business Review"
                },
                {
                    'principle': "The IKEA Effect",
                    'insight': "When customers upload photos of their issue, they feel invested in the solution - higher conversion.",
                    'source': "Michael Norton, Harvard"
                },
            ],
            'case_studies': [
                {
                    'company': "Thumbtack",
                    'result': "$1B+ in services booked annually",
                    'insight': "Instant quotes remove friction"
                },
                {
                    'company': "Handy",
                    'result': "3M+ homes serviced",
                    'insight': "Flat-rate pricing builds trust"
                },
                {
                    'company': "TaskRabbit",
                    'result': "Acquired by IKEA for $500M",
                    'insight': "Reviews + background checks = trust"
                },
            ],
            'market_stats': {
                'market_size': '$1.2 Trillion',
                'growth_rate': '8.5% annually',
                'mobile_adoption': '78% prefer online booking',
                'avg_roi': '350-500% on app investment',
            },
        },
        'beauty': {
            'fun_facts': [
                "82% of salon bookings now happen online",
                "Salons with apps see 45% more repeat bookings",
                "The average salon loses $67,000/year to no-shows - apps reduce this by 40%",
                "Instagram integration increases booking by 35%",
                "Gift card features generate 20% additional revenue",
            ],
            'psychology': [
                {
                    'principle': "Self-Investment",
                    'insight': "Beauty is self-care. Framing services as 'treat yourself' moments increases booking rates.",
                    'source': "Consumer Psychology Research"
                },
                {
                    'principle': "Visual Social Proof",
                    'insight': "Stylist portfolios with before/after photos reduce decision anxiety - 'I want to look like that'",
                    'source': "Instagram Effect Studies"
                },
                {
                    'principle': "Appointment Psychology",
                    'insight': "Confirmation + reminder sequence reduces no-shows by 40%. People don't want to let down 'their' stylist.",
                    'source': "Behavioral Economics Research"
                },
            ],
            'case_studies': [
                {
                    'company': "Drybar",
                    'result': "100+ locations, $100M+ revenue",
                    'insight': "Single service focus + premium experience"
                },
                {
                    'company': "Glamsquad",
                    'result': "On-demand beauty in minutes",
                    'insight': "Uber for beauty model works"
                },
                {
                    'company': "Booksy",
                    'result': "#1 beauty booking app",
                    'insight': "Free for clients = massive adoption"
                },
            ],
            'market_stats': {
                'market_size': '$63 Billion',
                'growth_rate': '5.9% annually',
                'mobile_adoption': '82% book online',
                'avg_roi': '300-450% on app investment',
            },
        },
        'healthcare': {
            'fun_facts': [
                "76% of patients want telehealth options",
                "Digital scheduling reduces no-shows by 38%",
                "Patient portals increase medication adherence by 20%",
                "Average wait time for appointments has dropped 50% with online booking",
                "Secure messaging reduces unnecessary office visits by 25%",
            ],
            'psychology': [
                {
                    'principle': "Control & Autonomy",
                    'insight': "Patients who can access their records feel more in control of their health - leading to better outcomes.",
                    'source': "Journal of Medical Internet Research"
                },
                {
                    'principle': "Friction Reduction",
                    'insight': "Every step removed from booking = 20% more appointments made. One-tap booking is ideal.",
                    'source': "Healthcare UX Research"
                },
                {
                    'principle': "Trust Through Access",
                    'insight': "Patients who can see their lab results immediately trust their provider more - even with bad news.",
                    'source': "JAMA Internal Medicine"
                },
            ],
            'case_studies': [
                {
                    'company': "One Medical",
                    'result': "Acquired for $3.9B by Amazon",
                    'insight': "Same-day appointments + modern app"
                },
                {
                    'company': "Zocdoc",
                    'result': "6M+ monthly users",
                    'insight': "Real-time availability removes friction"
                },
                {
                    'company': "Teladoc",
                    'result': "$2B+ revenue",
                    'insight': "Telehealth is now expected, not optional"
                },
            ],
            'market_stats': {
                'market_size': '$4.3 Trillion',
                'growth_rate': '5.4% annually',
                'mobile_adoption': '76% want telehealth',
                'avg_roi': '200-350% on app investment',
            },
        },
        'education': {
            'fun_facts': [
                "Online learning market will hit $375B by 2026",
                "Students complete 60% more content on apps vs. websites",
                "Gamification increases course completion by 40%",
                "Push notifications for reminders increase daily engagement by 50%",
                "Progress tracking motivates 78% of learners to continue",
            ],
            'psychology': [
                {
                    'principle': "The Zeigarnik Effect",
                    'insight': "Incomplete progress bars bother people. 'You're 80% done!' compels completion.",
                    'source': "Bluma Zeigarnik, Psychology Research"
                },
                {
                    'principle': "Micro-Learning",
                    'insight': "5-minute lessons fit into any schedule. Small wins compound into big results.",
                    'source': "Learning Science Research"
                },
                {
                    'principle': "Spaced Repetition",
                    'insight': "Smart reminders at optimal intervals increase retention by 200%. The app does the timing.",
                    'source': "Hermann Ebbinghaus, Memory Research"
                },
            ],
            'case_studies': [
                {
                    'company': "Duolingo",
                    'result': "500M+ users, $6B valuation",
                    'insight': "Gamification + streaks = addiction"
                },
                {
                    'company': "MasterClass",
                    'result': "$2.75B valuation",
                    'insight': "Celebrity instructors + premium content"
                },
                {
                    'company': "Coursera",
                    'result': "100M+ learners",
                    'insight': "Credentials that employers recognize"
                },
            ],
            'market_stats': {
                'market_size': '$375 Billion',
                'growth_rate': '14.6% annually',
                'mobile_adoption': '89% prefer online options',
                'avg_roi': '500-800% on app investment',
            },
        },
        'realestate': {
            'fun_facts': [
                "97% of home buyers search online first",
                "Listings with virtual tours get 87% more views",
                "The average buyer views 10 homes before purchasing",
                "Agents with apps close 28% more deals",
                "Mortgage calculators increase lead conversion by 40%",
            ],
            'psychology': [
                {
                    'principle': "Visualization",
                    'insight': "Virtual tours let buyers mentally 'move in' before visiting. Emotional investment = serious inquiries.",
                    'source': "Real Estate Psychology Research"
                },
                {
                    'principle': "Fear of Missing Out",
                    'insight': "'New listing!' notifications create urgency. In hot markets, speed wins.",
                    'source': "Behavioral Economics"
                },
                {
                    'principle': "The Endowment Effect",
                    'insight': "Saved/favorited homes feel like 'mine' before purchase. Loss aversion kicks in.",
                    'source': "Richard Thaler, Behavioral Economics"
                },
            ],
            'case_studies': [
                {
                    'company': "Zillow",
                    'result': "200M+ monthly users",
                    'insight': "Zestimate made home values accessible"
                },
                {
                    'company': "Redfin",
                    'result': "Saved buyers $1B+ in fees",
                    'insight': "Tech-first approach disrupted industry"
                },
                {
                    'company': "Compass",
                    'result': "$7B valuation",
                    'insight': "Premium tech tools attract top agents"
                },
            ],
            'market_stats': {
                'market_size': '$226 Billion',
                'growth_rate': '3.8% annually',
                'mobile_adoption': '97% search online',
                'avg_roi': '250-400% on app investment',
            },
        },
    }

    # Investment ROI calculations
    PRICING = {
        'high': {'min': 8000, 'max': 15000, 'time': '3-4 weeks'},
        'medium': {'min': 4000, 'max': 8000, 'time': '2-3 weeks'},
        'low': {'min': 1500, 'max': 4000, 'time': '1-2 weeks'},
    }

    def __init__(self, config: ReportConfig = None):
        self.config = config or ReportConfig()

    def generate_build_report(self, plan, prototype_html: str = None, output_path: str = None) -> str:
        """Generate report for BUILD mode (new app from business idea)"""
        return self._generate_report(
            plan=plan,
            mode='build',
            prototype_html=prototype_html,
            output_path=output_path
        )

    def generate_audit_report(self, audit_data: Dict, prototype_html: str = None, output_path: str = None) -> str:
        """Generate report for AUDIT mode (analyzing existing app)"""
        return self._generate_report(
            plan=None,
            mode='audit',
            audit_data=audit_data,
            prototype_html=prototype_html,
            output_path=output_path
        )

    def _generate_report(self, plan=None, mode='build', audit_data: Dict = None,
                         prototype_html: str = None, output_path: str = None) -> str:
        """Generate the premium report"""

        if mode == 'build' and plan:
            business_name = plan.business_name
            industry = plan.industry
            primary_color = plan.primary_color
            secondary_color = plan.secondary_color
        elif mode == 'audit' and audit_data:
            business_name = audit_data.get('app_name', 'App')
            industry = audit_data.get('industry', 'service')
            primary_color = audit_data.get('primary_color', '#6366F1')
            secondary_color = audit_data.get('secondary_color', '#818CF8')
        else:
            raise ValueError("Must provide plan for build mode or audit_data for audit mode")

        # Get industry insights
        insights = self.INDUSTRY_INSIGHTS.get(industry, self.INDUSTRY_INSIGHTS['service'])

        # Calculate costs (for build mode)
        if plan:
            total_min = sum(self.PRICING.get(f.get('priority', 'medium'), self.PRICING['medium'])['min']
                           for f in plan.core_features)
            total_max = sum(self.PRICING.get(f.get('priority', 'medium'), self.PRICING['medium'])['max']
                           for f in plan.core_features)
        else:
            total_min = 15000
            total_max = 35000

        # Build sections
        fun_facts_html = self._build_fun_facts(insights)
        psychology_html = self._build_psychology(insights)
        case_studies_html = self._build_case_studies(insights)
        market_stats_html = self._build_market_stats(insights)

        if mode == 'build' and plan:
            features_html = self._build_features_section(plan)
            screens_html = self._build_screens_section(plan)
            deliberation_html = self._build_deliberation_section(plan)
            design_html = self._build_design_section(plan)
            title = "Digital Transformation Proposal"
            subtitle = f"Custom App Development for {business_name}"
        else:
            features_html = self._build_audit_findings(audit_data)
            screens_html = self._build_before_after(audit_data)
            deliberation_html = ""
            design_html = self._build_audit_recommendations(audit_data)
            title = "UX Audit Report"
            subtitle = f"Analysis & Recommendations for {business_name}"

        # Embed prototype if provided
        prototype_section = ""
        if prototype_html:
            prototype_section = f"""
            <div class="section prototype-section">
                <div class="section-header">
                    <div class="section-icon">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17 1.01L7 1c-1.1 0-2 .9-2 2v18c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V3c0-1.1-.9-1.99-2-1.99zM17 19H7V5h10v14z"/></svg>
                    </div>
                    <h2>Interactive Prototype</h2>
                </div>
                <p class="section-intro">Click through the screens below to experience the proposed app design.</p>
                <div class="prototype-embed">
                    <iframe srcdoc='{prototype_html.replace("'", "&#39;")}' style="width: 100%; height: 700px; border: none; border-radius: 16px;"></iframe>
                </div>
                <p class="prototype-note">This is a functional prototype. The final app will include additional polish and animations.</p>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} - {title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');

        :root {{
            --primary: {primary_color};
            --secondary: {secondary_color};
            --accent: #F59E0B;
            --dark: #0F172A;
            --dark-secondary: #1E293B;
            --light: #F8FAFC;
            --text: #334155;
            --text-light: #64748B;
            --success: #10B981;
            --warning: #F59E0B;
            --danger: #EF4444;
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

        /* Cover */
        .cover {{
            background: linear-gradient(135deg, var(--dark) 0%, var(--dark-secondary) 100%);
            color: white;
            padding: 100px 60px;
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
            background: radial-gradient(circle, {primary_color}20 0%, transparent 70%);
            border-radius: 50%;
        }}

        .cover::after {{
            content: '';
            position: absolute;
            bottom: -30%;
            left: -10%;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, {secondary_color}15 0%, transparent 70%);
            border-radius: 50%;
        }}

        .cover-content {{
            position: relative;
            z-index: 1;
            max-width: 700px;
        }}

        .cover-badge {{
            display: inline-block;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            padding: 8px 20px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 24px;
        }}

        .cover h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 56px;
            font-weight: 700;
            line-height: 1.1;
            margin-bottom: 20px;
        }}

        .cover .subtitle {{
            font-size: 22px;
            opacity: 0.9;
            margin-bottom: 40px;
            font-weight: 400;
        }}

        .cover-meta {{
            display: flex;
            gap: 40px;
            font-size: 14px;
            opacity: 0.7;
        }}

        .cover-stat {{
            text-align: center;
        }}

        .cover-stat-value {{
            font-size: 32px;
            font-weight: 700;
            color: var(--primary);
        }}

        .cover-stat-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.8;
        }}

        /* Main Container */
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 60px 40px;
        }}

        /* Sections */
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
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }}

        .section-icon svg {{
            width: 24px;
            height: 24px;
        }}

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

        /* Fun Facts */
        .fun-facts-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}

        .fun-fact {{
            background: linear-gradient(135deg, var(--primary)08, var(--secondary)05);
            border: 1px solid var(--primary)15;
            border-radius: 16px;
            padding: 24px;
            display: flex;
            gap: 16px;
            align-items: flex-start;
        }}

        .fun-fact-icon {{
            width: 40px;
            height: 40px;
            background: var(--primary);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 18px;
            flex-shrink: 0;
        }}

        .fun-fact-text {{
            font-size: 15px;
            color: var(--dark);
            line-height: 1.5;
        }}

        /* Psychology */
        .psychology-cards {{
            display: grid;
            gap: 20px;
        }}

        .psychology-card {{
            background: var(--light);
            border-radius: 16px;
            padding: 28px;
            border-left: 4px solid var(--primary);
        }}

        .psychology-principle {{
            font-size: 18px;
            font-weight: 700;
            color: var(--dark);
            margin-bottom: 12px;
        }}

        .psychology-insight {{
            font-size: 15px;
            color: var(--text);
            margin-bottom: 12px;
            line-height: 1.6;
        }}

        .psychology-source {{
            font-size: 13px;
            color: var(--text-light);
            font-style: italic;
        }}

        /* Case Studies */
        .case-studies-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }}

        .case-study {{
            background: var(--dark);
            color: white;
            border-radius: 20px;
            padding: 28px;
            text-align: center;
        }}

        .case-study-company {{
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 16px;
        }}

        .case-study-result {{
            background: var(--primary);
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 16px;
        }}

        .case-study-insight {{
            font-size: 14px;
            opacity: 0.9;
            line-height: 1.5;
        }}

        /* Market Stats */
        .market-stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }}

        .market-stat {{
            text-align: center;
            padding: 24px;
            background: linear-gradient(135deg, var(--primary)10, var(--secondary)05);
            border-radius: 16px;
        }}

        .market-stat-value {{
            font-size: 28px;
            font-weight: 800;
            color: var(--primary);
            margin-bottom: 8px;
        }}

        .market-stat-label {{
            font-size: 13px;
            color: var(--text-light);
        }}

        /* Features */
        .features-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .features-table th {{
            text-align: left;
            padding: 16px;
            background: var(--light);
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-light);
        }}

        .features-table td {{
            padding: 20px 16px;
            border-bottom: 1px solid var(--light);
        }}

        .feature-name {{
            font-weight: 600;
            color: var(--dark);
            margin-bottom: 4px;
        }}

        .feature-desc {{
            font-size: 14px;
            color: var(--text-light);
        }}

        .priority-badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}

        .priority-high {{
            background: #FEE2E2;
            color: #DC2626;
        }}

        .priority-medium {{
            background: #FEF3C7;
            color: #D97706;
        }}

        .priority-low {{
            background: #D1FAE5;
            color: #059669;
        }}

        /* Design System */
        .design-preview {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 32px;
        }}

        .color-palette {{
            display: flex;
            gap: 12px;
        }}

        .color-swatch {{
            width: 80px;
            height: 80px;
            border-radius: 16px;
            display: flex;
            align-items: flex-end;
            justify-content: center;
            padding-bottom: 10px;
            color: white;
            font-size: 11px;
            font-weight: 500;
            text-shadow: 0 1px 2px rgba(0,0,0,0.2);
        }}

        /* Prototype */
        .prototype-embed {{
            background: var(--dark);
            border-radius: 20px;
            padding: 24px;
            margin: 24px 0;
        }}

        .prototype-note {{
            text-align: center;
            font-size: 14px;
            color: var(--text-light);
            font-style: italic;
        }}

        /* Investment */
        .investment-card {{
            background: linear-gradient(135deg, var(--dark), var(--dark-secondary));
            color: white;
            border-radius: 24px;
            padding: 48px;
            text-align: center;
        }}

        .investment-label {{
            font-size: 14px;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }}

        .investment-amount {{
            font-size: 56px;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 16px;
        }}

        .investment-note {{
            font-size: 15px;
            opacity: 0.8;
            margin-bottom: 32px;
        }}

        .roi-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
        }}

        .roi-item {{
            background: rgba(255,255,255,0.1);
            padding: 24px;
            border-radius: 16px;
        }}

        .roi-value {{
            font-size: 28px;
            font-weight: 700;
            color: var(--primary);
        }}

        .roi-label {{
            font-size: 13px;
            opacity: 0.8;
            margin-top: 8px;
        }}

        /* Next Steps */
        .next-steps {{
            background: var(--light);
            border-radius: 20px;
            padding: 32px;
        }}

        .step {{
            display: flex;
            gap: 20px;
            margin-bottom: 24px;
        }}

        .step:last-child {{
            margin-bottom: 0;
        }}

        .step-number {{
            width: 44px;
            height: 44px;
            background: var(--primary);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 18px;
            flex-shrink: 0;
        }}

        .step-content h4 {{
            font-size: 17px;
            font-weight: 600;
            color: var(--dark);
            margin-bottom: 4px;
        }}

        .step-content p {{
            font-size: 14px;
            color: var(--text-light);
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 60px 40px;
            background: var(--dark);
            color: white;
        }}

        .footer-logo {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }}

        .footer-tagline {{
            font-size: 15px;
            opacity: 0.7;
            margin-bottom: 24px;
        }}

        .footer-contact {{
            font-size: 14px;
            opacity: 0.6;
        }}

        /* Quote Callout */
        .quote-callout {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            margin: 32px 0;
        }}

        .quote-text {{
            font-size: 22px;
            font-weight: 500;
            line-height: 1.5;
            margin-bottom: 16px;
        }}

        .quote-author {{
            font-size: 14px;
            opacity: 0.9;
        }}

        /* Print */
        @media print {{
            .cover {{ min-height: auto; padding: 60px 40px; }}
            .section {{ break-inside: avoid; }}
            body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        }}

        @media (max-width: 768px) {{
            .cover h1 {{ font-size: 36px; }}
            .fun-facts-grid, .case-studies-grid, .market-stats {{ grid-template-columns: 1fr; }}
            .design-preview {{ grid-template-columns: 1fr; }}
            .roi-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <!-- Cover -->
    <div class="cover">
        <div class="cover-content">
            <span class="cover-badge">{title}</span>
            <h1>{business_name}</h1>
            <p class="subtitle">{subtitle}</p>
            <div class="cover-meta">
                <div class="cover-stat">
                    <div class="cover-stat-value">{insights['market_stats']['market_size']}</div>
                    <div class="cover-stat-label">Market Size</div>
                </div>
                <div class="cover-stat">
                    <div class="cover-stat-value">{insights['market_stats']['growth_rate']}</div>
                    <div class="cover-stat-label">Growth Rate</div>
                </div>
                <div class="cover-stat">
                    <div class="cover-stat-value">{insights['market_stats']['avg_roi']}</div>
                    <div class="cover-stat-label">Avg ROI</div>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <!-- Did You Know -->
        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
                </div>
                <h2>Did You Know?</h2>
            </div>
            <p class="section-intro">Key insights about your industry that will shape our approach.</p>
            {fun_facts_html}
        </div>

        <!-- Quote -->
        <div class="quote-callout">
            <div class="quote-text">"The best time to digitize was yesterday. The second best time is now."</div>
            <div class="quote-author">- Digital Transformation Research, 2024</div>
        </div>

        <!-- Market Overview -->
        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/></svg>
                </div>
                <h2>Market Overview</h2>
            </div>
            <p class="section-intro">Understanding the landscape helps us position you for success.</p>
            {market_stats_html}
        </div>

        <!-- Psychology -->
        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                </div>
                <h2>The Psychology Behind Our Approach</h2>
            </div>
            <p class="section-intro">Every design decision is backed by behavioral science.</p>
            {psychology_html}
        </div>

        <!-- Case Studies -->
        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
                </div>
                <h2>Success Stories</h2>
            </div>
            <p class="section-intro">Companies in your space that got it right.</p>
            {case_studies_html}
        </div>

        {prototype_section}

        {design_html}

        {features_html}

        {screens_html}

        {deliberation_html}

        <!-- Investment -->
        <div class="section" style="padding: 0; background: transparent; box-shadow: none;">
            <div class="investment-card">
                <div class="investment-label">Estimated Investment</div>
                <div class="investment-amount">${total_min:,} - ${total_max:,}</div>
                <div class="investment-note">Includes design, development, testing, and 30-day support</div>
                <div class="roi-grid">
                    <div class="roi-item">
                        <div class="roi-value">10-20%</div>
                        <div class="roi-label">Revenue Increase</div>
                    </div>
                    <div class="roi-item">
                        <div class="roi-value">30-40%</div>
                        <div class="roi-label">Retention Boost</div>
                    </div>
                    <div class="roi-item">
                        <div class="roi-value">6-12 mo</div>
                        <div class="roi-label">Typical Payback</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Next Steps -->
        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"/></svg>
                </div>
                <h2>Next Steps</h2>
            </div>
            <div class="next-steps">
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-content">
                        <h4>Review This Proposal</h4>
                        <p>Take your time. Note any questions, ideas, or concerns that come up.</p>
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-content">
                        <h4>Schedule a Call</h4>
                        <p>Let's walk through the proposal together and refine the approach.</p>
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-content">
                        <h4>Kick Off</h4>
                        <p>Once aligned, we'll begin the discovery phase and start building your vision.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <div class="footer">
        <div class="footer-logo">{self.config.company_name}</div>
        <div class="footer-tagline">{self.config.company_tagline}</div>
        <div class="footer-contact">
            {self.config.contact_email} | {self.config.contact_phone} | {self.config.website}
        </div>
    </div>
</body>
</html>"""

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"[PREMIUM REPORT] Saved to: {output_path}")

        return html

    def _build_fun_facts(self, insights: Dict) -> str:
        facts = insights.get('fun_facts', [])
        icons = ['%', '#', '+', '!', '*']

        html = '<div class="fun-facts-grid">'
        for i, fact in enumerate(facts[:6]):
            html += f"""
            <div class="fun-fact">
                <div class="fun-fact-icon">{icons[i % len(icons)]}</div>
                <div class="fun-fact-text">{fact}</div>
            </div>
            """
        html += '</div>'
        return html

    def _build_psychology(self, insights: Dict) -> str:
        psychology = insights.get('psychology', [])

        html = '<div class="psychology-cards">'
        for p in psychology:
            html += f"""
            <div class="psychology-card">
                <div class="psychology-principle">{p['principle']}</div>
                <div class="psychology-insight">{p['insight']}</div>
                <div class="psychology-source">Source: {p['source']}</div>
            </div>
            """
        html += '</div>'
        return html

    def _build_case_studies(self, insights: Dict) -> str:
        cases = insights.get('case_studies', [])

        html = '<div class="case-studies-grid">'
        for case in cases:
            html += f"""
            <div class="case-study">
                <div class="case-study-company">{case['company']}</div>
                <div class="case-study-result">{case['result']}</div>
                <div class="case-study-insight">{case['insight']}</div>
            </div>
            """
        html += '</div>'
        return html

    def _build_market_stats(self, insights: Dict) -> str:
        stats = insights.get('market_stats', {})

        return f"""
        <div class="market-stats">
            <div class="market-stat">
                <div class="market-stat-value">{stats.get('market_size', 'N/A')}</div>
                <div class="market-stat-label">Market Size</div>
            </div>
            <div class="market-stat">
                <div class="market-stat-value">{stats.get('growth_rate', 'N/A')}</div>
                <div class="market-stat-label">Annual Growth</div>
            </div>
            <div class="market-stat">
                <div class="market-stat-value">{stats.get('mobile_adoption', 'N/A')}</div>
                <div class="market-stat-label">Mobile Adoption</div>
            </div>
            <div class="market-stat">
                <div class="market-stat-value">{stats.get('avg_roi', 'N/A')}</div>
                <div class="market-stat-label">Typical ROI</div>
            </div>
        </div>
        """

    def _build_features_section(self, plan) -> str:
        rows = ""
        for f in plan.core_features:
            priority = f.get('priority', 'medium')
            pricing = self.PRICING.get(priority, self.PRICING['medium'])
            rows += f"""
            <tr>
                <td>
                    <div class="feature-name">{f['name']}</div>
                    <div class="feature-desc">{f['description']}</div>
                </td>
                <td><span class="priority-badge priority-{priority}">{priority.upper()}</span></td>
                <td>${pricing['min']:,} - ${pricing['max']:,}</td>
                <td>{pricing['time']}</td>
            </tr>
            """

        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
                </div>
                <h2>Recommended Features</h2>
            </div>
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
                    {rows}
                </tbody>
            </table>
        </div>
        """

    def _build_screens_section(self, plan) -> str:
        screens_html = ""
        for i, screen in enumerate(plan.screens, 1):
            screens_html += f"""
            <div style="display: flex; gap: 16px; padding: 16px; background: var(--light); border-radius: 12px; margin-bottom: 12px;">
                <div style="width: 40px; height: 40px; background: var(--primary); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700;">{i}</div>
                <div>
                    <div style="font-weight: 600; color: var(--dark);">{screen['name']}</div>
                    <div style="font-size: 14px; color: var(--text-light);">{screen['description']}</div>
                </div>
            </div>
            """

        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17 1.01L7 1c-1.1 0-2 .9-2 2v18c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V3c0-1.1-.9-1.99-2-1.99zM17 19H7V5h10v14z"/></svg>
                </div>
                <h2>App Screens</h2>
            </div>
            <p class="section-intro">The complete user journey, designed for maximum engagement.</p>
            {screens_html}
        </div>
        """

    def _build_design_section(self, plan) -> str:
        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9c.83 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-.99 0-.83.67-1.5 1.5-1.5H16c2.76 0 5-2.24 5-5 0-4.42-4.03-8-9-8zm-5.5 9c-.83 0-1.5-.67-1.5-1.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12zm3-4C8.67 8 8 7.33 8 6.5S8.67 5 9.5 5s1.5.67 1.5 1.5S10.33 8 9.5 8zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 5 14.5 5s1.5.67 1.5 1.5S15.33 8 14.5 8zm3 4c-.83 0-1.5-.67-1.5-1.5S16.67 9 17.5 9s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/></svg>
                </div>
                <h2>Design System</h2>
            </div>
            <p class="section-intro">A cohesive visual language that reflects your brand.</p>
            <div class="design-preview">
                <div>
                    <h4 style="margin-bottom: 16px; color: var(--dark);">Color Palette</h4>
                    <div class="color-palette">
                        <div class="color-swatch" style="background: {plan.primary_color}">{plan.primary_color}</div>
                        <div class="color-swatch" style="background: {plan.secondary_color}">{plan.secondary_color}</div>
                        <div class="color-swatch" style="background: {plan.accent_color}">{plan.accent_color}</div>
                    </div>
                </div>
                <div>
                    <h4 style="margin-bottom: 16px; color: var(--dark);">Typography</h4>
                    <div style="background: var(--light); padding: 20px; border-radius: 12px; margin-bottom: 12px;">
                        <div style="font-size: 13px; color: var(--text-light); margin-bottom: 8px;">Headings</div>
                        <div style="font-size: 24px; font-weight: 600; color: var(--dark);">{plan.heading_font}</div>
                    </div>
                    <div style="background: var(--light); padding: 20px; border-radius: 12px;">
                        <div style="font-size: 13px; color: var(--text-light); margin-bottom: 8px;">Body Text</div>
                        <div style="font-size: 18px; color: var(--dark);">{plan.body_font}</div>
                    </div>
                </div>
            </div>
            <div style="margin-top: 24px; padding: 20px; background: linear-gradient(135deg, var(--primary)10, var(--secondary)05); border-radius: 16px;">
                <div style="font-weight: 600; color: var(--dark); margin-bottom: 8px;">Design Mood</div>
                <div style="display: inline-block; background: var(--primary); color: white; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: 500;">{plan.style_mood.title()}</div>
            </div>
        </div>
        """

    def _build_deliberation_section(self, plan) -> str:
        log_html = ""
        for thought in plan.deliberation_log:
            if thought.decision:
                log_html += f"""
                <div style="display: flex; gap: 12px; padding: 14px; background: var(--light); border-radius: 10px; margin-bottom: 10px;">
                    <span style="background: var(--primary); color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; white-space: nowrap; height: fit-content;">{thought.agent}</span>
                    <p style="font-size: 14px; color: var(--text); margin: 0;">{thought.decision}</p>
                </div>
                """

        if not log_html:
            return ""

        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M21 6h-2v9H6v2c0 .55.45 1 1 1h11l4 4V7c0-.55-.45-1-1-1zm-4 6V3c0-.55-.45-1-1-1H3c-.55 0-1 .45-1 1v14l4-4h10c.55 0 1-.45 1-1z"/></svg>
                </div>
                <h2>How AI Agents Designed This</h2>
            </div>
            <p class="section-intro">Transparency into the decision-making process.</p>
            {log_html}
        </div>
        """

    def _build_audit_findings(self, audit_data: Dict) -> str:
        """Build findings section for audit mode"""
        findings = audit_data.get('findings', [])
        if not findings:
            return ""

        rows = ""
        for f in findings:
            severity = f.get('severity', 'medium')
            severity_class = f'priority-{severity}'
            rows += f"""
            <tr>
                <td>
                    <div class="feature-name">{f.get('title', 'Finding')}</div>
                    <div class="feature-desc">{f.get('description', '')}</div>
                </td>
                <td><span class="priority-badge {severity_class}">{severity.upper()}</span></td>
                <td>{f.get('impact', 'N/A')}</td>
            </tr>
            """

        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                </div>
                <h2>Issues Found</h2>
            </div>
            <table class="features-table">
                <thead>
                    <tr>
                        <th>Issue</th>
                        <th>Severity</th>
                        <th>Business Impact</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """

    def _build_before_after(self, audit_data: Dict) -> str:
        """Build before/after section for audit mode"""
        return ""  # Placeholder for future implementation

    def _build_audit_recommendations(self, audit_data: Dict) -> str:
        """Build recommendations section for audit mode"""
        recommendations = audit_data.get('recommendations', [])
        if not recommendations:
            return ""

        items_html = ""
        for i, rec in enumerate(recommendations, 1):
            items_html += f"""
            <div style="display: flex; gap: 16px; padding: 16px; background: var(--light); border-radius: 12px; margin-bottom: 12px;">
                <div style="width: 40px; height: 40px; background: var(--primary); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700;">{i}</div>
                <div>
                    <div style="font-weight: 600; color: var(--dark);">{rec.get('title', 'Recommendation')}</div>
                    <div style="font-size: 14px; color: var(--text-light);">{rec.get('description', '')}</div>
                </div>
            </div>
            """

        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                </div>
                <h2>Recommendations</h2>
            </div>
            {items_html}
        </div>
        """

    # =========================================================================
    # MODERNIZE MODE - Old business going digital
    # =========================================================================

    def generate_modernize_report(self, plan, prototype_html: str = None, output_path: str = None) -> str:
        """
        Generate report for MODERNIZE mode
        For: Traditional businesses that want to go digital
        Framing: "Here's your digital future"
        """
        business_name = plan.business_name
        industry = plan.industry
        insights = self.INDUSTRY_INSIGHTS.get(industry, self.INDUSTRY_INSIGHTS['service'])

        # Calculate costs
        total_min = sum(self.PRICING.get(f.get('priority', 'medium'), self.PRICING['medium'])['min']
                       for f in plan.core_features)
        total_max = sum(self.PRICING.get(f.get('priority', 'medium'), self.PRICING['medium'])['max']
                       for f in plan.core_features)

        # Build sections
        fun_facts_html = self._build_fun_facts(insights)
        psychology_html = self._build_psychology(insights)
        case_studies_html = self._build_case_studies(insights)
        market_stats_html = self._build_market_stats(insights)
        features_html = self._build_features_section(plan)
        design_html = self._build_design_section(plan)

        # Modernize-specific sections
        transformation_html = self._build_transformation_section(plan)
        competitors_html = self._build_competitors_section(insights)

        # Embed prototype
        prototype_section = ""
        if prototype_html:
            prototype_section = f"""
            <div class="section prototype-section">
                <div class="section-header">
                    <div class="section-icon">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17 1.01L7 1c-1.1 0-2 .9-2 2v18c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V3c0-1.1-.9-1.99-2-1.99zM17 19H7V5h10v14z"/></svg>
                    </div>
                    <h2>Your Digital Future</h2>
                </div>
                <p class="section-intro">This is what {business_name} looks like in the digital age. Click through to explore.</p>
                <div class="prototype-embed">
                    <iframe srcdoc='{prototype_html.replace("'", "&#39;")}' style="width: 100%; height: 700px; border: none; border-radius: 16px;"></iframe>
                </div>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} - Digital Transformation Vision</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');

        :root {{
            --primary: {plan.primary_color};
            --secondary: {plan.secondary_color};
            --accent: #F59E0B;
            --dark: #0F172A;
            --dark-secondary: #1E293B;
            --light: #F8FAFC;
            --text: #334155;
            --text-light: #64748B;
            --success: #10B981;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: var(--light); color: var(--text); line-height: 1.6; }}

        .cover {{
            background: linear-gradient(135deg, var(--dark) 0%, var(--dark-secondary) 100%);
            color: white;
            padding: 100px 60px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
        }}

        .cover::before {{
            content: 'DIGITAL TRANSFORMATION';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 120px;
            font-weight: 800;
            opacity: 0.03;
            white-space: nowrap;
        }}

        .cover-content {{ position: relative; z-index: 1; max-width: 700px; }}

        .cover-eyebrow {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255,255,255,0.1);
            padding: 10px 20px;
            border-radius: 30px;
            font-size: 13px;
            margin-bottom: 24px;
        }}

        .cover-eyebrow::before {{
            content: '';
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        .cover h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 64px;
            font-weight: 700;
            line-height: 1.1;
            margin-bottom: 24px;
        }}

        .cover h1 span {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .cover .subtitle {{
            font-size: 20px;
            opacity: 0.8;
            margin-bottom: 40px;
            line-height: 1.6;
        }}

        .container {{ max-width: 1000px; margin: 0 auto; padding: 60px 40px; }}

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
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }}

        .section-icon svg {{ width: 24px; height: 24px; }}
        .section h2 {{ font-size: 28px; font-weight: 700; color: var(--dark); }}
        .section-intro {{ font-size: 17px; color: var(--text-light); margin-bottom: 32px; line-height: 1.7; }}

        /* Transformation Section */
        .transformation-grid {{
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 32px;
            align-items: center;
        }}

        .transformation-side {{
            background: var(--light);
            border-radius: 16px;
            padding: 32px;
            text-align: center;
        }}

        .transformation-side.before {{ border: 2px dashed #CBD5E1; }}
        .transformation-side.after {{ border: 2px solid var(--primary); background: linear-gradient(135deg, var(--primary)08, var(--secondary)05); }}

        .transformation-label {{
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 16px;
        }}

        .transformation-side.before .transformation-label {{ color: var(--text-light); }}
        .transformation-side.after .transformation-label {{ color: var(--primary); }}

        .transformation-list {{ text-align: left; }}
        .transformation-list li {{
            padding: 8px 0;
            font-size: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .transformation-arrow {{
            width: 60px;
            height: 60px;
            background: var(--primary);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }}

        /* Reuse other styles from build report */
        .fun-facts-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }}
        .fun-fact {{ background: linear-gradient(135deg, var(--primary)08, var(--secondary)05); border: 1px solid var(--primary)15; border-radius: 16px; padding: 24px; display: flex; gap: 16px; }}
        .fun-fact-icon {{ width: 40px; height: 40px; background: var(--primary); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; font-size: 18px; flex-shrink: 0; }}
        .fun-fact-text {{ font-size: 15px; color: var(--dark); line-height: 1.5; }}

        .psychology-cards {{ display: grid; gap: 20px; }}
        .psychology-card {{ background: var(--light); border-radius: 16px; padding: 28px; border-left: 4px solid var(--primary); }}
        .psychology-principle {{ font-size: 18px; font-weight: 700; color: var(--dark); margin-bottom: 12px; }}
        .psychology-insight {{ font-size: 15px; color: var(--text); margin-bottom: 12px; line-height: 1.6; }}
        .psychology-source {{ font-size: 13px; color: var(--text-light); font-style: italic; }}

        .case-studies-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
        .case-study {{ background: var(--dark); color: white; border-radius: 20px; padding: 28px; text-align: center; }}
        .case-study-company {{ font-size: 22px; font-weight: 700; margin-bottom: 16px; }}
        .case-study-result {{ background: var(--primary); display: inline-block; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; margin-bottom: 16px; }}
        .case-study-insight {{ font-size: 14px; opacity: 0.9; line-height: 1.5; }}

        .market-stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }}
        .market-stat {{ text-align: center; padding: 24px; background: linear-gradient(135deg, var(--primary)10, var(--secondary)05); border-radius: 16px; }}
        .market-stat-value {{ font-size: 28px; font-weight: 800; color: var(--primary); margin-bottom: 8px; }}
        .market-stat-label {{ font-size: 13px; color: var(--text-light); }}

        .features-table {{ width: 100%; border-collapse: collapse; }}
        .features-table th {{ text-align: left; padding: 16px; background: var(--light); font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-light); }}
        .features-table td {{ padding: 20px 16px; border-bottom: 1px solid var(--light); }}
        .feature-name {{ font-weight: 600; color: var(--dark); margin-bottom: 4px; }}
        .feature-desc {{ font-size: 14px; color: var(--text-light); }}
        .priority-badge {{ display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
        .priority-high {{ background: #FEE2E2; color: #DC2626; }}
        .priority-medium {{ background: #FEF3C7; color: #D97706; }}
        .priority-low {{ background: #D1FAE5; color: #059669; }}

        .prototype-embed {{ background: var(--dark); border-radius: 20px; padding: 24px; margin: 24px 0; }}

        .investment-card {{
            background: linear-gradient(135deg, var(--dark), var(--dark-secondary));
            color: white;
            border-radius: 24px;
            padding: 48px;
            text-align: center;
        }}

        .investment-label {{ font-size: 14px; opacity: 0.8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }}
        .investment-amount {{ font-size: 56px; font-weight: 800; background: linear-gradient(135deg, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 16px; }}
        .investment-note {{ font-size: 15px; opacity: 0.8; margin-bottom: 32px; }}

        .roi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }}
        .roi-item {{ background: rgba(255,255,255,0.1); padding: 24px; border-radius: 16px; }}
        .roi-value {{ font-size: 28px; font-weight: 700; color: var(--primary); }}
        .roi-label {{ font-size: 13px; opacity: 0.8; margin-top: 8px; }}

        .quote-callout {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            margin: 32px 0;
        }}

        .quote-text {{ font-size: 22px; font-weight: 500; line-height: 1.5; margin-bottom: 16px; }}
        .quote-author {{ font-size: 14px; opacity: 0.9; }}

        .footer {{
            text-align: center;
            padding: 60px 40px;
            background: var(--dark);
            color: white;
        }}

        .footer-logo {{ font-size: 28px; font-weight: 700; margin-bottom: 8px; }}
        .footer-tagline {{ font-size: 15px; opacity: 0.7; margin-bottom: 24px; }}
        .footer-contact {{ font-size: 14px; opacity: 0.6; }}

        @media (max-width: 768px) {{
            .cover h1 {{ font-size: 40px; }}
            .transformation-grid {{ grid-template-columns: 1fr; }}
            .fun-facts-grid, .case-studies-grid, .market-stats {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="cover">
        <div class="cover-content">
            <span class="cover-eyebrow">Digital Transformation Vision</span>
            <h1>What if <span>{business_name}</span> had an app?</h1>
            <p class="subtitle">
                Your competitors are going digital. Your customers expect it.
                Here's exactly what your transformation looks like - and how to make it happen.
            </p>
        </div>
    </div>

    <div class="container">
        {transformation_html}

        <div class="quote-callout">
            <div class="quote-text">"Every business is a software business now."</div>
            <div class="quote-author">- Satya Nadella, CEO of Microsoft</div>
        </div>

        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
                </div>
                <h2>Why Now?</h2>
            </div>
            <p class="section-intro">The digital shift in your industry is happening faster than ever.</p>
            {fun_facts_html}
        </div>

        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/></svg>
                </div>
                <h2>Market Opportunity</h2>
            </div>
            {market_stats_html}
        </div>

        {competitors_html}

        {prototype_section}

        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                </div>
                <h2>The Psychology of Digital</h2>
            </div>
            <p class="section-intro">Why these features work - backed by behavioral science.</p>
            {psychology_html}
        </div>

        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
                </div>
                <h2>Success Stories</h2>
            </div>
            <p class="section-intro">Businesses like yours that made the leap.</p>
            {case_studies_html}
        </div>

        {features_html}

        {design_html}

        <div class="section" style="padding: 0; background: transparent; box-shadow: none;">
            <div class="investment-card">
                <div class="investment-label">Total Investment</div>
                <div class="investment-amount">${total_min:,} - ${total_max:,}</div>
                <div class="investment-note">One-time investment for a permanent competitive advantage</div>
                <div class="roi-grid">
                    <div class="roi-item">
                        <div class="roi-value">10-20%</div>
                        <div class="roi-label">Revenue Increase</div>
                    </div>
                    <div class="roi-item">
                        <div class="roi-value">30-40%</div>
                        <div class="roi-label">Retention Boost</div>
                    </div>
                    <div class="roi-item">
                        <div class="roi-value">6-12 mo</div>
                        <div class="roi-label">Typical Payback</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="footer-logo">{self.config.company_name}</div>
        <div class="footer-tagline">{self.config.company_tagline}</div>
        <div class="footer-contact">{self.config.contact_email} | {self.config.contact_phone}</div>
    </div>
</body>
</html>"""

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"[MODERNIZE REPORT] Saved to: {output_path}")

        return html

    def _build_transformation_section(self, plan) -> str:
        """Build the before/after transformation visualization"""
        before_items = [
            "Phone calls to book appointments",
            "Paper loyalty cards that get lost",
            "Walk-ins with long wait times",
            "No way to browse before visiting",
            "Lost revenue from no-shows",
        ]

        after_items = [
            "24/7 online booking",
            "Digital loyalty with push notifications",
            "Pre-order and skip the wait",
            "Full catalog browsable anytime",
            "Automated reminders reduce no-shows",
        ]

        before_html = "".join(f'<li><span style="color: #EF4444;">-</span> {item}</li>' for item in before_items)
        after_html = "".join(f'<li><span style="color: #10B981;">+</span> {item}</li>' for item in after_items)

        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"/></svg>
                </div>
                <h2>The Transformation</h2>
            </div>
            <div class="transformation-grid">
                <div class="transformation-side before">
                    <div class="transformation-label">Today</div>
                    <ul class="transformation-list">
                        {before_html}
                    </ul>
                </div>
                <div class="transformation-arrow">
                    <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor"><path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"/></svg>
                </div>
                <div class="transformation-side after">
                    <div class="transformation-label">With Your App</div>
                    <ul class="transformation-list">
                        {after_html}
                    </ul>
                </div>
            </div>
        </div>
        """

    def _build_competitors_section(self, insights: Dict) -> str:
        """Build section showing competitor apps"""
        competitors = insights.get('case_studies', [])
        if not competitors:
            return ""

        return f"""
        <div class="section">
            <div class="section-header">
                <div class="section-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
                </div>
                <h2>Your Competitors Are Already Digital</h2>
            </div>
            <p class="section-intro">These companies in your space have already made the leap - and they're reaping the rewards.</p>
            <div class="case-studies-grid">
                {''.join(f"""
                <div class="case-study">
                    <div class="case-study-company">{c['company']}</div>
                    <div class="case-study-result">{c['result']}</div>
                    <div class="case-study-insight">{c['insight']}</div>
                </div>
                """ for c in competitors)}
            </div>
        </div>
        """

    # =========================================================================
    # AUDIT MODE - Existing app with issues
    # =========================================================================

    def generate_audit_report_full(self, audit_data: Dict, prototype_html: str = None, output_path: str = None) -> str:
        """
        Generate report for AUDIT mode
        For: Existing apps with issues (abandonment, UX problems, etc.)
        Framing: "Here's what's wrong and how to fix it"
        """
        app_name = audit_data.get('app_name', 'Your App')
        industry = audit_data.get('industry', 'service')
        primary_color = audit_data.get('primary_color', '#EF4444')  # Red for issues
        secondary_color = audit_data.get('secondary_color', '#10B981')  # Green for solutions

        insights = self.INDUSTRY_INSIGHTS.get(industry, self.INDUSTRY_INSIGHTS['service'])

        # Extract audit data
        findings = audit_data.get('findings', [])
        metrics = audit_data.get('metrics', {})
        recommendations = audit_data.get('recommendations', [])

        # Calculate severity counts
        critical = len([f for f in findings if f.get('severity') == 'critical'])
        high = len([f for f in findings if f.get('severity') == 'high'])
        medium = len([f for f in findings if f.get('severity') == 'medium'])

        # Build findings HTML
        findings_html = ""
        for f in findings:
            severity = f.get('severity', 'medium')
            severity_colors = {
                'critical': ('#FEE2E2', '#DC2626'),
                'high': ('#FEF3C7', '#D97706'),
                'medium': ('#E0E7FF', '#4F46E5'),
                'low': ('#D1FAE5', '#059669')
            }
            bg, color = severity_colors.get(severity, severity_colors['medium'])

            findings_html += f"""
            <div style="background: white; border-radius: 16px; padding: 24px; margin-bottom: 16px; border-left: 4px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                    <h4 style="font-size: 17px; font-weight: 600; color: #1E293B; margin: 0;">{f.get('title', 'Issue')}</h4>
                    <span style="background: {bg}; color: {color}; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase;">{severity}</span>
                </div>
                <p style="font-size: 15px; color: #64748B; margin-bottom: 12px;">{f.get('description', '')}</p>
                <div style="background: #FEF2F2; border-radius: 8px; padding: 12px; font-size: 14px; color: #991B1B;">
                    <strong>Business Impact:</strong> {f.get('impact', 'Affects user experience')}
                </div>
            </div>
            """

        # Build recommendations HTML
        recs_html = ""
        for i, rec in enumerate(recommendations, 1):
            recs_html += f"""
            <div style="display: flex; gap: 20px; margin-bottom: 24px;">
                <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #10B981, #059669); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 18px; flex-shrink: 0;">{i}</div>
                <div style="flex: 1;">
                    <h4 style="font-size: 17px; font-weight: 600; color: #1E293B; margin-bottom: 8px;">{rec.get('title', 'Fix')}</h4>
                    <p style="font-size: 15px; color: #64748B; margin-bottom: 8px;">{rec.get('description', '')}</p>
                    <div style="display: flex; gap: 16px; font-size: 13px;">
                        <span style="color: #10B981;"><strong>Effort:</strong> {rec.get('effort', 'Medium')}</span>
                        <span style="color: #6366F1;"><strong>Impact:</strong> {rec.get('impact_level', 'High')}</span>
                    </div>
                </div>
            </div>
            """

        # Build before/after
        before_after_html = ""
        if prototype_html:
            before_after_html = f"""
            <div style="background: white; border-radius: 24px; padding: 48px; margin-bottom: 32px; box-shadow: 0 4px 20px rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px;">
                    <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #10B981, #059669); border-radius: 14px; display: flex; align-items: center; justify-content: center; color: white;">
                        <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z"/></svg>
                    </div>
                    <h2 style="font-size: 28px; font-weight: 700; color: #0F172A;">The Fixed Version</h2>
                </div>
                <p style="font-size: 17px; color: #64748B; margin-bottom: 32px;">Here's what {app_name} looks like with our recommendations implemented.</p>
                <div style="background: #0F172A; border-radius: 20px; padding: 24px;">
                    <iframe srcdoc='{prototype_html.replace("'", "&#39;")}' style="width: 100%; height: 700px; border: none; border-radius: 16px;"></iframe>
                </div>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name} - UX Audit Report</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #F1F5F9; color: #334155; line-height: 1.6; }}

        .cover {{
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            color: white;
            padding: 80px 60px;
            position: relative;
            overflow: hidden;
        }}

        .cover::before {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 50%;
            height: 100%;
            background: linear-gradient(135deg, #EF444420, #F59E0B20);
        }}

        .cover-content {{ position: relative; z-index: 1; max-width: 600px; }}

        .cover-badge {{
            display: inline-block;
            background: #EF4444;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 24px;
        }}

        .cover h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 48px;
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 20px;
        }}

        .cover .subtitle {{
            font-size: 18px;
            opacity: 0.9;
            margin-bottom: 40px;
        }}

        .stats-bar {{
            display: flex;
            gap: 32px;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 36px;
            font-weight: 800;
        }}

        .stat-value.critical {{ color: #EF4444; }}
        .stat-value.warning {{ color: #F59E0B; }}
        .stat-value.info {{ color: #6366F1; }}

        .stat-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.7;
        }}

        .container {{ max-width: 1000px; margin: 0 auto; padding: 60px 40px; }}

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
            width: 48px;
            height: 48px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }}

        .section-icon.danger {{ background: linear-gradient(135deg, #EF4444, #DC2626); }}
        .section-icon.success {{ background: linear-gradient(135deg, #10B981, #059669); }}
        .section-icon.info {{ background: linear-gradient(135deg, #6366F1, #4F46E5); }}

        .section-icon svg {{ width: 24px; height: 24px; }}
        .section h2 {{ font-size: 28px; font-weight: 700; color: #0F172A; }}
        .section-intro {{ font-size: 17px; color: #64748B; margin-bottom: 32px; line-height: 1.7; }}

        .funnel {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 32px 0;
        }}

        .funnel-step {{
            text-align: center;
            flex: 1;
        }}

        .funnel-bar {{
            height: 40px;
            background: linear-gradient(90deg, #10B981, #F59E0B, #EF4444);
            border-radius: 8px;
            margin-bottom: 8px;
            position: relative;
        }}

        .funnel-value {{
            font-size: 24px;
            font-weight: 700;
            color: #0F172A;
        }}

        .funnel-label {{
            font-size: 13px;
            color: #64748B;
        }}

        .drop-indicator {{
            color: #EF4444;
            font-size: 14px;
            font-weight: 600;
        }}

        .footer {{
            text-align: center;
            padding: 60px 40px;
            background: #0F172A;
            color: white;
        }}

        .footer-logo {{ font-size: 28px; font-weight: 700; margin-bottom: 8px; }}
        .footer-tagline {{ font-size: 15px; opacity: 0.7; margin-bottom: 24px; }}
        .footer-contact {{ font-size: 14px; opacity: 0.6; }}
    </style>
</head>
<body>
    <div class="cover">
        <div class="cover-content">
            <span class="cover-badge">UX Audit Complete</span>
            <h1>{app_name} Audit Report</h1>
            <p class="subtitle">We found {len(findings)} issues affecting your user experience and conversion rates. Here's the full breakdown and how to fix them.</p>
            <div class="stats-bar">
                <div class="stat">
                    <div class="stat-value critical">{critical}</div>
                    <div class="stat-label">Critical</div>
                </div>
                <div class="stat">
                    <div class="stat-value warning">{high}</div>
                    <div class="stat-label">High Priority</div>
                </div>
                <div class="stat">
                    <div class="stat-value info">{medium}</div>
                    <div class="stat-label">Medium</div>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <!-- Executive Summary -->
        <div class="section">
            <div class="section-header">
                <div class="section-icon danger">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>
                </div>
                <h2>Executive Summary</h2>
            </div>
            <p class="section-intro">
                Our audit identified <strong>{len(findings)} issues</strong> that are directly impacting your metrics.
                {f"<strong style='color: #EF4444;'>{critical} critical issues</strong> require immediate attention." if critical > 0 else ""}
                The good news: all of these are fixable, and we've prioritized them by impact.
            </p>
            <div style="background: #FEF2F2; border-radius: 16px; padding: 24px; border: 1px solid #FECACA;">
                <h4 style="color: #991B1B; margin-bottom: 12px;">Key Finding</h4>
                <p style="color: #7F1D1D; font-size: 15px;">
                    Based on industry benchmarks, fixing these issues could improve your conversion rate by <strong>15-25%</strong> and reduce drop-off by <strong>30-40%</strong>.
                </p>
            </div>
        </div>

        <!-- Issues Found -->
        <div class="section">
            <div class="section-header">
                <div class="section-icon danger">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                </div>
                <h2>Issues Found</h2>
            </div>
            <p class="section-intro">Each issue is prioritized by severity and includes the business impact.</p>
            {findings_html if findings_html else '<p style="color: #64748B;">No critical issues found.</p>'}
        </div>

        {before_after_html}

        <!-- Recommendations -->
        <div class="section">
            <div class="section-header">
                <div class="section-icon success">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                </div>
                <h2>Recommended Fixes</h2>
            </div>
            <p class="section-intro">Prioritized by impact and effort. Start with #1 for the biggest quick win.</p>
            {recs_html if recs_html else '<p style="color: #64748B;">Recommendations will be added based on findings.</p>'}
        </div>

        <!-- Industry Benchmarks -->
        <div class="section">
            <div class="section-header">
                <div class="section-icon info">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>
                </div>
                <h2>Industry Benchmarks</h2>
            </div>
            <p class="section-intro">How you compare to top performers in your space.</p>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;">
                <div style="text-align: center; padding: 24px; background: #F8FAFC; border-radius: 16px;">
                    <div style="font-size: 28px; font-weight: 800; color: #6366F1;">{insights['market_stats'].get('market_size', 'N/A')}</div>
                    <div style="font-size: 13px; color: #64748B;">Market Size</div>
                </div>
                <div style="text-align: center; padding: 24px; background: #F8FAFC; border-radius: 16px;">
                    <div style="font-size: 28px; font-weight: 800; color: #6366F1;">{insights['market_stats'].get('mobile_adoption', 'N/A')}</div>
                    <div style="font-size: 13px; color: #64748B;">Mobile Adoption</div>
                </div>
                <div style="text-align: center; padding: 24px; background: #F8FAFC; border-radius: 16px;">
                    <div style="font-size: 28px; font-weight: 800; color: #6366F1;">{insights['market_stats'].get('growth_rate', 'N/A')}</div>
                    <div style="font-size: 13px; color: #64748B;">Growth Rate</div>
                </div>
                <div style="text-align: center; padding: 24px; background: #F8FAFC; border-radius: 16px;">
                    <div style="font-size: 28px; font-weight: 800; color: #10B981;">{insights['market_stats'].get('avg_roi', 'N/A')}</div>
                    <div style="font-size: 13px; color: #64748B;">Avg ROI on Fixes</div>
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="footer-logo">{self.config.company_name}</div>
        <div class="footer-tagline">{self.config.company_tagline}</div>
        <div class="footer-contact">{self.config.contact_email} | {self.config.contact_phone}</div>
    </div>
</body>
</html>"""

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"[AUDIT REPORT] Saved to: {output_path}")

        return html
