"""
Analytics Data Parser for Weaver Pro

Parses analytics exports from various sources:
- Google Analytics 4 (CSV export)
- Lighthouse (JSON report)
- Firebase (JSON export)
- Search Console (CSV export)

Usage:
    from core.analytics_parser import parse_analytics_file

    with open('ga4-export.csv', 'rb') as f:
        data = parse_analytics_file(f.read(), 'ga4-export.csv')

    print(data.source)   # 'ga4'
    print(data.metrics)  # {'total_users': 45230, 'bounce_rate': 67.2, ...}
"""

import json
import csv
import io
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class AnalyticsData:
    """Container for parsed analytics data"""
    source: str  # 'ga4', 'lighthouse', 'firebase', 'search_console'
    metrics: Dict[str, Any]
    raw_data: Any = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'source': self.source,
            'metrics': self.metrics,
            # Exclude raw_data from serialization (can be large)
        }


def detect_format(data: bytes, filename: str) -> str:
    """
    Auto-detect analytics export format from file content and name.

    Args:
        data: Raw file bytes
        filename: Original filename (for extension detection)

    Returns:
        Format identifier: 'ga4', 'lighthouse', 'firebase', 'search_console', or 'unknown'
    """
    ext = filename.split('.')[-1].lower()

    # JSON formats
    if ext == 'json':
        try:
            parsed = json.loads(data.decode('utf-8'))

            # Lighthouse report
            if 'lighthouseVersion' in parsed or 'lhr' in parsed:
                return 'lighthouse'

            # Firebase export
            if 'events' in parsed or 'user_properties' in parsed:
                return 'firebase'

            # GA4 API response
            if 'dimensionHeaders' in parsed or 'rows' in parsed:
                return 'ga4_api'

        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    # CSV formats
    if ext == 'csv':
        try:
            first_lines = data.decode('utf-8').split('\n')[:3]
            header = first_lines[0].lower() if first_lines else ''

            # GA4 CSV export
            if any(term in header for term in ['sessions', 'users', 'pageviews', 'bounce']):
                return 'ga4'

            # Search Console export
            if 'clicks' in header and 'impressions' in header:
                return 'search_console'

        except UnicodeDecodeError:
            pass

    return 'unknown'


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float"""
    if value is None:
        return default
    try:
        # Handle percentage strings like "67.5%"
        if isinstance(value, str):
            value = value.replace('%', '').replace(',', '').strip()
        return float(value)
    except (ValueError, TypeError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int"""
    if value is None:
        return default
    try:
        if isinstance(value, str):
            value = value.replace(',', '').strip()
        return int(float(value))
    except (ValueError, TypeError):
        return default


def _calculate_avg(rows: List[Dict], field: str) -> float:
    """Calculate average of a numeric field across rows"""
    values = [_safe_float(r.get(field)) for r in rows if r.get(field)]
    return sum(values) / len(values) if values else 0.0


def _extract_top(rows: List[Dict], key_field: str, value_field: str, limit: int = 10) -> List[Dict]:
    """Extract top N items by value"""
    items = {}
    for row in rows:
        key = row.get(key_field, 'Unknown')
        value = _safe_int(row.get(value_field, 0))
        items[key] = items.get(key, 0) + value

    sorted_items = sorted(items.items(), key=lambda x: x[1], reverse=True)
    return [{'name': k, 'value': v} for k, v in sorted_items[:limit]]


