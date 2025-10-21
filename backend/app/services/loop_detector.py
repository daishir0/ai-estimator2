"""Loop detection service to prevent infinite loops and excessive iterations"""
import threading
from typing import Dict, Optional
from app.core.config import settings
from app.core.i18n import t
import logging

logger = logging.getLogger(__name__)


class LoopDetector:
    """Detects infinite loops and excessive iterations

    This service tracks iteration counts for operations and raises an exception
    when the maximum iteration limit is exceeded.

    Usage:
        detector = LoopDetector(context_id="task-123")
        for item in items:
            detector.check("processing_items")
            # ... process item
    """

    def __init__(self, context_id: str = "default", max_iterations: Optional[int] = None):
        """Initialize loop detector

        Args:
            context_id: Identifier for the context (e.g., task_id)
            max_iterations: Maximum allowed iterations (defaults to config setting)
        """
        self.context_id = context_id
        self.max_iterations = max_iterations or getattr(settings, 'MAX_ITERATIONS', 10)
        self.iteration_count = 0
        self._lock = threading.Lock()

    def check(self, operation_name: str = "operation") -> None:
        """Check iteration count and raise exception if limit exceeded

        Args:
            operation_name: Name of the operation being performed

        Raises:
            Exception: When iteration count exceeds max_iterations
        """
        with self._lock:
            self.iteration_count += 1

            if self.iteration_count > self.max_iterations:
                error_msg = (
                    f"{t('messages.max_iterations_exceeded')}: {operation_name} "
                    f"(context={self.context_id}, count={self.iteration_count}, "
                    f"limit={self.max_iterations})"
                )
                logger.error(error_msg)
                raise Exception(error_msg)

            # Log warning when approaching limit
            if self.iteration_count == self.max_iterations:
                logger.warning(
                    f"Iteration limit reached for {operation_name} "
                    f"(context={self.context_id}, count={self.iteration_count})"
                )

    def reset(self) -> None:
        """Reset iteration counter"""
        with self._lock:
            logger.debug(f"Loop detector reset (context={self.context_id})")
            self.iteration_count = 0

    def get_count(self) -> int:
        """Get current iteration count"""
        with self._lock:
            return self.iteration_count


class LoopDetectorManager:
    """Manages multiple loop detectors by context

    This class provides a centralized way to manage loop detectors
    for different contexts (e.g., different tasks).

    Usage:
        manager = LoopDetectorManager()
        detector = manager.get_detector("task-123")
        detector.check("processing")
    """

    def __init__(self):
        self._detectors: Dict[str, LoopDetector] = {}
        self._lock = threading.Lock()

    def get_detector(
        self,
        context_id: str,
        max_iterations: Optional[int] = None
    ) -> LoopDetector:
        """Get or create a loop detector for the given context

        Args:
            context_id: Identifier for the context
            max_iterations: Maximum allowed iterations (optional)

        Returns:
            LoopDetector instance for the context
        """
        with self._lock:
            if context_id not in self._detectors:
                self._detectors[context_id] = LoopDetector(
                    context_id=context_id,
                    max_iterations=max_iterations
                )
            return self._detectors[context_id]

    def remove_detector(self, context_id: str) -> None:
        """Remove a loop detector for the given context

        Args:
            context_id: Identifier for the context
        """
        with self._lock:
            if context_id in self._detectors:
                logger.debug(f"Removing loop detector for context: {context_id}")
                del self._detectors[context_id]

    def reset_detector(self, context_id: str) -> None:
        """Reset a loop detector for the given context

        Args:
            context_id: Identifier for the context
        """
        with self._lock:
            if context_id in self._detectors:
                self._detectors[context_id].reset()

    def cleanup_all(self) -> None:
        """Remove all loop detectors"""
        with self._lock:
            logger.debug(f"Cleaning up all loop detectors (count={len(self._detectors)})")
            self._detectors.clear()


# Global instance for shared use
loop_detector_manager = LoopDetectorManager()
