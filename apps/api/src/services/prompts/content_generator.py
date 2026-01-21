"""
Content Generator Prompt

Generates realistic mock data that makes prototypes feel like real applications.
Creates domain-specific data based on the domain analysis and architecture.

The key difference from generic mock data:
- "Pet grooming" -> Bella, Max, Luna (pet names) instead of User 1, User 2
- "Restaurant" -> Margherita Pizza, Caesar Salad instead of Item 1, Item 2
- Realistic prices, times, and quantities for this industry
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class MockDataSchema(BaseModel):
    """Schema for generated mock data"""

    # Stats for stat cards - MUST be an array of objects with title, value, change, changeType, icon
    stats: List[Dict[str, Any]] = Field(
        description="Array of stat card objects with title, value, change, changeType, icon"
    )

    # Main data arrays (appointments, users, items, etc.)
    primary_data: Dict[str, List[Dict[str, Any]]] = Field(
        description="Primary data arrays keyed by data_source names from architecture"
    )

    # Chart data
    chart_data: Dict[str, List[Dict[str, Any]]] = Field(
        description="Data formatted for charts (labels, values)"
    )

    # Activity/feed data
    recent_activity: List[Dict[str, Any]] = Field(
        description="Recent activity items for activity feeds"
    )

    # Reviews/feedback
    reviews: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Customer reviews/feedback with realistic text"
    )


CONTENT_GENERATOR_PROMPT = """
You are a Content Generator specializing in creating realistic mock data for prototypes.

## Domain Analysis
{domain_analysis}

## Architecture
{architecture}

## Required Data Sources
{required_data}

## Your Task
Generate realistic mock data that makes this prototype feel like a REAL application
for THIS specific business. The data should:

1. Use domain-specific names and terminology
2. Have realistic prices, times, and quantities
3. Tell a story (e.g., busy morning, satisfied customers, growing revenue)
4. Include variety (different statuses, types, amounts)

## Output Format
Return a JSON object that will become mock.json:

IMPORTANT: stats MUST be an array of objects, not a flat object!

