"""
Pytest Configuration and Shared Fixtures for Weaver Pro Tests
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, MagicMock, patch
import sys

# Set mock API key BEFORE importing any modules that need it
os.environ.setdefault('ANTHROPIC_API_KEY', 'test-key-for-pytest')
os.environ.setdefault('OPENAI_API_KEY', 'test-key-for-pytest')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup after test
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_config(temp_dir) -> Dict[str, Any]:
    """Create a sample configuration for testing."""
    return {
        'projects_dir': str(temp_dir / 'projects'),
        'api_key': 'test-api-key',
        'default_model': 'haiku',
        'agents': {
            'MetaPrompt': {'role': 'Project Expander'},
            'Research': {'role': 'Market Researcher'},
            'Challenger': {'role': 'Critical Reviewer'},
            'PM': {'role': 'Product Manager'},
            'Ideas': {'role': 'Ideas Generator'},
            'Designs': {'role': 'Designer'},
            'Senior': {'role': 'Senior Developer'},
            'Reflector': {'role': 'Synthesizer'},
            'Web': {'role': 'Web Developer'},
            'iOS': {'role': 'iOS Developer'},
            'Android': {'role': 'Android Developer'},
        },
        'orchestration': {
            'max_reflection_iterations': 3,
            'quality_threshold': 0.8,
            'progress_callback': None,
            'terminal_callback': None,
        }
    }


@pytest.fixture
def mock_agent():
    """Create a mock CrewAI agent."""
    agent = Mock()
    agent.role = "Test Agent"
    agent.goal = "Test goal"
    agent.backstory = "Test backstory"
    return agent


@pytest.fixture
def mock_crew():
    """Create a mock CrewAI crew."""
    crew = Mock()
    crew.kickoff.return_value = "Mock crew result"
    return crew


@pytest.fixture
def sample_workflow_state():
    """Create a sample WorkflowState for testing."""
    from core.orchestrator import WorkflowState

    state = WorkflowState(
        user_input="Build a todo app with user authentication",
        platforms=['Web App'],
        do_market_research=False,
        research_only=False,
        existing_code=None
    )
    return state


@pytest.fixture
def sample_code_file(temp_dir):
    """Create a sample code file for testing."""
    code_file = temp_dir / "sample.py"
    code_file.write_text('''
def hello_world():
    """Say hello."""
    print("Hello, World!")

def add_numbers(a, b):
    """Add two numbers."""
    return a + b
''')
    return str(code_file)


@pytest.fixture
def sample_code_with_issues(temp_dir):
    """Create a sample code file with intentional issues for testing."""
    code_file = temp_dir / "issues.py"
    code_file.write_text('''
import os
import sys
import json  # unused import

def bad_function():
    x = 1
    y = 2  # unused variable
    return x

def no_docstring():
    pass

def too_long_function():
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    g = 7
    h = 8
    i = 9
    j = 10
    return a + b + c + d + e + f + g + h + i + j
''')
    return str(code_file)


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response."""
    return {
        'content': 'This is a mock LLM response for testing purposes.',
        'model': 'claude-3-haiku',
        'usage': {'input_tokens': 10, 'output_tokens': 50}
    }


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    client = Mock()
    response = Mock()
    response.content = [Mock(text="Mock response from Claude")]
    client.messages.create.return_value = response
    return client


# Markers for test categories
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external deps)")
    config.addinivalue_line("markers", "integration: Integration tests (may need external services)")
    config.addinivalue_line("markers", "slow: Slow tests (skip with -m 'not slow')")
    config.addinivalue_line("markers", "api: Tests that require API keys")
