"""
Tests for the Agent Result Caching System (core/agent_cache.py)
"""

import pytest
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
import pickle
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent_cache import AgentCache


class TestAgentCacheInit:
    """Tests for AgentCache initialization."""

    @pytest.mark.unit
    def test_init_creates_cache_dir(self, temp_dir):
        """Test that initialization creates the cache directory."""
        cache = AgentCache(temp_dir, ttl_hours=24)
        assert (temp_dir / "agent_cache").exists()
        assert (temp_dir / "agent_cache").is_dir()

    @pytest.mark.unit
    def test_init_with_custom_ttl(self, temp_dir):
        """Test initialization with custom TTL."""
        cache = AgentCache(temp_dir, ttl_hours=48)
        assert cache.ttl == timedelta(hours=48)

    @pytest.mark.unit
    def test_init_default_ttl(self, temp_dir):
        """Test initialization with default TTL of 24 hours."""
        cache = AgentCache(temp_dir)
        assert cache.ttl == timedelta(hours=24)


class TestFileHashing:
    """Tests for file content hashing."""

    @pytest.mark.unit
    def test_get_file_hash_consistent(self, temp_dir):
        """Test that same file content produces same hash."""
        cache = AgentCache(temp_dir)

        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text("def hello(): pass")

        hash1 = cache._get_file_hash(str(test_file))
        hash2 = cache._get_file_hash(str(test_file))

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    @pytest.mark.unit
    def test_get_file_hash_different_content(self, temp_dir):
        """Test that different content produces different hash."""
        cache = AgentCache(temp_dir)

        file1 = temp_dir / "file1.py"
        file2 = temp_dir / "file2.py"
        file1.write_text("def foo(): pass")
        file2.write_text("def bar(): pass")

        hash1 = cache._get_file_hash(str(file1))
        hash2 = cache._get_file_hash(str(file2))

        assert hash1 != hash2

    @pytest.mark.unit
    def test_get_file_hash_nonexistent_file(self, temp_dir):
        """Test hashing a nonexistent file returns error-based hash."""
        cache = AgentCache(temp_dir)
        hash_result = cache._get_file_hash(str(temp_dir / "nonexistent.py"))

        # Should return a hash (error-based), not raise exception
        assert len(hash_result) == 64


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    @pytest.mark.unit
    def test_cache_key_format(self, temp_dir):
        """Test cache key format: filename_hash[:16]_mode."""
        cache = AgentCache(temp_dir)

        key = cache._get_cache_key("/path/to/file.py", "abcd1234efgh5678ijkl9012", "ui_ux")

        assert key == "file.py_abcd1234efgh5678_ui_ux"

    @pytest.mark.unit
    def test_cache_key_different_modes(self, temp_dir):
        """Test that different modes produce different cache keys."""
        cache = AgentCache(temp_dir)
        file_hash = "abcd1234efgh5678ijkl9012"

        key1 = cache._get_cache_key("/path/file.py", file_hash, "ui_ux")
        key2 = cache._get_cache_key("/path/file.py", file_hash, "performance")

        assert key1 != key2
        assert "ui_ux" in key1
        assert "performance" in key2


class TestCacheOperations:
    """Tests for cache get/set operations."""

    @pytest.mark.unit
    def test_set_and_get_cached_analysis(self, temp_dir, sample_code_file):
        """Test setting and retrieving cached analysis."""
        cache = AgentCache(temp_dir)
        issues = [
            {"type": "ui_ux", "severity": "medium", "description": "Button too small"},
            {"type": "ui_ux", "severity": "low", "description": "Missing hover state"}
        ]

        # Set cache
        cache.set_cached_analysis(sample_code_file, "ui_ux", issues)

        # Get cache
        cached = cache.get_cached_analysis(sample_code_file, "ui_ux")

        assert cached is not None
        assert len(cached) == 2
        assert cached[0]["type"] == "ui_ux"

    @pytest.mark.unit
    def test_cache_miss_no_entry(self, temp_dir, sample_code_file):
        """Test cache miss when no entry exists."""
        cache = AgentCache(temp_dir)
        cached = cache.get_cached_analysis(sample_code_file, "ui_ux")
        assert cached is None

    @pytest.mark.unit
    def test_cache_invalidation_on_file_change(self, temp_dir):
        """Test that cache is invalidated when file content changes."""
        cache = AgentCache(temp_dir)

        # Create file and cache
        test_file = temp_dir / "test.py"
        test_file.write_text("original content")

        issues = [{"type": "test", "description": "Issue 1"}]
        cache.set_cached_analysis(str(test_file), "ui_ux", issues)

        # Verify cache hit
        cached = cache.get_cached_analysis(str(test_file), "ui_ux")
        assert cached is not None

        # Modify file content
        test_file.write_text("modified content")

        # Cache should miss (content hash changed)
        cached = cache.get_cached_analysis(str(test_file), "ui_ux")
        assert cached is None

    @pytest.mark.unit
    def test_cache_different_modes_separate(self, temp_dir, sample_code_file):
        """Test that different modes have separate cache entries."""
        cache = AgentCache(temp_dir)

        issues_ui = [{"type": "ui_ux", "description": "UI issue"}]
        issues_perf = [{"type": "performance", "description": "Perf issue"}]

        cache.set_cached_analysis(sample_code_file, "ui_ux", issues_ui)
        cache.set_cached_analysis(sample_code_file, "performance", issues_perf)

        cached_ui = cache.get_cached_analysis(sample_code_file, "ui_ux")
        cached_perf = cache.get_cached_analysis(sample_code_file, "performance")

        assert cached_ui[0]["type"] == "ui_ux"
        assert cached_perf[0]["type"] == "performance"


