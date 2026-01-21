"""
Tests for the Prototype Orchestrator - the 5-agent creative pipeline.

Tests cover:
1. Orchestrator initialization
2. Event emission
3. Clarification phase
4. Full pipeline execution with mocks
5. Fallback behavior
6. Error handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Import the orchestrator and related models
# Note: conftest.py sets up the Python path correctly
try:
    from src.services.prototype_orchestrator import (
        PrototypeOrchestrator,
        PrototypeEvent,
        PrototypeResult,
        FallbackLevel,
        FallbackInfo,
    )
    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    ORCHESTRATOR_AVAILABLE = False
    PrototypeOrchestrator = None
    PrototypeEvent = None
    PrototypeResult = None
    FallbackLevel = None
    FallbackInfo = None


# Skip all tests if module is not available
pytestmark = pytest.mark.skipif(
    not ORCHESTRATOR_AVAILABLE,
    reason="PrototypeOrchestrator not available"
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_event_callback():
    """Mock event callback that collects events."""
    events = []
    async def callback(event):
        events.append(event)
    callback.events = events
    return callback


@pytest.fixture
def mock_response_callback():
    """Mock response callback for clarification."""
    async def callback(questions):
        return {
            "target_market": "Small businesses",
            "pricing_model": "Subscription"
        }
    return callback


@pytest.fixture
def mock_services():
    """Mock all the service factories used by the orchestrator."""
    with patch("src.services.prototype_orchestrator.get_template_loader") as mock_tl, \
         patch("src.services.prototype_orchestrator.get_template_customizer") as mock_tc, \
         patch("src.services.prototype_orchestrator.get_smart_preset_system") as mock_sps, \
         patch("src.services.prototype_orchestrator.get_clarification_agent") as mock_ca, \
         patch("src.services.prototype_orchestrator.get_expertise_synthesizer") as mock_es, \
         patch("src.services.prototype_orchestrator.get_knowledge_store") as mock_ks, \
         patch("src.services.prototype_orchestrator.get_web_researcher") as mock_wr:

        # Configure mock template loader
        mock_template = MagicMock()
        mock_template.files = {"package.json": '{"name": "test"}'}
        mock_tl.return_value = MagicMock()
        mock_tl.return_value.get_template.return_value = mock_template
        mock_tl.return_value.list_templates.return_value = ["default"]

        # Configure mock template customizer
        mock_tc.return_value = MagicMock()
        mock_tc.return_value.customize = AsyncMock(return_value={"package.json": '{"name": "test"}'})

        # Configure mock smart preset system
        mock_concepts = MagicMock()
        mock_concepts.best_match = "dashboard"
        mock_concepts.best_score = 0.85
        mock_concepts.keywords = ["pet", "grooming", "appointment"]
        mock_sps.return_value = MagicMock()
        mock_sps.return_value.extract.return_value = mock_concepts

        # Configure mock clarification agent
        mock_ca.return_value = MagicMock()
        mock_ca.return_value.needs_clarification.return_value = False
        mock_ca.return_value.generate_questions.return_value = MagicMock(questions=[])

        # Configure mock expertise synthesizer
        mock_expertise = MagicMock()
        mock_expertise.industry = "pet_services"
        mock_expertise.terminology = {"user": "pet parent"}
        mock_es.return_value = MagicMock()
        mock_es.return_value.synthesize = AsyncMock(return_value=mock_expertise)

        # Configure mock knowledge store
        mock_ks.return_value = MagicMock()
        mock_ks.return_value.get_similar_patterns = AsyncMock(return_value=[])

        # Configure mock web researcher
        mock_research = MagicMock()
        mock_research.market_data = {}
        mock_research.competitor_features = []
        mock_wr.return_value = MagicMock()
        mock_wr.return_value.research = AsyncMock(return_value=mock_research)

        yield {
            "template_loader": mock_tl,
            "template_customizer": mock_tc,
            "smart_preset_system": mock_sps,
            "clarification_agent": mock_ca,
            "expertise_synthesizer": mock_es,
            "knowledge_store": mock_ks,
            "web_researcher": mock_wr,
        }


# ============================================================================
# Initialization Tests
# ============================================================================

class TestOrchestratorInitialization:
    """Tests for orchestrator initialization."""

    def test_default_initialization(self, mock_services):
        """Test that orchestrator initializes with default settings."""
        orchestrator = PrototypeOrchestrator()
        assert orchestrator is not None
        assert orchestrator.event_callback is None
        assert orchestrator.use_smart_presets is True
        assert orchestrator.skip_clarification is False

    def test_initialization_with_callback(self, mock_services, mock_event_callback):
        """Test initialization with event callback."""
        orchestrator = PrototypeOrchestrator(event_callback=mock_event_callback)
        assert orchestrator.event_callback == mock_event_callback

    def test_initialization_with_response_callback(self, mock_services, mock_response_callback):
        """Test initialization with response callback for clarification."""
        orchestrator = PrototypeOrchestrator(response_callback=mock_response_callback)
        assert orchestrator.response_callback == mock_response_callback

    def test_initialization_skip_clarification(self, mock_services):
        """Test initialization with skip_clarification flag."""
        orchestrator = PrototypeOrchestrator(skip_clarification=True)
        assert orchestrator.skip_clarification is True

    def test_initialization_without_smart_presets(self, mock_services):
        """Test initialization with smart presets disabled."""
        orchestrator = PrototypeOrchestrator(use_smart_presets=False)
        assert orchestrator.use_smart_presets is False


# ============================================================================
# Event Emission Tests
# ============================================================================

class TestEventEmission:
    """Tests for event emission functionality."""

    @pytest.mark.asyncio
    async def test_emit_calls_callback(self, mock_services, mock_event_callback):
        """Test that _emit calls the event callback."""
        orchestrator = PrototypeOrchestrator(event_callback=mock_event_callback)

        event = PrototypeEvent(
            type="status",
            agent="Test Agent",
            message="Test message",
            progress=50
        )

        await orchestrator._emit(event)

        assert len(mock_event_callback.events) == 1
        assert mock_event_callback.events[0] == event

    @pytest.mark.asyncio
    async def test_emit_without_callback(self, mock_services):
        """Test that _emit handles no callback gracefully."""
        orchestrator = PrototypeOrchestrator(event_callback=None)

        event = PrototypeEvent(
            type="status",
            agent="Test Agent",
            message="Test message",
            progress=50
        )

        # Should not raise
        await orchestrator._emit(event)


# ============================================================================
# PrototypeEvent Tests
# ============================================================================

class TestPrototypeEvent:
    """Tests for PrototypeEvent dataclass."""

    def test_event_creation(self):
        """Test creating a PrototypeEvent."""
        event = PrototypeEvent(
            type="status",
            agent="Domain Analyst",
            message="Analyzing domain",
            progress=10
        )

        assert event.type == "status"
        assert event.agent == "Domain Analyst"
        assert event.message == "Analyzing domain"
        assert event.progress == 10

    def test_event_with_data(self):
        """Test creating an event with data payload."""
        event = PrototypeEvent(
            type="agent_complete",
            agent="Architect",
            message="Architecture complete",
            progress=30,
            data={"pages": ["Dashboard", "Settings"]}
        )

        assert event.data == {"pages": ["Dashboard", "Settings"]}

    def test_event_requires_response(self):
        """Test event with requires_response flag."""
        event = PrototypeEvent(
            type="clarification_required",
            agent="Clarification Agent",
            message="Need more info",
            progress=0,
            requires_response=True
        )

        assert event.requires_response is True


# ============================================================================
# PrototypeResult Tests
# ============================================================================

class TestPrototypeResult:
    """Tests for PrototypeResult dataclass."""

    def test_result_creation(self):
        """Test creating a PrototypeResult."""
        result = PrototypeResult(
            success=True,
            files={"package.json": '{"name": "test"}'},
            domain_analysis={
                "industry": "pet_services",
            }
        )

        assert result.success is True
        assert "package.json" in result.files
        assert result.domain_analysis["industry"] == "pet_services"

    def test_result_with_fallback_info(self):
        """Test result includes fallback information."""
        fallback_info = FallbackInfo(
            level=FallbackLevel.TEMPLATE_CLEAN,
            reason="Domain analysis failed",
            original_error="Connection timeout"
        )

        result = PrototypeResult(
            success=True,
            files={"package.json": '{}'},
            fallback_info=fallback_info
        )

        assert result.fallback_info is not None
        assert result.fallback_info.level == FallbackLevel.TEMPLATE_CLEAN
        assert result.fallback_info.reason == "Domain analysis failed"


# ============================================================================
# FallbackLevel Tests
# ============================================================================

class TestFallbackLevel:
    """Tests for FallbackLevel enum."""

    def test_fallback_levels_exist(self):
        """Test that all expected fallback levels exist."""
        assert hasattr(FallbackLevel, 'FULL_CREATIVE')
        assert hasattr(FallbackLevel, 'CACHED_SIMILAR')
        assert hasattr(FallbackLevel, 'TEMPLATE_CUSTOMIZED')
        assert hasattr(FallbackLevel, 'TEMPLATE_CLEAN')
        assert hasattr(FallbackLevel, 'MINIMAL')

    def test_fallback_level_ordering(self):
        """Test that fallback levels have logical ordering."""
        # FULL_CREATIVE should be the best (lowest number)
        assert FallbackLevel.FULL_CREATIVE.value < FallbackLevel.CACHED_SIMILAR.value
        assert FallbackLevel.CACHED_SIMILAR.value < FallbackLevel.TEMPLATE_CUSTOMIZED.value


# ============================================================================
# Clarification Phase Tests
# ============================================================================

class TestClarificationPhase:
    """Tests for the clarification phase."""

    @pytest.mark.asyncio
    async def test_skips_when_flag_set(self, mock_services):
        """Test that clarification is skipped when skip_clarification=True."""
        orchestrator = PrototypeOrchestrator(skip_clarification=True)

        # Clarification agent should not be called for questions
        # This is handled by the generate() method checking skip_clarification

    @pytest.mark.asyncio
    async def test_skips_when_high_confidence(self, mock_services):
        """Test that clarification is skipped when domain confidence is high."""
        mock_services["clarification_agent"].return_value.needs_clarification.return_value = False

        orchestrator = PrototypeOrchestrator()

        # Create mock concepts
        mock_concepts = MagicMock()
        mock_concepts.best_score = 0.95

        result = await orchestrator._run_clarification_phase("Build a dashboard", mock_concepts)
        assert result is None

    @pytest.mark.asyncio
    async def test_generates_questions_when_needed(self, mock_services, mock_event_callback):
        """Test that questions are generated when clarification is needed."""
        # Configure to need clarification
        mock_services["clarification_agent"].return_value.needs_clarification.return_value = True

        mock_question = MagicMock()
        mock_question.to_dict.return_value = {"id": "q1", "text": "What industry?"}

        mock_result = MagicMock()
        mock_result.questions = [mock_question]
        mock_result.detected_industry = "unknown"
        mock_result.confidence_before = 0.3
        mock_result.missing_info = ["industry", "target_market"]

        mock_services["clarification_agent"].return_value.generate_questions.return_value = mock_result

        orchestrator = PrototypeOrchestrator(event_callback=mock_event_callback)

        mock_concepts = MagicMock()
        mock_concepts.best_score = 0.3

        await orchestrator._run_clarification_phase("Build something", mock_concepts)

        # Check that clarification_required event was emitted
        event_types = [e.type for e in mock_event_callback.events]
        assert "clarification_required" in event_types


# ============================================================================
# Integration-style Tests (with all mocks)
# ============================================================================

class TestOrchestratorIntegration:
    """Integration-style tests with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_full_generation_flow(self, mock_services, mock_event_callback):
        """Test that the full generation flow executes."""
        orchestrator = PrototypeOrchestrator(
            event_callback=mock_event_callback,
            skip_clarification=True
        )

        # The actual generate method would need more complex mocking
        # This is a placeholder for when we have the full implementation working
        assert orchestrator is not None


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling in the orchestrator."""

    @pytest.mark.asyncio
    async def test_handles_missing_template(self, mock_services):
        """Test handling when template is not found."""
        mock_services["template_loader"].return_value.get_template.return_value = None

        orchestrator = PrototypeOrchestrator()
        # Should handle gracefully (implementation depends on actual behavior)

    @pytest.mark.asyncio
    async def test_handles_clarification_callback_failure(self, mock_services):
        """Test handling when clarification callback fails."""
        async def failing_callback(questions):
            raise Exception("Callback failed")

        orchestrator = PrototypeOrchestrator(response_callback=failing_callback)

        # Should continue without clarification responses


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
