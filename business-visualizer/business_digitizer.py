"""
Business Digitization Visualizer
Transform business ideas into visual app prototypes through multi-agent deliberation.

Usage:
    python business_digitizer.py --interactive
    python business_digitizer.py --business "Local coffee shop in Brooklyn"
    python business_digitizer.py --config business_brief.json

Flow:
    1. Business intake (what does the business do?)
    2. Agent deliberation (research, strategy, design)
    3. Plan generation (features, screens, style)
    4. Prototype creation (interactive HTML)
    5. Client presentation ready!
"""

import json
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import random


# ============================================================================
# BUSINESS PROFILES & INDUSTRY DATA
# ============================================================================

INDUSTRY_PROFILES = {
    "restaurant": {
        "keywords": ["restaurant", "cafe", "coffee", "bakery", "food", "dining", "eatery", "bistro", "pizzeria", "bar", "pub", "grill"],
        "colors": {
            "warm": ["#D4A574", "#8B4513", "#CD853F", "#DEB887", "#F4A460"],
            "modern": ["#2D3436", "#636E72", "#B2BEC3", "#DFE6E9", "#FF7675"],
            "fresh": ["#00B894", "#55EFC4", "#81ECEC", "#74B9FF", "#A29BFE"]
        },
        "fonts": {
            "headings": ["Playfair Display", "Merriweather", "Lora", "Cormorant Garamond"],
            "body": ["Open Sans", "Lato", "Source Sans Pro", "Nunito"]
        },
        "core_features": [
            {"name": "Mobile Ordering", "description": "Order ahead, skip the line", "priority": "high"},
            {"name": "Digital Menu", "description": "Browse menu with photos and descriptions", "priority": "high"},
            {"name": "Loyalty Rewards", "description": "Earn points, get free items", "priority": "high"},
            {"name": "Table Reservation", "description": "Book tables in advance", "priority": "medium"},
            {"name": "Order History", "description": "Reorder favorites quickly", "priority": "medium"},
            {"name": "Push Notifications", "description": "Daily specials and promotions", "priority": "low"}
        ],
        "screens": ["Home", "Menu", "Cart", "Order Tracking", "Loyalty", "Profile"],
        "style_keywords": ["warm", "inviting", "cozy", "appetizing", "friendly"]
    },

    "fitness": {
        "keywords": ["gym", "fitness", "yoga", "pilates", "crossfit", "trainer", "wellness", "health", "workout", "studio"],
        "colors": {
            "energetic": ["#E84545", "#FF6B6B", "#FFA502", "#FF6348", "#EE5A24"],
            "calm": ["#00CEC9", "#81ECEC", "#55EFC4", "#00B894", "#A29BFE"],
            "dark": ["#2D3436", "#636E72", "#1E272E", "#485460", "#0A3D62"]
        },
        "fonts": {
            "headings": ["Montserrat", "Oswald", "Bebas Neue", "Anton"],
            "body": ["Roboto", "Open Sans", "Lato", "Poppins"]
        },
        "core_features": [
            {"name": "Class Booking", "description": "Book fitness classes instantly", "priority": "high"},
            {"name": "Workout Tracking", "description": "Log exercises and progress", "priority": "high"},
            {"name": "Trainer Profiles", "description": "Find and book personal trainers", "priority": "medium"},
            {"name": "Membership Management", "description": "View and manage membership", "priority": "high"},
            {"name": "Progress Photos", "description": "Track visual transformation", "priority": "medium"},
            {"name": "Nutrition Logging", "description": "Track meals and macros", "priority": "low"}
        ],
        "screens": ["Home", "Classes", "Book Class", "My Schedule", "Progress", "Profile"],
        "style_keywords": ["energetic", "motivating", "bold", "dynamic", "powerful"]
    },

    "retail": {
        "keywords": ["shop", "store", "retail", "boutique", "clothing", "fashion", "jewelry", "accessories", "gifts"],
        "colors": {
            "luxury": ["#2C3E50", "#34495E", "#BDC3C7", "#ECF0F1", "#D4AC0D"],
            "playful": ["#E91E63", "#9C27B0", "#673AB7", "#3F51B5", "#00BCD4"],
            "minimal": ["#FFFFFF", "#F5F5F5", "#E0E0E0", "#212121", "#757575"]
        },
        "fonts": {
            "headings": ["Playfair Display", "Bodoni Moda", "Cormorant", "Libre Baskerville"],
            "body": ["Helvetica Neue", "Inter", "Roboto", "SF Pro Display"]
        },
        "core_features": [
            {"name": "Product Catalog", "description": "Browse full inventory with filters", "priority": "high"},
            {"name": "Shopping Cart", "description": "Easy checkout experience", "priority": "high"},
            {"name": "Wishlist", "description": "Save items for later", "priority": "medium"},
            {"name": "Order Tracking", "description": "Track shipments in real-time", "priority": "high"},
            {"name": "Size Guide", "description": "Find the perfect fit", "priority": "medium"},
            {"name": "Reviews", "description": "Read customer reviews", "priority": "medium"}
        ],
        "screens": ["Home", "Shop", "Product Detail", "Cart", "Checkout", "Orders"],
        "style_keywords": ["elegant", "clean", "sophisticated", "curated", "stylish"]
    },

    "service": {
        "keywords": ["plumber", "electrician", "cleaner", "handyman", "contractor", "repair", "maintenance", "lawn", "pest", "hvac"],
        "colors": {
            "professional": ["#2C3E50", "#3498DB", "#1ABC9C", "#27AE60", "#F39C12"],
            "trustworthy": ["#1E3A5F", "#3D5A80", "#98C1D9", "#E0FBFC", "#EE6C4D"],
            "clean": ["#FFFFFF", "#F8F9FA", "#4A90A4", "#2C3E50", "#28A745"]
        },
        "fonts": {
            "headings": ["Poppins", "Raleway", "Montserrat", "Work Sans"],
            "body": ["Open Sans", "Lato", "Source Sans Pro", "Nunito"]
        },
        "core_features": [
            {"name": "Service Booking", "description": "Book appointments instantly", "priority": "high"},
            {"name": "Instant Quotes", "description": "Get price estimates upfront", "priority": "high"},
            {"name": "Technician Tracking", "description": "See when they'll arrive", "priority": "high"},
            {"name": "Service History", "description": "View past jobs and invoices", "priority": "medium"},
            {"name": "Photo Uploads", "description": "Share photos of the issue", "priority": "medium"},
            {"name": "Reviews & Ratings", "description": "Rate your experience", "priority": "medium"}
        ],
        "screens": ["Home", "Services", "Book Service", "Tracking", "History", "Profile"],
        "style_keywords": ["professional", "trustworthy", "reliable", "clean", "efficient"]
    },

    "healthcare": {
        "keywords": ["doctor", "clinic", "dental", "medical", "health", "therapy", "counseling", "chiropractic", "dermatology", "optometry"],
        "colors": {
            "calming": ["#E8F4F8", "#B8D4E3", "#7FB3D5", "#2980B9", "#1A5276"],
            "clean": ["#FFFFFF", "#F0F4F8", "#D9E2EC", "#627D98", "#243B53"],
            "warm": ["#FEF9E7", "#FADBD8", "#D5F5E3", "#AED6F1", "#D7BDE2"]
        },
        "fonts": {
            "headings": ["Nunito", "Poppins", "Quicksand", "Cabin"],
            "body": ["Open Sans", "Lato", "Source Sans Pro", "Roboto"]
        },
        "core_features": [
            {"name": "Appointment Booking", "description": "Schedule visits online", "priority": "high"},
            {"name": "Telehealth", "description": "Video consultations from home", "priority": "high"},
            {"name": "Medical Records", "description": "Access your health history", "priority": "high"},
            {"name": "Prescription Refills", "description": "Request refills easily", "priority": "medium"},
            {"name": "Lab Results", "description": "View test results securely", "priority": "medium"},
            {"name": "Symptom Checker", "description": "AI-powered symptom assessment", "priority": "low"}
        ],
        "screens": ["Home", "Book Appointment", "My Health", "Messages", "Prescriptions", "Profile"],
        "style_keywords": ["calming", "trustworthy", "clean", "caring", "professional"]
    },

    "beauty": {
        "keywords": ["salon", "spa", "beauty", "hair", "nails", "massage", "skincare", "barbershop", "aesthetic", "wellness"],
        "colors": {
            "elegant": ["#F8E1E7", "#E8B4BC", "#D4A5A5", "#9E7777", "#6F4E4E"],
            "modern": ["#2D3436", "#636E72", "#DFE6E9", "#FFEAA7", "#FDCB6E"],
            "fresh": ["#DFE6DA", "#A8DADC", "#457B9D", "#1D3557", "#F1FAEE"]
        },
        "fonts": {
            "headings": ["Cormorant Garamond", "Playfair Display", "Libre Baskerville", "Lora"],
            "body": ["Montserrat", "Lato", "Raleway", "Nunito"]
        },
        "core_features": [
            {"name": "Service Booking", "description": "Book appointments 24/7", "priority": "high"},
            {"name": "Stylist Selection", "description": "Choose your preferred stylist", "priority": "high"},
            {"name": "Service Menu", "description": "Browse all services and prices", "priority": "high"},
            {"name": "Loyalty Program", "description": "Earn rewards on visits", "priority": "medium"},
            {"name": "Photo Gallery", "description": "See stylist portfolios", "priority": "medium"},
            {"name": "Gift Cards", "description": "Purchase digital gift cards", "priority": "low"}
        ],
        "screens": ["Home", "Services", "Stylists", "Book", "My Appointments", "Profile"],
        "style_keywords": ["elegant", "luxurious", "relaxing", "sophisticated", "pampering"]
    },

    "education": {
        "keywords": ["school", "tutor", "learning", "course", "training", "academy", "education", "teaching", "coaching", "music lessons"],
        "colors": {
            "academic": ["#1E3A5F", "#3D5A80", "#98C1D9", "#E0FBFC", "#293241"],
            "playful": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"],
            "modern": ["#6C5CE7", "#A29BFE", "#DFE6E9", "#2D3436", "#00B894"]
        },
        "fonts": {
            "headings": ["Poppins", "Nunito", "Quicksand", "Comfortaa"],
            "body": ["Open Sans", "Lato", "Roboto", "Source Sans Pro"]
        },
        "core_features": [
            {"name": "Course Catalog", "description": "Browse available courses", "priority": "high"},
            {"name": "Class Scheduling", "description": "Book lessons and sessions", "priority": "high"},
            {"name": "Progress Tracking", "description": "Monitor learning progress", "priority": "high"},
            {"name": "Video Lessons", "description": "Access recorded content", "priority": "medium"},
            {"name": "Assignments", "description": "Submit and track homework", "priority": "medium"},
            {"name": "Certificates", "description": "Earn completion certificates", "priority": "low"}
        ],
        "screens": ["Home", "Courses", "My Learning", "Schedule", "Progress", "Profile"],
        "style_keywords": ["inspiring", "engaging", "friendly", "organized", "encouraging"]
    },

    "realestate": {
        "keywords": ["real estate", "realtor", "property", "homes", "apartment", "rental", "broker", "housing", "mortgage"],
        "colors": {
            "luxury": ["#1A1A2E", "#16213E", "#0F3460", "#E94560", "#FFFFFF"],
            "trustworthy": ["#2C3E50", "#34495E", "#3498DB", "#ECF0F1", "#1ABC9C"],
            "warm": ["#F5E6D3", "#E8D4C4", "#C9B79C", "#8E7F7F", "#5C5C5C"]
        },
        "fonts": {
            "headings": ["Playfair Display", "Cormorant Garamond", "Bodoni Moda", "Libre Baskerville"],
            "body": ["Montserrat", "Raleway", "Open Sans", "Lato"]
        },
        "core_features": [
            {"name": "Property Search", "description": "Find homes with smart filters", "priority": "high"},
            {"name": "Virtual Tours", "description": "360° property walkthroughs", "priority": "high"},
            {"name": "Saved Listings", "description": "Save and compare favorites", "priority": "high"},
            {"name": "Agent Contact", "description": "Message agents directly", "priority": "high"},
            {"name": "Mortgage Calculator", "description": "Estimate monthly payments", "priority": "medium"},
            {"name": "Neighborhood Info", "description": "Schools, transit, amenities", "priority": "medium"}
        ],
        "screens": ["Home", "Search", "Property Detail", "Saved", "Messages", "Profile"],
        "style_keywords": ["trustworthy", "sophisticated", "premium", "professional", "welcoming"]
    }
}


