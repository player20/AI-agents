#!/usr/bin/env python3
"""
Environment Validation Script for Code Weaver Pro

Validates that all required dependencies, API keys, and services
are properly configured before starting the application.

Usage:
    python scripts/check_env.py
    python scripts/check_env.py --fix  # Attempts to fix common issues
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Status(Enum):
    OK = "✅"
    WARN = "⚠️"
    ERROR = "❌"
    INFO = "ℹ️"


@dataclass
class CheckResult:
    name: str
    status: Status
    message: str
    fix_hint: Optional[str] = None


def print_result(result: CheckResult):
    """Print a formatted check result."""
    print(f"  {result.status.value} {result.name}: {result.message}")
    if result.fix_hint and result.status in (Status.ERROR, Status.WARN):
        print(f"      💡 {result.fix_hint}")


def check_python_version() -> CheckResult:
    """Check Python version is 3.10+."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        return CheckResult(
            "Python Version",
            Status.OK,
            f"Python {version.major}.{version.minor}.{version.micro}"
        )
    return CheckResult(
        "Python Version",
        Status.ERROR,
        f"Python {version.major}.{version.minor} (requires 3.10+)",
        "Install Python 3.10 or higher"
    )


def check_env_file() -> CheckResult:
    """Check if .env file exists."""
    env_path = Path(__file__).parent.parent / ".env"
    env_local_path = Path(__file__).parent.parent / ".env.local"

    if env_path.exists() or env_local_path.exists():
        return CheckResult("Environment File", Status.OK, "Found .env file")

    return CheckResult(
        "Environment File",
        Status.WARN,
        "No .env file found",
        "Copy .env.example to .env and configure your settings"
    )


def check_env_var(name: str, required: bool = True, secret: bool = False) -> CheckResult:
    """Check if an environment variable is set."""
    value = os.environ.get(name)

    if value:
        display_value = "****" if secret else (value[:20] + "..." if len(value) > 20 else value)
        return CheckResult(name, Status.OK, f"Set ({display_value})")

    if required:
        return CheckResult(
            name,
            Status.ERROR,
            "Not set (required)",
            f"Set {name} in your .env file"
        )

    return CheckResult(name, Status.WARN, "Not set (optional)")


def check_package_installed(package: str, import_name: Optional[str] = None) -> CheckResult:
    """Check if a Python package is installed."""
    import_name = import_name or package.replace("-", "_")

    spec = importlib.util.find_spec(import_name)
    if spec is not None:
        return CheckResult(f"Package: {package}", Status.OK, "Installed")

    return CheckResult(
        f"Package: {package}",
        Status.ERROR,
        "Not installed",
        f"Run: pip install {package}"
    )


def check_docker() -> CheckResult:
    """Check if Docker is available and running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            return CheckResult("Docker", Status.OK, "Running")
        return CheckResult(
            "Docker",
            Status.WARN,
            "Installed but not running",
            "Start Docker Desktop or the Docker daemon"
        )
    except FileNotFoundError:
        return CheckResult(
            "Docker",
            Status.WARN,
            "Not installed (optional for local dev)",
            "Install Docker for containerized execution"
        )
    except subprocess.TimeoutExpired:
        return CheckResult("Docker", Status.WARN, "Timeout checking Docker status")


def check_node() -> CheckResult:
    """Check if Node.js is available."""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            major = int(version.replace("v", "").split(".")[0])
            if major >= 18:
                return CheckResult("Node.js", Status.OK, version)
            return CheckResult(
                "Node.js",
                Status.WARN,
                f"{version} (recommend 18+)",
                "Update Node.js to version 18 or higher"
            )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return CheckResult(
        "Node.js",
        Status.WARN,
        "Not found (needed for frontend)",
        "Install Node.js 18+ from nodejs.org"
    )


def check_api_connectivity(name: str, test_fn) -> CheckResult:
    """Check API connectivity."""
    try:
        test_fn()
        return CheckResult(f"{name} API", Status.OK, "Connected")
    except Exception as e:
        return CheckResult(
            f"{name} API",
            Status.WARN,
            f"Connection failed: {str(e)[:50]}",
            f"Check your {name} API key and network connection"
        )


def check_anthropic_api() -> CheckResult:
    """Check Anthropic API connectivity."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return CheckResult(
            "Anthropic API",
            Status.WARN,
            "API key not set",
            "Set ANTHROPIC_API_KEY for Claude integration"
        )

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        # Just verify the client can be created
        return CheckResult("Anthropic API", Status.OK, "Configured")
    except ImportError:
        return CheckResult(
            "Anthropic API",
            Status.WARN,
            "anthropic package not installed",
            "Run: pip install anthropic"
        )
    except Exception as e:
        return CheckResult(
            "Anthropic API",
            Status.WARN,
            f"Configuration issue: {str(e)[:40]}",
            "Check your ANTHROPIC_API_KEY"
        )


