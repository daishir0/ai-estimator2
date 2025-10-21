"""Metrics collection system for monitoring and observability"""
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
import statistics
import threading


@dataclass
class APICallMetric:
    """Metric for API call tracking"""
    endpoint: str
    method: str
    status_code: int
    duration: float
    timestamp: str
    request_id: str


@dataclass
class OpenAICallMetric:
    """Metric for OpenAI API call tracking"""
    model: str
    tokens: int
    duration: float
    success: bool
    timestamp: str
    request_id: str
    operation: str  # "estimate", "question", "chat"
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class ErrorMetric:
    """Metric for error tracking"""
    error_type: str
    message: str
    timestamp: str
    request_id: str
    endpoint: Optional[str] = None


class MetricsCollector:
    """
    Singleton metrics collector for system-wide monitoring

    Thread-safe metrics collection for:
    - API call statistics
    - OpenAI API usage
    - Error tracking
    - Performance metrics
    - Cost tracking (TODO-9)
    """

    # OpenAI API pricing (as of 2025-10, gpt-4o-mini)
    # https://openai.com/pricing
    PRICE_PER_1M_INPUT_TOKENS = 0.15  # $0.15 per 1M input tokens
    PRICE_PER_1M_OUTPUT_TOKENS = 0.60  # $0.60 per 1M output tokens

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.api_calls: List[APICallMetric] = []
        self.openai_calls: List[OpenAICallMetric] = []
        self.errors: List[ErrorMetric] = []
        self._data_lock = threading.Lock()

        # Cost tracking (TODO-9)
        self.daily_cost = 0.0
        self.monthly_cost = 0.0
        self.last_reset_date = datetime.utcnow().date()
        self.last_reset_month = datetime.utcnow().month

        self._initialized = True

    def record_api_call(self, endpoint: str, method: str, status_code: int,
                       duration: float, request_id: str):
        """Record API call metric"""
        with self._data_lock:
            metric = APICallMetric(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                duration=duration,
                timestamp=datetime.utcnow().isoformat() + "Z",
                request_id=request_id
            )
            self.api_calls.append(metric)

    def record_openai_call(self, model: str, tokens: int, duration: float,
                           success: bool, request_id: str, operation: str = "unknown",
                           input_tokens: int = 0, output_tokens: int = 0):
        """
        Record OpenAI API call metric with cost tracking (TODO-9)

        Args:
            model: OpenAI model name
            tokens: Total tokens used (for backward compatibility)
            duration: API call duration in seconds
            success: Whether the call succeeded
            request_id: Request ID for tracing
            operation: Operation type (estimate/question/chat)
            input_tokens: Number of input (prompt) tokens
            output_tokens: Number of output (completion) tokens
        """
        with self._data_lock:
            # Auto-reset check (TODO-9)
            self._auto_reset_if_needed()

            # Calculate cost (TODO-9)
            cost = self._calculate_cost(input_tokens, output_tokens)

            # Update cumulative costs
            self.daily_cost += cost
            self.monthly_cost += cost

            # Record metric
            metric = OpenAICallMetric(
                model=model,
                tokens=tokens,
                duration=duration,
                success=success,
                timestamp=datetime.utcnow().isoformat() + "Z",
                request_id=request_id,
                operation=operation,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost
            )
            self.openai_calls.append(metric)

            # Cost limit check (TODO-9)
            self._check_cost_limit(request_id, cost)

    def record_error(self, error_type: str, message: str, request_id: str,
                    endpoint: Optional[str] = None):
        """Record error metric"""
        with self._data_lock:
            metric = ErrorMetric(
                error_type=error_type,
                message=message,
                timestamp=datetime.utcnow().isoformat() + "Z",
                request_id=request_id,
                endpoint=endpoint
            )
            self.errors.append(metric)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get metrics summary

        Returns:
            Dictionary with aggregated metrics:
            - total_api_calls: Total number of API calls
            - avg_response_time: Average response time in seconds
            - p95_response_time: 95th percentile response time
            - success_rate: Percentage of successful requests
            - total_openai_calls: Total OpenAI API calls
            - openai_success_rate: OpenAI API success rate
            - total_tokens_used: Total tokens consumed
            - openai_operations: Operation breakdown (estimate/question/chat)
            - total_errors: Total number of errors
            - error_rate: Percentage of requests with errors
        """
        with self._data_lock:
            # OpenAI statistics (calculated independently of API calls)
            openai_success = sum(1 for call in self.openai_calls if call.success)
            openai_total = len(self.openai_calls)
            total_tokens = sum(call.tokens for call in self.openai_calls)

            # OpenAI operation breakdown
            operation_stats = defaultdict(lambda: {"count": 0, "tokens": 0})
            for call in self.openai_calls:
                operation_stats[call.operation]["count"] += 1
                operation_stats[call.operation]["tokens"] += call.tokens

            # API call statistics
            if not self.api_calls:
                return {
                    "total_api_calls": 0,
                    "avg_response_time": 0.0,
                    "p95_response_time": 0.0,
                    "success_rate": 100.0,
                    "total_openai_calls": openai_total,
                    "openai_success_rate": round(openai_success / openai_total * 100, 2) if openai_total > 0 else 0.0,
                    "total_tokens_used": total_tokens,
                    "openai_operations": dict(operation_stats),
                    "total_errors": len(self.errors),
                    "error_rate": 0.0
                }

            durations = [call.duration for call in self.api_calls]
            status_codes = [call.status_code for call in self.api_calls]
            success_count = sum(1 for s in status_codes if 200 <= s < 300)

            # Calculate P95
            p95 = 0.0
            if len(durations) >= 20:
                sorted_durations = sorted(durations)
                p95_index = int(len(sorted_durations) * 0.95)
                p95 = sorted_durations[p95_index]
            elif durations:
                p95 = max(durations)

            return {
                "total_api_calls": len(self.api_calls),
                "avg_response_time": round(statistics.mean(durations), 3) if durations else 0.0,
                "p95_response_time": round(p95, 3),
                "success_rate": round(success_count / len(status_codes) * 100, 2) if status_codes else 100.0,
                "total_openai_calls": openai_total,
                "openai_success_rate": round(openai_success / openai_total * 100, 2) if openai_total > 0 else 0.0,
                "total_tokens_used": total_tokens,
                "openai_operations": dict(operation_stats),
                "total_errors": len(self.errors),
                "error_rate": round(len(self.errors) / len(self.api_calls) * 100, 2) if self.api_calls else 0.0
            }

    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent errors"""
        with self._data_lock:
            recent = self.errors[-limit:]
            return [asdict(err) for err in recent]

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate OpenAI API cost in USD (TODO-9)

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        cost = (
            (input_tokens / 1_000_000) * self.PRICE_PER_1M_INPUT_TOKENS +
            (output_tokens / 1_000_000) * self.PRICE_PER_1M_OUTPUT_TOKENS
        )
        return cost

    def _auto_reset_if_needed(self):
        """
        Auto-reset daily/monthly costs if date/month changed (TODO-9)

        This method should be called with _data_lock already acquired.
        """
        today = datetime.utcnow().date()
        current_month = datetime.utcnow().month

        # Daily reset
        if today != self.last_reset_date:
            self.daily_cost = 0.0
            self.last_reset_date = today

        # Monthly reset
        if current_month != self.last_reset_month:
            self.monthly_cost = 0.0
            self.last_reset_month = current_month

    def _check_cost_limit(self, request_id: str, cost: float):
        """
        Check cost limits and raise exception if exceeded (TODO-9)

        This method should be called with _data_lock already acquired.

        Args:
            request_id: Request ID for logging
            cost: Cost of current API call

        Raises:
            Exception: If monthly cost limit is exceeded
        """
        # Import here to avoid circular dependency
        try:
            from app.core.config import settings
            from app.core.logging_config import get_logger
            from app.core.i18n import t

            logger = get_logger(__name__)

            # Monthly cost limit (hard limit - raises exception)
            if self.monthly_cost > settings.MONTHLY_COST_LIMIT:
                logger.critical(
                    "Monthly cost limit exceeded!",
                    request_id=request_id,
                    monthly_cost_usd=round(self.monthly_cost, 4),
                    limit_usd=settings.MONTHLY_COST_LIMIT
                )
                raise Exception(t('messages.cost_limit_exceeded'))

            # Daily cost warning (80% threshold)
            if self.daily_cost > settings.DAILY_COST_LIMIT * 0.8:
                logger.warning(
                    "Daily cost approaching limit (80%)",
                    request_id=request_id,
                    daily_cost_usd=round(self.daily_cost, 4),
                    limit_usd=settings.DAILY_COST_LIMIT,
                    usage_percent=round((self.daily_cost / settings.DAILY_COST_LIMIT) * 100, 1)
                )

        except ImportError:
            # If imports fail, skip cost limit check
            pass

    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get cost tracking summary (TODO-9)

        Returns:
            Dictionary with cost information:
            - daily_cost_usd: Today's accumulated cost
            - monthly_cost_usd: This month's accumulated cost
            - daily_limit_usd: Daily cost limit
            - monthly_limit_usd: Monthly cost limit
            - daily_usage_percent: Daily usage percentage
            - monthly_usage_percent: Monthly usage percentage
        """
        with self._data_lock:
            # Import here to avoid circular dependency
            try:
                from app.core.config import settings

                daily_limit = settings.DAILY_COST_LIMIT
                monthly_limit = settings.MONTHLY_COST_LIMIT
            except ImportError:
                daily_limit = 10.0
                monthly_limit = 200.0

            return {
                "daily_cost_usd": round(self.daily_cost, 4),
                "monthly_cost_usd": round(self.monthly_cost, 4),
                "daily_limit_usd": daily_limit,
                "monthly_limit_usd": monthly_limit,
                "daily_usage_percent": round((self.daily_cost / daily_limit) * 100, 2) if daily_limit > 0 else 0.0,
                "monthly_usage_percent": round((self.monthly_cost / monthly_limit) * 100, 2) if monthly_limit > 0 else 0.0
            }

    def reset(self):
        """Reset all metrics (for memory management)"""
        with self._data_lock:
            self.api_calls.clear()
            self.openai_calls.clear()
            self.errors.clear()
            # Note: Cost tracking is NOT reset here (only auto-reset by date/month change)


# Global singleton instance
metrics_collector = MetricsCollector()
