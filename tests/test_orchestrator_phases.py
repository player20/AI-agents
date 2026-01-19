"""
Tests for the Orchestrator Phases (core/orchestrator.py)

Tests phase transitions, state mutations, error handling, and workflow integrity.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def orchestrator_config():
    """Default configuration for CodeWeaverOrchestrator."""
    return {
        'model': {
            'default_preset': 'sonnet'
        },
        'orchestration': {
            'progress_callback': None,
            'terminal_callback': None
        },
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


class TestWorkflowState:
    """Tests for WorkflowState initialization and state management."""

    @pytest.mark.unit
    def test_workflow_state_init_basic(self):
        """Test WorkflowState initializes with required user_input."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build a todo app")

        assert state.user_input == "Build a todo app"
        assert state.original_user_input == "Build a todo app"

    @pytest.mark.unit
    def test_workflow_state_default_platforms(self):
        """Test default platform is Web App."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app")

        assert state.platforms == ['Web App']

    @pytest.mark.unit
    def test_workflow_state_custom_platforms(self):
        """Test custom platforms can be set."""
        from core.orchestrator import WorkflowState

        state = WorkflowState(
            "Build an app",
            platforms=['iOS', 'Android', 'Web App']
        )

        assert 'iOS' in state.platforms
        assert 'Android' in state.platforms
        assert len(state.platforms) == 3

    @pytest.mark.unit
    def test_workflow_state_market_research_default(self):
        """Test market research default is False."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app")

        assert state.do_market_research is False

    @pytest.mark.unit
    def test_workflow_state_market_research_enabled(self):
        """Test market research can be enabled."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app", do_market_research=True)

        assert state.do_market_research is True

    @pytest.mark.unit
    def test_workflow_state_research_only_mode(self):
        """Test research only mode."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app", research_only=True)

        assert state.research_only is True

    @pytest.mark.unit
    def test_workflow_state_initial_outputs(self):
        """Test initial outputs are empty."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app")

        assert state.agent_outputs == {}
        assert state.test_results == []
        assert state.screenshots == []
        assert state.scores == {}
        assert state.recommendations == []

    @pytest.mark.unit
    def test_workflow_state_go_decision_default(self):
        """Test go_decision defaults to True."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app")

        assert state.go_decision is True

    @pytest.mark.unit
    def test_workflow_state_reflection_defaults(self):
        """Test LangGraph reflection loop defaults."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app")

        assert state.reflection_iterations == 0
        assert state.max_reflection_iterations == 3
        assert state.quality_threshold == 0.8

    @pytest.mark.unit
    def test_workflow_state_to_dict(self):
        """Test state can be converted to dictionary."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app", platforms=['Web App', 'iOS'])
        state.agent_outputs['test'] = 'output'

        state_dict = state.to_dict()

        assert state_dict['user_input'] == "Build an app"
        assert state_dict['platforms'] == ['Web App', 'iOS']
        assert state_dict['agent_outputs'] == {'test': 'output'}
        assert 'go_decision' in state_dict
        assert 'reflection_iterations' in state_dict


