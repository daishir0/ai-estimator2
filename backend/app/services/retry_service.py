"""Retry service with exponential backoff

This module provides a decorator for retrying operations with exponential backoff,
primarily designed for OpenAI API calls and other external service interactions.
"""
import time
import logging
from functools import wraps
from typing import Callable, Any, Tuple, Type
from app.core.config import settings

logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(
    max_retries: int = None,
    initial_delay: float = None,
    backoff_factor: float = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """Decorator for retrying operations with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts (default: settings.OPENAI_MAX_RETRIES)
        initial_delay: Initial delay in seconds (default: settings.OPENAI_RETRY_INITIAL_DELAY)
        backoff_factor: Exponential backoff factor (default: settings.OPENAI_RETRY_BACKOFF_FACTOR)
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_exponential_backoff(max_retries=3)
        def call_api():
            return client.chat.completions.create(...)
    """
    max_retries = max_retries if max_retries is not None else settings.OPENAI_MAX_RETRIES
    initial_delay = initial_delay if initial_delay is not None else settings.OPENAI_RETRY_INITIAL_DELAY
    backoff_factor = backoff_factor if backoff_factor is not None else settings.OPENAI_RETRY_BACKOFF_FACTOR

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # If this is the last attempt, raise the exception
                    if attempt == max_retries - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = initial_delay * (backoff_factor ** attempt)

                    logger.warning(
                        f"{func.__name__} retry {attempt + 1}/{max_retries} "
                        f"after {delay:.1f}s: {e}"
                    )

                    time.sleep(delay)

            # This should never be reached, but raise if it does
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def retry_with_custom_backoff(
    backoff_delays: list[float],
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """Decorator for retrying operations with custom backoff delays

    This function is provided for backward compatibility with existing retry logic
    that uses fixed delays like [0, 1.0, 2.0].

    Args:
        backoff_delays: List of delays in seconds for each retry attempt
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_custom_backoff([0, 1.0, 2.0])
        def call_api():
            return client.chat.completions.create(...)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt, delay in enumerate(backoff_delays):
                if delay > 0:
                    logger.warning(
                        f"{func.__name__} retry {attempt + 1}/{len(backoff_delays)} "
                        f"after {delay:.1f}s"
                    )
                    time.sleep(delay)

                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # If this is the last attempt, raise the exception
                    if attempt == len(backoff_delays) - 1:
                        logger.error(
                            f"{func.__name__} failed after {len(backoff_delays)} attempts: {e}"
                        )
                        raise

            # This should never be reached, but raise if it does
            if last_exception:
                raise last_exception

        return wrapper
    return decorator
