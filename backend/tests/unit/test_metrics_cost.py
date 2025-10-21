"""Unit tests for cost tracking in MetricsCollector (TODO-9)"""
import pytest
from datetime import datetime
from app.core.metrics import MetricsCollector


class TestMetricsCostTracking:
    """Test cost tracking functionality in MetricsCollector"""

    def setup_method(self):
        """Setup test - reset metrics collector"""
        self.collector = MetricsCollector()
        self.collector.reset()
        # Reset cost tracking
        with self.collector._data_lock:
            self.collector.daily_cost = 0.0
            self.collector.monthly_cost = 0.0

    def test_calculate_cost(self):
        """Test cost calculation formula"""
        # Test cost calculation
        # GPT-4o-mini: $0.15/1M input, $0.60/1M output
        cost = self.collector._calculate_cost(1000, 500)
        expected = (1000 / 1_000_000) * 0.15 + (500 / 1_000_000) * 0.60
        assert abs(cost - expected) < 0.0001

    def test_record_openai_call_with_cost(self):
        """Test recording OpenAI call with cost tracking"""
        self.collector.record_openai_call(
            model="gpt-4o-mini",
            tokens=1500,
            duration=2.5,
            success=True,
            request_id="test_req_1",
            operation="estimate",
            input_tokens=1000,
            output_tokens=500
        )

        # Check that cost was recorded
        assert self.collector.daily_cost > 0
        assert self.collector.monthly_cost > 0

        # Check OpenAI call was recorded
        assert len(self.collector.openai_calls) == 1
        call = self.collector.openai_calls[0]
        assert call.input_tokens == 1000
        assert call.output_tokens == 500
        assert call.cost_usd > 0

    def test_cost_accumulation(self):
        """Test that costs accumulate correctly"""
        # First call
        self.collector.record_openai_call(
            model="gpt-4o-mini",
            tokens=1000,
            duration=1.0,
            success=True,
            request_id="test_req_1",
            operation="estimate",
            input_tokens=500,
            output_tokens=500
        )

        first_cost = self.collector.daily_cost

        # Second call
        self.collector.record_openai_call(
            model="gpt-4o-mini",
            tokens=2000,
            duration=2.0,
            success=True,
            request_id="test_req_2",
            operation="question",
            input_tokens=1000,
            output_tokens=1000
        )

        # Cost should have increased
        assert self.collector.daily_cost > first_cost
        assert self.collector.monthly_cost > first_cost

    def test_get_cost_summary(self):
        """Test get_cost_summary method"""
        # Record some calls
        for i in range(3):
            self.collector.record_openai_call(
                model="gpt-4o-mini",
                tokens=1000,
                duration=1.0,
                success=True,
                request_id=f"test_req_{i}",
                operation="estimate",
                input_tokens=500,
                output_tokens=500
            )

        summary = self.collector.get_cost_summary()

        assert "daily_cost_usd" in summary
        assert "monthly_cost_usd" in summary
        assert "daily_limit_usd" in summary
        assert "monthly_limit_usd" in summary
        assert "daily_usage_percent" in summary
        assert "monthly_usage_percent" in summary

        assert summary["daily_cost_usd"] > 0
        assert summary["monthly_cost_usd"] > 0

    def test_cost_tracking_with_failed_calls(self):
        """Test that failed calls don't incur costs"""
        # Failed call (0 tokens)
        self.collector.record_openai_call(
            model="gpt-4o-mini",
            tokens=0,
            duration=1.0,
            success=False,
            request_id="test_req_fail",
            operation="estimate",
            input_tokens=0,
            output_tokens=0
        )

        # Cost should be 0
        assert self.collector.daily_cost == 0.0
        assert self.collector.monthly_cost == 0.0

    def test_backward_compatibility(self):
        """Test that old calls without input/output tokens still work"""
        # Call without input/output tokens (backward compatibility)
        self.collector.record_openai_call(
            model="gpt-4o-mini",
            tokens=1000,
            duration=1.0,
            success=True,
            request_id="test_req_old",
            operation="estimate"
            # No input_tokens, output_tokens (defaults to 0)
        )

        # Should not raise error
        assert len(self.collector.openai_calls) == 1
        assert self.collector.daily_cost == 0.0  # No cost since tokens=0
