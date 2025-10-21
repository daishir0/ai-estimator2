"""Unit tests for LoopDetector"""
import pytest
import threading
import time
from app.services.loop_detector import LoopDetector, LoopDetectorManager


class TestLoopDetector:
    """Test class for LoopDetector"""

    def test_check_within_limit(self):
        """Test that iterations within limit do not raise exception"""
        detector = LoopDetector(context_id="test-1", max_iterations=5)

        # Should not raise exception for iterations within limit
        for i in range(5):
            detector.check("test_operation")

        assert detector.get_count() == 5

    def test_check_exceeds_limit(self):
        """Test that exceeding iteration limit raises exception"""
        detector = LoopDetector(context_id="test-2", max_iterations=3)

        # First 3 iterations should succeed
        for i in range(3):
            detector.check("test_operation")

        # 4th iteration should raise exception
        with pytest.raises(Exception) as exc_info:
            detector.check("test_operation")

        assert "max_iterations_exceeded" in str(exc_info.value) or "最大イテレーション数を超過" in str(exc_info.value)
        assert "test_operation" in str(exc_info.value)
        assert detector.get_count() == 4

    def test_reset(self):
        """Test that reset clears iteration count"""
        detector = LoopDetector(context_id="test-3", max_iterations=5)

        # Perform some iterations
        for i in range(3):
            detector.check("test_operation")

        assert detector.get_count() == 3

        # Reset
        detector.reset()
        assert detector.get_count() == 0

        # Should be able to iterate again
        for i in range(5):
            detector.check("test_operation")

        assert detector.get_count() == 5

    def test_get_count(self):
        """Test get_count returns correct iteration count"""
        detector = LoopDetector(context_id="test-4", max_iterations=10)

        assert detector.get_count() == 0

        detector.check("op1")
        assert detector.get_count() == 1

        detector.check("op2")
        detector.check("op3")
        assert detector.get_count() == 3

    def test_thread_safety(self):
        """Test that loop detector is thread-safe"""
        detector = LoopDetector(context_id="test-5", max_iterations=100)
        errors = []

        def worker():
            try:
                for i in range(10):
                    detector.check("thread_operation")
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = [threading.Thread(target=worker) for _ in range(5)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Should have performed 5 * 10 = 50 iterations
        assert detector.get_count() == 50
        assert len(errors) == 0

    def test_default_max_iterations(self):
        """Test that default max_iterations is used from settings"""
        detector = LoopDetector(context_id="test-6")

        # Should use default from settings (10)
        for i in range(10):
            detector.check("test_operation")

        # 11th iteration should raise exception
        with pytest.raises(Exception):
            detector.check("test_operation")

    def test_context_id_in_error_message(self):
        """Test that context_id is included in error message"""
        detector = LoopDetector(context_id="task-abc-123", max_iterations=1)

        detector.check("operation")

        with pytest.raises(Exception) as exc_info:
            detector.check("operation")

        assert "task-abc-123" in str(exc_info.value)


class TestLoopDetectorManager:
    """Test class for LoopDetectorManager"""

    def test_get_detector_creates_new(self):
        """Test that get_detector creates a new detector if it doesn't exist"""
        manager = LoopDetectorManager()

        detector = manager.get_detector("context-1")
        assert detector is not None
        assert detector.context_id == "context-1"

    def test_get_detector_returns_existing(self):
        """Test that get_detector returns existing detector for same context"""
        manager = LoopDetectorManager()

        detector1 = manager.get_detector("context-2")
        detector1.check("op1")

        detector2 = manager.get_detector("context-2")
        assert detector1 is detector2
        assert detector2.get_count() == 1

    def test_get_detector_with_custom_max_iterations(self):
        """Test that get_detector respects custom max_iterations"""
        manager = LoopDetectorManager()

        detector = manager.get_detector("context-3", max_iterations=20)
        assert detector.max_iterations == 20

    def test_remove_detector(self):
        """Test that remove_detector removes the detector"""
        manager = LoopDetectorManager()

        detector1 = manager.get_detector("context-4")
        detector1.check("op1")

        manager.remove_detector("context-4")

        # Getting detector again should create a new one
        detector2 = manager.get_detector("context-4")
        assert detector2.get_count() == 0

    def test_reset_detector(self):
        """Test that reset_detector resets the detector's count"""
        manager = LoopDetectorManager()

        detector = manager.get_detector("context-5")
        detector.check("op1")
        detector.check("op2")
        assert detector.get_count() == 2

        manager.reset_detector("context-5")
        assert detector.get_count() == 0

    def test_cleanup_all(self):
        """Test that cleanup_all removes all detectors"""
        manager = LoopDetectorManager()

        # Create multiple detectors
        detector1 = manager.get_detector("context-6")
        detector2 = manager.get_detector("context-7")
        detector3 = manager.get_detector("context-8")

        detector1.check("op1")
        detector2.check("op2")
        detector3.check("op3")

        # Cleanup all
        manager.cleanup_all()

        # Getting detectors again should create new ones
        new_detector1 = manager.get_detector("context-6")
        assert new_detector1.get_count() == 0

    def test_manager_thread_safety(self):
        """Test that manager operations are thread-safe"""
        manager = LoopDetectorManager()
        errors = []

        def worker(context_id):
            try:
                detector = manager.get_detector(context_id)
                for i in range(5):
                    detector.check("thread_op")
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        # Create multiple threads accessing different contexts
        threads = [
            threading.Thread(target=worker, args=(f"context-{i}",))
            for i in range(10)
        ]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Each context should have 5 iterations
        for i in range(10):
            detector = manager.get_detector(f"context-{i}")
            assert detector.get_count() == 5

        assert len(errors) == 0
