"""Rate limit middleware for DoS attack prevention (TODO-9)"""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.rate_limiter import get_rate_limiter
from app.core.config import settings
from app.core.i18n import t
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limit middleware

    Enforces rate limits per client IP address to prevent DoS attacks
    """

    def __init__(self, app):
        super().__init__(app)
        # Initialize rate limiter with config
        self.rate_limiter = get_rate_limiter(
            max_requests=settings.RATE_LIMIT_MAX_REQUESTS,
            window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS
        )
        logger.info(
            "RateLimitMiddleware initialized",
            max_requests=settings.RATE_LIMIT_MAX_REQUESTS,
            window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS
        )

    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limit check

        Args:
            request: FastAPI Request object
            call_next: Next middleware/endpoint handler

        Returns:
            Response (429 if rate limit exceeded, otherwise normal response)
        """
        # Get client ID (IP address)
        client_id = request.client.host if request.client else "unknown"

        # Check rate limit
        is_allowed, retry_after = self.rate_limiter.check_limit(client_id)

        if not is_allowed:
            logger.warning(
                "Rate limit exceeded - request rejected",
                client_id=client_id,
                path=request.url.path,
                method=request.method,
                retry_after=retry_after
            )

            return JSONResponse(
                status_code=429,
                content={
                    "detail": t('messages.rate_limit_exceeded'),
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.rate_limiter.max_requests),
                    "X-RateLimit-Remaining": "0"
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        remaining = self.rate_limiter.get_remaining(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(self.rate_limiter.window_seconds)

        return response
