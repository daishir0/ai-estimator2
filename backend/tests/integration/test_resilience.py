"""Integration tests for resilience features"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.estimator_service import EstimatorService
from app.services.question_service import QuestionService
from app.services.retry_service import retry_with_exponential_backoff
from app.services.circuit_breaker import CircuitBreaker, openai_circuit_breaker
from app.services.loop_detector import LoopDetector


class TestRetryCircuitBreakerIntegration:
    """Integration tests for Retry + CircuitBreaker"""

    def test_retry_then_circuit_breaker_opens(self):
        """Test that circuit breaker opens after multiple retry failures"""
        # Create a new circuit breaker for this test
        cb = CircuitBreaker(name="test_cb", failure_threshold=3, timeout=5)

        # Create a function that always fails
        call_count = {"count": 0}

        @retry_with_exponential_backoff(max_retries=2, initial_delay=0.01)
        def failing_function():
            call_count["count"] += 1
            raise Exception("Simulated failure")

        # Call through circuit breaker multiple times
        for i in range(3):
            try:
                cb.call(failing_function)
            except Exception:
                pass  # Expected to fail

        # Circuit breaker should now be OPEN
        assert cb.state == "OPEN"
        # Total calls = 3 attempts * (1 initial + 1 retry) = 6 calls
        # max_retries=2 means it retries up to 2 times, so total attempts = 1 + min(2, actual_retries)
        # In practice with exponential backoff, it does 2 attempts per call
        assert call_count["count"] == 6

        # Next call should fail immediately due to open circuit
        initial_count = call_count["count"]
        with pytest.raises(Exception) as exc_info:
            cb.call(failing_function)

        # Should not have retried (circuit is open)
        assert call_count["count"] == initial_count
        assert "circuit_breaker_open" in str(exc_info.value) or "一時的にサービスが利用できません" in str(exc_info.value)

    def test_circuit_breaker_recovers_after_timeout(self):
        """Test that circuit breaker transitions to HALF_OPEN and recovers"""
        # Create a circuit breaker with short timeout
        cb = CircuitBreaker(name="test_cb_recovery", failure_threshold=2, timeout=1)

        # Track call count
        call_count = {"count": 0}

        @retry_with_exponential_backoff(max_retries=1, initial_delay=0.01)
        def failing_then_succeeding():
            call_count["count"] += 1
            # Fail for first 2 calls (to open circuit), then succeed on 3rd call (recovery)
            if call_count["count"] <= 2:
                raise Exception("Initial failures")
            return "success"

        # Open the circuit by failing twice
        for i in range(2):
            try:
                cb.call(failing_then_succeeding)
            except Exception:
                pass

        assert cb.state == "OPEN"

        # Wait for timeout
        time.sleep(1.1)

        # Next call should transition to HALF_OPEN and succeed
        result = cb.call(failing_then_succeeding)
        assert result == "success"
        assert cb.state == "CLOSED"


class TestLoopDetectorIntegration:
    """Integration tests for LoopDetector"""

    def test_loop_detector_prevents_infinite_loop(self):
        """Test that loop detector prevents infinite loops"""
        detector = LoopDetector(context_id="test-loop", max_iterations=10)

        processed_items = []

        def process_items(items):
            for item in items:
                detector.check("process_items")
                processed_items.append(item)

        # Process within limit - should succeed
        process_items(range(5))
        assert len(processed_items) == 5

        # Process more items - should fail when exceeding limit
        with pytest.raises(Exception) as exc_info:
            process_items(range(10))  # 5 + 10 = 15 > 10

        assert "max_iterations_exceeded" in str(exc_info.value) or "最大イテレーション数" in str(exc_info.value)


@pytest.mark.integration
class TestResourceLimiterIntegration:
    """Integration tests for ResourceLimiterMiddleware"""

    def test_resource_limiter_allows_within_limit(self, client):
        """Test that requests within limit are processed"""
        # Simple health check should work
        response = client.get("/health")
        assert response.status_code == 200

    def test_resource_limiter_with_concurrent_requests(self):
        """Test resource limiter with concurrent requests"""
        # This test uses TestClient which doesn't support true async concurrency
        # In production, the semaphore would limit concurrent requests

        client = TestClient(app)

        # Make multiple sequential requests (TestClient doesn't support true concurrency)
        responses = []
        for i in range(3):
            response = client.get("/health")
            responses.append(response)

        # All should succeed in sequential mode
        for response in responses:
            assert response.status_code == 200

    def test_file_size_limiter_rejects_large_files(self):
        """Test that file size limiter rejects oversized uploads"""
        client = TestClient(app)

        # Simulate a large file upload with Content-Length header
        large_size = 15 * 1024 * 1024  # 15 MB (exceeds 10 MB limit)

        response = client.post(
            f"/api/v1/tasks",
            headers={"Content-Length": str(large_size)},
            json={"deliverables": [], "system_requirements": "test"}
        )

        # Should be rejected with 413 Payload Too Large
        assert response.status_code == 413
        assert "file_too_large" in response.json()["error"]


@pytest.mark.integration
class TestEndToEndResilience:
    """End-to-end integration tests for resilience features"""

    def test_estimator_service_with_retry_and_circuit_breaker(self, monkeypatch, sample_deliverables, sample_qa_pairs):
        """Test EstimatorService with retry and circuit breaker integration"""
        service = EstimatorService()

        # Mock OpenAI to fail initially then succeed
        call_count = {"count": 0}

        def mock_create_fail_then_succeed(**kwargs):
            call_count["count"] += 1
            if call_count["count"] < 2:
                raise Exception("Temporary API error")
            # Return success response
            return Mock(choices=[Mock(message=Mock(content='{"person_days": 5.0, "reasoning_breakdown": "Test", "reasoning_notes": "Test"}'))])

        monkeypatch.setattr(service.client.chat.completions, "create", mock_create_fail_then_succeed)

        # Should succeed with retry
        result = service._estimate_single_deliverable(
            sample_deliverables[0],
            "Test system",
            sample_qa_pairs
        )

        assert result is not None
        assert "person_days" in result
        # Should have retried once
        assert call_count["count"] == 2

    def test_estimator_service_fallback_on_failure(self, monkeypatch, sample_deliverables, sample_qa_pairs):
        """Test EstimatorService uses fallback when all retries fail"""
        service = EstimatorService()

        # Mock OpenAI to always fail
        def mock_create_always_fail(**kwargs):
            raise Exception("Persistent API error")

        monkeypatch.setattr(service.client.chat.completions, "create", mock_create_always_fail)

        # Should use fallback estimation
        result = service._estimate_single_deliverable(
            sample_deliverables[0],  # 要件定義書
            "Test system",
            sample_qa_pairs
        )

        assert result is not None
        assert "person_days" in result
        # Should use keyword-based fallback (10.0 for 要件定義書)
        assert result["person_days"] == 10.0

    def test_question_service_with_retry_and_fallback(self, monkeypatch, sample_deliverables):
        """Test QuestionService with retry and fallback integration"""
        service = QuestionService()

        # Mock OpenAI to always fail
        def mock_create_always_fail(**kwargs):
            raise Exception("API error")

        monkeypatch.setattr(service.client.chat.completions, "create", mock_create_always_fail)

        # Should use fallback (default questions)
        questions = service.generate_questions(sample_deliverables, "Test system")

        assert isinstance(questions, list)
        assert len(questions) == 3
        # Should be default questions
        for q in questions:
            assert isinstance(q, str)
            assert len(q) > 0


@pytest.mark.integration
class TestCircuitBreakerState:
    """Integration tests for circuit breaker state management"""

    def test_global_circuit_breaker_state(self):
        """Test that global OpenAI circuit breaker maintains state"""
        # Reset circuit breaker for clean test
        openai_circuit_breaker.reset()
        assert openai_circuit_breaker.state == "CLOSED"

        # Simulate failures
        def always_fails():
            raise Exception("Test failure")

        # Fail multiple times
        for i in range(openai_circuit_breaker.failure_threshold):
            try:
                openai_circuit_breaker.call(always_fails)
            except Exception:
                pass

        # Should be open now
        assert openai_circuit_breaker.state == "OPEN"

        # Reset for next test
        openai_circuit_breaker.reset()
