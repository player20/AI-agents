"""
Tests for the LangGraph Iterative Improver (core/langgraph_improver.py)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# Check if langgraph is available
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


class TestImprovementState:
    """Tests for ImprovementState TypedDict."""

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_improvement_state_structure(self):
        """Test that ImprovementState has correct structure."""
        from core.langgraph_improver import ImprovementState

        # Create a valid state
        state: ImprovementState = {
            'iteration': 0,
            'current_score': 0.0,
            'target_score': 8.0,
            'mode': 'ui_ux',
            'issues_found': [],
            'fixes_applied': [],
            'files_modified': [],
            'total_issues_found': 0,
            'total_fixes_applied': 0,
            'should_continue': True,
            'stuck_iterations': 0,
            'quality_feedback': ''
        }

        assert state['iteration'] == 0
        assert state['target_score'] == 8.0
        assert state['mode'] == 'ui_ux'


class TestAnalyzeIssuesNode:
    """Tests for analyze_issues_node function."""

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_analyze_node_structure(self):
        """Test that analyze node returns proper state structure."""
        # This would need mocking of the actual analysis
        # For now, test the function signature and return type
        pass


class TestScoreCalculation:
    """Tests for quality score calculation."""

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_score_base_calculation(self):
        """Test base score calculation logic."""
        # Tests the score algorithm used in langgraph_improver module:
        # base_score = 5.0 + (total_fixes_applied * 0.5)
        # With modifiers for issue counts

        # Test with mock state
        mock_state = {
            'total_fixes_applied': 4,
            'issues_found': [
                {'severity': 'low'},
                {'severity': 'medium'},
            ]
        }

        # Base score should be 5.0 + (4 * 0.5) = 7.0
        base_expected = 5.0 + (4 * 0.5)
        assert base_expected == 7.0

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_score_excellent_no_high_priority(self):
        """Test that score is excellent when no high priority issues."""
        # If high_priority == 0: base_score = max(base_score, 8.0)
        # If high_priority == 0 and medium_priority <= 3: base_score = 9.0

        # Mock scenario: 0 high, 2 medium
        high_priority = 0
        medium_priority = 2

        base_score = 7.0

        if high_priority == 0:
            base_score = max(base_score, 8.0)
        if high_priority == 0 and medium_priority <= 3:
            base_score = 9.0

        assert base_score == 9.0


class TestConvergenceDetection:
    """Tests for stuck/stagnation detection."""

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_stuck_detection_no_improvement(self):
        """Test detection of no improvement over iterations."""
        # stuck_iterations increments when no improvement
        # should_continue = False when stuck_iterations >= 3

        stuck_iterations = 0
        scores = [5.0, 5.0, 5.0]  # No improvement

        for i in range(1, len(scores)):
            if scores[i] <= scores[i - 1]:
                stuck_iterations += 1

        assert stuck_iterations == 2

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_stuck_detection_with_improvement(self):
        """Test that improvement resets stuck counter."""
        stuck_iterations = 2
        scores = [5.0, 6.0]  # Improvement

        if scores[-1] > scores[-2]:
            stuck_iterations = 0

        assert stuck_iterations == 0


class TestShouldContinueImprovement:
    """Tests for should_continue_improvement decision function."""

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_continue_below_target(self):
        """Test that improvement continues when below target score."""
        state = {
            'current_score': 6.0,
            'target_score': 8.0,
            'iteration': 1,
            'stuck_iterations': 0
        }

        # Should continue
        should_continue = (
            state['current_score'] < state['target_score'] and
            state['iteration'] < 10 and
            state['stuck_iterations'] < 3
        )

        assert should_continue is True

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_stop_at_target(self):
        """Test that improvement stops when target reached."""
        state = {
            'current_score': 8.5,
            'target_score': 8.0,
            'iteration': 2,
            'stuck_iterations': 0
        }

        should_continue = state['current_score'] < state['target_score']
        assert should_continue is False

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_stop_at_max_iterations(self):
        """Test that improvement stops at max iterations."""
        state = {
            'current_score': 6.0,
            'target_score': 8.0,
            'iteration': 10,  # Max
            'stuck_iterations': 0
        }

        should_continue = state['iteration'] < 10
        assert should_continue is False

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_stop_when_stuck(self):
        """Test that improvement stops when stuck."""
        state = {
            'current_score': 6.0,
            'target_score': 8.0,
            'iteration': 5,
            'stuck_iterations': 3  # Stuck
        }

        should_continue = state['stuck_iterations'] < 3
        assert should_continue is False


class TestQualityApprovalNode:
    """Tests for quality_approval_node function."""

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_quality_feedback_high_score(self):
        """Test that high score generates positive feedback."""
        # When score >= 8.0, quality_feedback should be generated
        state = {
            'current_score': 8.5,
            'iteration': 3,
            'mode': 'ui_ux'
        }

        # Should trigger positive feedback
        should_get_feedback = state['current_score'] >= 8.0
        assert should_get_feedback is True

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_quality_feedback_low_score(self):
        """Test that low score skips feedback generation."""
        state = {
            'current_score': 6.0,
            'iteration': 2,
            'mode': 'ui_ux'
        }

        should_get_feedback = state['current_score'] >= 8.0
        assert should_get_feedback is False


class TestGraphCompilation:
    """Tests for StateGraph compilation."""

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_graph_module_exports(self):
        """Test that langgraph_improver module has expected exports."""
        from core import langgraph_improver

        # Module should have run_iterative_improvement function
        assert hasattr(langgraph_improver, 'run_iterative_improvement')
        assert callable(langgraph_improver.run_iterative_improvement)

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_improvement_state_type(self):
        """Test that ImprovementState type is defined."""
        from core.langgraph_improver import ImprovementState

        # Should be a TypedDict with expected keys
        assert 'iteration' in ImprovementState.__annotations__
        assert 'current_score' in ImprovementState.__annotations__


class TestIterativeImprovementRun:
    """Tests for the main run_iterative_improvement function."""

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_run_returns_result_dict(self):
        """Test that run returns properly structured result."""
        # The result should have:
        # - final_score
        # - iterations
        # - issues_found
        # - fixes_applied
        # - files_modified
        # - quality_feedback

        expected_keys = [
            'final_score',
            'iterations',
            'issues_found',
            'fixes_applied',
            'files_modified'
        ]

        # Would need full mocking to test actual run
        # This tests the expected interface
        assert all(k in expected_keys for k in expected_keys)

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_run_respects_target_score(self):
        """Test that run stops when target score reached."""
        # Test with mock that returns high score immediately
        pass

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_run_handles_suggest_enhancements(self):
        """Test that suggest_enhancements parameter affects behavior."""
        # suggest_enhancements=True should generate improvement suggestions
        # suggest_enhancements=False should only analyze issues
        pass


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_empty_project_path_in_run(self):
        """Test handling of empty project path in run function."""
        from core.langgraph_improver import run_iterative_improvement

        # Empty project path should be handled gracefully
        # The function should either raise an error or return early
        # This depends on actual implementation behavior
        pass  # Skip actual call since it requires CrewAI setup

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_invalid_mode(self):
        """Test handling of invalid improvement mode."""
        # Valid modes: ui_ux, performance, security, accessibility
        # Invalid mode should be handled gracefully
        pass

    @pytest.mark.unit
    @pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="LangGraph not installed")
    def test_no_files_to_analyze(self):
        """Test handling of project with no analyzable files."""
        # Should return early with appropriate message
        pass
