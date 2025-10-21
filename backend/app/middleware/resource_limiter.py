"""Resource limiter middleware to control concurrent requests"""
import asyncio
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.config import settings
from app.core.i18n import t

logger = logging.getLogger(__name__)


class ResourceLimiterMiddleware(BaseHTTPMiddleware):
    """Middleware to limit concurrent resource-intensive requests

    This middleware uses a semaphore to control the number of concurrent
    requests to resource-intensive endpoints (e.g., estimate generation).

    Usage:
        app.add_middleware(
            ResourceLimiterMiddleware,
            max_concurrent=5,
            timeout=30.0,
            limited_paths=["/api/v1/tasks"]
        )
    """

    def __init__(
        self,
        app,
        max_concurrent: int = None,
        timeout: float = 30.0,
        limited_paths: list = None
    ):
        """Initialize resource limiter middleware

        Args:
            app: FastAPI application instance
            max_concurrent: Maximum number of concurrent requests (default from settings)
            timeout: Timeout for acquiring semaphore in seconds (default 30.0)
            limited_paths: List of path prefixes to limit (None = limit all)
        """
        super().__init__(app)
        self.max_concurrent = max_concurrent or getattr(
            settings, 'MAX_CONCURRENT_ESTIMATES', 5
        )
        self.timeout = timeout
        self.limited_paths = limited_paths or []
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

        logger.info(
            f"ResourceLimiterMiddleware initialized: "
            f"max_concurrent={self.max_concurrent}, "
            f"timeout={self.timeout}s, "
            f"limited_paths={self.limited_paths}"
        )

    def _should_limit(self, path: str) -> bool:
        """Check if the given path should be rate limited

        Args:
            path: Request path

        Returns:
            True if path should be limited, False otherwise
        """
        # If no specific paths configured, limit all
        if not self.limited_paths:
            return True

        # Check if path starts with any limited path prefix
        return any(path.startswith(prefix) for prefix in self.limited_paths)

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with resource limiting

        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain

        Returns:
            Response from next handler or 503 error if resource limit exceeded
        """
        # Check if this path should be limited
        if not self._should_limit(request.url.path):
            # No limiting for this path, pass through
            return await call_next(request)

        # Try to acquire semaphore with timeout
        try:
            async with asyncio.timeout(self.timeout):
                acquired = await self.semaphore.acquire()

                if not acquired:
                    logger.warning(
                        f"Resource limit exceeded for {request.url.path} "
                        f"(max_concurrent={self.max_concurrent})"
                    )
                    return JSONResponse(
                        status_code=503,
                        content={
                            "detail": "Service temporarily unavailable due to high load. "
                                     "Please retry after a moment.",
                            "error": "resource_limit_exceeded"
                        }
                    )

                try:
                    # Process request
                    logger.debug(
                        f"Processing request: {request.method} {request.url.path} "
                        f"(active={self.max_concurrent - self.semaphore._value}/"
                        f"{self.max_concurrent})"
                    )
                    response = await call_next(request)
                    return response
                finally:
                    # Release semaphore
                    self.semaphore.release()

        except asyncio.TimeoutError:
            logger.error(
                f"Timeout waiting for resource availability: {request.url.path} "
                f"(timeout={self.timeout}s)"
            )
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Service temporarily unavailable. Please retry after a moment.",
                    "error": "resource_timeout"
                }
            )
        except Exception as e:
            logger.error(f"Error in resource limiter middleware: {e}", exc_info=True)
            # On error, try to release semaphore if it was acquired
            try:
                self.semaphore.release()
            except Exception:
                pass
            raise


class FileSizeLimiterMiddleware(BaseHTTPMiddleware):
    """Middleware to check file size limits before processing

    This middleware checks Content-Length header to reject oversized uploads
    before they are fully received.

    Usage:
        app.add_middleware(
            FileSizeLimiterMiddleware,
            max_file_size=10 * 1024 * 1024  # 10 MB
        )
    """

    def __init__(self, app, max_file_size: int = 10 * 1024 * 1024):
        """Initialize file size limiter middleware

        Args:
            app: FastAPI application instance
            max_file_size: Maximum file size in bytes (default 10 MB)
        """
        super().__init__(app)
        self.max_file_size = max_file_size

        logger.info(
            f"FileSizeLimiterMiddleware initialized: "
            f"max_file_size={self.max_file_size / (1024*1024):.1f} MB"
        )

    async def dispatch(self, request: Request, call_next: Callable):
        """Check file size and process request

        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain

        Returns:
            Response from next handler or 413 error if file too large
        """
        # Check Content-Length header
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                content_length = int(content_length)
                if content_length > self.max_file_size:
                    logger.warning(
                        f"File size limit exceeded: {content_length} > {self.max_file_size} "
                        f"for {request.url.path}"
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": t('messages.file_too_large'),
                            "error": "file_too_large",
                            "max_size_mb": self.max_file_size / (1024 * 1024)
                        }
                    )
            except ValueError:
                # Invalid Content-Length header, let it pass
                logger.warning(f"Invalid Content-Length header: {content_length}")

        # Process request
        return await call_next(request)
