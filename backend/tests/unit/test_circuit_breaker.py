"""Unit tests for CircuitBreaker"""
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from app.services.circuit_breaker import CircuitBreaker


class TestCircuitBreaker:
    """Test class for CircuitBreaker"""

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker initial state"""
        cb = CircuitBreaker(name="Test", failure_threshold=3, timeout=60)

        assert cb.state == "CLOSED"
        assert cb.failures == 0
        assert cb.last_failure_time is None

    def test_circuit_breaker_successful_call(self):
        """Test successful call through circuit breaker"""
        cb = CircuitBreaker(name="Test", failure_threshold=3, timeout=60)

        def successful_func():
            return "success"

        result = cb.call(successful_func)

        assert result == "success"
        assert cb.state == "CLOSED"
        assert cb.failures == 0

    def test_circuit_breaker_failure_below_threshold(self):
        """Test failure below threshold keeps circuit closed"""
        cb = CircuitBreaker(name="Test", failure_threshold=3, timeout=60)

        def failing_func():
            raise Exception("Test error")

        # First failure
        with pytest.raises(Exception, match="Test error"):
            cb.call(failing_func)

        assert cb.state == "CLOSED"
        assert cb.failures == 1

        # Second failure
        with pytest.raises(Exception, match="Test error"):
            cb.call(failing_func)

        assert cb.state == "CLOSED"
        assert cb.failures == 2

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit opens after reaching failure threshold"""
        cb = CircuitBreaker(name="Test", failure_threshold=3, timeout=60)

        def failing_func():
            raise Exception("Test error")

        # Trigger 3 failures
        for i in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == "OPEN"
        assert cb.failures == 3
        assert cb.last_failure_time is not None

    def test_circuit_breaker_rejects_calls_when_open(self):
        """Test circuit breaker rejects calls when open"""
        cb = CircuitBreaker(name="Test", failure_threshold=3, timeout=60)

        def failing_func():
            raise Exception("Test error")

        # Trigger failures to open circuit
        for i in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)

        # Circuit should be open
        assert cb.state == "OPEN"

        # Subsequent call should fail immediately with circuit breaker message
        with pytest.raises(Exception) as exc_info:
            cb.call(lambda: "should not execute")

        # Check that it's the circuit breaker exception, not the function exception
        assert "一時的にサービスが利用できません" in str(exc_info.value) or "circuit breaker" in str(exc_info.value).lower()

    def test_circuit_breaker_transitions_to_half_open(self):
        """Test circuit transitions to half-open after timeout"""
        cb = CircuitBreaker(name="Test", failure_threshold=3, timeout=1)  # 1 second timeout

        def failing_func():
            raise Exception("Test error")

        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == "OPEN"

        # Wait for timeout
        time.sleep(1.1)

        # Next call should transition to HALF_OPEN, then fail and stay OPEN
        with pytest.raises(Exception, match="Test error"):
            cb.call(failing_func)

        # State should be OPEN again (because the call failed)
        assert cb.state == "OPEN"

    def test_circuit_breaker_closes_after_successful_half_open(self):
        """Test circuit closes after successful call in half-open state"""
        cb = CircuitBreaker(name="Test", failure_threshold=3, timeout=1)  # 1 second timeout

        def failing_func():
            raise Exception("Test error")

        def successful_func():
            return "success"

        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == "OPEN"

        # Wait for timeout
        time.sleep(1.1)

        # Successful call should transition from OPEN -> HALF_OPEN -> CLOSED
        result = cb.call(successful_func)

        assert result == "success"
        assert cb.state == "CLOSED"
        assert cb.failures == 0

    def test_circuit_breaker_reset(self):
        """Test manual reset of circuit breaker"""
        cb = CircuitBreaker(name="Test", failure_threshold=3, timeout=60)

        def failing_func():
            raise Exception("Test error")

        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == "OPEN"
        assert cb.failures == 3

        # Reset
        cb.reset()

        assert cb.state == "CLOSED"
        assert cb.failures == 0
        assert cb.last_failure_time is None

    def test_circuit_breaker_get_state(self):
        """Test getting circuit breaker state"""
        cb = CircuitBreaker(name="TestService", failure_threshold=5, timeout=120)

        state = cb.get_state()

        assert state["name"] == "TestService"
        assert state["state"] == "CLOSED"
        assert state["failures"] == 0
        assert state["failure_threshold"] == 5
        assert state["timeout"] == 120
        assert state["last_failure_time"] is None

    def test_circuit_breaker_call_with_args_and_kwargs(self):
        """Test circuit breaker with function arguments"""
        cb = CircuitBreaker(name="Test", failure_threshold=3, timeout=60)

        def func_with_args(x, y, z=3):
            return x + y + z

        result = cb.call(func_with_args, 1, 2, z=4)
        assert result == 7

    def test_circuit_breaker_multiple_successes_after_failures(self):
        """Test that circuit remains closed after successes following failures"""
        cb = CircuitBreaker(name="Test", failure_threshold=5, timeout=60)

        call_count = 0

        def intermittent_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Temporary error")
            return "success"

        # First two calls fail
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(intermittent_func)

        assert cb.state == "CLOSED"  # Still below threshold
        assert cb.failures == 2

        # Next call succeeds
        result = cb.call(intermittent_func)

        assert result == "success"
        assert cb.state == "CLOSED"
        assert cb.failures == 0  # Reset after success

    def test_circuit_breaker_default_settings(self):
        """Test circuit breaker with default settings from config"""
        cb = CircuitBreaker(name="Test")

        # Should use settings from config
        assert cb.failure_threshold > 0
        assert cb.timeout > 0
