"""Unit tests for rate limiter (TODO-9)"""
import pytest
import time
from datetime import datetime, timedelta
from app.core.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test RateLimiter class"""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60

    def test_allow_requests_within_limit(self):
        """Test that requests within limit are allowed"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        client_id = "test_client_1"

        # First 5 requests should be allowed
        for i in range(5):
            is_allowed, retry_after = limiter.check_limit(client_id)
            assert is_allowed is True
            assert retry_after is None

    def test_block_requests_exceeding_limit(self):
        """Test that requests exceeding limit are blocked"""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        client_id = "test_client_2"

        # First 3 requests allowed
        for i in range(3):
            is_allowed, _ = limiter.check_limit(client_id)
            assert is_allowed is True

        # 4th request should be blocked
        is_allowed, retry_after = limiter.check_limit(client_id)
        assert is_allowed is False
        assert retry_after is not None
        assert retry_after > 0

    def test_get_remaining(self):
        """Test get_remaining method"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        client_id = "test_client_3"

        # Initially 10 requests remaining
        assert limiter.get_remaining(client_id) == 10

        # After 3 requests, 7 remaining
        for i in range(3):
            limiter.check_limit(client_id)
        assert limiter.get_remaining(client_id) == 7

    def test_reset_client(self):
        """Test reset_client method"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        client_id = "test_client_4"

        # Use up all requests
        for i in range(5):
            limiter.check_limit(client_id)

        # Reset
        limiter.reset_client(client_id)

        # Should be able to make requests again
        is_allowed, _ = limiter.check_limit(client_id)
        assert is_allowed is True

    def test_get_status(self):
        """Test get_status method"""
        limiter = RateLimiter(max_requests=100, window_seconds=3600)
        status = limiter.get_status()

        assert status["max_requests"] == 100
        assert status["window_seconds"] == 3600
        assert "active_clients" in status

    def test_multiple_clients(self):
        """Test that different clients are tracked independently"""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        client1 = "client_1"
        client2 = "client_2"

        # Client 1 uses 2 requests
        for i in range(2):
            is_allowed, _ = limiter.check_limit(client1)
            assert is_allowed is True

        # Client 1 should be blocked
        is_allowed, _ = limiter.check_limit(client1)
        assert is_allowed is False

        # Client 2 should still be allowed
        is_allowed, _ = limiter.check_limit(client2)
        assert is_allowed is True