```json
{{
  "stats": [
    {{"title": "Appointments Today", "value": "8", "change": "+12%", "changeType": "increase", "icon": "Calendar"}},
    {{"title": "Completed This Week", "value": "47", "change": "+8%", "changeType": "increase", "icon": "CheckCircle"}},
    {{"title": "Weekly Revenue", "value": "$2,840", "change": "+24%", "changeType": "increase", "icon": "DollarSign"}},
    {{"title": "Avg Wait Time", "value": "12 min", "change": "-15%", "changeType": "decrease", "icon": "Clock"}}
  ],

  "appointments": [
    {{
      "id": "apt-001",
      "pet_name": "Bella",
      "pet_type": "Golden Retriever",
      "owner": "Sarah Mitchell",
      "service": "Full Groom",
      "time": "2:00 PM",
      "status": "in_progress",
      "duration": "1.5 hrs",
      "price": "$85",
      "notes": "Extra sensitive skin - use hypoallergenic shampoo"
    }},
    {{
      "id": "apt-002",
      "pet_name": "Max",
      "pet_type": "Labrador",
      "owner": "Mike Johnson",
      "service": "Bath & Brush",
      "time": "2:30 PM",
      "status": "waiting",
      "duration": "45 min",
      "price": "$45"
    }},
    {{
      "id": "apt-003",
      "pet_name": "Luna",
      "pet_type": "Poodle Mix",
      "owner": "Emily Chen",
      "service": "Full Groom + Nail Trim",
      "time": "3:15 PM",
      "status": "scheduled",
      "duration": "2 hrs",
      "price": "$110"
    }}
  ],

  "pets": [
    {{
      "id": "pet-001",
      "name": "Bella",
      "type": "Golden Retriever",
      "age": "3 years",
      "owner": "Sarah Mitchell",
      "last_visit": "2 weeks ago",
      "visits_total": 12,
      "notes": "Sensitive skin, loves treats",
      "avatar_initials": "B"
    }}
  ],

  "services": [
    {{
      "id": "svc-001",
      "name": "Bath & Brush",
      "description": "Full bath, blow dry, and brush out",
      "duration": "45 min",
      "price_small": "$35",
      "price_medium": "$45",
      "price_large": "$55",
      "popular": true
    }},
    {{
      "id": "svc-002",
      "name": "Full Groom",
      "description": "Bath, haircut, nail trim, ear cleaning",
      "duration": "1.5 hrs",
      "price_small": "$65",
      "price_medium": "$85",
      "price_large": "$110",
      "popular": true
    }}
  ],

  "revenue_data": [
    {{ "month": "Jan", "value": 8200 }},
    {{ "month": "Feb", "value": 9100 }},
    {{ "month": "Mar", "value": 8800 }},
    {{ "month": "Apr", "value": 10500 }},
    {{ "month": "May", "value": 11200 }},
    {{ "month": "Jun", "value": 12400 }}
  ],

  "popular_services": [
    {{ "service": "Full Groom", "count": 145, "revenue": 12325 }},
    {{ "service": "Bath & Brush", "count": 210, "revenue": 9450 }},
    {{ "service": "Nail Trim", "count": 180, "revenue": 3600 }}
  ],

  "recentActivity": [
    {{
      "id": "act-001",
      "user": "Sarah M.",
      "action": "booked appointment for",
      "target": "Bella",
      "time": "5 min ago",
      "icon": "calendar"
    }},
    {{
      "id": "act-002",
      "user": "Groomer Jake",
      "action": "completed grooming",
      "target": "Cooper",
      "time": "15 min ago",
      "icon": "check-circle"
    }},
    {{
      "id": "act-003",
      "user": "Mike J.",
      "action": "left a 5-star review for",
      "target": "Max's grooming",
      "time": "1 hour ago",
      "icon": "star"
    }}
  ],

  "reviews": [
    {{
      "id": "rev-001",
      "author": "Sarah M.",
      "rating": 5,
      "text": "Bella looks amazing! The team is always so gentle with her.",
      "date": "2 days ago",
      "pet": "Bella"
    }},
    {{
      "id": "rev-002",
      "author": "Mike J.",
      "rating": 5,
      "text": "Max actually enjoys coming here now. That says everything!",
      "date": "1 week ago",
      "pet": "Max"
    }}
  ]
}}
```

## Guidelines

1. **Realistic Names**: Use common, realistic names for the domain
   - Pet grooming: Bella, Max, Luna, Charlie, Cooper, Daisy
   - Restaurant: John Smith, Emily Chen, Michael Brown
   - Fitness: Sarah, Mike, Jessica, David

2. **Realistic Prices**: Match industry norms
   - Pet grooming: $35-$120
   - Restaurant: $12-$45 entrees
   - Fitness: $20-$150/month memberships

3. **Realistic Times**: Match business hours and typical durations
   - Pet grooming: 45 min - 2 hrs per service
   - Restaurant: 30-60 min average meal
   - Fitness: 30-90 min classes

4. **Variety in Status**: Include mix of statuses
   - completed, in_progress, waiting, scheduled, cancelled

5. **Positive Narrative**: Data should tell a success story
   - Growing revenue trend
   - Good reviews
   - Busy schedule (shows demand)

6. **Actionable Insights**: Include data that suggests actions
   - "Most popular service" suggests focus area
   - "Avg wait time" suggests efficiency opportunity