# ============================================================================
# AGENT DEFINITIONS
# ============================================================================

@dataclass
class AgentThought:
    """A single thought from an agent during deliberation"""
    agent: str
    thought: str
    decision: Optional[str] = None
    confidence: float = 0.8


@dataclass
class BusinessPlan:
    """The complete plan for digitizing a business"""
    business_name: str
    business_type: str
    industry: str
    target_audience: str

    # Design decisions
    primary_color: str
    secondary_color: str
    accent_color: str
    heading_font: str
    body_font: str
    style_mood: str

    # Features
    core_features: List[Dict]
    screens: List[Dict]

    # Agent deliberation log
    deliberation_log: List[AgentThought] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ResearchAgent:
    """Researches the industry and competitors"""

    name = "Research Agent"

    def analyze(self, business_description: str, industry_data: Dict) -> List[AgentThought]:
        thoughts = []

        thoughts.append(AgentThought(
            agent=self.name,
            thought=f"Analyzing business: '{business_description}'",
        ))

        thoughts.append(AgentThought(
            agent=self.name,
            thought=f"Industry identified: {industry_data.get('keywords', ['general'])[0].title()}",
            decision=f"This is a {industry_data.get('keywords', ['general'])[0]} business"
        ))

        # Analyze common features in industry
        features = industry_data.get('core_features', [])
        high_priority = [f['name'] for f in features if f.get('priority') == 'high']

        thoughts.append(AgentThought(
            agent=self.name,
            thought=f"Top features in this industry: {', '.join(high_priority)}",
            decision="These features are essential for competitive positioning"
        ))

        # Target audience insight
        thoughts.append(AgentThought(
            agent=self.name,
            thought="Analyzing typical customer demographics and behavior patterns",
            decision="Target users expect mobile-first, quick interactions"
        ))

        return thoughts


