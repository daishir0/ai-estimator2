"""Unit tests for metrics collection system"""
import pytest
from app.core.metrics import (
    MetricsCollector,
    APICallMetric,
    OpenAICallMetric,
    ErrorMetric,
    metrics_collector
)


class TestAPICallMetric:
    """Test APICallMetric dataclass"""

    def test_create_api_call_metric(self):
        """Test creating API call metric"""
        metric = APICallMetric(
            endpoint="/api/v1/tasks",
            method="POST",
            status_code=200,
            duration=1.234,
            timestamp="2025-10-22T00:00:00Z",
            request_id="req-123"
        )

        assert metric.endpoint == "/api/v1/tasks"
        assert metric.method == "POST"
        assert metric.status_code == 200
        assert metric.duration == 1.234
        assert metric.request_id == "req-123"


class TestOpenAICallMetric:
    """Test OpenAICallMetric dataclass"""

    def test_create_openai_call_metric(self):
        """Test creating OpenAI call metric"""
        metric = OpenAICallMetric(
            model="gpt-4o-mini",
            tokens=1500,
            duration=3.456,
            success=True,
            timestamp="2025-10-22T00:00:00Z",
            request_id="req-123",
            operation="estimate"
        )

        assert metric.model == "gpt-4o-mini"
        assert metric.tokens == 1500
        assert metric.duration == 3.456
        assert metric.success is True
        assert metric.operation == "estimate"


class TestErrorMetric:
    """Test ErrorMetric dataclass"""

    def test_create_error_metric(self):
        """Test creating error metric"""
        metric = ErrorMetric(
            error_type="ValueError",
            message="Invalid input",
            timestamp="2025-10-22T00:00:00Z",
            request_id="req-123",
            endpoint="/api/v1/tasks"
        )

        assert metric.error_type == "ValueError"
        assert metric.message == "Invalid input"
        assert metric.endpoint == "/api/v1/tasks"


