"""
Architect Prompt

Plans the structure and layout of domain-specific prototypes.
Takes domain analysis and creates page structures, component selections,
and navigation that makes sense for this specific business.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class PageSection(BaseModel):
    """A section within a page"""
    id: str = Field(description="Unique section identifier")
    title: str = Field(description="Section title using domain terminology")
    component_type: str = Field(
        description="Component type: 'stats', 'table', 'chart', 'cards', 'list', 'form', 'calendar', 'queue'"
    )
    data_source: str = Field(description="Key in mock.json that provides data for this section")
    description: str = Field(description="Brief description of what this section shows")
    colspan: int = Field(default=1, description="How many columns this section spans (1-3)")


class PageConfig(BaseModel):
    """Configuration for a single page"""
    path: str = Field(description="URL path (e.g., '/', '/appointments', '/reports')")
    title: str = Field(description="Page title using domain terminology")
    icon: str = Field(description="Icon name for navigation (lucide-react icon)")
    sections: List[PageSection] = Field(description="Sections on this page")
    is_default: bool = Field(default=False, description="Whether this is the main/home page")


class StatCardConfig(BaseModel):
    """Configuration for a stat card"""
    title: str = Field(description="Stat title using domain terminology")
    data_key: str = Field(description="Key in mock.json for this stat's value")
    icon: str = Field(description="Icon name (lucide-react)")
    change_type: str = Field(default="increase", description="'increase' or 'decrease'")
    color: str = Field(description="Color theme: 'blue', 'green', 'purple', 'amber'")


class PrototypeArchitecture(BaseModel):
    """Complete architecture for a prototype"""

    # Template selection
    template_id: str = Field(description="Base template to use: 'dashboard' or 'landing-page'")
    template_variant: str = Field(default="default", description="Template variant if any")

    # Branding
    app_name: str = Field(description="Name of the app/business")
    tagline: str = Field(description="Short tagline for the business")

    # Navigation
    pages: List[PageConfig] = Field(description="All pages in the app")
    sidebar_items: List[str] = Field(description="Navigation labels for sidebar")

    # Dashboard-specific
    stat_cards: List[StatCardConfig] = Field(
        default_factory=list,
        description="Stat cards for dashboard header"
    )
    primary_action: str = Field(
        default="New Item",
        description="Primary action button text (e.g., 'New Appointment', 'Add Member')"
    )
    primary_action_icon: str = Field(default="plus", description="Icon for primary action")

    # Components to generate
    key_components: List[str] = Field(
        description="List of key component names to generate (e.g., ['AppointmentQueue', 'PetCard'])"
    )

    # Data requirements
    required_mock_data: List[str] = Field(
        description="Keys needed in mock.json (e.g., ['appointments', 'pets', 'services'])"
    )


ARCHITECT_PROMPT = """
You are a Prototype Architect specializing in creating app structures tailored to specific businesses.

## Domain Analysis
{domain_analysis}

## User Request
{description}

## Your Task
Design the architecture for a prototype that feels custom-built for this business.
The architecture should:
1. Use domain-specific terminology throughout
2. Have pages and sections that make sense for THIS business
3. Show the most important metrics prominently
4. Include components that would genuinely help run this business

## Template Options
- "dashboard": Admin/management interface with sidebar, stats, tables, charts
- "landing-page": Marketing/public-facing page with hero, features, testimonials

## Component Types Available
- stats: Stat cards showing key metrics (number + change %)
- table: Data table with sorting and filtering
- chart: Bar/line chart for trends
- cards: Grid of cards (customers, products, etc.)
- list: Activity feed or simple list
- form: Input form
- calendar: Schedule/calendar view
- queue: Queue of items (appointments, orders, etc.)

## Output Format
Return a JSON object:

