"""
Tests for the Modular Audit Data System (business-visualizer/audit_data.py)
"""

import pytest
import json
from pathlib import Path
import sys

# Add business-visualizer to path
sys.path.insert(0, str(Path(__file__).parent.parent / "business-visualizer"))

from audit_data import (
    DataConfidence, AuditType, ChartType,
    Metric, Issue, Recommendation, ReportSection, AuditData,
    get_ux_app_sections, get_marketing_sections, get_business_sections,
    get_technical_sections, get_sections_for_type,
    NIELSENS_HEURISTICS, MARKETING_SCORE_CATEGORIES, TECHNICAL_SCORE_CATEGORIES
)


class TestDataConfidence:
    """Tests for DataConfidence enum."""

    @pytest.mark.unit
    def test_confidence_values(self):
        """Test all confidence levels exist."""
        assert DataConfidence.VERIFIED.value == "verified"
        assert DataConfidence.ESTIMATED.value == "estimated"
        assert DataConfidence.PLACEHOLDER.value == "placeholder"

    @pytest.mark.unit
    def test_confidence_from_string(self):
        """Test creating confidence from string value."""
        assert DataConfidence("verified") == DataConfidence.VERIFIED
        assert DataConfidence("estimated") == DataConfidence.ESTIMATED
        assert DataConfidence("placeholder") == DataConfidence.PLACEHOLDER


class TestAuditType:
    """Tests for AuditType enum."""

    @pytest.mark.unit
    def test_audit_types(self):
        """Test all audit types exist."""
        assert AuditType.UX_APP.value == "ux_app"
        assert AuditType.MARKETING.value == "marketing"
        assert AuditType.BUSINESS.value == "business"
        assert AuditType.TECHNICAL.value == "technical"
        assert AuditType.CUSTOM.value == "custom"


class TestMetric:
    """Tests for Metric dataclass."""

    @pytest.mark.unit
    def test_metric_creation_minimal(self):
        """Test creating metric with minimal fields."""
        metric = Metric(id="signups", name="Signups", value=1000)

        assert metric.id == "signups"
        assert metric.name == "Signups"
        assert metric.value == 1000
        assert metric.category == "general"
        assert metric.confidence == DataConfidence.PLACEHOLDER

    @pytest.mark.unit
    def test_metric_creation_full(self):
        """Test creating metric with all fields."""
        metric = Metric(
            id="cac",
            name="Customer Acquisition Cost",
            value=45.50,
            category="financial",
            unit="$",
            previous_value=52.00,
            target_value=40.00,
            rate=None,
            dropoff=None,
            confidence=DataConfidence.VERIFIED,
            source="database",
            chart_type=ChartType.METRIC,
            order=1
        )

        assert metric.value == 45.50
        assert metric.unit == "$"
        assert metric.previous_value == 52.00
        assert metric.confidence == DataConfidence.VERIFIED

    @pytest.mark.unit
    def test_metric_to_dict(self):
        """Test metric serialization."""
        metric = Metric(id="test", name="Test Metric", value=100, category="funnel")
        data = metric.to_dict()

        assert data['id'] == "test"
        assert data['value'] == 100
        assert data['category'] == "funnel"
        assert data['confidence'] == "placeholder"
        assert data['chart_type'] == "metric"

    @pytest.mark.unit
    def test_metric_from_dict(self):
        """Test metric deserialization."""
        data = {
            'id': 'revenue',
            'name': 'Monthly Revenue',
            'value': 50000,
            'category': 'financial',
            'unit': '$',
            'confidence': 'verified'
        }
        metric = Metric.from_dict(data)

        assert metric.id == "revenue"
        assert metric.value == 50000
        assert metric.confidence == DataConfidence.VERIFIED

    @pytest.mark.unit
    def test_funnel_metric(self):
        """Test creating a funnel metric with rate and dropoff."""
        metric = Metric(
            id="email_verified",
            name="Email Verified",
            value=1543,
            category="funnel",
            rate=76.7,
            dropoff=23.3
        )

        assert metric.rate == 76.7
        assert metric.dropoff == 23.3


