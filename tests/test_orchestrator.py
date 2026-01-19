"""
Tests for the Code Weaver Orchestrator (core/orchestrator.py)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import (
    WorkflowState,
    DSPyPromptOptimizer,
    LangGraphWorkflowBuilder,
    ReflectionState,
    LANGGRAPH_AVAILABLE
)


class TestWorkflowState:
    """Tests for WorkflowState class."""

    @pytest.mark.unit
    def test_init_with_defaults(self):
        """Test WorkflowState initialization with defaults."""
        state = WorkflowState("Build a todo app")

        assert state.user_input == "Build a todo app"
        assert state.platforms == ['Web App']
        assert state.do_market_research is False
        assert state.research_only is False
        assert state.existing_code is None
        assert state.go_decision is True
        assert state.reflection_iterations == 0

    @pytest.mark.unit
    def test_init_with_custom_values(self):
        """Test WorkflowState with custom parameters."""
        state = WorkflowState(
            "Build a mobile app",
            platforms=['iOS', 'Android'],
            do_market_research=True,
            research_only=True,
            existing_code={'main.py': 'print("hello")'}
        )

        assert state.platforms == ['iOS', 'Android']
        assert state.do_market_research is True
        assert state.research_only is True
        assert state.existing_code == {'main.py': 'print("hello")'}

    @pytest.mark.unit
    def test_to_dict(self):
        """Test WorkflowState to_dict conversion."""
        state = WorkflowState(
            "Build an app",
            platforms=['Web App', 'iOS']
        )
        state.agent_outputs['test'] = 'output'
        state.scores = {'speed': 8, 'mobile': 7}

        result = state.to_dict()

        assert result['user_input'] == "Build an app"
        assert result['platforms'] == ['Web App', 'iOS']
        assert result['agent_outputs'] == {'test': 'output'}
        assert result['scores'] == {'speed': 8, 'mobile': 7}

    @pytest.mark.unit
    def test_audit_mode_parameters(self):
        """Test audit mode specific parameters."""
        state = WorkflowState(
            "Audit my app",
            analyze_dropoffs=True,
            app_url="https://example.com",
            test_credentials={'email': 'test@test.com', 'password': 'test'}
        )

        assert state.analyze_dropoffs is True
        assert state.app_url == "https://example.com"
        assert state.test_credentials['email'] == 'test@test.com'

    @pytest.mark.unit
    def test_reflection_loop_state(self):
        """Test reflection loop state initialization."""
        state = WorkflowState("Test input")

        assert state.reflection_iterations == 0
        assert state.max_reflection_iterations == 3
        assert state.quality_threshold == 0.8


class TestDSPyPromptOptimizer:
    """Tests for DSPy prompt optimization."""

    @pytest.mark.unit
    def test_template_optimize_basic(self):
        """Test basic template optimization."""
        optimizer = DSPyPromptOptimizer()

        result = optimizer._template_optimize(
            "Build a todo app",
            context={'platforms': ['Web App'], 'do_market_research': True}
        )

        assert "Build a todo app" in result
        assert "Web App" in result
        assert "Market Research: True" in result

    @pytest.mark.unit
    def test_template_optimize_with_existing_code(self):
        """Test template optimization with existing code context."""
        optimizer = DSPyPromptOptimizer()

        result = optimizer._template_optimize(
            "Improve my app",
            context={'existing_code': True, 'platforms': ['iOS']}
        )

        assert "Existing Code: Yes" in result
        assert "iOS" in result

    @pytest.mark.unit
    def test_template_optimize_empty_context(self):
        """Test template optimization with empty context."""
        optimizer = DSPyPromptOptimizer()

        result = optimizer._template_optimize("Build an app", context=None)

        assert "Build an app" in result
        assert "Web App" in result  # Default platform

    @pytest.mark.unit
    def test_optimize_user_input_fallback(self):
        """Test that optimize_user_input falls back to template when DSPy unavailable."""
        optimizer = DSPyPromptOptimizer()
        optimizer.dspy_configured = False

        result = optimizer.optimize_user_input(
            "Build a chat app",
            context={'platforms': ['Web App']}
        )

        assert "Build a chat app" in result


class TestLangGraphWorkflowBuilder:
    """Tests for LangGraph workflow builder."""

    @pytest.mark.unit
    def test_init_checks_langgraph_availability(self):
        """Test that init checks for LangGraph availability."""
        builder = LangGraphWorkflowBuilder()
        assert builder.langgraph_available == LANGGRAPH_AVAILABLE

    @pytest.mark.unit
    def test_reflection_loop_fallback_no_langgraph(self):
        """Test reflection loop fallback when LangGraph unavailable."""
        builder = LangGraphWorkflowBuilder()
        builder.langgraph_available = False

        state = WorkflowState("Test")
        improve_called = []

        def mock_check(s):
            return 0.5

        def mock_improve(s):
            improve_called.append(True)
            return s

        result = builder.create_reflection_loop(state, mock_check, mock_improve)

        # Without LangGraph, should call improve once
        assert len(improve_called) == 1

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_reflection_loop_with_langgraph(self):
        """Test reflection loop with LangGraph StateGraph."""
        builder = LangGraphWorkflowBuilder()

        state = WorkflowState("Test")
        state.max_reflection_iterations = 3
        state.quality_threshold = 0.8

        check_calls = []
        improve_calls = []

        def mock_check(s):
            check_calls.append(True)
            # Return increasing scores to simulate improvement
            return 0.5 + (len(check_calls) * 0.2)

        def mock_improve(s):
            improve_calls.append(True)
            return s

        result = builder.create_reflection_loop(state, mock_check, mock_improve)

        # Should have called check multiple times
        assert len(check_calls) >= 1
        assert isinstance(result, WorkflowState)

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_reflection_loop_stops_at_threshold(self):
        """Test that reflection loop stops when quality threshold reached."""
        builder = LangGraphWorkflowBuilder()

        state = WorkflowState("Test")
        state.max_reflection_iterations = 10
        state.quality_threshold = 0.9

        iterations = [0]

        def mock_check(s):
            iterations[0] += 1
            return 0.95  # Above threshold immediately

        def mock_improve(s):
            return s

        result = builder.create_reflection_loop(state, mock_check, mock_improve)

        # Should stop after first check (score above threshold)
        assert iterations[0] == 1

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_reflection_loop_stops_at_max_iterations(self):
        """Test that reflection loop stops at max iterations."""
        builder = LangGraphWorkflowBuilder()

        state = WorkflowState("Test")
        state.max_reflection_iterations = 2
        state.quality_threshold = 0.99  # Very high, won't be reached

        iterations = [0]

        def mock_check(s):
            iterations[0] += 1
            return 0.5  # Never reaches threshold

        def mock_improve(s):
            return s

        result = builder.create_reflection_loop(state, mock_check, mock_improve)

        # Should stop at max iterations
        assert result.reflection_iterations <= 2

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_reflection_loop_convergence_detection(self):
        """Test that reflection loop detects stagnation."""
        builder = LangGraphWorkflowBuilder()

        state = WorkflowState("Test")
        state.max_reflection_iterations = 10
        state.quality_threshold = 0.99

        def mock_check(s):
            return 0.6  # Same score every time = stagnation

        def mock_improve(s):
            return s

        result = builder.create_reflection_loop(state, mock_check, mock_improve)

        # Should stop due to stagnation (no improvement for 2+ iterations)
        assert result.reflection_iterations < 10


class TestReflectionState:
    """Tests for ReflectionState TypedDict."""

    @pytest.mark.unit
    def test_reflection_state_structure(self):
        """Test ReflectionState has all required keys."""
        state: ReflectionState = {
            'workflow_state': {},
            'quality_score': 0.0,
            'iteration': 0,
            'max_iterations': 3,
            'quality_threshold': 0.8,
            'should_continue': True,
            'improvement_history': [],
            'stuck_iterations': 0
        }

        assert 'workflow_state' in state
        assert 'quality_score' in state
        assert 'improvement_history' in state
        assert 'stuck_iterations' in state


class TestCodeWeaverOrchestrator:
    """Tests for the main CodeWeaverOrchestrator class."""

    @pytest.mark.unit
    def test_init_with_config(self, sample_config, temp_dir):
        """Test orchestrator initialization."""
        # Create projects directory
        (temp_dir / 'projects').mkdir(exist_ok=True)

        with patch('core.orchestrator.load_agent_configs') as mock_load:
            mock_load.return_value = sample_config['agents']

            from core.orchestrator import CodeWeaverOrchestrator
            orchestrator = CodeWeaverOrchestrator(sample_config)

            assert orchestrator.config == sample_config

    @pytest.mark.unit
    def test_log_callbacks(self, sample_config, temp_dir):
        """Test that log callbacks are called correctly."""
        (temp_dir / 'projects').mkdir(exist_ok=True)
        sample_config['projects_dir'] = str(temp_dir / 'projects')

        log_messages = []

        def mock_terminal_callback(msg, level="info"):
            log_messages.append((msg, level))

        sample_config['orchestration']['terminal_callback'] = mock_terminal_callback

        with patch('core.orchestrator.load_agent_configs') as mock_load:
            mock_load.return_value = sample_config['agents']

            from core.orchestrator import CodeWeaverOrchestrator
            orchestrator = CodeWeaverOrchestrator(sample_config)
            orchestrator._log("Test message", "info")

            # Orchestrator logs framework status during init, plus our test message
            assert len(log_messages) >= 1
            assert any("Test message" in msg[0] for msg in log_messages)

    @pytest.mark.unit
    def test_format_no_go_result(self, sample_config, temp_dir):
        """Test formatting of no-go result."""
        (temp_dir / 'projects').mkdir(exist_ok=True)
        sample_config['projects_dir'] = str(temp_dir / 'projects')

        with patch('core.orchestrator.load_agent_configs') as mock_load:
            mock_load.return_value = sample_config['agents']

            from core.orchestrator import CodeWeaverOrchestrator
            orchestrator = CodeWeaverOrchestrator(sample_config)

            state = WorkflowState("Test project")
            state.go_decision = False
            state.agent_outputs['market_research'] = "Market too saturated"

            result = orchestrator._format_no_go_result(state)

            assert result['status'] == 'no-go'
            assert 'agent_outputs' in result

    @pytest.mark.unit
    def test_format_error_result(self, sample_config, temp_dir):
        """Test formatting of error result."""
        (temp_dir / 'projects').mkdir(exist_ok=True)
        sample_config['projects_dir'] = str(temp_dir / 'projects')

        with patch('core.orchestrator.load_agent_configs') as mock_load:
            mock_load.return_value = sample_config['agents']

            from core.orchestrator import CodeWeaverOrchestrator
            orchestrator = CodeWeaverOrchestrator(sample_config)

            state = WorkflowState("Test project")
            error = Exception("Test error")

            result = orchestrator._format_error_result(state, error)

            assert result['status'] == 'error'
            assert 'Test error' in result['error']


class TestPhaseGraphCreation:
    """Tests for multi-phase StateGraph creation."""

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_create_phase_graph(self):
        """Test creating a multi-phase StateGraph."""
        builder = LangGraphWorkflowBuilder()

        phases = [
            {'name': 'phase1', 'func': lambda x: {'phase1_done': True}},
            {'name': 'phase2', 'func': lambda x: {'phase2_done': True}},
        ]

        graph = builder.create_phase_graph(phases)

        # Should return a compiled graph (not None)
        assert graph is not None

    @pytest.mark.unit
    def test_create_phase_graph_fallback(self):
        """Test phase graph creation fallback when LangGraph unavailable."""
        builder = LangGraphWorkflowBuilder()
        builder.langgraph_available = False

        phases = [
            {'name': 'phase1', 'func': lambda x: x},
        ]

        graph = builder.create_phase_graph(phases)

        assert graph is None  # Should return None without LangGraph