class StrategyAgent:
    """Decides on features and prioritization"""

    name = "Strategy Agent"

    def analyze(self, business_description: str, industry_data: Dict, research_thoughts: List[AgentThought]) -> List[AgentThought]:
        thoughts = []

        thoughts.append(AgentThought(
            agent=self.name,
            thought="Reviewing research findings and formulating strategy",
        ))

        # Feature prioritization
        features = industry_data.get('core_features', [])

        thoughts.append(AgentThought(
            agent=self.name,
            thought="Prioritizing features based on user value and implementation effort",
            decision=f"MVP should include: {', '.join([f['name'] for f in features[:3]])}"
        ))

        # Screens decision
        screens = industry_data.get('screens', ['Home', 'Main', 'Profile'])

        thoughts.append(AgentThought(
            agent=self.name,
            thought=f"Core user journey requires {len(screens)} main screens",
            decision=f"Screens: {' > '.join(screens)}"
        ))

        # Differentiation
        thoughts.append(AgentThought(
            agent=self.name,
            thought="Identifying opportunities for differentiation from competitors",
            decision="Focus on speed, simplicity, and delightful micro-interactions"
        ))

        return thoughts


class DesignAgent:
    """Decides on visual style, colors, fonts"""

    name = "Design Agent"

    def analyze(self, business_description: str, industry_data: Dict, strategy_thoughts: List[AgentThought]) -> List[AgentThought]:
        thoughts = []

        thoughts.append(AgentThought(
            agent=self.name,
            thought="Analyzing brand personality and visual direction",
        ))

        # Color palette selection
        color_options = industry_data.get('colors', {})
        style_keywords = industry_data.get('style_keywords', ['modern', 'clean'])

        # Pick a color scheme
        scheme_name = random.choice(list(color_options.keys())) if color_options else 'modern'
        colors = color_options.get(scheme_name, ['#6366F1', '#818CF8', '#C7D2FE'])

        thoughts.append(AgentThought(
            agent=self.name,
            thought=f"Evaluating color psychology for {style_keywords[0]} feel",
            decision=f"Selected '{scheme_name}' palette: {colors[0]} primary"
        ))

        # Font selection
        fonts = industry_data.get('fonts', {'headings': ['Poppins'], 'body': ['Open Sans']})
        heading_font = random.choice(fonts.get('headings', ['Poppins']))
        body_font = random.choice(fonts.get('body', ['Open Sans']))

        thoughts.append(AgentThought(
            agent=self.name,
            thought="Selecting typography for readability and brand personality",
            decision=f"Headings: {heading_font}, Body: {body_font}"
        ))

        # Overall mood
        mood = random.choice(style_keywords)
        thoughts.append(AgentThought(
            agent=self.name,
            thought=f"Defining overall visual mood as '{mood}'",
            decision=f"Design should feel: {', '.join(style_keywords[:3])}"
        ))

        return thoughts, {
            'scheme': scheme_name,
            'colors': colors,
            'heading_font': heading_font,
            'body_font': body_font,
            'mood': mood
        }