class TestMetricsCollector:
    """Test MetricsCollector functionality"""

    @pytest.fixture
    def collector(self):
        """Create fresh metrics collector for each test"""
        collector = MetricsCollector()
        collector.reset()
        return collector

    def test_singleton_instance(self):
        """Test MetricsCollector is singleton"""
        collector1 = MetricsCollector()
        collector2 = MetricsCollector()
        assert collector1 is collector2

    def test_record_api_call(self, collector):
        """Test recording API call"""
        collector.record_api_call(
            endpoint="/api/v1/tasks",
            method="POST",
            status_code=200,
            duration=1.234,
            request_id="req-123"
        )

        assert len(collector.api_calls) == 1
        metric = collector.api_calls[0]
        assert metric.endpoint == "/api/v1/tasks"
        assert metric.method == "POST"
        assert metric.status_code == 200

    def test_record_openai_call(self, collector):
        """Test recording OpenAI call"""
        collector.record_openai_call(
            model="gpt-4o-mini",
            tokens=1500,
            duration=3.456,
            success=True,
            request_id="req-123",
            operation="estimate"
        )

        assert len(collector.openai_calls) == 1
        metric = collector.openai_calls[0]
        assert metric.model == "gpt-4o-mini"
        assert metric.tokens == 1500
        assert metric.operation == "estimate"

    def test_record_error(self, collector):
        """Test recording error"""
        collector.record_error(
            error_type="ValueError",
            message="Invalid input",
            request_id="req-123",
            endpoint="/api/v1/tasks"
        )

        assert len(collector.errors) == 1
        error = collector.errors[0]
        assert error.error_type == "ValueError"
        assert error.message == "Invalid input"

    def test_get_summary_empty(self, collector):
        """Test summary with no metrics"""
        summary = collector.get_summary()

        assert summary["total_api_calls"] == 0
        assert summary["avg_response_time"] == 0.0
        assert summary["success_rate"] == 100.0
        assert summary["total_errors"] == 0

    def test_get_summary_with_metrics(self, collector):
        """Test summary with metrics"""
        # Record API calls
        for i in range(10):
            collector.record_api_call(
                endpoint="/api/v1/tasks",
                method="GET",
                status_code=200,
                duration=1.0 + i * 0.1,
                request_id=f"req-{i}"
            )

        # Record OpenAI calls
        collector.record_openai_call(
            model="gpt-4o-mini",
            tokens=1000,
            duration=2.0,
            success=True,
            request_id="req-1",
            operation="estimate"
        )
        collector.record_openai_call(
            model="gpt-4o-mini",
            tokens=500,
            duration=1.5,
            success=True,
            request_id="req-2",
            operation="question"
        )

        # Record error
        collector.record_error(
            error_type="ValueError",
            message="Test error",
            request_id="req-3"
        )

        summary = collector.get_summary()

        assert summary["total_api_calls"] == 10
        assert summary["avg_response_time"] > 0
        assert summary["success_rate"] == 100.0
        assert summary["total_openai_calls"] == 2
        assert summary["openai_success_rate"] == 100.0
        assert summary["total_tokens_used"] == 1500
        assert summary["total_errors"] == 1

    def test_get_summary_with_failures(self, collector):
        """Test summary with failed requests"""
        # Successful calls
        for i in range(8):
            collector.record_api_call(
                endpoint="/api/v1/tasks",
                method="GET",
                status_code=200,
                duration=1.0,
                request_id=f"req-{i}"
            )

        # Failed calls
        for i in range(2):
            collector.record_api_call(
                endpoint="/api/v1/tasks",
                method="GET",
                status_code=500,
                duration=0.5,
                request_id=f"req-fail-{i}"
            )

        summary = collector.get_summary()

        assert summary["total_api_calls"] == 10
        assert summary["success_rate"] == 80.0  # 8/10 = 80%

    def test_get_summary_openai_operations(self, collector):
        """Test OpenAI operation statistics"""
        collector.record_openai_call(
            model="gpt-4o-mini",
            tokens=1000,
            duration=2.0,
            success=True,
            request_id="req-1",
            operation="estimate"
        )
        collector.record_openai_call(
            model="gpt-4o-mini",
            tokens=2000,
            duration=3.0,
            success=True,
            request_id="req-2",
            operation="estimate"
        )
        collector.record_openai_call(
            model="gpt-4o-mini",
            tokens=500,
            duration=1.0,
            success=True,
            request_id="req-3",
            operation="question"
        )

        summary = collector.get_summary()

        assert "openai_operations" in summary
        assert summary["openai_operations"]["estimate"]["count"] == 2
        assert summary["openai_operations"]["estimate"]["tokens"] == 3000
        assert summary["openai_operations"]["question"]["count"] == 1
        assert summary["openai_operations"]["question"]["tokens"] == 500

    def test_get_recent_errors(self, collector):
        """Test getting recent errors"""
        # Record errors
        for i in range(15):
            collector.record_error(
                error_type="TestError",
                message=f"Error {i}",
                request_id=f"req-{i}"
            )

        # Get last 10 errors
        recent = collector.get_recent_errors(limit=10)

        assert len(recent) == 10
        # Should be most recent errors
        assert recent[-1]["message"] == "Error 14"

    def test_reset(self, collector):
        """Test resetting metrics"""
        # Add some metrics
        collector.record_api_call(
            endpoint="/api/v1/tasks",
            method="GET",
            status_code=200,
            duration=1.0,
            request_id="req-1"
        )
        collector.record_openai_call(
            model="gpt-4o-mini",
            tokens=1000,
            duration=2.0,
            success=True,
            request_id="req-1",
            operation="estimate"
        )
        collector.record_error(
            error_type="TestError",
            message="Test",
            request_id="req-1"
        )

        assert len(collector.api_calls) > 0
        assert len(collector.openai_calls) > 0
        assert len(collector.errors) > 0

        # Reset
        collector.reset()

        assert len(collector.api_calls) == 0
        assert len(collector.openai_calls) == 0
        assert len(collector.errors) == 0

    def test_p95_calculation(self, collector):
        """Test P95 response time calculation"""
        # Record 100 calls with varying durations
        for i in range(100):
            collector.record_api_call(
                endpoint="/api/v1/tasks",
                method="GET",
                status_code=200,
                duration=i * 0.01,  # 0.00, 0.01, 0.02, ..., 0.99
                request_id=f"req-{i}"
            )

        summary = collector.get_summary()

        # P95 should be around 0.94 (95th out of 100 items)
        assert 0.90 <= summary["p95_response_time"] <= 0.99

    def test_thread_safety(self, collector):
        """Test thread-safe operations"""
        import threading

        def record_calls():
            for i in range(100):
                collector.record_api_call(
                    endpoint="/api/v1/tasks",
                    method="GET",
                    status_code=200,
                    duration=1.0,
                    request_id=f"req-{threading.get_ident()}-{i}"
                )

        # Run multiple threads
        threads = [threading.Thread(target=record_calls) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have 500 total calls (5 threads * 100 calls)
        assert len(collector.api_calls) == 500


class TestGlobalMetricsCollector:
    """Test global metrics_collector instance"""

    def test_global_instance(self):
        """Test global metrics_collector is singleton"""
        from app.core.metrics import metrics_collector as mc1
        from app.core.metrics import metrics_collector as mc2
        assert mc1 is mc2
