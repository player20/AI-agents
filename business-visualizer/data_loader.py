"""
Data Loader for Weaver Pro Audit Reports

This module provides functions to load audit data from various sources:
- CSV import (client-provided metrics)
- JSON import (saved configurations)
- Default templates for different audit types

Works with ANY business type - the system is fully modular.
"""

import csv
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from audit_data import (
    AuditData,
    AuditType,
    Metric,
    Issue,
    Recommendation,
    ReportSection,
    DataConfidence,
    ChartType,
    get_sections_for_type,
    NIELSENS_HEURISTICS,
    MARKETING_SCORE_CATEGORIES,
    TECHNICAL_SCORE_CATEGORIES
)


def load_from_csv(csv_path: str, name: str = "", audit_type: AuditType = AuditType.CUSTOM) -> AuditData:
    """
    Load audit data from a client-provided CSV file.

    Flexible CSV format - recognizes different metric types:

    metric_type,name,value,category,unit
    funnel,Signup,2012,funnel,users
    funnel,Email Verified,1543,funnel,users
    financial,MRR,45000,financial,$
    engagement,DAU,5200,engagement,users

    Args:
        csv_path: Path to the CSV file
        name: Name of the business being audited
        audit_type: Type of audit for default sections

    Returns:
        AuditData with verified confidence for imported metrics
    """
    data = AuditData(
        name=name,
        audit_type=audit_type,
        sections=get_sections_for_type(audit_type)
    )
    data.data_sources.append(f"CSV import: {csv_path}")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        order = 0
        for row in reader:
            metric = Metric(
                id=f"csv_{order}",
                name=row.get('name', ''),
                value=float(row.get('value', 0)),
                category=row.get('category', row.get('metric_type', 'general')),
                unit=row.get('unit', ''),
                rate=float(row['rate']) if row.get('rate') else None,
                dropoff=float(row['dropoff']) if row.get('dropoff') else None,
                confidence=DataConfidence.VERIFIED,
                source="csv_import",
                order=order
            )
            data.add_metric(metric)
            order += 1

    # Calculate rates for funnel metrics if not provided
    _calculate_funnel_rates(data)

    data.overall_confidence = data.calculate_confidence()
    return data