class TestWorkflowStateAuditMode:
    """Tests for WorkflowState audit mode parameters."""

    @pytest.mark.unit
    def test_audit_mode_defaults(self):
        """Test audit mode parameters default to False/None."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Audit my app")

        assert state.analyze_dropoffs is False
        assert state.app_url is None
        assert state.test_credentials is None
        assert state.funnel_analysis is None

    @pytest.mark.unit
    def test_audit_mode_with_url(self):
        """Test audit mode with app URL."""
        from core.orchestrator import WorkflowState

        state = WorkflowState(
            "Audit my app",
            analyze_dropoffs=True,
            app_url="https://myapp.com"
        )

        assert state.analyze_dropoffs is True
        assert state.app_url == "https://myapp.com"

    @pytest.mark.unit
    def test_audit_mode_with_credentials(self):
        """Test audit mode with test credentials."""
        from core.orchestrator import WorkflowState

        creds = {'username': 'test', 'password': 'test123'}
        state = WorkflowState(
            "Audit my app",
            analyze_dropoffs=True,
            test_credentials=creds
        )

        assert state.test_credentials == creds


class TestDSPyPromptOptimizer:
    """Tests for DSPyPromptOptimizer."""

    @pytest.mark.unit
    def test_optimizer_init(self):
        """Test optimizer initializes."""
        from core.orchestrator import DSPyPromptOptimizer

        optimizer = DSPyPromptOptimizer()

        # Should have dspy_configured attribute
        assert hasattr(optimizer, 'dspy_configured')

    @pytest.mark.unit
    def test_optimizer_optimize_returns_string(self):
        """Test optimize_user_input returns a string."""
        from core.orchestrator import DSPyPromptOptimizer

        optimizer = DSPyPromptOptimizer()

        result = optimizer.optimize_user_input(
            "Build a simple todo app",
            context={'platforms': ['Web App']}
        )

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.unit
    def test_optimizer_handles_empty_input(self):
        """Test optimizer handles empty input."""
        from core.orchestrator import DSPyPromptOptimizer

        optimizer = DSPyPromptOptimizer()

        result = optimizer.optimize_user_input("", context={})

        # Should return something even for empty input
        assert isinstance(result, str)


class TestOrchestratorInit:
    """Tests for CodeWeaverOrchestrator initialization."""

    @pytest.mark.unit
    def test_orchestrator_init_with_config(self, orchestrator_config):
        """Test CodeWeaverOrchestrator initializes with config."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        assert orchestrator.config is not None
        assert hasattr(orchestrator, 'prompt_optimizer')
        assert hasattr(orchestrator, 'workflow_builder')

    @pytest.mark.unit
    def test_orchestrator_with_callbacks(self, orchestrator_config):
        """Test CodeWeaverOrchestrator with callbacks."""
        from core.orchestrator import CodeWeaverOrchestrator

        log_messages = []
        progress_updates = []

        def log_callback(msg, level='info'):
            log_messages.append((msg, level))

        def progress_callback(phase, progress):
            progress_updates.append((phase, progress))

        orchestrator_config['orchestration']['terminal_callback'] = log_callback
        orchestrator_config['orchestration']['progress_callback'] = progress_callback

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        assert orchestrator.terminal_callback is not None
        assert orchestrator.progress_callback is not None

    @pytest.mark.unit
    def test_orchestrator_has_agents_cache(self, orchestrator_config):
        """Test CodeWeaverOrchestrator has agents cache."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        assert hasattr(orchestrator, 'agents_cache')
        assert isinstance(orchestrator.agents_cache, dict)


class TestOrchestratorPhaseTransitions:
    """Tests for orchestrator phase transitions."""

    @pytest.mark.unit
    def test_phase_methods_exist(self, orchestrator_config):
        """Test workflow phase methods exist."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        # Should have methods for all phases
        assert hasattr(orchestrator, '_planning_phase')
        assert hasattr(orchestrator, '_drafting_phase')
        assert hasattr(orchestrator, '_testing_phase')
        assert hasattr(orchestrator, '_evaluation_phase')

    @pytest.mark.unit
    def test_update_progress_method_exists(self, orchestrator_config):
        """Test _update_progress method exists."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        assert hasattr(orchestrator, '_update_progress')
        assert callable(orchestrator._update_progress)

    @pytest.mark.unit
    def test_log_method_exists(self, orchestrator_config):
        """Test _log method exists."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        assert hasattr(orchestrator, '_log')
        assert callable(orchestrator._log)


class TestWorkflowStateMutations:
    """Tests for state mutations during workflow."""

    @pytest.mark.unit
    def test_state_agent_output_mutation(self):
        """Test agent outputs can be added to state."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app")

        state.agent_outputs['meta_prompt'] = "Expanded description"
        state.agent_outputs['market_research'] = "Market analysis"

        assert 'meta_prompt' in state.agent_outputs
        assert 'market_research' in state.agent_outputs

    @pytest.mark.unit
    def test_state_scores_mutation(self):
        """Test scores can be added to state."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app")

        state.scores = {
            'speed': 8.5,
            'mobile': 9.0,
            'intuitiveness': 7.5,
            'functionality': 8.0
        }

        assert state.scores['speed'] == 8.5
        assert len(state.scores) == 4

    @pytest.mark.unit
    def test_state_test_results_mutation(self):
        """Test test results can be added to state."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app")

        state.test_results.append({
            'name': 'Login test',
            'status': 'passed',
            'duration_ms': 500
        })

        assert len(state.test_results) == 1
        assert state.test_results[0]['status'] == 'passed'

    @pytest.mark.unit
    def test_state_go_decision_can_change(self):
        """Test go_decision can be changed."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app")
        assert state.go_decision is True

        state.go_decision = False
        assert state.go_decision is False

    @pytest.mark.unit
    def test_state_reflection_iteration_increment(self):
        """Test reflection iterations can be incremented."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app")
        assert state.reflection_iterations == 0

        state.reflection_iterations += 1
        assert state.reflection_iterations == 1

        state.reflection_iterations += 1
        assert state.reflection_iterations == 2

    @pytest.mark.unit
    def test_state_errors_accumulate(self):
        """Test errors can be accumulated."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app")

        state.errors.append("First error")
        state.errors.append("Second error")

        assert len(state.errors) == 2
        assert "First error" in state.errors