class PrototypeAgent:
    """Generates the actual prototype"""

    name = "Prototype Agent"

    def analyze(self, plan: BusinessPlan) -> List[AgentThought]:
        thoughts = []

        thoughts.append(AgentThought(
            agent=self.name,
            thought="Preparing to generate interactive prototype",
        ))

        thoughts.append(AgentThought(
            agent=self.name,
            thought=f"Building {len(plan.screens)} screens with {plan.style_mood} aesthetic",
            decision="Prototype will include mobile frames and navigation"
        ))

        thoughts.append(AgentThought(
            agent=self.name,
            thought="Generating HTML/CSS with responsive design",
            decision="Output: Interactive HTML file ready for client presentation"
        ))

        return thoughts


# ============================================================================
# MAIN DIGITIZER CLASS
# ============================================================================

class BusinessDigitizer:
    """Main orchestrator for business digitization"""

    def __init__(self, output_dir: str = "visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.research_agent = ResearchAgent()
        self.strategy_agent = StrategyAgent()
        self.design_agent = DesignAgent()
        self.prototype_agent = PrototypeAgent()

    def identify_industry(self, business_description: str) -> tuple:
        """Identify the industry from business description"""
        description_lower = business_description.lower()

        for industry, data in INDUSTRY_PROFILES.items():
            for keyword in data['keywords']:
                if keyword in description_lower:
                    return industry, data

        # Default to service if no match
        return "service", INDUSTRY_PROFILES["service"]

    def run_deliberation(self, business_description: str, business_name: str = None) -> BusinessPlan:
        """Run multi-agent deliberation to create a plan"""

        print("\n" + "="*60)
        print("BUSINESS DIGITIZATION - AGENT DELIBERATION")
        print("="*60)

        # Identify industry
        industry, industry_data = self.identify_industry(business_description)
        print(f"\n[INDUSTRY] Identified: {industry.title()}")

        all_thoughts = []

        # Research Agent
        print(f"\n[RESEARCH] {self.research_agent.name} analyzing...")
        research_thoughts = self.research_agent.analyze(business_description, industry_data)
        all_thoughts.extend(research_thoughts)
        for t in research_thoughts:
            if t.decision:
                print(f"   > {t.decision}")

        # Strategy Agent
        print(f"\n[STRATEGY] {self.strategy_agent.name} planning...")
        strategy_thoughts = self.strategy_agent.analyze(business_description, industry_data, research_thoughts)
        all_thoughts.extend(strategy_thoughts)
        for t in strategy_thoughts:
            if t.decision:
                print(f"   > {t.decision}")

        # Design Agent
        print(f"\n[DESIGN] {self.design_agent.name} designing...")
        design_thoughts, design_decisions = self.design_agent.analyze(business_description, industry_data, strategy_thoughts)
        all_thoughts.extend(design_thoughts)
        for t in design_thoughts:
            if t.decision:
                print(f"   > {t.decision}")

        # Build the plan
        colors = design_decisions['colors']

        plan = BusinessPlan(
            business_name=business_name or self._extract_name(business_description),
            business_type=industry,
            industry=industry,
            target_audience=f"{industry.title()} customers seeking convenience",
            primary_color=colors[0] if len(colors) > 0 else "#6366F1",
            secondary_color=colors[1] if len(colors) > 1 else "#818CF8",
            accent_color=colors[2] if len(colors) > 2 else "#C7D2FE",
            heading_font=design_decisions['heading_font'],
            body_font=design_decisions['body_font'],
            style_mood=design_decisions['mood'],
            core_features=industry_data.get('core_features', []),
            screens=self._build_screens(industry_data, design_decisions),
            deliberation_log=all_thoughts
        )

        # Prototype Agent
        print(f"\n[BUILD] {self.prototype_agent.name} building...")
        proto_thoughts = self.prototype_agent.analyze(plan)
        plan.deliberation_log.extend(proto_thoughts)
        for t in proto_thoughts:
            if t.decision:
                print(f"   > {t.decision}")

        print("\n" + "="*60)
        print("DELIBERATION COMPLETE")
        print("="*60)

        return plan

    def _extract_name(self, description: str) -> str:
        """Extract a business name from description"""
        # Simple extraction - take first few words
        words = description.split()[:3]
        return ' '.join(words).title()

    def _build_screens(self, industry_data: Dict, design: Dict) -> List[Dict]:
        """Build screen definitions for prototype"""
        screen_names = industry_data.get('screens', ['Home', 'Main', 'Profile'])
        features = industry_data.get('core_features', [])

        screens = []
        for i, name in enumerate(screen_names):
            # Find relevant feature for this screen
            related_feature = features[i] if i < len(features) else None

            screens.append({
                'id': name.lower().replace(' ', '-'),
                'name': name,
                'description': related_feature['description'] if related_feature else f'{name} screen',
                'feature': related_feature['name'] if related_feature else None
            })

        return screens

    def generate_prototype(self, plan: BusinessPlan, output_path: str = None) -> str:
        """Generate the HTML prototype from the plan"""

        if not output_path:
            safe_name = plan.business_name.lower().replace(' ', '_')[:20]
            output_path = self.output_dir / f"{safe_name}_prototype.html"

        # Build screen mockups
        screens_html = ""
        nav_tabs = ""

        for i, screen in enumerate(plan.screens):
            active = "active" if i == 0 else ""
            display = "block" if i == 0 else "none"

            nav_tabs += f"""
            <button class="nav-tab {active}" onclick="showScreen('{screen['id']}')" data-screen="{screen['id']}">
                {screen['name']}
            </button>
            """

            # Generate screen content based on type
            screen_content = self._generate_screen_content(screen, plan)

            screens_html += f"""
            <div class="screen-panel" id="screen-{screen['id']}" style="display: {display}">
                <div class="phone-frame">
                    <div class="phone-notch"></div>
                    <div class="phone-content">
                        {screen_content}
                    </div>
                </div>
                <div class="screen-info">
                    <h3>{screen['name']}</h3>
                    <p>{screen['description']}</p>
                </div>
            </div>
            """

        # Build features list
        features_html = ""
        for feature in plan.core_features[:6]:
            priority_color = {
                'high': plan.primary_color,
                'medium': plan.secondary_color,
                'low': '#94A3B8'
            }.get(feature.get('priority', 'medium'), plan.secondary_color)

            features_html += f"""
            <div class="feature-card">
                <div class="feature-priority" style="background: {priority_color}">
                    {feature.get('priority', 'medium').upper()}
                </div>
                <h4>{feature['name']}</h4>
                <p>{feature['description']}</p>
            </div>
            """

        # Build deliberation log
        deliberation_html = ""
        for thought in plan.deliberation_log:
            if thought.decision:
                deliberation_html += f"""
                <div class="thought">
                    <span class="agent-name">{thought.agent}</span>
                    <p>{thought.decision}</p>
                </div>
                """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{plan.business_name} - Digital Vision</title>
    <link href="https://fonts.googleapis.com/css2?family={plan.heading_font.replace(' ', '+')}:wght@400;600;700&family={plan.body_font.replace(' ', '+')}:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: {plan.primary_color};
            --secondary: {plan.secondary_color};
            --accent: {plan.accent_color};
            --dark: #0F172A;
            --light: #F8FAFC;
            --heading-font: '{plan.heading_font}', sans-serif;
            --body-font: '{plan.body_font}', sans-serif;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: var(--body-font);
            background: linear-gradient(135deg, var(--dark) 0%, #1E293B 100%);
            min-height: 100vh;
            color: white;
        }}

        /* Header */
        .header {{
            text-align: center;
            padding: 60px 20px 40px;
        }}

        .header h1 {{
            font-family: var(--heading-font);
            font-size: 48px;
            margin-bottom: 12px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .header .subtitle {{
            font-size: 20px;
            color: #94A3B8;
        }}

        .header .mood-badge {{
            display: inline-block;
            margin-top: 16px;
            padding: 8px 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            font-size: 14px;
            color: var(--accent);
        }}

        /* Design System Preview */
        .design-system {{
            display: flex;
            justify-content: center;
            gap: 40px;
            padding: 20px;
            flex-wrap: wrap;
        }}

        .color-preview {{
            display: flex;
            gap: 8px;
        }}

        .color-swatch {{
            width: 40px;
            height: 40px;
            border-radius: 8px;
            border: 2px solid rgba(255,255,255,0.2);
        }}

        .font-preview {{
            text-align: center;
        }}

        .font-preview .heading {{
            font-family: var(--heading-font);
            font-size: 20px;
            margin-bottom: 4px;
        }}

        .font-preview .body {{
            font-family: var(--body-font);
            font-size: 14px;
            color: #94A3B8;
        }}

        /* Navigation */
        .nav {{
            display: flex;
            justify-content: center;
            gap: 8px;
            padding: 20px;
            flex-wrap: wrap;
            background: rgba(0,0,0,0.3);
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .nav-tab {{
            background: rgba(255,255,255,0.1);
            border: none;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-family: var(--body-font);
            font-size: 14px;
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
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
        }}

        /* Phone Frame */
        .phone-frame {{
            background: #000;
            border-radius: 50px;
            padding: 12px;
            box-shadow: 0 25px 80px rgba(0,0,0,0.5);
            position: relative;
            width: 320px;
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
            border-radius: 40px;
            min-height: 650px;
            overflow: hidden;
            position: relative;
        }}

        /* Screen Info */
        .screen-info {{
            margin-top: 24px;
            text-align: center;
            max-width: 400px;
        }}

        .screen-info h3 {{
            font-family: var(--heading-font);
            font-size: 24px;
            margin-bottom: 8px;
        }}

        .screen-info p {{
            color: #94A3B8;
        }}

        /* Features Section */
        .features-section {{
            padding: 60px 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}

        .features-section h2 {{
            font-family: var(--heading-font);
            font-size: 32px;
            text-align: center;
            margin-bottom: 40px;
        }}

        .features-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}

        .feature-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px;
            position: relative;
        }}

        .feature-priority {{
            position: absolute;
            top: 16px;
            right: 16px;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 600;
            color: white;
        }}

        .feature-card h4 {{
            font-family: var(--heading-font);
            font-size: 18px;
            margin-bottom: 8px;
            margin-top: 8px;
        }}

        .feature-card p {{
            color: #94A3B8;
            font-size: 14px;
        }}

        /* Deliberation Log */
        .deliberation-section {{
            padding: 60px 20px;
            max-width: 800px;
            margin: 0 auto;
        }}

        .deliberation-section h2 {{
            font-family: var(--heading-font);
            font-size: 28px;
            text-align: center;
            margin-bottom: 32px;
        }}

        .thought {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 12px;
            border-left: 3px solid var(--primary);
        }}

        .agent-name {{
            font-size: 12px;
            color: var(--primary);
            font-weight: 600;
            display: block;
            margin-bottom: 4px;
        }}

        .thought p {{
            color: #CBD5E1;
            font-size: 14px;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 40px;
            color: #64748B;
            font-size: 12px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}

        /* Screen-specific styles */
        .app-header {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            padding: 60px 20px 30px;
            color: white;
        }}

        .app-header h1 {{
            font-family: var(--heading-font);
            font-size: 24px;
        }}

        .app-content {{
            padding: 20px;
        }}

        .app-card {{
            background: #F8FAFC;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}

        .app-card-title {{
            font-family: var(--heading-font);
            font-size: 16px;
            color: #1E293B;
            margin-bottom: 4px;
        }}

        .app-card-desc {{
            font-size: 13px;
            color: #64748B;
        }}

        .app-btn {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 14px 24px;
            border-radius: 12px;
            font-family: var(--body-font);
            font-size: 16px;
            font-weight: 600;
            width: 100%;
            margin-top: 20px;
            cursor: pointer;
        }}

        .app-nav {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            display: flex;
            justify-content: space-around;
            padding: 16px;
            background: white;
            border-top: 1px solid #E2E8F0;
        }}

        .app-nav-item {{
            text-align: center;
            color: #94A3B8;
            font-size: 11px;
        }}

        .app-nav-item.active {{
            color: var(--primary);
        }}

        .app-nav-icon {{
            width: 24px;
            height: 24px;
            background: currentColor;
            border-radius: 6px;
            margin: 0 auto 4px;
            opacity: 0.5;
        }}

        .app-nav-item.active .app-nav-icon {{
            opacity: 1;
        }}

        @media (max-width: 600px) {{
            .header h1 {{ font-size: 32px; }}
            .phone-frame {{ width: 280px; }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <h1>{plan.business_name}</h1>
        <p class="subtitle">Your Digital Future, Visualized</p>
        <span class="mood-badge">{plan.style_mood.title()} Design</span>
    </header>

    <div class="design-system">
        <div class="color-preview">
            <div class="color-swatch" style="background: {plan.primary_color}" title="Primary"></div>
            <div class="color-swatch" style="background: {plan.secondary_color}" title="Secondary"></div>
            <div class="color-swatch" style="background: {plan.accent_color}" title="Accent"></div>
        </div>
        <div class="font-preview">
            <div class="heading">{plan.heading_font}</div>
            <div class="body">{plan.body_font}</div>
        </div>
    </div>

    <nav class="nav">
        {nav_tabs}
    </nav>

    <main>
        {screens_html}
    </main>

    <section class="features-section">
        <h2>Core Features</h2>
        <div class="features-grid">
            {features_html}
        </div>
    </section>

    <section class="deliberation-section">
        <h2>How We Got Here</h2>
        <p style="text-align: center; color: #64748B; margin-bottom: 24px;">
            AI agents analyzed your business and made these decisions:
        </p>
        {deliberation_html}
    </section>

    <footer class="footer">
        <p>This prototype represents a vision for digitizing {plan.business_name}.</p>
        <p>Generated by Business Digitizer | {datetime.now().strftime('%Y-%m-%d')}</p>
    </footer>

    <script>
        function showScreen(screenId) {{
            document.querySelectorAll('.screen-panel').forEach(panel => {{
                panel.style.display = 'none';
            }});
            document.getElementById('screen-' + screenId).style.display = 'flex';

            document.querySelectorAll('.nav-tab').forEach(tab => {{
                tab.classList.remove('active');
                if (tab.dataset.screen === screenId) {{
                    tab.classList.add('active');
                }}
            }});
        }}

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

        print(f"\n[DONE] Prototype saved to: {output_path}")
        return str(output_path)

    def _generate_screen_content(self, screen: Dict, plan: BusinessPlan) -> str:
        """Generate content for a specific screen"""
        # Try to use rich templates first
        try:
            from screen_templates import ScreenTemplates
            return ScreenTemplates.get_screen_content(screen, plan)
        except ImportError:
            pass  # Fall back to basic templates below

        screen_id = screen['id']
        feature = screen.get('feature', '')

        # Generate appropriate content based on screen type
        if 'home' in screen_id:
            return f"""
            <div class="app-header">
                <h1>Welcome to<br>{plan.business_name}</h1>
            </div>
            <div class="app-content">
                <div class="app-card">
                    <div class="app-card-title">Quick Actions</div>
                    <div class="app-card-desc">Get started with one tap</div>
                </div>
                <div class="app-card">
                    <div class="app-card-title">{plan.core_features[0]['name'] if plan.core_features else 'Main Feature'}</div>
                    <div class="app-card-desc">{plan.core_features[0]['description'] if plan.core_features else 'Primary functionality'}</div>
                </div>
                <div class="app-card">
                    <div class="app-card-title">{plan.core_features[1]['name'] if len(plan.core_features) > 1 else 'Feature'}</div>
                    <div class="app-card-desc">{plan.core_features[1]['description'] if len(plan.core_features) > 1 else 'Additional functionality'}</div>
                </div>
                <button class="app-btn">Get Started</button>
            </div>
            <nav class="app-nav">
                <div class="app-nav-item active"><div class="app-nav-icon"></div>Home</div>
                <div class="app-nav-item"><div class="app-nav-icon"></div>Browse</div>
                <div class="app-nav-item"><div class="app-nav-icon"></div>Activity</div>
                <div class="app-nav-item"><div class="app-nav-icon"></div>Profile</div>
            </nav>
            """

        elif any(x in screen_id for x in ['menu', 'shop', 'browse', 'service', 'course', 'class', 'search']):
            return f"""
            <div style="padding: 60px 20px 20px;">
                <h2 style="font-family: var(--heading-font); font-size: 24px; color: #1E293B; margin-bottom: 16px;">{screen['name']}</h2>
                <input type="text" placeholder="Search..." style="width: 100%; padding: 14px; border: 1px solid #E2E8F0; border-radius: 12px; font-size: 16px; margin-bottom: 20px;">
            </div>
            <div class="app-content" style="padding-top: 0;">
                <div class="app-card">
                    <div class="app-card-title">Featured Item</div>
                    <div class="app-card-desc">Top rated • Most popular</div>
                </div>
                <div class="app-card">
                    <div class="app-card-title">Option 2</div>
                    <div class="app-card-desc">Great choice for beginners</div>
                </div>
                <div class="app-card">
                    <div class="app-card-title">Option 3</div>
                    <div class="app-card-desc">Premium selection</div>
                </div>
                <div class="app-card">
                    <div class="app-card-title">Option 4</div>
                    <div class="app-card-desc">New arrival</div>
                </div>
            </div>
            <nav class="app-nav">
                <div class="app-nav-item"><div class="app-nav-icon"></div>Home</div>
                <div class="app-nav-item active"><div class="app-nav-icon"></div>Browse</div>
                <div class="app-nav-item"><div class="app-nav-icon"></div>Activity</div>
                <div class="app-nav-item"><div class="app-nav-icon"></div>Profile</div>
            </nav>
            """

        elif any(x in screen_id for x in ['cart', 'book', 'checkout', 'order']):
            return f"""
            <div style="padding: 60px 20px 20px;">
                <h2 style="font-family: var(--heading-font); font-size: 24px; color: #1E293B; margin-bottom: 20px;">{screen['name']}</h2>
            </div>
            <div class="app-content" style="padding-top: 0;">
                <div class="app-card" style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div class="app-card-title">Selected Item</div>
                        <div class="app-card-desc">Qty: 1</div>
                    </div>
                    <div style="font-weight: 600; color: var(--primary);">$24.99</div>
                </div>
                <div style="padding: 20px 0; border-bottom: 1px solid #E2E8F0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #64748B;">Subtotal</span>
                        <span style="color: #1E293B;">$24.99</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #64748B;">Tax</span>
                        <span style="color: #1E293B;">$2.00</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-weight: 600;">
                        <span style="color: #1E293B;">Total</span>
                        <span style="color: var(--primary);">$26.99</span>
                    </div>
                </div>
                <button class="app-btn">Complete Order</button>
            </div>
            <nav class="app-nav">
                <div class="app-nav-item"><div class="app-nav-icon"></div>Home</div>
                <div class="app-nav-item"><div class="app-nav-icon"></div>Browse</div>
                <div class="app-nav-item active"><div class="app-nav-icon"></div>Activity</div>
                <div class="app-nav-item"><div class="app-nav-icon"></div>Profile</div>
            </nav>
            """

        elif any(x in screen_id for x in ['profile', 'account', 'settings']):
            return f"""
            <div style="padding: 60px 20px 20px; text-align: center;">
                <div style="width: 80px; height: 80px; background: linear-gradient(135deg, var(--primary), var(--secondary)); border-radius: 50%; margin: 0 auto 16px;"></div>
                <h2 style="font-family: var(--heading-font); font-size: 22px; color: #1E293B;">John Doe</h2>
                <p style="color: #64748B; font-size: 14px;">Member since 2024</p>
            </div>
            <div class="app-content">
                <div class="app-card">
                    <div class="app-card-title">My Orders</div>
                    <div class="app-card-desc">View order history</div>
                </div>
                <div class="app-card">
                    <div class="app-card-title">Payment Methods</div>
                    <div class="app-card-desc">Manage cards and accounts</div>
                </div>
                <div class="app-card">
                    <div class="app-card-title">Notifications</div>
                    <div class="app-card-desc">Customize alerts</div>
                </div>
                <div class="app-card">
                    <div class="app-card-title">Help & Support</div>
                    <div class="app-card-desc">FAQ and contact us</div>
                </div>
            </div>
            <nav class="app-nav">
                <div class="app-nav-item"><div class="app-nav-icon"></div>Home</div>
                <div class="app-nav-item"><div class="app-nav-icon"></div>Browse</div>
                <div class="app-nav-item"><div class="app-nav-icon"></div>Activity</div>
                <div class="app-nav-item active"><div class="app-nav-icon"></div>Profile</div>
            </nav>
            """

        else:
            # Generic screen
            return f"""
            <div style="padding: 60px 20px 20px;">
                <h2 style="font-family: var(--heading-font); font-size: 24px; color: #1E293B; margin-bottom: 20px;">{screen['name']}</h2>
            </div>
            <div class="app-content">
                <div class="app-card">
                    <div class="app-card-title">{feature or 'Main Content'}</div>
                    <div class="app-card-desc">{screen['description']}</div>
                </div>
                <div class="app-card">
                    <div class="app-card-title">Additional Info</div>
                    <div class="app-card-desc">More details here</div>
                </div>
                <button class="app-btn">Take Action</button>
            </div>
            <nav class="app-nav">
                <div class="app-nav-item"><div class="app-nav-icon"></div>Home</div>
                <div class="app-nav-item"><div class="app-nav-icon"></div>Browse</div>
                <div class="app-nav-item"><div class="app-nav-icon"></div>Activity</div>
                <div class="app-nav-item"><div class="app-nav-icon"></div>Profile</div>
            </nav>
            """


def interactive_session():
    """Run an interactive session with the user"""
    print("\n" + "="*60)
    print("  BUSINESS DIGITIZATION VISUALIZER")
    print("  Transform any business idea into a visual prototype")
    print("="*60)

    print("\nDescribe the business you want to digitize:")
    print("(e.g., 'A local coffee shop in Brooklyn called Bean There')")
    print()

    business_desc = input("Business: ").strip()

    if not business_desc:
        print("No business description provided. Exiting.")
        return

    print("\nOptional: Give the business a name (or press Enter to auto-generate):")
    business_name = input("Name: ").strip() or None

    digitizer = BusinessDigitizer()
    plan = digitizer.run_deliberation(business_desc, business_name)

    print("\n" + "-"*40)
    print("PLAN SUMMARY")
    print("-"*40)
    print(f"Business: {plan.business_name}")
    print(f"Industry: {plan.industry.title()}")
    print(f"Style: {plan.style_mood.title()}")
    print(f"Colors: {plan.primary_color}, {plan.secondary_color}, {plan.accent_color}")
    print(f"Fonts: {plan.heading_font} / {plan.body_font}")
    print(f"Screens: {', '.join([s['name'] for s in plan.screens])}")
    print(f"Features: {', '.join([f['name'] for f in plan.core_features[:4]])}")

    print("\nGenerate prototype? (Y/n): ", end="")
    if input().strip().lower() != 'n':
        output_path = digitizer.generate_prototype(plan)
        print(f"\nSUCCESS! Open {output_path} in your browser to see the prototype!")


def main():
    parser = argparse.ArgumentParser(
        description='Transform business ideas into visual app prototypes'
    )
    parser.add_argument('--business', type=str, help='Business description')
    parser.add_argument('--name', type=str, help='Business name')
    parser.add_argument('--config', type=str, help='Path to business config JSON')
    parser.add_argument('--output', type=str, help='Output HTML path')
    parser.add_argument('--interactive', action='store_true', help='Run interactive session')

    args = parser.parse_args()

    if args.interactive or (not args.business and not args.config):
        interactive_session()
        return

    digitizer = BusinessDigitizer()

    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
        business_desc = config.get('description', '')
        business_name = config.get('name')
    else:
        business_desc = args.business
        business_name = args.name

    plan = digitizer.run_deliberation(business_desc, business_name)
    output_path = args.output or None
    prototype_path = digitizer.generate_prototype(plan, output_path)

    # Read prototype HTML for embedding
    prototype_html = None
    try:
        with open(prototype_path, 'r', encoding='utf-8') as f:
            prototype_html = f.read()
    except:
        pass

    # Generate PREMIUM report with embedded prototype
    try:
        from premium_report import PremiumReport
        report = PremiumReport()
        report_path = prototype_path.replace('_prototype.html', '_premium_report.html')
        report.generate_build_report(plan, prototype_html=prototype_html, output_path=report_path)
        print(f"\nDeliverables ready:")
        print(f"  1. Prototype: {prototype_path}")
        print(f"  2. Premium Report: {report_path}")
    except ImportError as e:
        print(f"\n[Note] Premium report not generated: {e}")
        # Fallback to basic report
        try:
            from report_generator import BusinessReport
            report = BusinessReport()
            report_path = prototype_path.replace('_prototype.html', '_report.html')
            report.generate_report(plan, report_path)
            print(f"  2. Basic Report: {report_path}")
        except ImportError:
            print("  Only prototype generated.")


if __name__ == "__main__":
    main()
