"""
Pytest configuration and shared fixtures for Code Weaver Pro tests.

This file sets up the Python path correctly and provides common fixtures.
"""
import sys
from pathlib import Path

# Add the API directory to Python path for imports
# This allows imports like: from src.services.prototype_orchestrator import ...
API_DIR = Path(__file__).parent.parent

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

import pytest
from unittest.mock import AsyncMock, MagicMock


# ============================================================================
# Common Fixtures
# ============================================================================

@pytest.fixture
def sample_description():
    """Sample project description for testing."""
    return "Build a pet grooming appointment dashboard with booking calendar, customer management, and payment tracking"


@pytest.fixture
def sample_domain_analysis():
    """Sample domain analysis result."""
    return {
        "industry": "pet_services",
        "confidence": 0.85,
        "entities": ["customer", "pet", "appointment", "service"],
        "actions": ["book", "cancel", "pay", "groom"],
        "metrics": ["appointments_today", "revenue_mtd", "customer_count"],
        "terminology": {
            "user": "pet parent",
            "order": "appointment",
            "item": "service"
        }
    }


@pytest.fixture
def sample_architecture():
    """Sample architecture result."""
    return {
        "pages": [
            {"name": "Dashboard", "path": "/", "components": ["StatsGrid", "AppointmentList"]},
            {"name": "Customers", "path": "/customers", "components": ["CustomerTable"]},
            {"name": "Calendar", "path": "/calendar", "components": ["BookingCalendar"]},
        ],
        "navigation": ["Dashboard", "Customers", "Calendar", "Settings"],
        "stat_cards": [
            {"label": "Today's Appointments", "value": "12", "trend": "+3"},
            {"label": "Revenue MTD", "value": "$4,520", "trend": "+12%"},
        ]
    }


@pytest.fixture
def sample_mock_data():
    """Sample mock data for testing."""
    return {
        "customers": [
            {"id": 1, "name": "John Doe", "pet": "Max (Golden Retriever)", "visits": 12},
            {"id": 2, "name": "Jane Smith", "pet": "Luna (Persian Cat)", "visits": 8}
        ],
        "appointments": [
            {"id": 1, "customer": "John Doe", "service": "Full Grooming", "date": "2024-01-15", "time": "10:00 AM"}
        ],
        "stats": {
            "total_customers": 150,
            "appointments_today": 8,
            "revenue_mtd": 4520
        }
    }


@pytest.fixture
def sample_user_clarifications():
    """Sample user clarification responses."""
    return {
        "target_market": "Small businesses with 1-5 employees",
        "pricing_model": "Subscription, $50-150/month",
        "unique_value": "Simple and affordable"
    }


@pytest.fixture
def sample_domain_expertise():
    """Sample domain expertise for testing."""
    return {
        "industry": "pet_services",
        "target_market": "Small pet grooming businesses",
        "service_model": "Appointment-based grooming services",
        "pricing_approach": "Monthly subscription",
        "unique_differentiators": ["Mobile-first", "Affordable pricing"],
        "market_size": "$14.5 billion by 2025",
        "industry_trends": [
            "Mobile grooming on the rise",
            "Technology integration increasing",
            "Organic/natural products trending"
        ],
        "competitor_features": [
            "Online booking",
            "Customer management",
            "Payment processing"
        ],
        "pricing_benchmarks": {
            "basic": "$39-50/month",
            "professional": "$95-150/month",
            "enterprise": "$200-300/month"
        },
        "terminology": {
            "user": "pet parent",
            "order": "appointment"
        }
    }


@pytest.fixture
def mock_llm_responses():
    """Pre-defined LLM responses for deterministic testing."""
    return {
        "domain_analysis": {
            "industry": "pet_services",
            "confidence": 0.85,
            "entities": ["customer", "pet", "appointment", "service"],
            "actions": ["book", "cancel", "pay", "groom"],
            "metrics": ["appointments_today", "revenue_mtd", "customer_count"]
        },
        "architecture": {
            "pages": [
                {"name": "Dashboard", "path": "/", "components": ["StatsGrid", "AppointmentList"]},
                {"name": "Customers", "path": "/customers", "components": ["CustomerTable"]},
                {"name": "Calendar", "path": "/calendar", "components": ["BookingCalendar"]}
            ],
            "navigation": ["Dashboard", "Customers", "Calendar", "Settings"],
            "stat_cards": [
                {"label": "Today's Appointments", "value": "12", "trend": "+3"},
                {"label": "Revenue MTD", "value": "$4,520", "trend": "+12%"}
            ]
        },
        "mock_data": {
            "customers": [
                {"id": 1, "name": "John Doe", "pet": "Max (Golden Retriever)", "visits": 12},
                {"id": 2, "name": "Jane Smith", "pet": "Luna (Persian Cat)", "visits": 8}
            ],
            "appointments": [
                {"id": 1, "customer": "John Doe", "service": "Full Grooming", "date": "2024-01-15", "time": "10:00 AM"}
            ]
        },
        "files": {
            "package.json": '{"name": "pet-dashboard", "version": "1.0.0"}',
            "src/app/page.tsx": "export default function Dashboard() { return <div>Dashboard</div> }",
            "src/app/layout.tsx": "export default function Layout({ children }) { return <html><body>{children}</body></html> }",
            "src/app/globals.css": ":root { --primary: #3B82F6; }"
        }
    }


@pytest.fixture
def mock_tavily_response():
    """Pre-defined Tavily API response."""
    return {
        "results": [
            {
                "title": "Pet Grooming Industry Trends 2024",
                "url": "https://example.com/trends",
                "content": "The pet grooming market is expected to reach $14.5 billion by 2025. Key trends include mobile grooming, organic products, and technology integration.",
                "score": 0.95
            },
            {
                "title": "Top Pet Grooming Software Features",
                "url": "https://example.com/software",
                "content": "Essential features include appointment scheduling, customer management, payment processing, and automated reminders.",
                "score": 0.88
            },
            {
                "title": "Competitor Analysis: PetDesk vs Gingr",
                "url": "https://example.com/competitors",
                "content": "Leading software solutions include PetDesk ($50-200/mo), Gingr ($95-300/mo), and Pawfinity ($39-99/mo).",
                "score": 0.82
            }
        ],
        "query": "pet grooming industry trends 2024"
    }


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider that returns predictable responses."""
    provider = MagicMock()
    provider.generate = AsyncMock(return_value={
        "content": "Generated content",
        "usage": {"tokens": 100}
    })
    return provider


@pytest.fixture
def mock_tavily_client(mock_tavily_response):
    """Mock Tavily API client."""
    client = MagicMock()
    client.search = AsyncMock(return_value=mock_tavily_response)
    return client