{
  "template_id": "dashboard",
  "template_variant": "default",
  "app_name": "Bella's Grooming",
  "tagline": "Professional pet care, happy pets",
  "pages": [
    {
      "path": "/",
      "title": "Today's Schedule",
      "icon": "calendar",
      "is_default": true,
      "sections": [
        {
          "id": "queue",
          "title": "Grooming Queue",
          "component_type": "queue",
          "data_source": "appointments",
          "description": "Pets waiting for grooming today",
          "colspan": 2
        },
        {
          "id": "activity",
          "title": "Recent Activity",
          "component_type": "list",
          "data_source": "recent_activity",
          "description": "Latest updates and completions",
          "colspan": 1
        }
      ]
    },
    {
      "path": "/pets",
      "title": "Pet Profiles",
      "icon": "paw-print",
      "sections": [
        {
          "id": "pets-grid",
          "title": "All Pets",
          "component_type": "cards",
          "data_source": "pets",
          "description": "Pet profiles with notes and history",
          "colspan": 3
        }
      ]
    },
    {
      "path": "/services",
      "title": "Services & Pricing",
      "icon": "scissors",
      "sections": [
        {
          "id": "services-table",
          "title": "Service Menu",
          "component_type": "table",
          "data_source": "services",
          "description": "All services with pricing",
          "colspan": 2
        },
        {
          "id": "popular",
          "title": "Most Popular",
          "component_type": "chart",
          "data_source": "popular_services",
          "description": "Top services by bookings",
          "colspan": 1
        }
      ]
    },
    {
      "path": "/reports",
      "title": "Business Insights",
      "icon": "bar-chart-3",
      "sections": [
        {
          "id": "revenue",
          "title": "Revenue Trends",
          "component_type": "chart",
          "data_source": "revenue_data",
          "description": "Weekly and monthly revenue",
          "colspan": 2
        },
        {
          "id": "reviews",
          "title": "Recent Reviews",
          "component_type": "list",
          "data_source": "reviews",
          "description": "Customer feedback",
          "colspan": 1
        }
      ]
    }
  ],
  "sidebar_items": ["Today's Schedule", "Pet Profiles", "Services", "Reports"],
  "stat_cards": [
    {
      "title": "Appointments Today",
      "data_key": "appointments_today",
      "icon": "calendar",
      "change_type": "increase",
      "color": "blue"
    },
    {
      "title": "Happy Pups This Week",
      "data_key": "completed_this_week",
      "icon": "heart",
      "change_type": "increase",
      "color": "green"
    },
    {
      "title": "Weekly Revenue",
      "data_key": "weekly_revenue",
      "icon": "dollar-sign",
      "change_type": "increase",
      "color": "purple"
    },
    {
      "title": "Avg Wait Time",
      "data_key": "avg_wait_time",
      "icon": "clock",
      "change_type": "decrease",
      "color": "amber"
    }
  ],
  "primary_action": "New Appointment",
  "primary_action_icon": "plus",
  "key_components": ["AppointmentQueue", "PetCard", "ServiceCard", "ReviewCard"],
  "required_mock_data": ["appointments", "pets", "services", "reviews", "revenue_data", "recent_activity"]
}

## Guidelines
1. Use domain terminology from the analysis (e.g., "pet parent" not "customer")
2. Put the most important/frequent actions on the default page
3. Stat cards should show metrics that matter to THIS business
4. Pages should follow a logical workflow
5. Include realistic data requirements - what data would this dashboard need?