def load_from_json(json_path: str) -> AuditData:
    """
    Load audit data from a saved JSON configuration.

    Args:
        json_path: Path to the JSON file

    Returns:
        AuditData deserialized from JSON
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    return AuditData.from_dict(raw)


def save_to_json(data: AuditData, json_path: str) -> str:
    """
    Save audit data to a JSON file.

    Args:
        data: AuditData to save
        json_path: Path for the output file

    Returns:
        Path to the saved file
    """
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(data.to_json())
    return json_path


def create_audit(
    name: str,
    audit_type: AuditType = AuditType.CUSTOM,
    include_samples: bool = False
) -> AuditData:
    """
    Create a new audit with the appropriate template.

    This is the main entry point for creating new audits.
    It sets up the correct sections and optionally includes sample data.

    Args:
        name: Name of the business/app being audited
        audit_type: Type of audit (determines default sections)
        include_samples: If True, include sample issues and recommendations

    Returns:
        AuditData configured for the specified audit type
    """
    data = AuditData(
        name=name,
        audit_type=audit_type,
        audit_date=datetime.now().strftime("%B %Y"),
        sections=get_sections_for_type(audit_type),
        overall_confidence=DataConfidence.PLACEHOLDER
    )

    # Set up default scores based on audit type
    if audit_type == AuditType.UX_APP:
        data.scores = {h: 5 for h in NIELSENS_HEURISTICS}
    elif audit_type == AuditType.MARKETING:
        data.scores = {c: 5 for c in MARKETING_SCORE_CATEGORIES}
    elif audit_type == AuditType.TECHNICAL:
        data.scores = {c: 5 for c in TECHNICAL_SCORE_CATEGORIES}

    if include_samples:
        _add_sample_data(data, audit_type)

    return data


def _add_sample_data(data: AuditData, audit_type: AuditType):
    """Add sample metrics, issues, and recommendations based on audit type."""

    if audit_type == AuditType.UX_APP:
        # Sample funnel metrics
        data.metrics = [
            Metric("m1", "Signup", 1000, "funnel", "users", rate=100, order=1),
            Metric("m2", "Email Verified", 700, "funnel", "users", rate=70, dropoff=30, order=2),
            Metric("m3", "Profile Complete", 400, "funnel", "users", rate=40, dropoff=43, order=3),
            Metric("m4", "First Action", 100, "funnel", "users", rate=10, dropoff=75, order=4),
        ]
        data.issues = [
            Issue("i1", "No Email Verification Reminder", "Users who don't verify receive no follow-up", "ux", "high", "30% drop-off at verification"),
            Issue("i2", "Complex Signup Form", "Too many required fields", "ux", "medium", "Form abandonment"),
        ]
        data.recommendations = [
            Recommendation("r1", "Add Email Reminders", "Send automated verification reminders", "ux", 1, "Recover 20-30% of users", "Low"),
            Recommendation("r2", "Simplify Signup", "Reduce required fields", "ux", 2, "15-20% less abandonment", "Medium"),
        ]

    elif audit_type == AuditType.MARKETING:
        data.metrics = [
            Metric("m1", "Website Visitors", 50000, "traffic", "visitors/mo", order=1),
            Metric("m2", "Lead Conversion Rate", 2.5, "conversion", "%", order=2),
            Metric("m3", "CAC", 85, "financial", "$", order=3),
            Metric("m4", "MRR", 45000, "financial", "$", order=4),
        ]
        data.issues = [
            Issue("i1", "Low Email Open Rate", "Email campaigns averaging 12% open rate", "marketing", "high", "Industry avg is 21%"),
            Issue("i2", "High CAC", "Customer acquisition cost above industry benchmark", "marketing", "medium", "$85 vs $50 benchmark"),
        ]
        data.recommendations = [
            Recommendation("r1", "Improve Email Subject Lines", "A/B test subject lines", "marketing", 1, "Increase opens by 30-50%", "Low"),
            Recommendation("r2", "Optimize Ad Targeting", "Refine audience segments", "marketing", 2, "Reduce CAC by 20-30%", "Medium"),
        ]

    elif audit_type == AuditType.BUSINESS:
        data.metrics = [
            Metric("m1", "Monthly Revenue", 125000, "financial", "$", order=1),
            Metric("m2", "Gross Margin", 65, "financial", "%", order=2),
            Metric("m3", "Customer LTV", 850, "customers", "$", order=3),
            Metric("m4", "Churn Rate", 5.2, "customers", "%", order=4),
        ]
        data.issues = [
            Issue("i1", "High Churn Rate", "Monthly churn exceeds industry benchmark", "business", "critical", "5.2% vs 3% benchmark"),
            Issue("i2", "Limited Revenue Streams", "Single product dependency", "business", "high", "95% revenue from one product"),
        ]
        data.recommendations = [
            Recommendation("r1", "Implement Retention Program", "Add loyalty features and proactive support", "business", 1, "Reduce churn by 30%", "Medium"),
            Recommendation("r2", "Diversify Revenue", "Introduce complementary products", "business", 2, "Add 20% revenue stream", "High"),
        ]

    elif audit_type == AuditType.TECHNICAL:
        data.metrics = [
            Metric("m1", "Page Load Time", 3.2, "performance", "seconds", order=1),
            Metric("m2", "API Response Time", 450, "performance", "ms", order=2),
            Metric("m3", "Uptime", 99.5, "reliability", "%", order=3),
            Metric("m4", "Test Coverage", 45, "quality", "%", order=4),
        ]
        data.issues = [
            Issue("i1", "Slow Page Load", "Homepage takes 3.2s to load", "technical", "high", "Target is under 2s"),
            Issue("i2", "Low Test Coverage", "Only 45% of code has tests", "technical", "medium", "Target is 80%"),
        ]
        data.recommendations = [
            Recommendation("r1", "Optimize Images", "Implement lazy loading and compression", "technical", 1, "Reduce load time by 40%", "Low"),
            Recommendation("r2", "Increase Test Coverage", "Add unit tests for critical paths", "technical", 2, "Reach 80% coverage", "High"),
        ]


def _calculate_funnel_rates(data: AuditData):
    """Calculate rates and dropoffs for funnel metrics if not provided."""
    funnel_metrics = data.get_funnel_metrics()
    if not funnel_metrics:
        return

    # Sort by order
    funnel_metrics = sorted(funnel_metrics, key=lambda x: x.order)

    if funnel_metrics[0].value == 0:
        return

    first_value = funnel_metrics[0].value
    funnel_metrics[0].rate = 100
    funnel_metrics[0].dropoff = 0

    for i in range(1, len(funnel_metrics)):
        if funnel_metrics[i].rate is None:
            funnel_metrics[i].rate = round((funnel_metrics[i].value / first_value) * 100, 1)

        if funnel_metrics[i].dropoff is None:
            prev_value = funnel_metrics[i-1].value
            if prev_value > 0:
                funnel_metrics[i].dropoff = round(
                    ((prev_value - funnel_metrics[i].value) / prev_value) * 100, 1
                )


def merge_csv_into_data(data: AuditData, csv_path: str) -> AuditData:
    """
    Merge CSV metrics into existing AuditData.

    This allows updating specific metrics without losing other data.
    """
    csv_data = load_from_csv(csv_path, data.name, data.audit_type)

    # Add or update metrics from CSV
    existing_names = {m.name for m in data.metrics}
    for metric in csv_data.metrics:
        if metric.name in existing_names:
            # Update existing metric
            for i, m in enumerate(data.metrics):
                if m.name == metric.name:
                    data.metrics[i] = metric
                    break
        else:
            # Add new metric
            data.add_metric(metric)

    # Update data sources
    data.data_sources.extend(csv_data.data_sources)
    data.overall_confidence = data.calculate_confidence()

    return data


# --- TEMPLATE FUNCTIONS FOR QUICK START ---

def create_ux_audit(name: str, include_samples: bool = False) -> AuditData:
    """Shortcut to create a UX/App audit."""
    return create_audit(name, AuditType.UX_APP, include_samples)


def create_marketing_audit(name: str, include_samples: bool = False) -> AuditData:
    """Shortcut to create a Marketing audit."""
    return create_audit(name, AuditType.MARKETING, include_samples)


def create_business_audit(name: str, include_samples: bool = False) -> AuditData:
    """Shortcut to create a Business Model audit."""
    return create_audit(name, AuditType.BUSINESS, include_samples)


def create_technical_audit(name: str, include_samples: bool = False) -> AuditData:
    """Shortcut to create a Technical audit."""
    return create_audit(name, AuditType.TECHNICAL, include_samples)


def create_custom_audit(name: str) -> AuditData:
    """Create a blank custom audit with no pre-defined sections."""
    return create_audit(name, AuditType.CUSTOM, include_samples=False)
