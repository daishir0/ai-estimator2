"""Circuit Breaker service

This module implements the Circuit Breaker pattern to prevent cascading failures
when calling external services (e.g., OpenAI API).

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Failures exceeded threshold, requests fail immediately
- HALF_OPEN: Testing if service recovered, limited requests allowed
"""
from datetime import datetime, timedelta
from typing import Callable, Any
import logging
from app.core.config import settings
from app.core.i18n import t

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit Breaker pattern implementation

    The circuit breaker monitors failures and prevents calls to failing services
    by transitioning between CLOSED, OPEN, and HALF_OPEN states.

    Attributes:
        name: Circuit breaker identifier
        failure_threshold: Number of failures before opening circuit
        timeout: Seconds before attempting HALF_OPEN state
        failures: Current count of consecutive failures
        last_failure_time: Timestamp of last failure
        state: Current state (CLOSED/OPEN/HALF_OPEN)
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = None,
        timeout: int = None
    ):
        """Initialize circuit breaker

        Args:
            name: Circuit breaker identifier
            failure_threshold: Number of failures before opening (default: settings)
            timeout: Timeout in seconds before attempting half-open (default: settings)
        """
        self.name = name
        self.failure_threshold = failure_threshold or settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        self.timeout = timeout or settings.CIRCUIT_BREAKER_TIMEOUT

        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "OPEN":
            # Check if timeout has elapsed, transition to HALF_OPEN
            if self.last_failure_time and \
               datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker '{self.name}' transitioned to HALF_OPEN")
            else:
                logger.warning(f"Circuit breaker '{self.name}' is OPEN")
                raise Exception(t('messages.circuit_breaker_open'))

        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        """Handle successful call

        Transitions to CLOSED state and resets failure count.
        """
        if self.state == "HALF_OPEN":
            logger.info(f"Circuit breaker '{self.name}' transitioned to CLOSED")
        self.failures = 0
        self.state = "CLOSED"

    def on_failure(self):
        """Handle failed call

        Increments failure count and transitions to OPEN if threshold exceeded.
        """
        self.failures += 1
        self.last_failure_time = datetime.now()

        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(
                f"Circuit breaker '{self.name}' transitioned to OPEN "
                f"({self.failures} failures)"
            )

    def reset(self):
        """Reset circuit breaker to CLOSED state

        This method can be called manually to reset the circuit breaker
        (e.g., after manual intervention or configuration change).
        """
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        logger.info(f"Circuit breaker '{self.name}' reset")

    def get_state(self) -> dict:
        """Get current circuit breaker state

        Returns:
            Dictionary with current state information
        """
        return {
            "name": self.name,
            "state": self.state,
            "failures": self.failures,
            "failure_threshold": self.failure_threshold,
            "timeout": self.timeout,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


# Global circuit breaker instance for OpenAI API
openai_circuit_breaker = CircuitBreaker(name="OpenAI_API")