def parse_ga4_csv(data: bytes) -> AnalyticsData:
    """
    Parse Google Analytics 4 CSV export.

    Expected columns: Date, Users, Sessions, Bounce Rate, Avg. Session Duration,
                     Page path, Source, Medium, etc.
    """
    try:
        text = data.decode('utf-8')
        # Skip BOM if present
        if text.startswith('\ufeff'):
            text = text[1:]

        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)

        if not rows:
            return AnalyticsData(source='ga4', metrics={'error': 'No data rows found'})

        # Normalize column names (GA4 exports vary)
        normalized_rows = []
        for row in rows:
            normalized = {}
            for key, value in row.items():
                # Normalize common variations
                norm_key = key.lower().strip()
                normalized[norm_key] = value
                normalized[key] = value  # Keep original too
            normalized_rows.append(normalized)

        # Extract metrics with flexible column matching
        def find_column(patterns: List[str]) -> Optional[str]:
            """Find first matching column, returns None if not found"""
            if not normalized_rows:
                return None
            for key in normalized_rows[0].keys():
                key_lower = key.lower()
                for pattern in patterns:
                    if pattern in key_lower:
                        return key
            return None

        users_col = find_column(['users', 'total users', 'active users'])
        sessions_col = find_column(['sessions', 'total sessions'])
        bounce_col = find_column(['bounce rate', 'bounce_rate', 'bounces'])
        duration_col = find_column(['session duration', 'avg. session duration', 'average session'])
        page_col = find_column(['page path', 'page', 'page title', 'landing page'])
        source_col = find_column(['source', 'source / medium', 'traffic source'])

        metrics = {
            'total_users': sum(_safe_int(r.get(users_col)) for r in normalized_rows),
            'total_sessions': sum(_safe_int(r.get(sessions_col)) for r in normalized_rows),
            'bounce_rate': _calculate_avg(normalized_rows, bounce_col),
            'avg_session_duration': _calculate_avg(normalized_rows, duration_col),
            'top_pages': _extract_top(normalized_rows, page_col, users_col, 10),
            'top_sources': _extract_top(normalized_rows, source_col, users_col, 5),
            'row_count': len(normalized_rows),
        }

        return AnalyticsData(source='ga4', metrics=metrics, raw_data=normalized_rows)

    except Exception as e:
        return AnalyticsData(source='ga4', metrics={'error': str(e)})


def parse_lighthouse_json(data: bytes) -> AnalyticsData:
    """
    Parse Lighthouse JSON report.

    Supports both direct reports and PageSpeed Insights API responses.
    """
    try:
        report = json.loads(data.decode('utf-8'))

        # Handle PageSpeed Insights wrapper
        if 'lighthouseResult' in report:
            report = report['lighthouseResult']

        categories = report.get('categories', {})
        audits = report.get('audits', {})

        # Extract category scores (0-1 scale, convert to 0-100)
        metrics = {
            'performance': round(categories.get('performance', {}).get('score', 0) * 100, 1),
            'accessibility': round(categories.get('accessibility', {}).get('score', 0) * 100, 1),
            'best_practices': round(categories.get('best-practices', {}).get('score', 0) * 100, 1),
            'seo': round(categories.get('seo', {}).get('score', 0) * 100, 1),
        }

        # Core Web Vitals
        if 'largest-contentful-paint' in audits:
            metrics['lcp_ms'] = audits['largest-contentful-paint'].get('numericValue', 0)
            metrics['lcp_score'] = audits['largest-contentful-paint'].get('score', 0) * 100

        if 'max-potential-fid' in audits:
            metrics['fid_ms'] = audits['max-potential-fid'].get('numericValue', 0)

        if 'cumulative-layout-shift' in audits:
            metrics['cls'] = audits['cumulative-layout-shift'].get('numericValue', 0)

        if 'first-contentful-paint' in audits:
            metrics['fcp_ms'] = audits['first-contentful-paint'].get('numericValue', 0)

        if 'speed-index' in audits:
            metrics['speed_index'] = audits['speed-index'].get('numericValue', 0)

        if 'total-blocking-time' in audits:
            metrics['tbt_ms'] = audits['total-blocking-time'].get('numericValue', 0)

        # URL analyzed
        metrics['url'] = report.get('finalUrl', report.get('requestedUrl', 'unknown'))

        return AnalyticsData(source='lighthouse', metrics=metrics, raw_data=report)

    except Exception as e:
        return AnalyticsData(source='lighthouse', metrics={'error': str(e)})


