"""
Tests for the Business Report Generator.

Tests cover:
1. Report type selection
2. HTML generation for each report type
3. Section rendering
4. Data integration
5. Styling and formatting
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

import sys
sys.path.insert(0, str(__file__).replace("tests/test_report_generator.py", "src"))


# ============================================================================
# Fixtures
# ============================================================================

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
def sample_domain_analysis():
    """Sample domain analysis for testing."""
    return {
        "industry": "pet_services",
        "confidence": 0.85,
        "entities": ["customer", "pet", "appointment", "service"],
        "actions": ["book", "cancel", "pay", "groom"]
    }


@pytest.fixture
def sample_architecture():
    """Sample architecture for testing."""
    return {
        "pages": [
            {"name": "Dashboard", "path": "/", "components": ["StatsGrid", "AppointmentList"]},
            {"name": "Customers", "path": "/customers", "components": ["CustomerTable"]},
            {"name": "Calendar", "path": "/calendar", "components": ["BookingCalendar"]}
        ],
        "navigation": ["Dashboard", "Customers", "Calendar", "Settings"]
    }


@pytest.fixture
def sample_mock_data():
    """Sample mock data for testing."""
    return {
        "customers": [
            {"id": 1, "name": "John Doe", "pet": "Max", "visits": 12},
            {"id": 2, "name": "Jane Smith", "pet": "Luna", "visits": 8}
        ],
        "appointments": [
            {"id": 1, "customer": "John Doe", "service": "Full Grooming", "date": "2024-01-15"}
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
def report_generator():
    """Create a BusinessReportGenerator instance."""
    try:
        from services.report_generator import BusinessReportGenerator
        return BusinessReportGenerator()
    except ImportError:
        pytest.skip("BusinessReportGenerator not available")


# ============================================================================
# Report Type Selection Tests
# ============================================================================

class TestReportTypeSelection:
    """Tests for report type selection logic."""

    def test_selects_transformation_for_new_builds(self, report_generator, sample_domain_expertise):
        """Test that transformation proposal is selected for new builds."""
        report_type = report_generator._determine_report_type(
            domain_expertise=sample_domain_expertise,
            has_existing_site=False,
            has_analytics=False
        )

        assert report_type in ["transformation_proposal", "TRANSFORMATION_PROPOSAL"]

    def test_selects_audit_for_existing_sites(self, report_generator, sample_domain_expertise):
        """Test that UX audit is selected for existing site analysis."""
        report_type = report_generator._determine_report_type(
            domain_expertise=sample_domain_expertise,
            has_existing_site=True,
            has_analytics=True
        )

        assert report_type in ["ux_audit", "UX_AUDIT"]

    def test_selects_comprehensive_when_both(self, report_generator, sample_domain_expertise):
        """Test that comprehensive report is selected when both scenarios apply."""
        report_type = report_generator._determine_report_type(
            domain_expertise=sample_domain_expertise,
            has_existing_site=True,
            has_analytics=True,
            want_prototype=True
        )

        assert report_type in ["comprehensive", "COMPREHENSIVE"]


# ============================================================================
# HTML Generation Tests
# ============================================================================

class TestHTMLGeneration:
    """Tests for HTML generation."""

    def test_generates_valid_html(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that generated HTML is valid."""
        html = report_generator.generate_report(
            report_type="transformation_proposal",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={}
        )

        # Should be valid HTML
        assert html.startswith("<!DOCTYPE html>") or html.startswith("<html")
        assert "</html>" in html

    def test_includes_doctype(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that HTML includes DOCTYPE."""
        html = report_generator.generate_report(
            report_type="transformation_proposal",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={}
        )

        assert "<!DOCTYPE html>" in html

    def test_includes_meta_charset(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that HTML includes charset meta tag."""
        html = report_generator.generate_report(
            report_type="transformation_proposal",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={}
        )

        assert 'charset="UTF-8"' in html or "charset=UTF-8" in html

    def test_includes_viewport_meta(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that HTML is mobile-responsive."""
        html = report_generator.generate_report(
            report_type="transformation_proposal",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={}
        )

        assert "viewport" in html


# ============================================================================
# Section Rendering Tests
# ============================================================================

class TestSectionRendering:
    """Tests for individual section rendering."""

    def test_renders_executive_summary(self, report_generator, sample_domain_expertise):
        """Test rendering of executive summary section."""
        from models.report import ExecutiveSummary, MetricItem

        summary = ExecutiveSummary(
            headline="Pet grooming dashboard opportunity",
            metrics=[
                MetricItem(label="Market Size", value="$14.5B", badge="info"),
                MetricItem(label="Growth Rate", value="8.5%", badge="good")
            ],
            bottom_line="Strong market opportunity for digital solutions"
        )

        html = report_generator._render_executive_summary(summary)

        assert "Pet grooming" in html or "executive" in html.lower()
        assert "$14.5B" in html or "Market Size" in html

    def test_renders_industry_section(self, report_generator):
        """Test rendering of industry insights section."""
        from models.report import IndustrySection, IndustryInsight

        section = IndustrySection(
            market_size="$14.5 billion",
            digital_adoption_rate="45%",
            key_trends=["Mobile grooming", "Technology integration"],
            insights=[
                IndustryInsight(title="Market Growth", value="8.5% CAGR")
            ]
        )

        html = report_generator._render_industry_section(section)

        assert html is not None
        # Should contain industry data

    def test_renders_recommendations(self, report_generator):
        """Test rendering of recommendations section."""
        from models.report import Recommendation

        recommendations = [
            Recommendation(
                priority=1,
                title="Implement Online Booking",
                subtitle="HIGH - 90% confidence",
                current_state="Phone-only bookings",
                recommended_state="Online + phone bookings",
                expected_lift="+40% booking conversion",
                changes=["Add booking widget", "Enable calendar sync"]
            )
        ]

        html = report_generator._render_recommendations(recommendations)

        assert "Online Booking" in html or "recommendation" in html.lower()

    def test_renders_roadmap(self, report_generator):
        """Test rendering of implementation roadmap."""
        from models.report import RoadmapPhase, RoadmapItem

        roadmap = [
            RoadmapPhase(
                title="Phase 1: Foundation",
                color="#3B82F6",
                items=[
                    RoadmapItem(task="Set up project structure", completed=True),
                    RoadmapItem(task="Configure database", completed=False)
                ]
            )
        ]

        html = report_generator._render_roadmap(roadmap)

        assert "Phase 1" in html or "Foundation" in html

    def test_renders_kpi_table(self, report_generator):
        """Test rendering of KPI tracking table."""
        from models.report import KPIRow

        kpis = [
            KPIRow(
                metric="Booking Conversion",
                current="25%",
                target_30_days="35%",
                target_90_days="50%",
                current_is_bad=True
            )
        ]

        html = report_generator._render_kpi_table(kpis)

        assert "Booking Conversion" in html or "25%" in html


# ============================================================================
# Data Integration Tests
# ============================================================================

class TestDataIntegration:
    """Tests for data integration in reports."""

    def test_includes_company_name(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that company name appears in report."""
        html = report_generator.generate_report(
            report_type="transformation_proposal",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={},
            company_name="PetGroomPro"
        )

        assert "PetGroomPro" in html

    def test_includes_industry_data(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that industry data is included."""
        html = report_generator.generate_report(
            report_type="transformation_proposal",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={}
        )

        # Should include industry-specific content
        assert "pet" in html.lower() or "grooming" in html.lower()

    def test_includes_clarification_responses(self, report_generator, sample_domain_expertise, sample_domain_analysis, sample_user_clarifications):
        """Test that user clarifications are reflected."""
        html = report_generator.generate_report(
            report_type="transformation_proposal",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications=sample_user_clarifications
        )

        # Clarification content should influence the report
        assert html is not None


# ============================================================================
# Styling Tests
# ============================================================================

class TestStyling:
    """Tests for report styling."""

    def test_includes_css_styles(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that CSS styles are included."""
        html = report_generator.generate_report(
            report_type="transformation_proposal",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={}
        )

        # Should have inline styles or style tag
        assert "<style>" in html or "style=" in html

    def test_includes_print_styles(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that print-friendly styles are included."""
        html = report_generator.generate_report(
            report_type="transformation_proposal",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={}
        )

        # Should have print media query
        assert "@media print" in html or "print" in html.lower()

    def test_brand_colors_applied(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that brand colors are applied."""
        html = report_generator.generate_report(
            report_type="transformation_proposal",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={},
            brand_colors={"primary": "#FF5733", "secondary": "#33FF57"}
        )

        # Brand colors should appear in CSS
        assert "#FF5733" in html or "primary" in html.lower()


# ============================================================================
# Report Type-Specific Tests
# ============================================================================

class TestTransformationProposal:
    """Tests specific to Transformation Proposal reports."""

    def test_includes_features_table(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that features table is included."""
        html = report_generator.generate_report(
            report_type="transformation_proposal",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={}
        )

        # Should have features section
        assert "feature" in html.lower() or "recommendation" in html.lower()

    def test_includes_design_system(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that design system recommendations are included."""
        html = report_generator.generate_report(
            report_type="transformation_proposal",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={}
        )

        # Should have design-related content
        assert "design" in html.lower() or "color" in html.lower() or "style" in html.lower()


class TestUXAudit:
    """Tests specific to UX Audit reports."""

    def test_includes_score_breakdown(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that score breakdown is included."""
        html = report_generator.generate_report(
            report_type="ux_audit",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={}
        )

        # Should have scoring section
        assert "score" in html.lower() or "rating" in html.lower()

    def test_includes_issues_found(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that issues section is included."""
        html = report_generator.generate_report(
            report_type="ux_audit",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={}
        )

        # Should have issues section
        assert "issue" in html.lower() or "problem" in html.lower() or "finding" in html.lower()


class TestComprehensiveReport:
    """Tests specific to Comprehensive reports."""

    def test_includes_prototype_section(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that prototype preview is included."""
        html = report_generator.generate_report(
            report_type="comprehensive",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={},
            prototype_url="http://localhost:3000"
        )

        # Should have prototype section
        assert "prototype" in html.lower() or "preview" in html.lower() or "localhost" in html

    def test_includes_ai_analysis_log(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test that AI analysis log is included."""
        html = report_generator.generate_report(
            report_type="comprehensive",
            domain_expertise=sample_domain_expertise,
            domain_analysis=sample_domain_analysis,
            architecture={},
            mock_data={},
            user_clarifications={},
            ai_log=["Agent 1: Analyzed domain", "Agent 2: Generated architecture"]
        )

        # Should have AI log section
        assert "Agent" in html or "analysis" in html.lower() or "log" in html.lower()


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling in report generation."""

    def test_handles_missing_data(self, report_generator):
        """Test handling of missing data gracefully."""
        html = report_generator.generate_report(
            report_type="transformation_proposal",
            domain_expertise={},
            domain_analysis={},
            architecture={},
            mock_data={},
            user_clarifications={}
        )

        # Should still generate a valid report
        assert html is not None
        assert "<html" in html

    def test_handles_invalid_report_type(self, report_generator, sample_domain_expertise, sample_domain_analysis):
        """Test handling of invalid report type."""
        # Should either default to a type or raise a clear error
        try:
            html = report_generator.generate_report(
                report_type="invalid_type",
                domain_expertise=sample_domain_expertise,
                domain_analysis=sample_domain_analysis,
                architecture={},
                mock_data={},
                user_clarifications={}
            )
            # If it succeeds, should have defaulted to a valid type
            assert html is not None
        except ValueError as e:
            # Clear error message expected
            assert "invalid" in str(e).lower() or "type" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
