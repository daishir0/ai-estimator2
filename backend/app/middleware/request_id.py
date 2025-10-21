"""Request ID tracking middleware for distributed tracing"""
import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from app.core.logging_config import get_logger
from app.core.metrics import metrics_collector

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request ID to each request

    Features:
    - Generates unique UUID for each request
    - Adds request_id to request.state (accessible in all endpoints)
    - Adds X-Request-ID to response headers
    - Logs all requests with timing information
    - Handles errors gracefully
    """

    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Record start time
        start_time = time.perf_counter()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.perf_counter() - start_time

            # Log successful request
            logger.info(
                f"{request.method} {request.url.path}",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=round(duration, 3)
            )

            # Record metrics
            metrics_collector.record_api_call(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                duration=duration,
                request_id=request_id
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration even on error
            duration = time.perf_counter() - start_time

            # Log failed request
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration=round(duration, 3)
            )

            # Record error metrics
            metrics_collector.record_error(
                error_type=type(e).__name__,
                message=str(e),
                request_id=request_id,
                endpoint=request.url.path
            )

            # Re-raise exception to let FastAPI handle it
            raise
