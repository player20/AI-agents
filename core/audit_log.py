"""
Audit logging for self-improvement operations.
Append-only JSONL format for traceability and compound improvement tracking.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Log file location - relative to project root
AUDIT_FILE = Path(__file__).parent.parent / "logs" / "self_improvement_audit.jsonl"


def log_improvement(
    action: str,
    details: dict,
    git_commit: Optional[str] = None,
    git_branch: Optional[str] = None
) -> dict:
    """
    Append an improvement event to the audit log.

    Args:
        action: Type of action (e.g., "start", "complete", "rollback")
        details: Dictionary of action-specific details
        git_commit: Git commit hash if applicable
        git_branch: Git branch name if applicable

    Returns:
        The logged entry
    """
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "details": details,
        "git_commit": git_commit,
        "git_branch": git_branch
    }

    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def get_recent_improvements(limit: int = 10) -> list[dict]:
    """
    Read recent improvement events from the audit log.

    Args:
        limit: Maximum number of entries to return (most recent first)

    Returns:
        List of improvement entries, newest first
    """
    if not AUDIT_FILE.exists():
        return []

    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = [json.loads(line) for line in lines if line.strip()]
    return entries[-limit:][::-1]  # Return newest first


def get_improvement_stats() -> dict:
    """
    Calculate statistics about self-improvement runs.
    Useful for tracking compound improvement over time.

    Returns:
        Dictionary with stats (total runs, success rate, etc.)
    """
    if not AUDIT_FILE.exists():
        return {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "success_rate": 0.0,
            "last_run": None
        }

    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = [json.loads(line) for line in lines if line.strip()]

    starts = [e for e in entries if e["action"] == "self_improve_start"]
    completes = [e for e in entries if e["action"] == "self_improve_complete"]
    failures = [e for e in entries if e["action"] == "self_improve_failed"]

    total = len(starts)
    successful = len(completes)
    failed = len(failures)

    return {
        "total_runs": total,
        "successful_runs": successful,
        "failed_runs": failed,
        "success_rate": (successful / total * 100) if total > 0 else 0.0,
        "last_run": entries[-1]["timestamp"] if entries else None
    }


def clear_audit_log() -> bool:
    """
    Clear the audit log. Use with caution - for testing only.

    Returns:
        True if cleared, False if file didn't exist
    """
    if AUDIT_FILE.exists():
        AUDIT_FILE.unlink()
        return True
    return False
