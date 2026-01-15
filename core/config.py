"""
Configuration management for Code Weaver Pro
Loads environment variables, paths, and system settings
"""

import os
from pathlib import Path
from typing import Dict, Any
import json

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment and create necessary directories

    Returns:
        Dictionary with all configuration settings
    """

    # Base paths
    base_dir = Path(__file__).parent.parent
    projects_dir = base_dir / "projects"
    exports_dir = base_dir / "exports"
    screenshots_dir = base_dir / "screenshots"
    logs_dir = base_dir / "logs"

    # Create directories if they don't exist
    for directory in [projects_dir, exports_dir, screenshots_dir, logs_dir]:
        directory.mkdir(exist_ok=True)

    # API Keys from environment
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    xai_api_key = os.getenv("XAI_API_KEY")  # Grok API
    hf_token = os.getenv("HF_TOKEN", "")  # Optional

    if not anthropic_api_key and not xai_api_key:
        raise ValueError(
            "Neither ANTHROPIC_API_KEY nor XAI_API_KEY found in environment variables. "
            "Please set at least one API key before running Code Weaver Pro."
        )

    # Model configuration
    model_config = {
        "default_preset": "Grok Code Fast" if xai_api_key else "Speed (All Haiku)",  # Use Grok if available
        "fallback_chain": ["Grok Code Fast", "Grok Reasoning", "Quality (Critical=Opus, Rest=Sonnet)", "Balanced (All Sonnet)", "Speed (All Haiku)"],
        "max_retries": 3,
        "temperature": 0.7,
        "use_grok": xai_api_key is not None,  # Flag to enable Grok
    }

    # Playwright configuration
    playwright_config = {
        "timeout": 30000,  # 30 seconds
        "browser_type": "chromium",
        "headless": True,
        "viewport": {
            "desktop": {"width": 1920, "height": 1080},
            "mobile": {"width": 390, "height": 844},
            "tablet": {"width": 768, "height": 1024}
        }
    }

    # Testing configuration
    test_config = {
        "max_test_iterations": 10,  # Max test-fix-retest cycles
        "test_timeout": 60000,  # 60 seconds per test
        "required_pass_rate": 0.8,  # 80% tests must pass
    }

    # Server configuration
    server_config = {
        "startup_wait": 5,  # Seconds to wait for server startup
        "health_check_interval": 1,  # Seconds between health checks
        "max_startup_attempts": 10,
    }

    # Orchestration configuration
    orchestration_config = {
        "enable_market_research": True,
        "enable_challenger": True,
        "enable_reflector": True,
        "progress_callback": None,  # Will be set by UI
        "terminal_callback": None,  # Will be set by UI
    }

    # Self-improvement configuration (Phase 9: Parallel batch processing)
    self_improvement_config = {
        "max_parallel_batches": 3,  # Max concurrent batches (prevent rate limit issues)
        "batch_size": 3,            # Files per batch
        "enable_parallel": True,    # Enable/disable parallel processing
    }

    config = {
        "base_dir": str(base_dir),
        "projects_dir": str(projects_dir),
        "exports_dir": str(exports_dir),
        "screenshots_dir": str(screenshots_dir),
        "logs_dir": str(logs_dir),
        "anthropic_api_key": anthropic_api_key,
        "xai_api_key": xai_api_key,
        "hf_token": hf_token,
        "model": model_config,
        "playwright": playwright_config,
        "testing": test_config,
        "server": server_config,
        "orchestration": orchestration_config,
        "self_improvement": self_improvement_config,
    }

    return config


def save_project_metadata(project_path: str, metadata: Dict[str, Any]):
    """Save project metadata to JSON file"""
    metadata_path = Path(project_path) / "project_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)


def load_project_metadata(project_path: str) -> Dict[str, Any]:
    """Load project metadata from JSON file"""
    metadata_path = Path(project_path) / "project_metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}