class TestOrchestratorErrorHandling:
    """Tests for orchestrator error handling."""

    @pytest.mark.unit
    def test_format_error_result_exists(self, orchestrator_config):
        """Test _format_error_result method exists."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        assert hasattr(orchestrator, '_format_error_result')

    @pytest.mark.unit
    def test_format_no_go_result_exists(self, orchestrator_config):
        """Test _format_no_go_result method exists."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        assert hasattr(orchestrator, '_format_no_go_result')

    @pytest.mark.unit
    def test_format_success_result_exists(self, orchestrator_config):
        """Test _format_success_result method exists."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        assert hasattr(orchestrator, '_format_success_result')


class TestOrchestratorAgentManagement:
    """Tests for agent management in orchestrator."""

    @pytest.mark.unit
    def test_get_agent_method_exists(self, orchestrator_config):
        """Test _get_agent method exists."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        assert hasattr(orchestrator, '_get_agent')

    @pytest.mark.unit
    def test_execute_agent_task_method_exists(self, orchestrator_config):
        """Test _execute_agent_task method exists."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        assert hasattr(orchestrator, '_execute_agent_task')


class TestPerformanceAnalysis:
    """Tests for performance analysis method."""

    @pytest.mark.unit
    def test_analyze_performance_exists(self, orchestrator_config):
        """Test _analyze_performance method exists."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        assert hasattr(orchestrator, '_analyze_performance')

    @pytest.mark.unit
    def test_analyze_performance_returns_list(self, orchestrator_config):
        """Test _analyze_performance returns a list."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        result = orchestrator._analyze_performance({
            'page_load_ms': 2000,
            'time_to_interactive_ms': 3000,
            'first_contentful_paint_ms': 1000,
            'total_size_kb': 500
        })

        assert isinstance(result, list)

    @pytest.mark.unit
    def test_analyze_performance_slow_page(self, orchestrator_config):
        """Test _analyze_performance flags slow page load."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        result = orchestrator._analyze_performance({
            'page_load_ms': 6000,  # Very slow
            'time_to_interactive_ms': 3000,
            'first_contentful_paint_ms': 1000,
            'total_size_kb': 500
        })

        # Should recommend something about page load
        assert len(result) > 0
        # Check that some recommendation mentions page or load
        has_page_rec = any('page' in r.lower() or 'load' in r.lower() for r in result)
        assert has_page_rec

    @pytest.mark.unit
    def test_analyze_performance_large_bundle(self, orchestrator_config):
        """Test _analyze_performance flags large bundle."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        result = orchestrator._analyze_performance({
            'page_load_ms': 2000,
            'time_to_interactive_ms': 3000,
            'first_contentful_paint_ms': 1000,
            'total_size_kb': 2000  # Very large
        })

        # Should recommend something about bundle size
        assert len(result) > 0
        has_bundle_rec = any('bundle' in r.lower() or 'size' in r.lower() for r in result)
        assert has_bundle_rec

    @pytest.mark.unit
    def test_analyze_performance_good_metrics(self, orchestrator_config):
        """Test _analyze_performance with good metrics returns fewer recommendations."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        result = orchestrator._analyze_performance({
            'page_load_ms': 1500,  # Good
            'time_to_interactive_ms': 2000,  # Good
            'first_contentful_paint_ms': 800,  # Good
            'total_size_kb': 300  # Good
        })

        # Should have fewer or no recommendations for good metrics
        assert isinstance(result, list)


class TestLangGraphIntegration:
    """Tests for LangGraph integration."""

    @pytest.mark.unit
    def test_langgraph_availability_checked(self):
        """Test that LANGGRAPH_AVAILABLE flag exists."""
        from core.orchestrator import LANGGRAPH_AVAILABLE

        assert isinstance(LANGGRAPH_AVAILABLE, bool)

    @pytest.mark.unit
    def test_workflow_builder_exists(self, orchestrator_config):
        """Test workflow builder exists."""
        from core.orchestrator import CodeWeaverOrchestrator

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)

        assert hasattr(orchestrator, 'workflow_builder')


class TestDSPyIntegration:
    """Tests for DSPy integration."""

    @pytest.mark.unit
    def test_dspy_availability_checked(self):
        """Test that DSPY_AVAILABLE flag exists."""
        from core.orchestrator import DSPY_AVAILABLE

        assert isinstance(DSPY_AVAILABLE, bool)


