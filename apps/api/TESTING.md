# Code Weaver Pro - Testing Guide

## Quick Start

```bash
# Navigate to the API directory
cd apps/api

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-watch

# Run all tests
python run_tests.py

# Run with coverage
python run_tests.py --coverage

# Run specific component
python run_tests.py --component orchestrator
```

## Test Structure

```
apps/api/
├── tests/
│   ├── test_prototype_orchestrator.py  # 5-agent pipeline tests
│   ├── test_web_researcher.py          # Tavily/research tests
│   ├── test_report_generator.py        # Business report tests
│   ├── test_clarification_agent.py     # Smart questions tests
│   ├── test_integration.py             # Full pipeline tests
│   ├── test_health.py                  # Health check tests
│   └── test_llm_router.py              # LLM provider tests
├── run_tests.py                        # Test runner script
└── pytest.ini                          # Pytest configuration
```

## Test Categories

### Unit Tests
Test individual components in isolation with mocked dependencies.

```bash
python run_tests.py --unit
```

### Integration Tests
Test multiple components working together.

```bash
python run_tests.py --integration
```

### Slow Tests
Tests that may take longer (real API calls, performance tests).

```bash
# Skip slow tests for faster feedback
python run_tests.py --fast

# Run only slow tests
python run_tests.py -m slow
```

## Component Tests

### 1. Prototype Orchestrator (`--component orchestrator`)
Tests the 5-agent creative pipeline:
- Domain Analyst - industry detection, entity extraction
- Architect - page structure, navigation
- Content Generator - mock data generation
- UI Composer - code generation, styling
- Validator - syntax checking, auto-fixes

### 2. Web Researcher (`--component researcher`)
Tests Tavily API integration:
- Query generation
- Search execution
- Result parsing
- Confidence scoring
- Error handling

### 3. Report Generator (`--component report`)
Tests business report generation:
- HTML generation
- Section rendering
- Data integration
- Styling (including print)

### 4. Clarification Agent (`--component clarification`)
Tests smart question generation:
- Question selection
- Description enrichment
- Session management

### 5. Integration Tests (`--component integration`)
Tests the full pipeline:
- Description → Prototype + Report
- Clarification flow
- Research integration
- Error recovery

## Environment Variables

### Required for Live Tests
```env
ANTHROPIC_API_KEY=sk-ant-xxx
```

### Optional (enable more features)
```env
TAVILY_API_KEY=tvly-xxx        # Web research
OPENAI_API_KEY=sk-xxx          # LLM fallback
XAI_API_KEY=xai-xxx            # Grok provider
```

### Check Your Setup
```bash
python run_tests.py --check
```

## Running Tests

### Basic Commands

```bash
# All tests
python run_tests.py

# Verbose output
python run_tests.py -v

# Stop on first failure
python run_tests.py -x

# Specific component
python run_tests.py -c orchestrator
python run_tests.py -c researcher
python run_tests.py -c report
```

### Advanced Commands

```bash
# Watch mode (auto-rerun on changes)
python run_tests.py --watch

# Coverage report (generates HTML report)
python run_tests.py --coverage

# Live tests (real API calls)
python run_tests.py --live

# Combine options
python run_tests.py -c orchestrator --coverage -v
```

### Using pytest Directly

```bash
# Run all tests
pytest tests/ -v

# Run with markers
pytest tests/ -m "unit" -v
pytest tests/ -m "integration" -v
pytest tests/ -m "not slow" -v

# Run specific file
pytest tests/test_prototype_orchestrator.py -v

# Run specific test
pytest tests/test_prototype_orchestrator.py::TestDomainAnalyst -v
pytest tests/test_prototype_orchestrator.py::TestDomainAnalyst::test_extracts_entities -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## Writing Tests

### Test Markers

```python
import pytest

@pytest.mark.unit
def test_something():
    """A unit test."""
    pass

@pytest.mark.integration
async def test_full_flow():
    """An integration test."""
    pass

@pytest.mark.slow
async def test_performance():
    """A slow test."""
    pass

@pytest.mark.asyncio
async def test_async_code():
    """An async test."""
    pass
```

### Mocking LLM Calls

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mocked_llm():
    with patch("services.prototype_orchestrator.get_llm_provider") as mock_llm:
        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(return_value={
            "industry": "test",
            "confidence": 0.9
        })
        mock_llm.return_value = mock_provider

        # Your test code here
```

### Mocking Tavily API

```python
@pytest.fixture
def mock_tavily():
    with patch("services.web_researcher.TavilyClient") as mock:
        client = MagicMock()
        client.search = AsyncMock(return_value={
            "results": [
                {"title": "Test", "content": "Content", "score": 0.9}
            ]
        })
        mock.return_value = client
        yield client
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:

```python
@pytest.fixture
def sample_description():
    return "Build a pet grooming dashboard..."

@pytest.fixture
def mock_llm_responses():
    return {
        "domain_analysis": {...},
        "architecture": {...},
        ...
    }
```

## Coverage Reports

After running with `--coverage`:

```bash
# View HTML report
open coverage_report/index.html  # macOS
start coverage_report/index.html  # Windows
xdg-open coverage_report/index.html  # Linux

# Terminal report (shown automatically)
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        run: python run_tests.py --fast --coverage
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Troubleshooting

### Import Errors
Make sure you're in the `apps/api` directory:
```bash
cd apps/api
python run_tests.py
```

### Missing Dependencies
```bash
pip install pytest pytest-asyncio pytest-cov pytest-watch
```

### API Key Errors
Check your environment variables:
```bash
python run_tests.py --check
```

### Async Test Failures
Ensure you have the `@pytest.mark.asyncio` decorator and `pytest-asyncio` installed.

## Test Quality Goals

- **Unit test coverage**: > 80% for core components
- **Integration test coverage**: Full generation flow covered
- **All tests pass**: No failing tests on main branch
- **Fast feedback**: Unit tests complete in < 30 seconds