class TestCacheTTL:
    """Tests for cache TTL (time-to-live) functionality."""

    @pytest.mark.unit
    def test_cache_expires_after_ttl(self, temp_dir, sample_code_file):
        """Test that cache expires after TTL."""
        # Create cache with very short TTL for testing
        cache = AgentCache(temp_dir, ttl_hours=0)  # 0 hours = immediate expiry
        cache.ttl = timedelta(seconds=0)  # Override to 0 seconds

        issues = [{"type": "test", "description": "Test issue"}]
        cache.set_cached_analysis(sample_code_file, "ui_ux", issues)

        # Wait a tiny bit
        time.sleep(0.1)

        # Should be expired
        cached = cache.get_cached_analysis(sample_code_file, "ui_ux")
        assert cached is None

    @pytest.mark.unit
    def test_cache_valid_within_ttl(self, temp_dir, sample_code_file):
        """Test that cache is valid within TTL."""
        cache = AgentCache(temp_dir, ttl_hours=24)

        issues = [{"type": "test", "description": "Test issue"}]
        cache.set_cached_analysis(sample_code_file, "ui_ux", issues)

        # Should still be valid
        cached = cache.get_cached_analysis(sample_code_file, "ui_ux")
        assert cached is not None


class TestCacheManagement:
    """Tests for cache management operations."""

    @pytest.mark.unit
    def test_clear_cache(self, temp_dir, sample_code_file):
        """Test clearing all cache entries."""
        cache = AgentCache(temp_dir)

        # Add multiple entries
        for i in range(5):
            cache.set_cached_analysis(sample_code_file, f"mode_{i}", [{"id": i}])

        # Clear all
        count = cache.clear_cache()

        assert count == 5
        assert len(list((temp_dir / "agent_cache").glob("*.pkl"))) == 0

    @pytest.mark.unit
    def test_clear_expired(self, temp_dir, sample_code_file):
        """Test clearing only expired entries."""
        cache = AgentCache(temp_dir, ttl_hours=24)

        # Add an entry
        cache.set_cached_analysis(sample_code_file, "mode_1", [{"id": 1}])

        # No expired entries yet
        count = cache.clear_expired()
        assert count == 0

    @pytest.mark.unit
    def test_get_cache_stats(self, temp_dir, sample_code_file):
        """Test getting cache statistics."""
        cache = AgentCache(temp_dir, ttl_hours=24)

        # Add entries
        for i in range(3):
            cache.set_cached_analysis(sample_code_file, f"mode_{i}", [{"id": i}])

        stats = cache.get_cache_stats()

        assert stats['total_entries'] == 3
        assert stats['expired_entries'] == 0
        assert stats['total_size_mb'] >= 0
        assert stats['ttl_hours'] == 24.0


class TestCacheEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.unit
    def test_corrupted_cache_file(self, temp_dir, sample_code_file):
        """Test handling of corrupted cache file."""
        cache = AgentCache(temp_dir)

        # Set valid cache
        cache.set_cached_analysis(sample_code_file, "ui_ux", [{"id": 1}])

        # Corrupt the cache file
        cache_files = list((temp_dir / "agent_cache").glob("*.pkl"))
        assert len(cache_files) == 1
        cache_files[0].write_bytes(b"corrupted data")

        # Should return None and delete corrupted file
        cached = cache.get_cached_analysis(sample_code_file, "ui_ux")
        assert cached is None

    @pytest.mark.unit
    def test_empty_issues_list(self, temp_dir, sample_code_file):
        """Test caching empty issues list."""
        cache = AgentCache(temp_dir)

        cache.set_cached_analysis(sample_code_file, "ui_ux", [])
        cached = cache.get_cached_analysis(sample_code_file, "ui_ux")

        assert cached == []

    @pytest.mark.unit
    def test_large_issues_list(self, temp_dir, sample_code_file):
        """Test caching large issues list."""
        cache = AgentCache(temp_dir)

        # Create 1000 issues
        issues = [{"id": i, "description": f"Issue {i}" * 100} for i in range(1000)]

        cache.set_cached_analysis(sample_code_file, "ui_ux", issues)
        cached = cache.get_cached_analysis(sample_code_file, "ui_ux")

        assert len(cached) == 1000