class TestIssue:
    """Tests for Issue dataclass."""

    @pytest.mark.unit
    def test_issue_creation(self):
        """Test creating an issue."""
        issue = Issue(
            id="ux-001",
            title="Confusing Navigation",
            description="Users struggle to find settings",
            category="ux",
            severity="high",
            impact="30% users abandon settings search"
        )

        assert issue.id == "ux-001"
        assert issue.severity == "high"
        assert issue.enabled is True

    @pytest.mark.unit
    def test_issue_to_dict(self):
        """Test issue serialization."""
        issue = Issue(
            id="test-001",
            title="Test Issue",
            description="Test description",
            severity="critical"
        )
        data = issue.to_dict()

        assert data['severity'] == "critical"
        assert data['enabled'] is True

    @pytest.mark.unit
    def test_issue_from_dict(self):
        """Test issue deserialization."""
        data = {
            'id': 'sec-001',
            'title': 'SQL Injection Vulnerability',
            'description': 'Login form is vulnerable',
            'category': 'security',
            'severity': 'critical',
            'enabled': False
        }
        issue = Issue.from_dict(data)

        assert issue.category == "security"
        assert issue.enabled is False


class TestRecommendation:
    """Tests for Recommendation dataclass."""

    @pytest.mark.unit
    def test_recommendation_creation(self):
        """Test creating a recommendation."""
        rec = Recommendation(
            id="rec-001",
            title="Add Progress Indicators",
            description="Show users where they are in the flow",
            category="ux",
            priority=1,
            impact="Reduce dropoff by 15%",
            effort="Low",
            code_snippet="<ProgressBar step={currentStep} />"
        )

        assert rec.priority == 1
        assert rec.code_snippet is not None

    @pytest.mark.unit
    def test_recommendation_with_related_issues(self):
        """Test recommendation with related issues."""
        rec = Recommendation(
            id="rec-002",
            title="Improve Error Messages",
            description="Make errors user-friendly",
            related_issue_ids=["ux-001", "ux-003"]
        )

        assert len(rec.related_issue_ids) == 2
        assert "ux-001" in rec.related_issue_ids

    @pytest.mark.unit
    def test_recommendation_serialization(self):
        """Test recommendation to/from dict."""
        rec = Recommendation(
            id="test",
            title="Test Rec",
            description="Test",
            priority=2
        )
        data = rec.to_dict()
        restored = Recommendation.from_dict(data)

        assert restored.id == rec.id
        assert restored.priority == rec.priority


class TestReportSection:
    """Tests for ReportSection dataclass."""

    @pytest.mark.unit
    def test_section_creation(self):
        """Test creating a report section."""
        section = ReportSection(
            id="executive",
            title="Executive Summary",
            description="High-level overview",
            content_type="markdown",
            order=1
        )

        assert section.id == "executive"
        assert section.enabled is True

    @pytest.mark.unit
    def test_section_with_custom_content(self):
        """Test section with custom content."""
        section = ReportSection(
            id="custom",
            title="Custom Section",
            content_type="custom",
            custom_content="<h1>My Custom HTML</h1>"
        )

        assert section.content_type == "custom"
        assert "<h1>" in section.custom_content