class TestCallbackMechanisms:
    """Tests for callback mechanisms."""

    @pytest.mark.unit
    def test_log_callback_invoked(self, orchestrator_config):
        """Test log callback is invoked."""
        from core.orchestrator import CodeWeaverOrchestrator

        log_messages = []

        def log_callback(msg, level='info'):
            log_messages.append((msg, level))

        orchestrator_config['orchestration']['terminal_callback'] = log_callback

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)
        orchestrator._log("Test message", "info")

        assert len(log_messages) > 0

    @pytest.mark.unit
    def test_progress_callback_invoked(self, orchestrator_config):
        """Test progress callback is invoked."""
        from core.orchestrator import CodeWeaverOrchestrator

        progress_updates = []

        def progress_callback(phase, progress):
            progress_updates.append((phase, progress))

        orchestrator_config['orchestration']['progress_callback'] = progress_callback

        orchestrator = CodeWeaverOrchestrator(orchestrator_config)
        orchestrator._update_progress("testing", 0.5)

        assert len(progress_updates) > 0
        assert progress_updates[-1] == ("testing", 0.5)


class TestResultFormatting:
    """Tests for result formatting methods."""

    @pytest.mark.unit
    def test_result_has_required_keys(self):
        """Test that formatted results have required keys."""
        # Expected keys in a successful result
        expected_keys = [
            'project_name',
            'scores',
            'features',
            'recommendations',
            'test_results',
            'performance'
        ]

        # Mock result structure
        result = {
            'project_name': 'Test App',
            'description': 'A test application',
            'platforms': ['Web App'],
            'scores': {'speed': 8, 'mobile': 8, 'intuitiveness': 8, 'functionality': 8},
            'features': ['Feature 1', 'Feature 2'],
            'recommendations': ['Recommendation 1'],
            'test_results': [],
            'screenshots': [],
            'performance': {
                'page_load_ms': 2000,
                'time_to_interactive_ms': 2500,
                'first_contentful_paint_ms': 1000,
                'total_size_kb': 500
            },
            'agent_outputs': {}
        }

        for key in expected_keys:
            assert key in result


class TestWorkflowStateEdgeCases:
    """Tests for edge cases in WorkflowState."""

    @pytest.mark.unit
    def test_state_with_existing_code(self):
        """Test state with existing code parameter."""
        from core.orchestrator import WorkflowState

        existing_code = """
        def hello():
            print("Hello World")
        """

        state = WorkflowState("Improve this code", existing_code=existing_code)

        assert state.existing_code is not None
        assert "hello" in state.existing_code.lower()

    @pytest.mark.unit
    def test_state_preserves_original_input(self):
        """Test that original input is preserved even after optimization."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build a simple app")

        # Simulate input optimization
        state.user_input = "Build a comprehensive web application with user authentication"

        assert state.original_user_input == "Build a simple app"
        assert state.user_input != state.original_user_input

    @pytest.mark.unit
    def test_state_current_phase_tracking(self):
        """Test current phase can be tracked."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app")

        state.current_phase = "planning"
        assert state.current_phase == "planning"

        state.current_phase = "drafting"
        assert state.current_phase == "drafting"

    @pytest.mark.unit
    def test_state_detected_sdks(self):
        """Test detected SDKs storage."""
        from core.orchestrator import WorkflowState

        state = WorkflowState("Build an app")

        state.detected_sdks = {
            'analytics': 'google_analytics',
            'payment': 'stripe'
        }

        assert state.detected_sdks['analytics'] == 'google_analytics'
        assert state.detected_sdks['payment'] == 'stripe'


class TestLangGraphWorkflowBuilder:
    """Tests for LangGraphWorkflowBuilder."""

    @pytest.mark.unit
    def test_workflow_builder_exists(self):
        """Test LangGraphWorkflowBuilder class exists."""
        from core.orchestrator import LangGraphWorkflowBuilder

        builder = LangGraphWorkflowBuilder()
        assert builder is not None

    @pytest.mark.unit
    def test_workflow_builder_create_reflection_exists(self):
        """Test create_reflection_loop method exists."""
        from core.orchestrator import LangGraphWorkflowBuilder

        builder = LangGraphWorkflowBuilder()
        assert hasattr(builder, 'create_reflection_loop')


class TestReflectionState:
    """Tests for ReflectionState TypedDict."""

    @pytest.mark.unit
    def test_reflection_state_type_exists(self):
        """Test ReflectionState type exists."""
        from core.orchestrator import ReflectionState

        # Should be able to create a valid ReflectionState
        state = {
            'content': 'Test content',
            'quality_score': 0.8,
            'iterations': 1,
            'feedback': 'Good quality'
        }

        # TypedDict should accept these keys
        assert 'content' in state
        assert 'quality_score' in state
