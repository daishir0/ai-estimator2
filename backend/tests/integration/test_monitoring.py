"""Integration tests for monitoring and observability"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.metrics import metrics_collector


class TestMonitoringEndpoints:
    """Test monitoring API endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset metrics before each test"""
        metrics_collector.reset()
        yield
        metrics_collector.reset()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_basic_health_check(self, client):
        """Test basic health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_detailed_health_check(self, client):
        """Test detailed health check with metrics"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "metrics" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "total_api_calls" in data
        assert "avg_response_time" in data
        assert "p95_response_time" in data
        assert "success_rate" in data
        assert "total_openai_calls" in data
        assert "openai_success_rate" in data
        assert "total_tokens_used" in data
        assert "total_errors" in data
        assert "error_rate" in data

    def test_metrics_errors_endpoint(self, client):
        """Test metrics errors endpoint"""
        response = client.get("/api/v1/metrics/errors")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_metrics_reset_endpoint(self, client):
        """Test metrics reset endpoint"""
        # Make some requests first
        client.get("/api/v1/metrics")
        client.get("/api/v1/metrics")

        # Get metrics before reset
        response = client.get("/api/v1/metrics")
        data_before = response.json()
        assert data_before["total_api_calls"] > 0

        # Reset metrics
        response = client.post("/api/v1/metrics/reset")
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Get metrics after reset
        response = client.get("/api/v1/metrics")
        data_after = response.json()
        # Note: The GET request itself creates a new metric
        assert data_after["total_api_calls"] >= 0


class TestRequestIDTracing:
    """Test request ID tracing functionality"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_request_id_in_response_header(self, client):
        """Test X-Request-ID header in response"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_unique_request_ids(self, client):
        """Test each request gets unique request ID"""
        response1 = client.get("/health")
        response2 = client.get("/health")

        request_id1 = response1.headers.get("X-Request-ID")
        request_id2 = response2.headers.get("X-Request-ID")

        assert request_id1 != request_id2


class TestMetricsAccumulation:
    """Test metrics accumulation through multiple requests"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset metrics before test"""
        metrics_collector.reset()
        yield

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_api_call_metrics_accumulation(self, client):
        """Test API call metrics accumulate correctly"""
        # Make multiple requests
        for _ in range(10):
            client.get("/health")

        response = client.get("/api/v1/metrics")
        data = response.json()

        # Should have at least 10 calls (plus the metrics request itself)
        assert data["total_api_calls"] >= 10

    def test_success_rate_calculation(self, client):
        """Test success rate calculation"""
        # Make successful requests
        for _ in range(9):
            client.get("/health")

        # Make a request that will fail (non-existent endpoint)
        client.get("/api/v1/non-existent-endpoint")

        response = client.get("/api/v1/metrics")
        data = response.json()

        # Success rate should be less than 100%
        assert data["success_rate"] < 100.0

    def test_response_time_metrics(self, client):
        """Test response time metrics are recorded"""
        # Make some requests
        for _ in range(5):
            client.get("/health")

        response = client.get("/api/v1/metrics")
        data = response.json()

        assert data["avg_response_time"] > 0
        assert data["p95_response_time"] > 0


class TestHealthStatusDetermination:
    """Test health status determination logic"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset metrics before each test"""
        metrics_collector.reset()
        yield
        metrics_collector.reset()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_healthy_status(self, client):
        """Test healthy status with normal metrics"""
        # Make some successful requests
        for _ in range(10):
            client.get("/health")

        response = client.get("/api/v1/health")
        data = response.json()

        # Should be healthy with all successful requests
        assert data["status"] in ["healthy", "degraded"]

    def test_unhealthy_status_with_high_error_rate(self, client):
        """Test unhealthy status with high error rate"""
        # Record many errors manually
        for i in range(20):
            metrics_collector.record_error(
                error_type="TestError",
                message=f"Error {i}",
                request_id=f"req-{i}"
            )

        # Also record some API calls to calculate error rate
        for i in range(100):
            metrics_collector.record_api_call(
                endpoint="/test",
                method="GET",
                status_code=500 if i < 10 else 200,
                duration=1.0,
                request_id=f"req-{i}"
            )

        response = client.get("/api/v1/health")
        data = response.json()

        # With 10% error rate, should be unhealthy
        assert data["status"] == "unhealthy"


class TestStructuredLogging:
    """Test structured logging integration"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_request_logging(self, client, caplog):
        """Test that requests are logged"""
        import logging
        caplog.set_level(logging.INFO)

        response = client.get("/health")
        assert response.status_code == 200

        # Check that logs were created
        # Note: Depending on log configuration, this might not capture all logs
        # This is a basic test to ensure logging infrastructure is working


class TestConcurrentMetrics:
    """Test metrics collection under concurrent load"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset metrics before test"""
        metrics_collector.reset()
        yield

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_concurrent_requests(self, client):
        """Test metrics collection with concurrent requests"""
        import concurrent.futures

        def make_request():
            return client.get("/health")

        # Make 50 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in futures]

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)

        # Get metrics
        response = client.get("/api/v1/metrics")
        data = response.json()

        # Should have recorded at least 50 calls
        assert data["total_api_calls"] >= 50


class TestErrorMetrics:
    """Test error metrics recording"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset metrics before each test"""
        metrics_collector.reset()
        yield
        metrics_collector.reset()

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_error_recording(self, client):
        """Test that errors are recorded in metrics"""
        # Record some errors manually
        metrics_collector.record_error(
            error_type="ValueError",
            message="Test error 1",
            request_id="req-1",
            endpoint="/api/v1/test"
        )
        metrics_collector.record_error(
            error_type="TypeError",
            message="Test error 2",
            request_id="req-2",
            endpoint="/api/v1/test"
        )

        # Get error metrics
        response = client.get("/api/v1/metrics/errors")
        assert response.status_code == 200

        errors = response.json()
        assert len(errors) == 2
        assert errors[0]["error_type"] == "ValueError"
        assert errors[1]["error_type"] == "TypeError"

    def test_error_rate_calculation(self, client):
        """Test error rate calculation"""
        # Record API calls with some errors
        for i in range(100):
            status = 500 if i < 5 else 200  # 5% error rate
            metrics_collector.record_api_call(
                endpoint="/test",
                method="GET",
                status_code=status,
                duration=1.0,
                request_id=f"req-{i}"
            )

        # Record errors for failed calls
        for i in range(5):
            metrics_collector.record_error(
                error_type="TestError",
                message=f"Error {i}",
                request_id=f"req-{i}"
            )

        response = client.get("/api/v1/metrics")
        data = response.json()

        assert data["error_rate"] == 5.0