def check_openai_api() -> CheckResult:
    """Check OpenAI API connectivity."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return CheckResult(
            "OpenAI API",
            Status.INFO,
            "API key not set (optional fallback)",
            "Set OPENAI_API_KEY for GPT fallback"
        )

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        return CheckResult("OpenAI API", Status.OK, "Configured")
    except ImportError:
        return CheckResult(
            "OpenAI API",
            Status.INFO,
            "openai package not installed",
            "Run: pip install openai"
        )
    except Exception as e:
        return CheckResult(
            "OpenAI API",
            Status.WARN,
            f"Configuration issue: {str(e)[:40]}"
        )


def check_supabase() -> CheckResult:
    """Check Supabase configuration."""
    url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not url or not key:
        return CheckResult(
            "Supabase",
            Status.INFO,
            "Not configured (using local mode)",
            "Set SUPABASE_URL and SUPABASE_ANON_KEY for cloud database"
        )

    return CheckResult("Supabase", Status.OK, "Configured")


def run_all_checks() -> List[CheckResult]:
    """Run all environment checks."""
    results = []

    print("\n🔍 Code Weaver Pro - Environment Check\n")
    print("=" * 50)

    # System checks
    print("\n📦 System Requirements:")
    results.append(check_python_version())
    results.append(check_node())
    results.append(check_docker())
    for r in results[-3:]:
        print_result(r)

    # Environment files
    print("\n📄 Configuration:")
    results.append(check_env_file())
    print_result(results[-1])

    # Required packages
    print("\n📚 Python Packages:")
    packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("anthropic", "anthropic"),
        ("crewai", "crewai"),
        ("langgraph", "langgraph"),
    ]
    for pkg, import_name in packages:
        result = check_package_installed(pkg, import_name)
        results.append(result)
        print_result(result)

    # API Keys
    print("\n🔑 API Configuration:")
    results.append(check_anthropic_api())
    results.append(check_openai_api())
    results.append(check_supabase())
    for r in results[-3:]:
        print_result(r)

    # Summary
    print("\n" + "=" * 50)
    errors = sum(1 for r in results if r.status == Status.ERROR)
    warnings = sum(1 for r in results if r.status == Status.WARN)

    if errors == 0 and warnings == 0:
        print("✅ All checks passed! Ready to run.")
    elif errors == 0:
        print(f"⚠️  {warnings} warning(s) - can run with limited functionality")
    else:
        print(f"❌ {errors} error(s), {warnings} warning(s) - please fix errors before running")

    print()
    return results


def create_env_template():
    """Create a .env.example template file."""
    template = """# Code Weaver Pro - Environment Configuration
# Copy this file to .env and fill in your values

# ===========================================
# LLM API Keys (at least one required)
# ===========================================

# Anthropic Claude (Primary)
ANTHROPIC_API_KEY=

# OpenAI GPT (Fallback)
OPENAI_API_KEY=

# ===========================================
# Database (Optional - uses local mode if not set)
# ===========================================

# Supabase Configuration
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Or use these for Next.js frontend
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=

# ===========================================
# Optional Services
# ===========================================

# PostHog Analytics
NEXT_PUBLIC_POSTHOG_KEY=
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com

# Redis (for message queue)
REDIS_URL=redis://localhost:6379

# ===========================================
# Application Settings
# ===========================================

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Logging
LOG_LEVEL=INFO
"""

    env_example_path = Path(__file__).parent.parent / ".env.example"
    env_example_path.write_text(template)
    print(f"✅ Created {env_example_path}")


if __name__ == "__main__":
    # Load .env file if it exists
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        env_local = Path(__file__).parent.parent / ".env.local"
        if env_local.exists():
            load_dotenv(env_local)
    except ImportError:
        pass

    if "--fix" in sys.argv:
        print("🔧 Creating environment template...")
        create_env_template()

    results = run_all_checks()

    # Exit with error code if there are errors
    errors = sum(1 for r in results if r.status == Status.ERROR)
    sys.exit(1 if errors > 0 else 0)