def parse_firebase_json(data: bytes) -> AnalyticsData:
    """
    Parse Firebase Analytics JSON export.

    Handles BigQuery export format and direct Firebase console exports.
    """
    try:
        parsed = json.loads(data.decode('utf-8'))

        # Handle array of events
        if isinstance(parsed, list):
            events = parsed
        else:
            events = parsed.get('events', parsed.get('rows', []))

        metrics = {
            'total_events': len(events),
            'event_types': {},
            'user_count': 0,
        }

        # Count event types
        event_counts = {}
        users = set()

        for event in events:
            event_name = event.get('event_name', event.get('name', 'unknown'))
            event_counts[event_name] = event_counts.get(event_name, 0) + 1

            user_id = event.get('user_id', event.get('user_pseudo_id'))
            if user_id:
                users.add(user_id)

        metrics['event_types'] = dict(sorted(
            event_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20])
        metrics['user_count'] = len(users)

        return AnalyticsData(source='firebase', metrics=metrics, raw_data=parsed)

    except Exception as e:
        return AnalyticsData(source='firebase', metrics={'error': str(e)})


def parse_search_console_csv(data: bytes) -> AnalyticsData:
    """
    Parse Google Search Console CSV export.

    Expected columns: Query, Clicks, Impressions, CTR, Position
    """
    try:
        text = data.decode('utf-8')
        if text.startswith('\ufeff'):
            text = text[1:]

        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)

        if not rows:
            return AnalyticsData(source='search_console', metrics={'error': 'No data rows found'})

        # Extract metrics
        total_clicks = sum(_safe_int(r.get('Clicks', 0)) for r in rows)
        total_impressions = sum(_safe_int(r.get('Impressions', 0)) for r in rows)
        avg_position = _calculate_avg(rows, 'Position')

        # Top queries
        top_queries = sorted(rows, key=lambda x: _safe_int(x.get('Clicks', 0)), reverse=True)[:20]

        metrics = {
            'total_clicks': total_clicks,
            'total_impressions': total_impressions,
            'avg_ctr': (total_clicks / total_impressions * 100) if total_impressions > 0 else 0,
            'avg_position': round(avg_position, 1),
            'top_queries': [
                {
                    'query': q.get('Query', q.get('Top queries', 'unknown')),
                    'clicks': _safe_int(q.get('Clicks', 0)),
                    'impressions': _safe_int(q.get('Impressions', 0)),
                    'ctr': _safe_float(q.get('CTR', 0)),
                    'position': _safe_float(q.get('Position', 0)),
                }
                for q in top_queries
            ],
            'query_count': len(rows),
        }

        return AnalyticsData(source='search_console', metrics=metrics, raw_data=rows)

    except Exception as e:
        return AnalyticsData(source='search_console', metrics={'error': str(e)})


def parse_analytics_file(data: bytes, filename: str) -> Optional[AnalyticsData]:
    """
    Main entry point - detect format and parse any supported analytics file.

    Args:
        data: Raw file bytes
        filename: Original filename (for format detection)

    Returns:
        AnalyticsData object with parsed metrics, or None if format unknown
    """
    format_type = detect_format(data, filename)

    parsers = {
        'ga4': parse_ga4_csv,
        'ga4_api': parse_ga4_csv,  # Same parser handles both
        'lighthouse': parse_lighthouse_json,
        'firebase': parse_firebase_json,
        'search_console': parse_search_console_csv,
    }

    parser = parsers.get(format_type)
    if parser:
        return parser(data)

    return None


# Convenience function for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analytics_parser.py <file>")
        sys.exit(1)

    filepath = sys.argv[1]
    with open(filepath, 'rb') as f:
        result = parse_analytics_file(f.read(), filepath)

    if result:
        print(f"Source: {result.source}")
        print(f"Metrics: {json.dumps(result.metrics, indent=2, default=str)}")
    else:
        print("Could not parse file - unknown format")