class TestAuditData:
    """Tests for the main AuditData class."""

    @pytest.mark.unit
    def test_audit_data_creation(self):
        """Test creating AuditData with minimal fields."""
        data = AuditData(name="MyApp")

        assert data.name == "MyApp"
        assert data.audit_type == AuditType.CUSTOM
        assert len(data.metrics) == 0
        assert len(data.issues) == 0
        assert len(data.recommendations) == 0

    @pytest.mark.unit
    def test_add_metric(self):
        """Test adding metrics to AuditData."""
        data = AuditData(name="TestApp")
        metric = Metric(id="users", name="Total Users", value=5000)

        data.add_metric(metric)

        assert len(data.metrics) == 1
        assert data.metrics[0].value == 5000

    @pytest.mark.unit
    def test_add_issue(self):
        """Test adding issues to AuditData."""
        data = AuditData(name="TestApp")
        issue = Issue(id="bug-001", title="Bug", description="A bug")

        data.add_issue(issue)

        assert len(data.issues) == 1

    @pytest.mark.unit
    def test_add_recommendation(self):
        """Test adding recommendations to AuditData."""
        data = AuditData(name="TestApp")
        rec = Recommendation(id="rec-001", title="Rec", description="A rec")

        data.add_recommendation(rec)

        assert len(data.recommendations) == 1

    @pytest.mark.unit
    def test_get_metrics_by_category(self):
        """Test filtering metrics by category."""
        data = AuditData(name="TestApp")
        data.add_metric(Metric(id="m1", name="M1", value=100, category="funnel", order=1))
        data.add_metric(Metric(id="m2", name="M2", value=200, category="financial", order=1))
        data.add_metric(Metric(id="m3", name="M3", value=300, category="funnel", order=2))

        funnel_metrics = data.get_metrics_by_category("funnel")

        assert len(funnel_metrics) == 2
        assert funnel_metrics[0].id == "m1"  # Sorted by order

    @pytest.mark.unit
    def test_get_funnel_metrics(self):
        """Test convenience method for funnel metrics."""
        data = AuditData(name="TestApp")
        data.add_metric(Metric(id="signup", name="Signup", value=1000, category="funnel"))
        data.add_metric(Metric(id="other", name="Other", value=500, category="engagement"))

        funnel = data.get_funnel_metrics()

        assert len(funnel) == 1
        assert funnel[0].category == "funnel"

    @pytest.mark.unit
    def test_get_issues_by_severity(self):
        """Test filtering issues by severity."""
        data = AuditData(name="TestApp")
        data.add_issue(Issue(id="i1", title="I1", description="", severity="critical"))
        data.add_issue(Issue(id="i2", title="I2", description="", severity="low"))
        data.add_issue(Issue(id="i3", title="I3", description="", severity="critical"))

        critical = data.get_issues_by_severity("critical")

        assert len(critical) == 2

    @pytest.mark.unit
    def test_get_enabled_issues(self):
        """Test getting only enabled issues."""
        data = AuditData(name="TestApp")
        data.add_issue(Issue(id="i1", title="I1", description="", enabled=True))
        data.add_issue(Issue(id="i2", title="I2", description="", enabled=False))

        enabled = data.get_enabled_issues()

        assert len(enabled) == 1
        assert enabled[0].id == "i1"

    @pytest.mark.unit
    def test_get_enabled_recommendations(self):
        """Test getting enabled recommendations sorted by priority."""
        data = AuditData(name="TestApp")
        data.add_recommendation(Recommendation(id="r1", title="R1", description="", priority=3))
        data.add_recommendation(Recommendation(id="r2", title="R2", description="", priority=1))
        data.add_recommendation(Recommendation(id="r3", title="R3", description="", priority=2, enabled=False))

        enabled = data.get_enabled_recommendations()

        assert len(enabled) == 2
        assert enabled[0].priority == 1  # Sorted by priority

    @pytest.mark.unit
    def test_validation_empty_name(self):
        """Test validation catches empty name."""
        data = AuditData(name="")
        errors = data.validate()

        assert len(errors) > 0
        assert "name" in errors[0].lower()

    @pytest.mark.unit
    def test_validation_negative_metric(self):
        """Test validation catches negative metric values."""
        data = AuditData(name="TestApp")
        data.add_metric(Metric(id="m1", name="Bad Metric", value=-100))

        errors = data.validate()

        assert len(errors) > 0
        assert "negative" in errors[0].lower()

    @pytest.mark.unit
    def test_validation_invalid_priority(self):
        """Test validation catches invalid priority."""
        data = AuditData(name="TestApp")
        data.add_recommendation(Recommendation(id="r1", title="R1", description="", priority=0))

        errors = data.validate()

        assert len(errors) > 0
        assert "priority" in errors[0].lower()

    @pytest.mark.unit
    def test_calculate_confidence_all_verified(self):
        """Test confidence calculation with all verified data."""
        data = AuditData(name="TestApp")
        data.add_metric(Metric(id="m1", name="M1", value=100, confidence=DataConfidence.VERIFIED))
        data.add_metric(Metric(id="m2", name="M2", value=200, confidence=DataConfidence.VERIFIED))

        confidence = data.calculate_confidence()

        assert confidence == DataConfidence.VERIFIED

    @pytest.mark.unit
    def test_calculate_confidence_mixed(self):
        """Test confidence calculation with mixed data."""
        data = AuditData(name="TestApp")
        data.add_metric(Metric(id="m1", name="M1", value=100, confidence=DataConfidence.VERIFIED))
        data.add_metric(Metric(id="m2", name="M2", value=200, confidence=DataConfidence.PLACEHOLDER))

        confidence = data.calculate_confidence()

        assert confidence == DataConfidence.ESTIMATED

    @pytest.mark.unit
    def test_calculate_confidence_all_placeholder(self):
        """Test confidence calculation with all placeholder data."""
        data = AuditData(name="TestApp")
        data.add_metric(Metric(id="m1", name="M1", value=100, confidence=DataConfidence.PLACEHOLDER))

        confidence = data.calculate_confidence()

        assert confidence == DataConfidence.PLACEHOLDER

    @pytest.mark.unit
    def test_to_dict_full(self):
        """Test full serialization of AuditData."""
        data = AuditData(
            name="MyApp",
            audit_type=AuditType.UX_APP,
            tagline="Test App",
            company_name="TestCo"
        )
        data.add_metric(Metric(id="m1", name="M1", value=100))
        data.add_issue(Issue(id="i1", title="I1", description="D1"))
        data.scores = {"usability": 8}

        result = data.to_dict()

        assert result['name'] == "MyApp"
        assert result['audit_type'] == "ux_app"
        assert len(result['metrics']) == 1
        assert len(result['issues']) == 1
        assert result['scores']['usability'] == 8

    @pytest.mark.unit
    def test_from_dict_full(self):
        """Test full deserialization of AuditData."""
        source = {
            'name': 'RestoredApp',
            'audit_type': 'marketing',
            'tagline': 'Restored',
            'metrics': [{'id': 'm1', 'name': 'M1', 'value': 500}],
            'issues': [],
            'recommendations': [],
            'sections': [],
            'scores': {'awareness': 7}
        }

        data = AuditData.from_dict(source)

        assert data.name == "RestoredApp"
        assert data.audit_type == AuditType.MARKETING
        assert len(data.metrics) == 1
        assert data.scores['awareness'] == 7

    @pytest.mark.unit
    def test_json_round_trip(self):
        """Test JSON serialization and deserialization."""
        original = AuditData(
            name="JSONTest",
            audit_type=AuditType.TECHNICAL,
            executive_summary="Test summary"
        )
        original.add_metric(Metric(id="perf", name="Performance", value=95))

        json_str = original.to_json()
        restored = AuditData.from_json(json_str)

        assert restored.name == original.name
        assert restored.audit_type == original.audit_type
        assert len(restored.metrics) == 1


