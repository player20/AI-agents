"""
Generation Audit Trail

Provides an append-only audit log for all prototype generations.
This enables:
- Debugging failed generations
- Analyzing quality trends over time
- Understanding what types of projects succeed/fail
- Monitoring system health
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class GenerationEvent:
    """A single event in the generation audit trail"""
    timestamp: str
    description: str
    description_hash: str
    event_type: str  # "started", "domain_complete", "quality_enhanced", "success", "failure"
    quality_score: Optional[float] = None
    issues_fixed: Optional[List[str]] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    industry: Optional[str] = None
    entities: Optional[List[str]] = None


class GenerationAuditLog:
    """
    Append-only audit log for all generations.

    Uses JSONL format (one JSON object per line) for efficient appending
    without needing to parse the entire file.
    """

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path(__file__).parent.parent.parent / "data"
        self.log_file = self.log_dir / "generation_audit.jsonl"
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Ensure the log directory exists"""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create audit log directory: {e}")

    def _hash_description(self, description: str) -> str:
        """Create a short hash for the description"""
        normalized = " ".join(description.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:12]

    def record(self, event: GenerationEvent) -> None:
        """Record a generation event to the audit log"""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(event)) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")

    def record_start(
        self,
        description: str,
        industry: Optional[str] = None,
        entities: Optional[List[str]] = None
    ) -> None:
        """Record the start of a generation"""
        event = GenerationEvent(
            timestamp=datetime.utcnow().isoformat(),
            description=description[:200],  # Truncate for storage
            description_hash=self._hash_description(description),
            event_type="started",
            industry=industry,
            entities=entities[:5] if entities else None,
        )
        self.record(event)

    def record_quality(
        self,
        description: str,
        quality_score: float,
        issues_fixed: Optional[List[str]] = None,
        enhanced: bool = False
    ) -> None:
        """Record quality evaluation results"""
        event = GenerationEvent(
            timestamp=datetime.utcnow().isoformat(),
            description=description[:200],
            description_hash=self._hash_description(description),
            event_type="quality_enhanced" if enhanced else "quality_evaluated",
            quality_score=quality_score,
            issues_fixed=issues_fixed,
        )
        self.record(event)

    def record_success(
        self,
        description: str,
        quality_score: float,
        duration_ms: int,
        industry: Optional[str] = None
    ) -> None:
        """Record a successful generation"""
        event = GenerationEvent(
            timestamp=datetime.utcnow().isoformat(),
            description=description[:200],
            description_hash=self._hash_description(description),
            event_type="success",
            quality_score=quality_score,
            duration_ms=duration_ms,
            industry=industry,
        )
        self.record(event)

    def record_failure(
        self,
        description: str,
        error: str,
        duration_ms: int
    ) -> None:
        """Record a failed generation"""
        event = GenerationEvent(
            timestamp=datetime.utcnow().isoformat(),
            description=description[:200],
            description_hash=self._hash_description(description),
            event_type="failure",
            error=error[:500],  # Truncate error message
            duration_ms=duration_ms,
        )
        self.record(event)

    def get_recent(self, limit: int = 100) -> List[GenerationEvent]:
        """
        Get the most recent generation events.

        Uses efficient tail reading for large files.
        """
        events = []
        try:
            if not self.log_file.exists():
                return events

            # Read all lines (for small files, this is efficient enough)
            # For very large files, we could use a more efficient tail algorithm
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Take last N lines
            recent_lines = lines[-limit:] if len(lines) > limit else lines

            for line in recent_lines:
                try:
                    data = json.loads(line.strip())
                    events.append(GenerationEvent(**data))
                except (json.JSONDecodeError, TypeError) as e:
                    logger.debug(f"Skipping malformed log line: {e}")

        except Exception as e:
            logger.warning(f"Failed to read audit log: {e}")

        return events

    def get_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get quality and success trends over time.

        Returns daily aggregates of:
        - Average quality score
        - Success rate
        - Generation count
        - Common industries
        """
        events = self.get_recent(limit=10000)  # Last 10k events

        if not events:
            return {
                "daily_averages": {},
                "total_generations": 0,
                "success_rate": 0.0,
                "industry_distribution": {},
            }

        # Group by day
        daily_scores: Dict[str, List[float]] = defaultdict(list)
        daily_successes: Dict[str, int] = defaultdict(int)
        daily_failures: Dict[str, int] = defaultdict(int)
        industry_counts: Dict[str, int] = defaultdict(int)

        for event in events:
            day = event.timestamp[:10]  # YYYY-MM-DD

            if event.quality_score is not None:
                daily_scores[day].append(event.quality_score)

            if event.event_type == "success":
                daily_successes[day] += 1
                if event.industry:
                    industry_counts[event.industry] += 1
            elif event.event_type == "failure":
                daily_failures[day] += 1

        # Calculate daily averages
        daily_averages = {}
        for day in sorted(daily_scores.keys())[-days:]:
            scores = daily_scores[day]
            successes = daily_successes[day]
            failures = daily_failures[day]
            total = successes + failures

            daily_averages[day] = {
                "avg_quality_score": round(sum(scores) / len(scores), 3) if scores else 0,
                "success_rate": round(successes / total, 3) if total > 0 else 0,
                "total_generations": total,
            }

        # Overall stats
        total_success = sum(daily_successes.values())
        total_failure = sum(daily_failures.values())
        total = total_success + total_failure

        return {
            "daily_averages": daily_averages,
            "total_generations": total,
            "success_rate": round(total_success / total, 3) if total > 0 else 0,
            "industry_distribution": dict(
                sorted(industry_counts.items(), key=lambda x: -x[1])[:10]
            ),
        }

    def get_failures(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent failures for debugging"""
        events = self.get_recent(limit=500)
        failures = [
            {
                "timestamp": e.timestamp,
                "description": e.description,
                "error": e.error,
                "duration_ms": e.duration_ms,
            }
            for e in events
            if e.event_type == "failure"
        ]
        return failures[-limit:]


# Singleton instance
_audit_log: Optional[GenerationAuditLog] = None


def get_audit_log() -> GenerationAuditLog:
    """Get the singleton audit log instance"""
    global _audit_log
    if _audit_log is None:
        _audit_log = GenerationAuditLog()
    return _audit_log
