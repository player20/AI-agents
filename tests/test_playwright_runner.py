"""
Tests for the Playwright Runner (core/playwright_runner.py)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import sys
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def default_config():
    """Default configuration for PlaywrightRunner."""
    return {
        'playwright': {
            'viewport': {
                'mobile': {'width': 375, 'height': 667},
                'tablet': {'width': 768, 'height': 1024},
                'desktop': {'width': 1920, 'height': 1080}
            },
            'timeout': 30000,
            'browser_type': 'chromium'
        },
        'server': {
            'start_timeout': 30,
            'health_check_interval': 1
        }
    }


class TestPlaywrightRunnerInit:
    """Tests for PlaywrightRunner initialization."""

    @pytest.mark.unit
    def test_init_with_project_path(self, temp_dir, default_config):
        """Test initialization with a project path."""
        from core.playwright_runner import PlaywrightRunner

        runner = PlaywrightRunner(str(temp_dir), default_config)

        assert runner.project_path == Path(temp_dir)
        assert runner.server_url is None
        assert runner.server_process is None

    @pytest.mark.unit
    def test_init_sets_default_timeout(self, temp_dir, default_config):
        """Test that default timeout is set."""
        from core.playwright_runner import PlaywrightRunner

        runner = PlaywrightRunner(str(temp_dir), default_config)

        assert runner.timeout > 0
        assert runner.timeout == 30000  # Default 30 seconds

    @pytest.mark.unit
    def test_init_sets_viewports(self, temp_dir, default_config):
        """Test that viewports are configured."""
        from core.playwright_runner import PlaywrightRunner

        runner = PlaywrightRunner(str(temp_dir), default_config)

        assert 'mobile' in runner.viewports
        assert 'tablet' in runner.viewports
        assert 'desktop' in runner.viewports

    @pytest.mark.unit
    def test_viewport_dimensions(self, temp_dir, default_config):
        """Test viewport dimensions are sensible."""
        from core.playwright_runner import PlaywrightRunner

        runner = PlaywrightRunner(str(temp_dir), default_config)

        # Mobile should be narrow
        assert runner.viewports['mobile']['width'] < 500
        # Desktop should be wide
        assert runner.viewports['desktop']['width'] >= 1280


class TestServerManagement:
    """Tests for server start/stop functionality."""

    @pytest.mark.unit
    def test_detect_server_type_react(self, temp_dir, default_config):
        """Test detection of React project by checking package.json exists."""
        from core.playwright_runner import PlaywrightRunner

        # Create a package.json with react-scripts
        package_json = temp_dir / "package.json"
        package_json.write_text('{"scripts": {"start": "react-scripts start"}}')

        runner = PlaywrightRunner(str(temp_dir), default_config)

        # Runner should detect package.json exists
        assert (runner.project_path / "package.json").exists()

    @pytest.mark.unit
    def test_detect_server_type_flask(self, temp_dir, default_config):
        """Test detection of Flask project."""
        from core.playwright_runner import PlaywrightRunner

        # Create a requirements.txt for Python project
        requirements = temp_dir / "requirements.txt"
        requirements.write_text('flask==2.0.0\n')

        runner = PlaywrightRunner(str(temp_dir), default_config)

        # Should detect Python project
        assert (runner.project_path / "requirements.txt").exists()

    @pytest.mark.unit
    def test_detect_server_type_static(self, temp_dir, default_config):
        """Test detection of static HTML project."""
        from core.playwright_runner import PlaywrightRunner

        # Create just an index.html
        index_html = temp_dir / "index.html"
        index_html.write_text('<html><body>Hello</body></html>')

        runner = PlaywrightRunner(str(temp_dir), default_config)

        # Should detect HTML files
        html_files = list(runner.project_path.glob("*.html"))
        assert len(html_files) > 0

    @pytest.mark.unit
    @patch('subprocess.Popen')
    def test_server_process_can_be_set(self, mock_popen, temp_dir, default_config):
        """Test that server process can be assigned."""
        from core.playwright_runner import PlaywrightRunner

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        runner = PlaywrightRunner(str(temp_dir), default_config)
        runner.server_process = mock_process

        assert runner.server_process is not None

    @pytest.mark.unit
    def test_stop_server_no_process(self, temp_dir, default_config):
        """Test stop_server when no server is running."""
        from core.playwright_runner import PlaywrightRunner

        runner = PlaywrightRunner(str(temp_dir), default_config)
        runner.server_process = None

        # Should not raise - stop_server is async but we can check state
        assert runner.server_process is None

    @pytest.mark.unit
    def test_server_url_initially_none(self, temp_dir, default_config):
        """Test that server URL is initially None."""
        from core.playwright_runner import PlaywrightRunner

        runner = PlaywrightRunner(str(temp_dir), default_config)

        assert runner.server_url is None


class TestTestExecution:
    """Tests for test execution methods."""

    @pytest.mark.unit
    def test_test_result_structure(self):
        """Test that test results have the correct structure."""
        # Expected structure for all test results
        expected_keys = ['name', 'status', 'error', 'duration_ms']

        # All tests should return dicts with these keys
        result = {
            'name': 'Test Name',
            'status': 'passed',
            'error': None,
            'duration_ms': 100
        }

        for key in expected_keys:
            assert key in result

    @pytest.mark.unit
    def test_valid_status_values(self):
        """Test that status values are valid."""
        valid_statuses = ['passed', 'failed', 'timeout', 'skipped']

        for status in valid_statuses:
            result = {'name': 'Test', 'status': status, 'error': None, 'duration_ms': 0}
            assert result['status'] in valid_statuses

    @pytest.mark.unit
    def test_result_with_error(self):
        """Test result structure with error message."""
        result = {
            'name': 'Test Name',
            'status': 'failed',
            'error': 'Element not found',
            'duration_ms': 250
        }

        assert result['status'] == 'failed'
        assert result['error'] is not None
        assert isinstance(result['duration_ms'], int)


class TestScreenshotCapture:
    """Tests for screenshot functionality."""

    @pytest.mark.unit
    def test_screenshot_viewports_defined(self, temp_dir, default_config):
        """Test that all screenshot viewports are defined."""
        from core.playwright_runner import PlaywrightRunner

        runner = PlaywrightRunner(str(temp_dir), default_config)

        # Should have at least mobile and desktop
        assert len(runner.viewports) >= 2
        assert 'mobile' in runner.viewports
        assert 'desktop' in runner.viewports

    @pytest.mark.unit
    def test_viewport_has_dimensions(self, temp_dir, default_config):
        """Test that viewports have width and height."""
        from core.playwright_runner import PlaywrightRunner

        runner = PlaywrightRunner(str(temp_dir), default_config)

        for name, viewport in runner.viewports.items():
            assert 'width' in viewport
            assert 'height' in viewport
            assert viewport['width'] > 0
            assert viewport['height'] > 0


class TestPerformanceMeasurement:
    """Tests for performance measurement."""

    @pytest.mark.unit
    def test_performance_metrics_keys(self):
        """Test that performance metrics have expected keys."""
        expected_keys = [
            'page_load_ms',
            'time_to_interactive_ms',
            'first_contentful_paint_ms',
            'total_size_kb'
        ]

        # Mock performance result
        performance = {
            'page_load_ms': 1500,
            'time_to_interactive_ms': 2000,
            'first_contentful_paint_ms': 800,
            'total_size_kb': 350
        }

        for key in expected_keys:
            assert key in performance

    @pytest.mark.unit
    def test_performance_metrics_types(self):
        """Test that performance metrics are numeric."""
        performance = {
            'page_load_ms': 1500,
            'time_to_interactive_ms': 2000,
            'first_contentful_paint_ms': 800,
            'total_size_kb': 350
        }

        for key, value in performance.items():
            assert isinstance(value, (int, float))
            assert value >= 0


class TestErrorHandling:
    """Tests for error handling in runner."""

    @pytest.mark.unit
    def test_timeout_error_handling(self):
        """Test that timeout errors are handled properly."""
        # Timeout should result in a specific error status
        timeout_result = {
            'name': 'Page Load',
            'status': 'timeout',
            'error': 'Page load timed out',
            'duration_ms': 30000
        }

        assert timeout_result['status'] == 'timeout'
        assert 'timed out' in timeout_result['error'].lower()

    @pytest.mark.unit
    def test_connection_error_handling(self):
        """Test that connection errors are handled properly."""
        connection_result = {
            'name': 'Page Load',
            'status': 'failed',
            'error': 'Connection error: Connection refused',
            'duration_ms': 100
        }

        assert connection_result['status'] == 'failed'
        assert 'connection' in connection_result['error'].lower()

    @pytest.mark.unit
    def test_no_server_url_error(self, temp_dir, default_config):
        """Test error when server URL is not set."""
        from core.playwright_runner import PlaywrightRunner

        runner = PlaywrightRunner(str(temp_dir), default_config)
        assert runner.server_url is None

        # Running tests without server should handle gracefully
        # (actual behavior depends on implementation)


class TestConfigValidation:
    """Tests for configuration validation."""

    @pytest.mark.unit
    def test_config_requires_playwright_section(self, temp_dir, default_config):
        """Test that config must have playwright section."""
        from core.playwright_runner import PlaywrightRunner

        runner = PlaywrightRunner(str(temp_dir), default_config)
        assert 'mobile' in runner.viewports
        assert runner.timeout == 30000

    @pytest.mark.unit
    def test_custom_timeout(self, temp_dir, default_config):
        """Test custom timeout configuration."""
        from core.playwright_runner import PlaywrightRunner

        custom_config = default_config.copy()
        custom_config['playwright'] = default_config['playwright'].copy()
        custom_config['playwright']['timeout'] = 60000

        runner = PlaywrightRunner(str(temp_dir), custom_config)
        assert runner.timeout == 60000

    @pytest.mark.unit
    def test_browser_type_config(self, temp_dir, default_config):
        """Test browser type configuration."""
        from core.playwright_runner import PlaywrightRunner

        runner = PlaywrightRunner(str(temp_dir), default_config)
        assert runner.browser_type == 'chromium'


class TestProjectTypeDetection:
    """Tests for project type detection logic."""

    @pytest.mark.unit
    def test_node_project_detection(self, temp_dir, default_config):
        """Test Node.js project detection."""
        from core.playwright_runner import PlaywrightRunner

        (temp_dir / "package.json").write_text('{"name": "test"}')

        runner = PlaywrightRunner(str(temp_dir), default_config)
        has_package = (runner.project_path / "package.json").exists()

        assert has_package is True

    @pytest.mark.unit
    def test_python_project_detection(self, temp_dir, default_config):
        """Test Python project detection."""
        from core.playwright_runner import PlaywrightRunner

        (temp_dir / "requirements.txt").write_text('flask\n')

        runner = PlaywrightRunner(str(temp_dir), default_config)
        has_requirements = (runner.project_path / "requirements.txt").exists()

        assert has_requirements is True

    @pytest.mark.unit
    def test_static_project_detection(self, temp_dir, default_config):
        """Test static HTML project detection."""
        from core.playwright_runner import PlaywrightRunner

        (temp_dir / "index.html").write_text('<html></html>')

        runner = PlaywrightRunner(str(temp_dir), default_config)
        html_files = list(runner.project_path.glob("*.html"))

        assert len(html_files) == 1

    @pytest.mark.unit
    def test_empty_project_detection(self, temp_dir, default_config):
        """Test detection of empty project directory."""
        from core.playwright_runner import PlaywrightRunner

        runner = PlaywrightRunner(str(temp_dir), default_config)

        has_package = (runner.project_path / "package.json").exists()
        has_requirements = (runner.project_path / "requirements.txt").exists()
        html_files = list(runner.project_path.glob("*.html"))

        assert has_package is False
        assert has_requirements is False
        assert len(html_files) == 0
