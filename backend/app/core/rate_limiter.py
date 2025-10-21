"""Rate limiter for DoS attack prevention (TODO-9)"""
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Tuple, Dict, Any
import threading
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Rate limiter using sliding window algorithm

    Prevents DoS attacks by limiting requests per client (IP address)
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 3600
    ):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds (default: 1 hour)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()

        logger.info(
            "RateLimiter initialized",
            max_requests=max_requests,
            window_seconds=window_seconds
        )

    def check_limit(self, client_id: str) -> Tuple[bool, Optional[int]]:
        """
        Check if client is within rate limit

        Args:
            client_id: Client identifier (usually IP address)

        Returns:
            Tuple of (is_allowed: bool, retry_after: Optional[int])
            - is_allowed: True if request is allowed, False if rate limit exceeded
            - retry_after: Seconds to wait before retry (None if allowed)
        """
        with self.lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self.window_seconds)

            # Remove expired requests (sliding window)
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > window_start
            ]

            # Check rate limit
            if len(self.requests[client_id]) >= self.max_requests:
                # Calculate retry_after from oldest request
                oldest_request = self.requests[client_id][0]
                retry_after = int(
                    (oldest_request + timedelta(seconds=self.window_seconds) - now).total_seconds()
                )

                logger.warning(
                    "Rate limit exceeded",
                    client_id=client_id,
                    requests_count=len(self.requests[client_id]),
                    max_requests=self.max_requests,
                    retry_after=retry_after
                )

                return False, max(0, retry_after)

            # Record new request
            self.requests[client_id].append(now)
            return True, None

    def reset_client(self, client_id: str):
        """
        Reset rate limit for specific client (admin function)

        Args:
            client_id: Client identifier to reset
        """
        with self.lock:
            if client_id in self.requests:
                del self.requests[client_id]
                logger.info("Rate limit reset for client", client_id=client_id)

    def get_remaining(self, client_id: str) -> int:
        """
        Get remaining requests for client

        Args:
            client_id: Client identifier

        Returns:
            Number of remaining requests allowed
        """
        with self.lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self.window_seconds)

            # Count recent requests
            recent_requests = [
                req_time for req_time in self.requests.get(client_id, [])
                if req_time > window_start
            ]

            return max(0, self.max_requests - len(recent_requests))

    def get_status(self) -> Dict[str, Any]:
        """
        Get rate limiter status (admin function)

        Returns:
            Dictionary with rate limiter status:
            - max_requests: Maximum requests per window
            - window_seconds: Time window in seconds
            - active_clients: Number of active clients being tracked
        """
        with self.lock:
            return {
                "max_requests": self.max_requests,
                "window_seconds": self.window_seconds,
                "active_clients": len(self.requests)
            }


# Global instance (initialized with config in middleware)
rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(max_requests: int = 100, window_seconds: int = 3600) -> RateLimiter:
    """
    Get or create global rate limiter instance

    Args:
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds

    Returns:
        RateLimiter instance
    """
    global rate_limiter
    if rate_limiter is None:
        rate_limiter = RateLimiter(max_requests, window_seconds)
    return rate_limiter