class TestAuditTemplates:
    """Tests for audit template functions."""

    @pytest.mark.unit
    def test_ux_app_sections(self):
        """Test UX app sections template."""
        sections = get_ux_app_sections()

        assert len(sections) > 0
        assert any(s.id == "executive" for s in sections)
        assert any(s.id == "recommendations" for s in sections)

    @pytest.mark.unit
    def test_marketing_sections(self):
        """Test marketing sections template."""
        sections = get_marketing_sections()

        assert len(sections) > 0
        assert any(s.id == "channels" for s in sections)

    @pytest.mark.unit
    def test_business_sections(self):
        """Test business sections template."""
        sections = get_business_sections()

        assert len(sections) > 0
        assert any(s.id == "revenue" for s in sections)

    @pytest.mark.unit
    def test_technical_sections(self):
        """Test technical sections template."""
        sections = get_technical_sections()

        assert len(sections) > 0
        assert any(s.id == "security" for s in sections)

    @pytest.mark.unit
    def test_get_sections_for_type(self):
        """Test getting sections by audit type."""
        ux_sections = get_sections_for_type(AuditType.UX_APP)
        custom_sections = get_sections_for_type(AuditType.CUSTOM)

        assert len(ux_sections) > 0
        assert len(custom_sections) == 0  # Custom has no default sections


class TestScoringTemplates:
    """Tests for scoring template constants."""

    @pytest.mark.unit
    def test_nielsens_heuristics(self):
        """Test Nielsen's heuristics list."""
        assert len(NIELSENS_HEURISTICS) == 10
        assert "Visibility of System Status" in NIELSENS_HEURISTICS
        assert "Error Prevention" in NIELSENS_HEURISTICS

    @pytest.mark.unit
    def test_marketing_categories(self):
        """Test marketing score categories."""
        assert len(MARKETING_SCORE_CATEGORIES) == 10
        assert "Brand Awareness" in MARKETING_SCORE_CATEGORIES

    @pytest.mark.unit
    def test_technical_categories(self):
        """Test technical score categories."""
        assert len(TECHNICAL_SCORE_CATEGORIES) == 10
        assert "Security" in TECHNICAL_SCORE_CATEGORIES
        assert "Performance" in TECHNICAL_SCORE_CATEGORIES
