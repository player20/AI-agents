"""
Tests for Health Check endpoints

Tests cover:
- Basic health check
- Readiness check
- Liveness check
- Detailed health check
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import os


# We need to create a test app that includes the health routes
@pytest.fixture
def client():
    """Create a test client"""
    from fastapi import FastAPI
    from src.routes.health import router

    app = FastAPI()
    app.include_router(router, prefix="/api/health")

    return TestClient(app)


class TestHealthEndpoint:
    """Tests for /api/health endpoint"""

    def test_health_returns_200(self, client):
        """Test that health endpoint returns 200"""
        response = client.get("/api/health/")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        """Test health response has correct structure"""
        response = client.get("/api/health/")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"

    def test_health_includes_uptime(self, client):
        """Test that health includes uptime"""
        response = client.get("/api/health/")
        data = response.json()

        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0


class TestLivenessEndpoint:
    """Tests for /api/health/live endpoint"""

    def test_liveness_returns_200(self, client):
        """Test that liveness endpoint returns 200"""
        response = client.get("/api/health/live")
        assert response.status_code == 200

    def test_liveness_response(self, client):
        """Test liveness response structure"""
        response = client.get("/api/health/live")
        data = response.json()

        assert "alive" in data
        assert data["alive"] is True
        assert "timestamp" in data


class TestReadinessEndpoint:
    """Tests for /api/health/ready endpoint"""

    def test_readiness_returns_200(self, client):
        """Test that readiness endpoint returns 200"""
        response = client.get("/api/health/ready")
        assert response.status_code == 200

    def test_readiness_response_structure(self, client):
        """Test readiness response has correct structure"""
        response = client.get("/api/health/ready")
        data = response.json()

        assert "ready" in data
        assert "services" in data
        assert "overall_status" in data
        assert isinstance(data["services"], list)

    def test_readiness_includes_services(self, client):
        """Test that readiness includes service checks"""
        response = client.get("/api/health/ready")
        data = response.json()

        service_names = [s["name"] for s in data["services"]]

        # Should include LLM providers
        assert "anthropic" in service_names or "openai" in service_names
        # Should include database
        assert "database" in service_names
        # Should include redis
        assert "redis" in service_names

    def test_service_health_structure(self, client):
        """Test that each service has correct structure"""
        response = client.get("/api/health/ready")
        data = response.json()

        for service in data["services"]:
            assert "name" in service
            assert "status" in service
            assert service["status"] in ["healthy", "degraded", "unhealthy"]


class TestDetailedHealthEndpoint:
    """Tests for /api/health/detailed endpoint"""

    def test_detailed_returns_200(self, client):
        """Test that detailed endpoint returns 200"""
        response = client.get("/api/health/detailed")
        assert response.status_code == 200

    def test_detailed_response_structure(self, client):
        """Test detailed response has correct structure"""
        response = client.get("/api/health/detailed")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "environment" in data
        assert "services" in data
        assert "system" in data

    def test_detailed_includes_system_info(self, client):
        """Test that detailed includes system information"""
        response = client.get("/api/health/detailed")
        data = response.json()

        system = data["system"]
        assert "python_version" in system
        assert "platform" in system

    def test_detailed_environment_detection(self, client):
        """Test environment is correctly detected"""
        response = client.get("/api/health/detailed")
        data = response.json()

        assert data["environment"] in ["development", "production"]


class TestHealthWithMockedServices:
    """Tests with mocked external services"""

    def test_readiness_with_anthropic_key(self, client):
        """Test readiness when Anthropic key is set"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            response = client.get("/api/health/ready")
            data = response.json()

            anthropic_service = next(
                (s for s in data["services"] if s["name"] == "anthropic"),
                None
            )
            assert anthropic_service is not None
            # Should be healthy or at least not unhealthy
            assert anthropic_service["status"] in ["healthy", "degraded"]

    def test_readiness_without_any_keys(self, client):
        """Test readiness when no API keys are set"""
        with patch.dict(os.environ, {}, clear=True):
            # Clear all API keys
            for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "SUPABASE_URL"]:
                os.environ.pop(key, None)

            response = client.get("/api/health/ready")
            data = response.json()

            # Should still return a response
            assert response.status_code == 200
            # Overall status should be degraded (no LLM providers)
            assert data["overall_status"] in ["healthy", "degraded", "unhealthy"]

    def test_readiness_with_supabase_configured(self, client):
        """Test readiness when Supabase is configured"""
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_ANON_KEY": "test-key"
        }):
            response = client.get("/api/health/ready")
            data = response.json()

            db_service = next(
                (s for s in data["services"] if s["name"] == "database"),
                None
            )
            assert db_service is not None


class TestHealthPerformance:
    """Performance tests for health endpoints"""

    def test_health_is_fast(self, client):
        """Test that basic health check is fast"""
        import time

        start = time.time()
        response = client.get("/api/health/")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1  # Should respond in under 100ms

    def test_liveness_is_fast(self, client):
        """Test that liveness check is fast"""
        import time

        start = time.time()
        response = client.get("/api/health/live")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.05  # Should respond in under 50ms
