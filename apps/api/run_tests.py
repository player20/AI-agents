#!/usr/bin/env python3
"""
Test Runner for Code Weaver Pro

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --fast             # Skip slow tests
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --verbose          # Verbose output
    python run_tests.py --watch            # Watch mode (requires pytest-watch)
    python run_tests.py --component NAME   # Run tests for specific component
    python run_tests.py --live             # Run live tests (requires API keys)

Components:
    - orchestrator  : Prototype orchestrator tests
    - researcher    : Web researcher tests
    - clarification : Clarification agent tests
    - report        : Report generator tests
    - integration   : Integration tests
    - health        : Health check tests
    - llm           : LLM router tests
"""
import subprocess
import sys
import os
import argparse
from pathlib import Path

# Get the directory containing this script
SCRIPT_DIR = Path(__file__).parent.absolute()
TESTS_DIR = SCRIPT_DIR / "tests"

# Component to test file mapping
COMPONENT_MAP = {
    "orchestrator": "test_prototype_orchestrator.py",
    "researcher": "test_web_researcher.py",
    "clarification": "test_clarification_agent.py",
    "report": "test_report_generator.py",
    "integration": "test_integration.py",
    "health": "test_health.py",
    "llm": "test_llm_router.py",
}

def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def check_dependencies():
    """Check if required test dependencies are installed."""
    required = ["pytest", "pytest-asyncio"]
    optional = ["pytest-cov", "pytest-watch", "pytest-xdist"]

    missing_required = []
    missing_optional = []

    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing_required.append(pkg)

    for pkg in optional:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing_optional.append(pkg)

    if missing_required:
        print("ERROR: Missing required packages:")
        for pkg in missing_required:
            print(f"  - {pkg}")
        print("\nInstall with: pip install " + " ".join(missing_required))
        return False

    if missing_optional:
        print("Note: Some optional packages are missing:")
        for pkg in missing_optional:
            print(f"  - {pkg}")
        print("Install with: pip install " + " ".join(missing_optional))
        print("")

    return True

def check_env_vars():
    """Check for required environment variables."""
    required = []
    optional = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "TAVILY_API_KEY", "XAI_API_KEY"]

    missing_required = [v for v in required if not os.environ.get(v)]
    missing_optional = [v for v in optional if not os.environ.get(v)]

    if missing_required:
        print("ERROR: Missing required environment variables:")
        for var in missing_required:
            print(f"  - {var}")
        return False

    if missing_optional:
        print("Note: Some optional API keys are not set:")
        for var in missing_optional:
            print(f"  - {var}")
        print("Some tests may be skipped without these keys.")
        print("")

    return True

def run_tests(args):
    """Run pytest with the specified options."""
    cmd = ["python", "-m", "pytest"]

    # Add test directory
    if args.component:
        if args.component not in COMPONENT_MAP:
            print(f"Unknown component: {args.component}")
            print(f"Available: {', '.join(COMPONENT_MAP.keys())}")
            return 1
        cmd.append(str(TESTS_DIR / COMPONENT_MAP[args.component]))
    else:
        cmd.append(str(TESTS_DIR))

    # Add markers
    markers = []
    if args.unit:
        markers.append("unit")
    if args.integration:
        markers.append("integration")
    if args.fast:
        markers.append("not slow")

    if markers:
        cmd.extend(["-m", " and ".join(markers)])

    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    # Add coverage
    if args.coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:coverage_report"
        ])

    # Add other options
    cmd.extend([
        "--tb=short",  # Short traceback
        "-x" if args.failfast else "",  # Stop on first failure
        "--durations=10",  # Show 10 slowest tests
    ])
    cmd = [c for c in cmd if c]  # Remove empty strings

    # Watch mode
    if args.watch:
        cmd = ["ptw", "--", *cmd[2:]]  # Replace pytest with ptw

    # Live tests (with real API calls)
    if args.live:
        os.environ["RUN_LIVE_TESTS"] = "1"

    print_header("Running Tests")
    print(f"Command: {' '.join(cmd)}")
    print("")

    # Run the tests
    result = subprocess.run(cmd, cwd=str(SCRIPT_DIR))
    return result.returncode

def show_test_summary():
    """Show a summary of available tests."""
    print_header("Available Test Suites")

    for component, filename in COMPONENT_MAP.items():
        filepath = TESTS_DIR / filename
        if filepath.exists():
            # Count test functions
            content = filepath.read_text()
            test_count = content.count("def test_") + content.count("async def test_")
            print(f"  {component:15} : {test_count:3} tests ({filename})")
        else:
            print(f"  {component:15} : [NOT FOUND] ({filename})")

    print("")

def main():
    parser = argparse.ArgumentParser(
        description="Test Runner for Code Weaver Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument("--unit", action="store_true",
                        help="Run only unit tests")
    parser.add_argument("--integration", action="store_true",
                        help="Run only integration tests")
    parser.add_argument("--fast", action="store_true",
                        help="Skip slow tests")
    parser.add_argument("--coverage", action="store_true",
                        help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")
    parser.add_argument("--watch", "-w", action="store_true",
                        help="Watch mode (requires pytest-watch)")
    parser.add_argument("--failfast", "-x", action="store_true",
                        help="Stop on first failure")
    parser.add_argument("--component", "-c", type=str,
                        help=f"Run tests for specific component: {', '.join(COMPONENT_MAP.keys())}")
    parser.add_argument("--live", action="store_true",
                        help="Run live tests with real API calls")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List available test suites")
    parser.add_argument("--check", action="store_true",
                        help="Check dependencies and environment")

    args = parser.parse_args()

    if args.list:
        show_test_summary()
        return 0

    if args.check:
        print_header("Checking Environment")
        deps_ok = check_dependencies()
        env_ok = check_env_vars()
        if deps_ok and env_ok:
            print("All checks passed!")
        return 0 if (deps_ok and env_ok) else 1

    # Check dependencies before running
    if not check_dependencies():
        return 1

    # Check environment (but don't fail)
    check_env_vars()

    return run_tests(args)

if __name__ == "__main__":
    sys.exit(main())
