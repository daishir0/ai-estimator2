"""Unit tests for RetryService"""
import pytest
import time
from unittest.mock import Mock, patch
from app.services.retry_service import (
    retry_with_exponential_backoff,
    retry_with_custom_backoff
)


class TestRetryService:
    """Test class for RetryService"""

    def test_retry_with_exponential_backoff_success_first_attempt(self):
        """Test successful execution on first attempt"""
        call_count = 0

        @retry_with_exponential_backoff(max_retries=3, initial_delay=0.1, backoff_factor=2.0)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()

        assert result == "success"
        assert call_count == 1

    def test_retry_with_exponential_backoff_success_after_retries(self):
        """Test successful execution after retries"""
        call_count = 0

        @retry_with_exponential_backoff(max_retries=3, initial_delay=0.1, backoff_factor=2.0)
        def function_succeeds_on_third_attempt():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return "success"

        result = function_succeeds_on_third_attempt()

        assert result == "success"
        assert call_count == 3

    def test_retry_with_exponential_backoff_failure_after_max_retries(self):
        """Test failure after reaching max retries"""
        call_count = 0

        @retry_with_exponential_backoff(max_retries=3, initial_delay=0.1, backoff_factor=2.0)
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception("Permanent error")

        with pytest.raises(Exception, match="Permanent error"):
            always_failing_function()

        assert call_count == 3

    def test_retry_with_exponential_backoff_delay_timing(self):
        """Test exponential backoff delay timing"""
        call_times = []

        @retry_with_exponential_backoff(max_retries=3, initial_delay=0.1, backoff_factor=2.0)
        def function_with_timing():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception("Retry needed")
            return "success"

        result = function_with_timing()

        assert result == "success"
        assert len(call_times) == 3

        # Check delays: first retry ~0.1s, second retry ~0.2s
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        # Allow 50ms tolerance
        assert 0.05 < delay1 < 0.15  # ~0.1s
        assert 0.15 < delay2 < 0.25  # ~0.2s

    def test_retry_with_exponential_backoff_specific_exceptions(self):
        """Test retry with specific exception types"""
        call_count = 0

        @retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=0.1,
            backoff_factor=2.0,
            exceptions=(ValueError,)
        )
        def function_with_specific_exception():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Retryable error")
            return "success"

        result = function_with_specific_exception()
        assert result == "success"
        assert call_count == 2

    def test_retry_with_exponential_backoff_non_retryable_exception(self):
        """Test that non-retryable exceptions are not caught"""
        call_count = 0

        @retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=0.1,
            backoff_factor=2.0,
            exceptions=(ValueError,)
        )
        def function_with_non_retryable_exception():
            nonlocal call_count
            call_count += 1
            raise TypeError("Non-retryable error")

        with pytest.raises(TypeError, match="Non-retryable error"):
            function_with_non_retryable_exception()

        # Should fail immediately without retry
        assert call_count == 1

    def test_retry_with_custom_backoff_success(self):
        """Test custom backoff with success"""
        call_count = 0

        @retry_with_custom_backoff([0, 0.1, 0.2])
        def function_succeeds_on_second_attempt():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary error")
            return "success"

        result = function_succeeds_on_second_attempt()

        assert result == "success"
        assert call_count == 2

    def test_retry_with_custom_backoff_failure(self):
        """Test custom backoff with failure"""
        call_count = 0

        @retry_with_custom_backoff([0, 0.1, 0.2])
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception("Permanent error")

        with pytest.raises(Exception, match="Permanent error"):
            always_failing_function()

        assert call_count == 3

    def test_retry_with_custom_backoff_timing(self):
        """Test custom backoff delay timing"""
        call_times = []

        @retry_with_custom_backoff([0, 0.1, 0.2])
        def function_with_timing():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception("Retry needed")
            return "success"

        result = function_with_timing()

        assert result == "success"
        assert len(call_times) == 3

        # Check delays
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        # Allow 50ms tolerance
        assert 0.05 < delay1 < 0.15  # ~0.1s
        assert 0.15 < delay2 < 0.25  # ~0.2s

    def test_retry_preserves_function_metadata(self):
        """Test that decorator preserves function metadata"""
        @retry_with_exponential_backoff()
        def example_function():
            """Example docstring"""
            return "result"

        assert example_function.__name__ == "example_function"
        assert example_function.__doc__ == "Example docstring"

    def test_retry_with_args_and_kwargs(self):
        """Test retry with function arguments"""
        @retry_with_exponential_backoff(max_retries=3, initial_delay=0.1, backoff_factor=2.0)
        def function_with_args(x, y, z=3):
            return x + y + z

        result = function_with_args(1, 2, z=4)
        assert result == 7