Remember: The architecture should feel like it was designed BY someone who runs this type of business,
FOR someone who runs this type of business.
"""


def get_architect_prompt(description: str, domain_analysis: dict) -> str:
    """Get the formatted architect prompt"""
    import json
    return ARCHITECT_PROMPT.format(
        description=description,
        domain_analysis=json.dumps(domain_analysis, indent=2)
    )


# Pre-built architectures for common use cases
ARCHITECTURE_PRESETS: Dict[str, Dict[str, Any]] = {
    "pet-grooming-dashboard": {
        "template_id": "dashboard",
        "pages": [
            {
                "path": "/",
                "title": "Today's Schedule",
                "icon": "calendar",
                "is_default": True,
                "sections": [
                    {"id": "queue", "title": "Grooming Queue", "component_type": "queue", "data_source": "appointments", "colspan": 2},
                    {"id": "activity", "title": "Recent Activity", "component_type": "list", "data_source": "recent_activity", "colspan": 1}
                ]
            },
            {
                "path": "/pets",
                "title": "Pet Profiles",
                "icon": "paw-print",
                "sections": [
                    {"id": "pets", "title": "All Pets", "component_type": "cards", "data_source": "pets", "colspan": 3}
                ]
            },
            {
                "path": "/services",
                "title": "Services",
                "icon": "scissors",
                "sections": [
                    {"id": "services", "title": "Service Menu", "component_type": "table", "data_source": "services", "colspan": 2},
                    {"id": "popular", "title": "Popular Services", "component_type": "chart", "data_source": "popular_services", "colspan": 1}
                ]
            },
            {
                "path": "/reports",
                "title": "Reports",
                "icon": "bar-chart-3",
                "sections": [
                    {"id": "revenue", "title": "Revenue", "component_type": "chart", "data_source": "revenue_data", "colspan": 2},
                    {"id": "reviews", "title": "Reviews", "component_type": "list", "data_source": "reviews", "colspan": 1}
                ]
            }
        ],
        "stat_cards": [
            {"title": "Appointments Today", "data_key": "appointments_today", "icon": "calendar", "color": "blue"},
            {"title": "Happy Pups", "data_key": "completed_this_week", "icon": "heart", "color": "green"},
            {"title": "Weekly Revenue", "data_key": "weekly_revenue", "icon": "dollar-sign", "color": "purple"},
            {"title": "Avg Wait Time", "data_key": "avg_wait_time", "icon": "clock", "color": "amber"}
        ],
        "primary_action": "New Appointment",
        "key_components": ["AppointmentQueue", "PetCard", "ServiceCard"]
    },
    "restaurant-dashboard": {
        "template_id": "dashboard",
        "pages": [
            {
                "path": "/",
                "title": "Floor View",
                "icon": "layout-grid",
                "is_default": True,
                "sections": [
                    {"id": "tables", "title": "Table Status", "component_type": "cards", "data_source": "tables", "colspan": 2},
                    {"id": "orders", "title": "Order Queue", "component_type": "queue", "data_source": "orders", "colspan": 1}
                ]
            },
            {
                "path": "/menu",
                "title": "Menu",
                "icon": "utensils",
                "sections": [
                    {"id": "menu", "title": "Menu Items", "component_type": "table", "data_source": "menu_items", "colspan": 2},
                    {"id": "specials", "title": "Today's Specials", "component_type": "cards", "data_source": "specials", "colspan": 1}
                ]
            },
            {
                "path": "/reservations",
                "title": "Reservations",
                "icon": "calendar",
                "sections": [
                    {"id": "reservations", "title": "Upcoming", "component_type": "table", "data_source": "reservations", "colspan": 3}
                ]
            },
            {
                "path": "/reports",
                "title": "Reports",
                "icon": "bar-chart-3",
                "sections": [
                    {"id": "sales", "title": "Sales Trends", "component_type": "chart", "data_source": "sales_data", "colspan": 2},
                    {"id": "feedback", "title": "Guest Feedback", "component_type": "list", "data_source": "feedback", "colspan": 1}
                ]
            }
        ],
        "stat_cards": [
            {"title": "Tables Available", "data_key": "tables_available", "icon": "layout-grid", "color": "blue"},
            {"title": "Covers Today", "data_key": "covers_today", "icon": "users", "color": "green"},
            {"title": "Avg Ticket", "data_key": "avg_ticket", "icon": "dollar-sign", "color": "purple"},
            {"title": "Wait Time", "data_key": "wait_time", "icon": "clock", "color": "amber"}
        ],
        "primary_action": "New Reservation",
        "key_components": ["TableCard", "OrderQueue", "MenuItem"]
    },
    "fitness-dashboard": {
        "template_id": "dashboard",
        "pages": [
            {
                "path": "/",
                "title": "Today's Classes",
                "icon": "calendar",
                "is_default": True,
                "sections": [
                    {"id": "schedule", "title": "Class Schedule", "component_type": "calendar", "data_source": "classes", "colspan": 2},
                    {"id": "checkins", "title": "Recent Check-ins", "component_type": "list", "data_source": "checkins", "colspan": 1}
                ]
            },
            {
                "path": "/members",
                "title": "Members",
                "icon": "users",
                "sections": [
                    {"id": "members", "title": "All Members", "component_type": "table", "data_source": "members", "colspan": 3}
                ]
            },
            {
                "path": "/instructors",
                "title": "Instructors",
                "icon": "user-check",
                "sections": [
                    {"id": "instructors", "title": "Instructor Schedule", "component_type": "cards", "data_source": "instructors", "colspan": 2},
                    {"id": "availability", "title": "Availability", "component_type": "calendar", "data_source": "availability", "colspan": 1}
                ]
            },
            {
                "path": "/reports",
                "title": "Reports",
                "icon": "bar-chart-3",
                "sections": [
                    {"id": "attendance", "title": "Class Attendance", "component_type": "chart", "data_source": "attendance_data", "colspan": 2},
                    {"id": "retention", "title": "Member Retention", "component_type": "stats", "data_source": "retention_data", "colspan": 1}
                ]
            }
        ],
        "stat_cards": [
            {"title": "Classes Today", "data_key": "classes_today", "icon": "calendar", "color": "blue"},
            {"title": "Active Members", "data_key": "active_members", "icon": "users", "color": "green"},
            {"title": "Monthly Revenue", "data_key": "monthly_revenue", "icon": "dollar-sign", "color": "purple"},
            {"title": "Avg Attendance", "data_key": "avg_attendance", "icon": "trending-up", "color": "amber"}
        ],
        "primary_action": "New Booking",
        "key_components": ["ClassCard", "MemberCard", "InstructorCard"]
    },
    "news-media-dashboard": {
        "template_id": "dashboard",
        "description": "Full news platform with reader experience AND editor dashboard",
        "pages": [
            # Reader Pages (User-facing)
            {
                "path": "/reader",
                "title": "News Feed",
                "icon": "newspaper",
                "is_default": True,
                "category": "reader",
                "sections": [
                    {"id": "region-selector", "title": "Select Region", "component_type": "filter", "data_source": "regions", "colspan": 3},
                    {"id": "articles", "title": "Top Stories", "component_type": "cards", "data_source": "articles", "colspan": 2},
                    {"id": "trending", "title": "Trending Topics", "component_type": "list", "data_source": "trending", "colspan": 1}
                ]
            },
            {
                "path": "/reader/saved",
                "title": "Saved Articles",
                "icon": "bookmark",
                "category": "reader",
                "sections": [
                    {"id": "saved", "title": "Your Saved Articles", "component_type": "cards", "data_source": "saved_articles", "colspan": 3}
                ]
            },
            # Admin Dashboard Pages (Editor-facing)
            {
                "path": "/",
                "title": "Editor Dashboard",
                "icon": "layout-dashboard",
                "category": "admin",
                "sections": [
                    {"id": "stats", "title": "Key Metrics", "component_type": "stats", "data_source": "stats", "colspan": 3},
                    {"id": "top-stories", "title": "Today's Articles", "component_type": "table", "data_source": "articles", "colspan": 2},
                    {"id": "activity", "title": "Recent Activity", "component_type": "list", "data_source": "recentActivity", "colspan": 1}
                ]
            },
            {
                "path": "/sources",
                "title": "Sources",
                "icon": "check-circle",
                "category": "admin",
                "sections": [
                    {"id": "sources", "title": "Trusted Sources", "component_type": "table", "data_source": "sources", "colspan": 2},
                    {"id": "reliability", "title": "Source Reliability", "component_type": "chart", "data_source": "engagement_data", "colspan": 1}
                ]
            },
            {
                "path": "/analytics",
                "title": "Analytics",
                "icon": "bar-chart-3",
                "category": "admin",
                "sections": [
                    {"id": "engagement", "title": "Reader Engagement", "component_type": "chart", "data_source": "engagement_data", "colspan": 2},
                    {"id": "topics", "title": "Topic Performance", "component_type": "chart", "data_source": "trending", "colspan": 1}
                ]
            }
        ],
        "sidebar_sections": [
            {
                "title": "News Reader",
                "items": ["News Feed", "Saved Articles"]
            },
            {
                "title": "Admin Dashboard",
                "items": ["Editor Dashboard", "Sources", "Analytics"]
            }
        ],
        "stat_cards": [
            {"title": "Articles Today", "data_key": "articles_today", "icon": "FileText", "color": "blue"},
            {"title": "Active Readers", "data_key": "active_readers", "icon": "Users", "color": "green"},
            {"title": "Fact Accuracy", "data_key": "fact_accuracy", "icon": "CheckCircle", "color": "purple"},
            {"title": "Sources Tracked", "data_key": "sources_count", "icon": "Shield", "color": "amber"}
        ],
        "primary_action": "Add Source",
        "key_components": ["ArticleCard", "SourceCard", "TopicTag", "RegionSelector", "FactVerificationBadge"]
    },
    "universal-dashboard": {
        "template_id": "dashboard",
        "pages": [
            {
                "path": "/",
                "title": "Dashboard",
                "icon": "layout-dashboard",
                "is_default": True,
                "sections": [
                    {"id": "overview", "title": "Overview", "component_type": "stats", "data_source": "stats", "colspan": 3},
                    {"id": "items", "title": "Recent Items", "component_type": "cards", "data_source": "items", "colspan": 2},
                    {"id": "activity", "title": "Activity", "component_type": "list", "data_source": "recent_activity", "colspan": 1}
                ]
            },
            {
                "path": "/items",
                "title": "Items",
                "icon": "list",
                "sections": [
                    {"id": "all-items", "title": "All Items", "component_type": "table", "data_source": "items", "colspan": 3}
                ]
            },
            {
                "path": "/users",
                "title": "Users",
                "icon": "users",
                "sections": [
                    {"id": "users-table", "title": "All Users", "component_type": "table", "data_source": "users", "colspan": 2},
                    {"id": "roles", "title": "By Role", "component_type": "chart", "data_source": "roles_data", "colspan": 1}
                ]
            },
            {
                "path": "/analytics",
                "title": "Analytics",
                "icon": "bar-chart-3",
                "sections": [
                    {"id": "trends", "title": "Trends", "component_type": "chart", "data_source": "activity_data", "colspan": 2},
                    {"id": "categories", "title": "Categories", "component_type": "chart", "data_source": "categories", "colspan": 1}
                ]
            }
        ],
        "stat_cards": [
            {"title": "Total Items", "data_key": "total_items", "icon": "list", "color": "blue"},
            {"title": "Active Users", "data_key": "active_users", "icon": "users", "color": "green"},
            {"title": "Weekly Growth", "data_key": "weekly_growth", "icon": "trending-up", "color": "purple"},
            {"title": "Satisfaction", "data_key": "satisfaction", "icon": "star", "color": "amber"}
        ],
        "primary_action": "New Item",
        "key_components": ["ItemCard", "UserCard", "StatsCard"]
    }
}


def get_architecture_preset(industry: str) -> Dict[str, Any]:
    """Get a preset architecture for common industries. Returns universal for unmatched."""
    industry_lower = industry.lower()

    if "news" in industry_lower or "media" in industry_lower or "journalism" in industry_lower:
        return ARCHITECTURE_PRESETS.get("news-media-dashboard")
    elif "pet" in industry_lower or "grooming" in industry_lower:
        return ARCHITECTURE_PRESETS.get("pet-grooming-dashboard")
    elif "restaurant" in industry_lower or "cafe" in industry_lower or "food" in industry_lower:
        return ARCHITECTURE_PRESETS.get("restaurant-dashboard")
    elif "fitness" in industry_lower or "gym" in industry_lower or "yoga" in industry_lower:
        return ARCHITECTURE_PRESETS.get("fitness-dashboard")

    # Always return universal dashboard for any unmatched project
    return ARCHITECTURE_PRESETS.get("universal-dashboard")
