"""
Domain Analyst Prompt

Extracts business-specific information from user descriptions to create
domain-aware prototypes that feel tailored to the client's industry.

This agent transforms generic descriptions into rich domain context:
- "pet grooming salon" -> appointments, pet names, services, pricing
- "yoga studio" -> classes, members, instructors, schedules
- "restaurant" -> menu items, tables, orders, reservations
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class CompetitorInfo(BaseModel):
    """Information about a competitor in this industry"""
    name: str = Field(description="Competitor name")
    description: str = Field(description="Brief description of what they offer")
    strength: str = Field(description="Their main competitive strength")


class IndustryMetrics(BaseModel):
    """Key metrics for this industry"""
    market_size: str = Field(description="Estimated market size (e.g., '$899 billion US food service')")
    digital_adoption: str = Field(description="Digital/mobile adoption rate in this industry")
    success_metric: str = Field(description="Key success metric (e.g., '23% increase in order value with mobile apps')")
    key_trend: str = Field(description="Most important industry trend")


class DomainAnalysis(BaseModel):
    """Complete domain analysis for a business"""

    # Core classification
    industry: str = Field(description="Industry category (pet-services, fitness, restaurant, saas, healthcare, etc.)")
    industry_display_name: str = Field(description="Human-readable industry name for reports")

    # Key entities in this domain
    key_entities: List[str] = Field(
        description="Main objects/entities in this domain (e.g., ['pets', 'appointments', 'services'] for grooming)"
    )

    # Metrics that matter
    metrics: List[str] = Field(
        description="What numbers matter to this business (e.g., ['bookings', 'revenue', 'customer satisfaction'])"
    )

    # Terminology mapping (generic -> domain-specific)
    terminology: Dict[str, str] = Field(
        description="Map generic terms to domain terms (e.g., {'user': 'pet parent', 'order': 'appointment'})"
    )

    # Sample data for realistic prototypes
    sample_names: List[str] = Field(
        description="Realistic names for this domain (customer names, pet names, member names, etc.)"
    )
    sample_items: List[str] = Field(
        description="Sample items/services/products (e.g., ['Bath & Brush', 'Full Groom', 'Nail Trim'])"
    )
    sample_prices: Dict[str, str] = Field(
        description="Realistic price ranges for items/services"
    )

    # Dashboard sections
    suggested_sections: List[str] = Field(
        description="Dashboard sections that make sense (e.g., ['Appointment Queue', 'Pet Profiles', 'Service Metrics'])"
    )

    # Visual elements
    icons: List[str] = Field(
        description="Relevant emoji/icons for visual interest (e.g., ['paw', 'calendar', 'scissors'])"
    )
    emoji: List[str] = Field(
        description="Emoji that represent this business (e.g., ['paw-print', 'dog', 'soap'])"
    )

    # Industry insights for reports
    industry_metrics: Optional[IndustryMetrics] = Field(
        default=None,
        description="Key industry metrics for business reports"
    )
    competitors: List[CompetitorInfo] = Field(
        default_factory=list,
        description="Main competitors in this space"
    )

    # Design direction
    mood_words: List[str] = Field(
        description="Words that describe the desired feel (e.g., ['friendly', 'professional', 'cozy'])"
    )
    suggested_colors: Dict[str, str] = Field(
        description="Suggested brand colors based on industry (e.g., {'primary': '#00B894', 'secondary': '#55EFC4'})"
    )


DOMAIN_ANALYST_PROMPT = """
You are a Domain Analyst specializing in understanding business contexts.

Analyze this business description and extract domain-specific information that will
make the prototype feel tailored to THIS specific business, not generic.

## Business Description
{description}

## Your Task
Extract detailed domain information to create a prototype that makes the client say
"Wow, they really understand my business!"

## Rules
1. Be SPECIFIC to this industry - not generic placeholders
2. Use realistic sample data (real-sounding names, realistic prices)
3. Choose terminology that matches how people in this industry actually talk
4. Suggest dashboard sections that would be genuinely useful
5. Include industry metrics and competitors for business reports
6. Select colors and mood that fit the industry (warm for restaurants, fresh for fitness, etc.)

## Output Format
Return a JSON object with these fields:

{
  "industry": "pet-services",
  "industry_display_name": "Pet Grooming & Care",
  "key_entities": ["pets", "appointments", "services", "customers"],
  "metrics": ["appointments_today", "weekly_revenue", "customer_satisfaction", "repeat_bookings"],
  "terminology": {
    "user": "pet parent",
    "customer": "client",
    "order": "appointment",
    "product": "service",
    "item": "treatment",
    "booking": "reservation"
  },
  "sample_names": ["Bella", "Max", "Luna", "Charlie", "Cooper", "Daisy"],
  "sample_items": ["Bath & Brush", "Full Groom", "Nail Trim", "De-shedding", "Puppy Package"],
  "sample_prices": {
    "Bath & Brush": "$35-$55",
    "Full Groom": "$65-$95",
    "Nail Trim": "$15-$25"
  },
  "suggested_sections": [
    "Today's Appointments",
    "Grooming Queue",
    "Pet Profiles",
    "Service Revenue",
    "Recent Reviews"
  ],
  "icons": ["paw-print", "scissors", "calendar", "heart", "star"],
  "emoji": ["paw", "dog", "soap", "sparkles", "heart"],
  "industry_metrics": {
    "market_size": "$10.5 billion US pet grooming industry",
    "digital_adoption": "45% of pet owners prefer online booking",
    "success_metric": "Businesses with apps see 35% higher rebooking rates",
    "key_trend": "Mobile-first booking increased 200% since 2020"
  },
  "competitors": [
    {
      "name": "PetSmart",
      "description": "Large retail chain with grooming services",
      "strength": "Brand recognition and convenience"
    },
    {
      "name": "Rover",
      "description": "Marketplace for pet services",
      "strength": "Large network of providers"
    }
  ],
  "mood_words": ["friendly", "caring", "professional", "warm"],
  "suggested_colors": {
    "primary": "#00B894",
    "secondary": "#55EFC4",
    "accent": "#81ECEC"
  }
}

## Industry-Specific Examples

### Restaurant/Cafe
- Entities: menu items, orders, tables, reservations, staff
- Metrics: covers, average ticket, table turnover, wait time
- Terminology: guest (not customer), check (not bill), comp (not free)
- Sections: Table Status, Order Queue, Kitchen Display, Daily Sales

### Fitness/Yoga Studio
- Entities: classes, members, instructors, schedules, memberships
- Metrics: class attendance, member retention, instructor utilization
- Terminology: member (not user), session (not appointment), studio (not location)
- Sections: Today's Classes, Member Check-ins, Instructor Schedule, Membership Stats

### Healthcare/Medical
- Entities: patients, appointments, providers, treatments, records
- Metrics: patient visits, wait time, satisfaction scores, no-show rate
- Terminology: patient (not customer), visit (not appointment), provider (not staff)
- Sections: Patient Queue, Provider Schedule, Visit Summary, Lab Results

### SaaS/Tech
- Entities: users, subscriptions, features, support tickets, integrations
- Metrics: MRR, churn rate, active users, support response time
- Terminology: user (not customer), workspace (not account), seat (not license)
- Sections: User Growth, Revenue Metrics, Feature Usage, Support Tickets