Remember: The data should make the prototype feel REAL, not like a demo with
obvious placeholder content.
"""


def get_content_generator_prompt(
    domain_analysis: dict,
    architecture: dict,
    required_data: List[str]
) -> str:
    """Get the formatted content generator prompt"""
    import json
    return CONTENT_GENERATOR_PROMPT.format(
        domain_analysis=json.dumps(domain_analysis, indent=2),
        architecture=json.dumps(architecture, indent=2),
        required_data=", ".join(required_data)
    )


# Pre-built mock data for common industries
MOCK_DATA_PRESETS: Dict[str, Dict[str, Any]] = {
    "pet-grooming": {
        "stats": [
            {"title": "Appointments Today", "value": "8", "change": "+12%", "changeType": "increase", "icon": "Calendar"},
            {"title": "Completed This Week", "value": "47", "change": "+8%", "changeType": "increase", "icon": "CheckCircle"},
            {"title": "Weekly Revenue", "value": "$2,840", "change": "+24%", "changeType": "increase", "icon": "DollarSign"},
            {"title": "Avg Wait Time", "value": "12 min", "change": "-15%", "changeType": "decrease", "icon": "Clock"}
        ],
        "appointments": [
            {
                "id": "apt-001",
                "pet_name": "Bella",
                "pet_type": "Golden Retriever",
                "owner": "Sarah Mitchell",
                "service": "Full Groom",
                "time": "2:00 PM",
                "status": "in_progress",
                "duration": "1.5 hrs",
                "price": "$85",
                "notes": "Extra sensitive skin"
            },
            {
                "id": "apt-002",
                "pet_name": "Max",
                "pet_type": "Labrador",
                "owner": "Mike Johnson",
                "service": "Bath & Brush",
                "time": "2:30 PM",
                "status": "waiting",
                "duration": "45 min",
                "price": "$45"
            },
            {
                "id": "apt-003",
                "pet_name": "Luna",
                "pet_type": "Poodle Mix",
                "owner": "Emily Chen",
                "service": "Full Groom + Nail Trim",
                "time": "3:15 PM",
                "status": "scheduled",
                "duration": "2 hrs",
                "price": "$110"
            },
            {
                "id": "apt-004",
                "pet_name": "Charlie",
                "pet_type": "Shih Tzu",
                "owner": "David Park",
                "service": "Puppy Package",
                "time": "4:00 PM",
                "status": "scheduled",
                "duration": "1 hr",
                "price": "$55"
            }
        ],
        "pets": [
            {"id": "pet-001", "name": "Bella", "type": "Golden Retriever", "age": "3 years", "owner": "Sarah Mitchell", "visits": 12},
            {"id": "pet-002", "name": "Max", "type": "Labrador", "age": "5 years", "owner": "Mike Johnson", "visits": 24},
            {"id": "pet-003", "name": "Luna", "type": "Poodle Mix", "age": "2 years", "owner": "Emily Chen", "visits": 8},
            {"id": "pet-004", "name": "Charlie", "type": "Shih Tzu", "age": "6 months", "owner": "David Park", "visits": 3}
        ],
        "services": [
            {"id": "svc-001", "name": "Bath & Brush", "duration": "45 min", "price": "$35-$55", "popular": True},
            {"id": "svc-002", "name": "Full Groom", "duration": "1.5 hrs", "price": "$65-$110", "popular": True},
            {"id": "svc-003", "name": "Nail Trim", "duration": "15 min", "price": "$15-$25", "popular": False},
            {"id": "svc-004", "name": "De-shedding", "duration": "1 hr", "price": "$45-$75", "popular": False},
            {"id": "svc-005", "name": "Puppy Package", "duration": "1 hr", "price": "$45-$65", "popular": True}
        ],
        "revenue_data": [
            {"month": "Jan", "value": 8200},
            {"month": "Feb", "value": 9100},
            {"month": "Mar", "value": 8800},
            {"month": "Apr", "value": 10500},
            {"month": "May", "value": 11200},
            {"month": "Jun", "value": 12400}
        ],
        "recentActivity": [
            {"id": "act-001", "user": "Sarah M.", "action": "booked appointment for", "target": "Bella", "time": "5 min ago"},
            {"id": "act-002", "user": "Groomer Jake", "action": "completed grooming", "target": "Cooper", "time": "15 min ago"},
            {"id": "act-003", "user": "Mike J.", "action": "left a 5-star review", "target": "", "time": "1 hour ago"},
            {"id": "act-004", "user": "Emily C.", "action": "rescheduled appointment for", "target": "Luna", "time": "2 hours ago"}
        ],
        "reviews": [
            {"id": "rev-001", "author": "Sarah M.", "rating": 5, "text": "Bella looks amazing! The team is always so gentle with her.", "date": "2 days ago"},
            {"id": "rev-002", "author": "Mike J.", "rating": 5, "text": "Max actually enjoys coming here now. That says everything!", "date": "1 week ago"},
            {"id": "rev-003", "author": "Emily C.", "rating": 4, "text": "Great service, Luna loved it. Slightly longer wait than expected.", "date": "2 weeks ago"}
        ],
        "users": [
            {"id": "user-001", "name": "Sarah Mitchell", "email": "sarah.m@petgroom.com", "role": "Pet Parent", "status": "Active", "lastActive": "2 minutes ago", "avatar": "SM"},
            {"id": "user-002", "name": "Jake Thompson", "email": "jake.t@petgroom.com", "role": "Groomer", "status": "Active", "lastActive": "Now", "avatar": "JT"},
            {"id": "user-003", "name": "Mike Johnson", "email": "mike.j@petgroom.com", "role": "Pet Parent", "status": "Active", "lastActive": "5 minutes ago", "avatar": "MJ"},
            {"id": "user-004", "name": "Emily Chen", "email": "emily.c@petgroom.com", "role": "Pet Parent", "status": "Inactive", "lastActive": "1 hour ago", "avatar": "EC"}
        ]
    },
    "restaurant": {
        "stats": [
            {"title": "Tables Available", "value": "6", "change": "+2", "changeType": "increase", "icon": "LayoutGrid"},
            {"title": "Covers Today", "value": "84", "change": "+18%", "changeType": "increase", "icon": "Users"},
            {"title": "Avg Ticket", "value": "$47", "change": "+8%", "changeType": "increase", "icon": "DollarSign"},
            {"title": "Wait Time", "value": "15 min", "change": "-5 min", "changeType": "decrease", "icon": "Clock"}
        ],
        "tables": [
            {"id": "t-01", "number": 1, "capacity": 2, "status": "occupied", "server": "Maria", "time": "45 min"},
            {"id": "t-02", "number": 2, "capacity": 4, "status": "available", "server": None, "time": None},
            {"id": "t-03", "number": 3, "capacity": 4, "status": "reserved", "server": "Jake", "time": "6:30 PM"},
            {"id": "t-04", "number": 4, "capacity": 6, "status": "occupied", "server": "Maria", "time": "30 min"},
            {"id": "t-05", "number": 5, "capacity": 2, "status": "available", "server": None, "time": None},
            {"id": "t-06", "number": 6, "capacity": 8, "status": "reserved", "server": "Jake", "time": "7:00 PM"}
        ],
        "orders": [
            {"id": "ord-001", "table": 1, "items": 3, "total": "$67", "status": "preparing", "time": "12 min"},
            {"id": "ord-002", "table": 4, "items": 5, "total": "$124", "status": "ready", "time": "2 min"},
            {"id": "ord-003", "table": 1, "items": 2, "total": "$28", "status": "ordered", "time": "Just now"}
        ],
        "menu_items": [
            {"id": "m-001", "name": "Margherita Pizza", "category": "Pizza", "price": "$16", "popular": True},
            {"id": "m-002", "name": "Caesar Salad", "category": "Salads", "price": "$12", "popular": True},
            {"id": "m-003", "name": "Grilled Salmon", "category": "Mains", "price": "$28", "popular": False},
            {"id": "m-004", "name": "Truffle Pasta", "category": "Pasta", "price": "$24", "popular": True},
            {"id": "m-005", "name": "Tiramisu", "category": "Desserts", "price": "$10", "popular": True}
        ],
        "reservations": [
            {"id": "res-001", "name": "Johnson Party", "guests": 4, "time": "6:30 PM", "table": 3, "notes": "Birthday"},
            {"id": "res-002", "name": "Smith", "guests": 6, "time": "7:00 PM", "table": 6, "notes": "Anniversary"},
            {"id": "res-003", "name": "Chen", "guests": 2, "time": "7:30 PM", "table": None, "notes": ""}
        ],
        "sales_data": [
            {"day": "Mon", "value": 2400},
            {"day": "Tue", "value": 2100},
            {"day": "Wed", "value": 2800},
            {"day": "Thu", "value": 3200},
            {"day": "Fri", "value": 4500},
            {"day": "Sat", "value": 5200}
        ],
        "recentActivity": [
            {"id": "act-001", "user": "Table 1", "action": "ordered", "target": "Truffle Pasta", "time": "Just now"},
            {"id": "act-002", "user": "Kitchen", "action": "completed order for", "target": "Table 4", "time": "2 min ago"},
            {"id": "act-003", "user": "Host", "action": "seated", "target": "Walk-in party of 2", "time": "5 min ago"}
        ],
        "users": [
            {"id": "user-001", "name": "Maria Garcia", "email": "maria@restaurant.com", "role": "Server", "status": "Active", "lastActive": "Now", "avatar": "MG"},
            {"id": "user-002", "name": "Jake Wilson", "email": "jake@restaurant.com", "role": "Server", "status": "Active", "lastActive": "5 minutes ago", "avatar": "JW"},
            {"id": "user-003", "name": "Chef Marco", "email": "marco@restaurant.com", "role": "Head Chef", "status": "Active", "lastActive": "Now", "avatar": "CM"},
            {"id": "user-004", "name": "Lisa Chen", "email": "lisa@restaurant.com", "role": "Host", "status": "Active", "lastActive": "2 minutes ago", "avatar": "LC"}
        ]
    },
    "fitness": {
        "stats": [
            {"title": "Classes Today", "value": "12", "change": "+2", "changeType": "increase", "icon": "Calendar"},
            {"title": "Active Members", "value": "847", "change": "+5%", "changeType": "increase", "icon": "Users"},
            {"title": "Monthly Revenue", "value": "$42,350", "change": "+12%", "changeType": "increase", "icon": "DollarSign"},
            {"title": "Avg Attendance", "value": "18", "change": "+3", "changeType": "increase", "icon": "Activity"}
        ],
        "classes": [
            {"id": "cls-001", "name": "Morning Flow Yoga", "instructor": "Maya", "time": "7:00 AM", "spots": "18/20", "room": "Studio A"},
            {"id": "cls-002", "name": "HIIT Bootcamp", "instructor": "James", "time": "8:30 AM", "spots": "15/15", "room": "Main Floor"},
            {"id": "cls-003", "name": "Power Yoga", "instructor": "Maya", "time": "12:00 PM", "spots": "12/20", "room": "Studio A"},
            {"id": "cls-004", "name": "Spin Class", "instructor": "Sarah", "time": "5:30 PM", "spots": "20/24", "room": "Spin Studio"},
            {"id": "cls-005", "name": "Restorative", "instructor": "Luna", "time": "7:00 PM", "spots": "8/15", "room": "Studio B"}
        ],
        "members": [
            {"id": "mem-001", "name": "Jessica Chen", "membership": "Unlimited", "joined": "Jan 2024", "visits": 48, "status": "active"},
            {"id": "mem-002", "name": "Mike Thompson", "membership": "10-Class Pack", "joined": "Mar 2024", "visits": 7, "status": "active"},
            {"id": "mem-003", "name": "Sarah Williams", "membership": "Monthly", "joined": "Dec 2023", "visits": 62, "status": "active"},
            {"id": "mem-004", "name": "David Park", "membership": "Unlimited", "joined": "Feb 2024", "visits": 35, "status": "active"}
        ],
        "instructors": [
            {"id": "ins-001", "name": "Maya", "specialty": "Yoga", "classes_week": 8, "rating": 4.9},
            {"id": "ins-002", "name": "James", "specialty": "HIIT/Strength", "classes_week": 10, "rating": 4.8},
            {"id": "ins-003", "name": "Sarah", "specialty": "Cycling", "classes_week": 6, "rating": 4.7},
            {"id": "ins-004", "name": "Luna", "specialty": "Yoga/Meditation", "classes_week": 5, "rating": 4.9}
        ],
        "attendance_data": [
            {"week": "W1", "value": 342},
            {"week": "W2", "value": 378},
            {"week": "W3", "value": 356},
            {"week": "W4", "value": 412}
        ],
        "checkins": [
            {"id": "chk-001", "member": "Jessica C.", "class": "Morning Flow", "time": "6:55 AM"},
            {"id": "chk-002", "member": "Mike T.", "class": "HIIT Bootcamp", "time": "8:25 AM"},
            {"id": "chk-003", "member": "Sarah W.", "class": "Open Gym", "time": "9:00 AM"}
        ],
        "recentActivity": [
            {"id": "act-001", "user": "Jessica C.", "action": "checked in for", "target": "Morning Flow", "time": "5 min ago"},
            {"id": "act-002", "user": "New member", "action": "signed up:", "target": "David P.", "time": "1 hour ago"},
            {"id": "act-003", "user": "Maya", "action": "class completed:", "target": "Power Yoga", "time": "2 hours ago"}
        ],
        "users": [
            {"id": "user-001", "name": "Jessica Chen", "email": "jessica@zenflow.com", "role": "Member", "status": "Active", "lastActive": "5 minutes ago", "avatar": "JC"},
            {"id": "user-002", "name": "Maya Johnson", "email": "maya@zenflow.com", "role": "Instructor", "status": "Active", "lastActive": "Now", "avatar": "MJ"},
            {"id": "user-003", "name": "James Wilson", "email": "james@zenflow.com", "role": "Instructor", "status": "Active", "lastActive": "10 minutes ago", "avatar": "JW"},
            {"id": "user-004", "name": "Sarah Williams", "email": "sarah@zenflow.com", "role": "Member", "status": "Active", "lastActive": "1 hour ago", "avatar": "SW"}
        ]
    },
    "news-media": {
        "stats": [
            {"title": "Articles Today", "value": "47", "change": "+8%", "changeType": "increase", "icon": "FileText"},
            {"title": "Active Readers", "value": "12.4K", "change": "+24%", "changeType": "increase", "icon": "Users"},
            {"title": "Fact Accuracy", "value": "98.2%", "change": "+0.5%", "changeType": "increase", "icon": "CheckCircle"},
            {"title": "Sources Verified", "value": "156", "change": "+12", "changeType": "increase", "icon": "Shield"}
        ],
        "articles": [
            {
                "id": "art-001",
                "title": "Global Climate Summit Reaches Historic Agreement",
                "category": "World",
                "source": "Reuters",
                "sourceUrl": "https://reuters.com",
                "time": "2 hours ago",
                "readTime": "5 min read",
                "facts_verified": 12,
                "summary": "World leaders from 195 countries reached a landmark agreement, committing to reduce carbon emissions by 50% by 2035.",
                "pros": ["Reduced emissions targets with measurable milestones", "International cooperation at unprecedented scale", "Legally binding commitments with enforcement"],
                "cons": ["Implementation challenges remain significant", "Funding gaps for developing economies", "Political will may waver after leadership changes"],
                "status": "verified"
            },
            {
                "id": "art-002",
                "title": "Tech Giants Report Record Q4 Earnings",
                "category": "Business",
                "source": "AP News",
                "sourceUrl": "https://apnews.com",
                "time": "4 hours ago",
                "readTime": "4 min read",
                "facts_verified": 8,
                "summary": "Major technology companies reported better-than-expected quarterly earnings, driven by AI investments and cloud computing growth.",
                "pros": ["Strong job growth in tech sector", "Increased R&D investment", "Consumer confidence rising"],
                "cons": ["Privacy concerns mounting", "Market concentration issues", "Regulatory scrutiny increasing"],
                "status": "verified"
            },
            {
                "id": "art-003",
                "title": "Healthcare Reform Bill Advances in Senate",
                "category": "Politics",
                "source": "NPR",
                "sourceUrl": "https://npr.org",
                "time": "6 hours ago",
                "readTime": "6 min read",
                "facts_verified": 15,
                "summary": "The bipartisan healthcare reform bill passed a key committee vote, moving closer to a full Senate vote expected next week.",
                "pros": ["Expanded coverage for 15 million uninsured", "Cost controls on prescription drugs", "Mental health parity requirements"],
                "cons": ["Estimated $200B budget impact", "Implementation timeline concerns", "State opt-out provisions"],
                "status": "verified"
            },
            {
                "id": "art-004",
                "title": "Breakthrough in Ocean Plastic Cleanup Technology",
                "category": "Science",
                "source": "BBC",
                "sourceUrl": "https://bbc.com",
                "time": "8 hours ago",
                "readTime": "3 min read",
                "facts_verified": 6,
                "summary": "Researchers announce a new enzyme capable of breaking down ocean plastic 100x faster than previous methods.",
                "pros": ["Scalable technology", "Cost-effective solution", "No harmful byproducts"],
                "cons": ["Still in early testing phase", "Deployment challenges at scale", "Requires significant funding"],
                "status": "verified"
            }
        ],
        "sources": [
            {"id": "src-001", "name": "Reuters", "reliability": 98, "articles": 1240, "category": "Wire Service"},
            {"id": "src-002", "name": "AP News", "reliability": 97, "articles": 1180, "category": "Wire Service"},
            {"id": "src-003", "name": "NPR", "reliability": 95, "articles": 890, "category": "Public Media"},
            {"id": "src-004", "name": "BBC", "reliability": 94, "articles": 1450, "category": "International"}
        ],
        "trending": [
            {"id": "tr-001", "topic": "Climate Summit", "articles": 24, "trend": "up"},
            {"id": "tr-002", "topic": "Tech Earnings", "articles": 18, "trend": "up"},
            {"id": "tr-003", "topic": "Healthcare Reform", "articles": 15, "trend": "stable"},
            {"id": "tr-004", "topic": "Election Coverage", "articles": 12, "trend": "down"},
            {"id": "tr-005", "topic": "AI Regulation", "articles": 21, "trend": "up"}
        ],
        "regions": {
            "world": {"label": "World"},
            "countries": [
                {"id": "us", "label": "United States", "states": ["California", "New York", "Texas", "Florida"]},
                {"id": "uk", "label": "United Kingdom", "states": ["England", "Scotland", "Wales"]},
                {"id": "eu", "label": "European Union", "states": ["Germany", "France", "Spain", "Italy"]}
            ]
        },
        "saved_articles": [],
        "engagement_data": [
            {"day": "Mon", "readers": 8400},
            {"day": "Tue", "readers": 9200},
            {"day": "Wed", "readers": 11500},
            {"day": "Thu", "readers": 10800},
            {"day": "Fri", "readers": 12400}
        ],
        "recentActivity": [
            {"id": "act-001", "user": "System", "action": "verified facts for", "target": "Climate Summit article", "time": "5 min ago"},
            {"id": "act-002", "user": "Editor", "action": "published", "target": "Tech Earnings Report", "time": "15 min ago"},
            {"id": "act-003", "user": "AI", "action": "extracted 12 facts from", "target": "Healthcare article", "time": "30 min ago"},
            {"id": "act-004", "user": "Reader", "action": "saved article:", "target": "Climate Summit", "time": "45 min ago"}
        ],
        "users": [
            {"id": "user-001", "name": "Sarah Chen", "email": "sarah.chen@miranews.com", "role": "Editor in Chief", "status": "Active", "lastActive": "2 minutes ago", "avatar": "SC"},
            {"id": "user-002", "name": "James Wilson", "email": "james.wilson@miranews.com", "role": "Senior Reporter", "status": "Active", "lastActive": "5 minutes ago", "avatar": "JW"},
            {"id": "user-003", "name": "Emily Rodriguez", "email": "emily.r@miranews.com", "role": "Fact Checker", "status": "Active", "lastActive": "10 minutes ago", "avatar": "ER"},
            {"id": "user-004", "name": "Michael Park", "email": "m.park@miranews.com", "role": "Tech Editor", "status": "Inactive", "lastActive": "1 hour ago", "avatar": "MP"}
        ]
    },
    "universal": {
        "stats": [
            {"title": "Total Items", "value": "1,247", "change": "+12%", "changeType": "increase", "icon": "Package"},
            {"title": "Active Users", "value": "2.4K", "change": "+24%", "changeType": "increase", "icon": "Users"},
            {"title": "Weekly Growth", "value": "+18%", "change": "+5%", "changeType": "increase", "icon": "TrendingUp"},
            {"title": "Satisfaction", "value": "94%", "change": "+2%", "changeType": "increase", "icon": "ThumbsUp"}
        ],
        "items": [
            {"id": "item-001", "name": "Item Alpha", "status": "active", "category": "Primary", "created": "2 days ago"},
            {"id": "item-002", "name": "Item Beta", "status": "pending", "category": "Secondary", "created": "1 week ago"},
            {"id": "item-003", "name": "Item Gamma", "status": "active", "category": "Primary", "created": "3 days ago"},
            {"id": "item-004", "name": "Item Delta", "status": "completed", "category": "Tertiary", "created": "2 weeks ago"}
        ],
        "users": [
            {"id": "user-001", "name": "Alex Johnson", "email": "alex@company.com", "role": "Admin", "status": "Active", "lastActive": "2 minutes ago", "avatar": "AJ"},
            {"id": "user-002", "name": "Sam Chen", "email": "sam@company.com", "role": "User", "status": "Active", "lastActive": "5 minutes ago", "avatar": "SC"},
            {"id": "user-003", "name": "Jordan Smith", "email": "jordan@company.com", "role": "User", "status": "Active", "lastActive": "15 minutes ago", "avatar": "JS"},
            {"id": "user-004", "name": "Taylor Brown", "email": "taylor@company.com", "role": "Moderator", "status": "Inactive", "lastActive": "1 hour ago", "avatar": "TB"}
        ],
        "categories": [
            {"id": "cat-001", "name": "Primary", "count": 456, "growth": "+15%"},
            {"id": "cat-002", "name": "Secondary", "count": 312, "growth": "+8%"},
            {"id": "cat-003", "name": "Tertiary", "count": 189, "growth": "+22%"}
        ],
        "activity_data": [
            {"month": "Jan", "value": 4200},
            {"month": "Feb", "value": 5100},
            {"month": "Mar", "value": 4800},
            {"month": "Apr", "value": 6200},
            {"month": "May", "value": 7100},
            {"month": "Jun", "value": 8400}
        ],
        "recentActivity": [
            {"id": "act-001", "user": "Alex J.", "action": "created", "target": "new item", "time": "5 min ago"},
            {"id": "act-002", "user": "Sam C.", "action": "updated", "target": "settings", "time": "15 min ago"},
            {"id": "act-003", "user": "Jordan S.", "action": "completed", "target": "task #42", "time": "1 hour ago"},
            {"id": "act-004", "user": "Taylor B.", "action": "reviewed", "target": "submission", "time": "2 hours ago"}
        ]
    }
}


def get_mock_data_preset(industry: str) -> Optional[Dict[str, Any]]:
    """Get preset mock data for common industries. Returns universal preset if no match."""
    industry_lower = industry.lower()

    if "news" in industry_lower or "media" in industry_lower or "journalism" in industry_lower:
        return MOCK_DATA_PRESETS.get("news-media")
    elif "pet" in industry_lower or "grooming" in industry_lower:
        return MOCK_DATA_PRESETS.get("pet-grooming")
    elif "restaurant" in industry_lower or "cafe" in industry_lower or "food" in industry_lower:
        return MOCK_DATA_PRESETS.get("restaurant")
    elif "fitness" in industry_lower or "gym" in industry_lower or "yoga" in industry_lower:
        return MOCK_DATA_PRESETS.get("fitness")

    # Return universal preset for any unmatched industry
    return MOCK_DATA_PRESETS.get("universal")


def customize_mock_data(preset: Dict[str, Any], business_name: str) -> Dict[str, Any]:
    """Customize preset mock data with business-specific details"""
    import copy
    data = copy.deepcopy(preset)

    # Add business name where appropriate
    # This could be expanded to do more sophisticated customization

    return data