Remember: The goal is to make the prototype feel like it was built specifically for THIS business,
not a generic template with placeholder data.
"""


def get_domain_analyst_prompt(description: str) -> str:
    """Get the formatted domain analyst prompt"""
    return DOMAIN_ANALYST_PROMPT.format(description=description)


# Industry presets for quick lookups
INDUSTRY_PRESETS: Dict[str, Dict[str, Any]] = {
    "restaurant": {
        "industry": "restaurant",
        "industry_display_name": "Restaurant & Food Service",
        "key_entities": ["menu_items", "orders", "tables", "reservations", "staff"],
        "metrics": ["covers", "average_ticket", "table_turnover", "wait_time"],
        "terminology": {
            "user": "guest",
            "customer": "guest",
            "order": "check",
            "product": "dish",
            "booking": "reservation"
        },
        "icons": ["utensils", "plate", "clock", "users", "star"],
        "emoji": ["fork-knife", "plate", "chef", "sparkles", "fire"],
        "mood_words": ["warm", "inviting", "cozy", "appetizing"],
        "suggested_colors": {
            "primary": "#E74C3C",
            "secondary": "#F39C12",
            "accent": "#27AE60"
        }
    },
    "fitness": {
        "industry": "fitness",
        "industry_display_name": "Fitness & Wellness",
        "key_entities": ["classes", "members", "instructors", "schedules", "memberships"],
        "metrics": ["class_attendance", "member_retention", "instructor_hours", "new_signups"],
        "terminology": {
            "user": "member",
            "customer": "member",
            "order": "booking",
            "product": "class",
            "booking": "reservation"
        },
        "icons": ["dumbbell", "heart", "calendar", "users", "trophy"],
        "emoji": ["muscle", "fire", "sparkles", "medal", "heart"],
        "mood_words": ["energetic", "motivating", "fresh", "dynamic"],
        "suggested_colors": {
            "primary": "#9B59B6",
            "secondary": "#3498DB",
            "accent": "#1ABC9C"
        }
    },
    "pet-services": {
        "industry": "pet-services",
        "industry_display_name": "Pet Care & Grooming",
        "key_entities": ["pets", "appointments", "services", "customers"],
        "metrics": ["appointments_today", "weekly_revenue", "satisfaction", "repeat_rate"],
        "terminology": {
            "user": "pet parent",
            "customer": "client",
            "order": "appointment",
            "product": "service"
        },
        "icons": ["paw-print", "scissors", "heart", "calendar", "star"],
        "emoji": ["paw", "dog", "cat", "sparkles", "heart"],
        "mood_words": ["friendly", "caring", "playful", "professional"],
        "suggested_colors": {
            "primary": "#00B894",
            "secondary": "#55EFC4",
            "accent": "#81ECEC"
        }
    },
    "healthcare": {
        "industry": "healthcare",
        "industry_display_name": "Healthcare & Medical",
        "key_entities": ["patients", "appointments", "providers", "treatments"],
        "metrics": ["patient_visits", "wait_time", "satisfaction", "no_show_rate"],
        "terminology": {
            "user": "patient",
            "customer": "patient",
            "order": "visit",
            "product": "treatment",
            "staff": "provider"
        },
        "icons": ["heart-pulse", "clipboard", "calendar", "users", "activity"],
        "emoji": ["hospital", "heart", "clipboard", "doctor", "pill"],
        "mood_words": ["trustworthy", "professional", "calming", "clean"],
        "suggested_colors": {
            "primary": "#3498DB",
            "secondary": "#2ECC71",
            "accent": "#9B59B6"
        }
    },
    "saas": {
        "industry": "saas",
        "industry_display_name": "Software & Technology",
        "key_entities": ["users", "subscriptions", "features", "support_tickets"],
        "metrics": ["mrr", "churn_rate", "active_users", "nps"],
        "terminology": {
            "user": "user",
            "customer": "customer",
            "order": "subscription",
            "product": "plan"
        },
        "icons": ["code", "users", "trending-up", "settings", "zap"],
        "emoji": ["rocket", "chart", "sparkles", "lightning", "computer"],
        "mood_words": ["modern", "sleek", "innovative", "professional"],
        "suggested_colors": {
            "primary": "#6366F1",
            "secondary": "#8B5CF6",
            "accent": "#EC4899"
        }
    },
    "news-media": {
        "industry": "news-media",
        "industry_display_name": "News & Media Platform",
        "key_entities": ["articles", "sources", "topics", "regions", "readers"],
        "metrics": ["articles_today", "reader_engagement", "source_coverage", "fact_accuracy"],
        "terminology": {
            "user": "reader",
            "customer": "subscriber",
            "item": "article",
            "product": "story",
            "order": "subscription"
        },
        "sample_names": ["Breaking: ", "Analysis: ", "Update: ", "Report: "],
        "sample_items": ["World News", "Politics", "Technology", "Business", "Science"],
        "sample_prices": {"free": "Free", "premium": "$9.99/mo"},
        "suggested_sections": [
            "Top Stories",
            "Regional News",
            "Fact Check",
            "Analysis",
            "Trending Topics"
        ],
        "icons": ["newspaper", "globe", "check-circle", "trending-up", "bookmark"],
        "emoji": ["newspaper", "globe", "magnifying-glass", "check", "bookmark"],
        "mood_words": ["trustworthy", "factual", "neutral", "informative"],
        "suggested_colors": {
            "primary": "#1E40AF",
            "secondary": "#059669",
            "accent": "#DC2626"
        }
    },
    "ecommerce": {
        "industry": "ecommerce",
        "industry_display_name": "E-Commerce & Retail",
        "key_entities": ["products", "orders", "customers", "inventory", "reviews"],
        "metrics": ["daily_orders", "revenue", "conversion_rate", "avg_order_value"],
        "terminology": {
            "user": "customer",
            "item": "product",
            "booking": "order"
        },
        "icons": ["shopping-cart", "package", "credit-card", "truck", "star"],
        "emoji": ["shopping-cart", "package", "sparkles", "truck", "star"],
        "mood_words": ["modern", "trustworthy", "convenient", "premium"],
        "suggested_colors": {
            "primary": "#7C3AED",
            "secondary": "#10B981",
            "accent": "#F59E0B"
        }
    },
    "education": {
        "industry": "education",
        "industry_display_name": "Education & Learning",
        "key_entities": ["courses", "students", "instructors", "lessons", "assessments"],
        "metrics": ["enrolled_students", "completion_rate", "avg_score", "active_courses"],
        "terminology": {
            "user": "student",
            "customer": "learner",
            "item": "course",
            "product": "lesson"
        },
        "icons": ["graduation-cap", "book-open", "users", "award", "calendar"],
        "emoji": ["graduation-cap", "book", "brain", "star", "trophy"],
        "mood_words": ["inspiring", "accessible", "engaging", "professional"],
        "suggested_colors": {
            "primary": "#2563EB",
            "secondary": "#7C3AED",
            "accent": "#F59E0B"
        }
    },
    "real-estate": {
        "industry": "real-estate",
        "industry_display_name": "Real Estate & Property",
        "key_entities": ["properties", "listings", "agents", "clients", "viewings"],
        "metrics": ["active_listings", "monthly_sales", "avg_days_on_market", "leads"],
        "terminology": {
            "user": "client",
            "customer": "buyer",
            "item": "property",
            "product": "listing"
        },
        "icons": ["home", "map-pin", "key", "users", "trending-up"],
        "emoji": ["house", "key", "map", "handshake", "sparkles"],
        "mood_words": ["trustworthy", "professional", "premium", "welcoming"],
        "suggested_colors": {
            "primary": "#0F766E",
            "secondary": "#CA8A04",
            "accent": "#1E40AF"
        }
    },
    "universal": {
        "industry": "general",
        "industry_display_name": "Custom Application",
        "key_entities": ["items", "users", "categories", "actions", "reports"],
        "metrics": ["total_items", "active_users", "growth_rate", "engagement"],
        "terminology": {
            "user": "user",
            "customer": "user",
            "item": "item",
            "product": "item",
            "order": "action"
        },
        "sample_names": ["Alex", "Jordan", "Sam", "Taylor", "Morgan", "Casey"],
        "sample_items": ["Item A", "Item B", "Item C", "Item D"],
        "sample_prices": {"basic": "$29", "pro": "$99", "enterprise": "Custom"},
        "suggested_sections": [
            "Dashboard",
            "Items",
            "Users",
            "Analytics",
            "Settings"
        ],
        "icons": ["layout-dashboard", "list", "users", "bar-chart-3", "settings"],
        "emoji": ["rocket", "sparkles", "chart", "gear", "star"],
        "mood_words": ["modern", "clean", "professional", "efficient"],
        "suggested_colors": {
            "primary": "#3B82F6",
            "secondary": "#10B981",
            "accent": "#F59E0B"
        }
    }
}


def get_industry_preset(industry_keyword: str) -> Dict[str, Any]:
    """
    Get preset domain data for common industries.
    Always returns a preset - uses 'universal' for unmatched industries.
    """
    keyword = industry_keyword.lower()

    # Match keywords to presets (order matters - more specific first)
    if any(word in keyword for word in ["news", "media", "journalism", "article", "fact"]):
        return INDUSTRY_PRESETS["news-media"]
    elif any(word in keyword for word in ["restaurant", "cafe", "food", "dining", "bistro", "bar"]):
        return INDUSTRY_PRESETS["restaurant"]
    elif any(word in keyword for word in ["fitness", "gym", "yoga", "workout", "pilates"]):
        return INDUSTRY_PRESETS["fitness"]
    elif any(word in keyword for word in ["pet", "grooming", "dog", "cat", "veterinary", "animal"]):
        return INDUSTRY_PRESETS["pet-services"]
    elif any(word in keyword for word in ["health", "medical", "clinic", "doctor", "dental", "therapy"]):
        return INDUSTRY_PRESETS["healthcare"]
    elif any(word in keyword for word in ["ecommerce", "e-commerce", "shop", "store", "retail", "product"]):
        return INDUSTRY_PRESETS["ecommerce"]
    elif any(word in keyword for word in ["education", "learning", "course", "school", "training", "tutorial"]):
        return INDUSTRY_PRESETS["education"]
    elif any(word in keyword for word in ["real estate", "property", "housing", "rental", "listing"]):
        return INDUSTRY_PRESETS["real-estate"]
    elif any(word in keyword for word in ["saas", "software", "app", "tech", "platform", "startup", "dashboard"]):
        return INDUSTRY_PRESETS["saas"]

    # Always return universal preset for any unmatched project
    return INDUSTRY_PRESETS["universal"]
