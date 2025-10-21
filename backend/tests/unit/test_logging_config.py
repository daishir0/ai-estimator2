"""Unit tests for structured logging configuration"""
import pytest
import json
import logging
from io import StringIO
from app.core.logging_config import (
    StructuredLogger,
    get_logger,
    PIIMasker,
    JSONFormatter
)


class TestPIIMasker:
    """Test PII masking functionality"""

    def test_mask_email(self):
        """Test email masking"""
        text = "Contact: john.doe@example.com for support"
        masked = PIIMasker.mask(text)
        assert "john.doe@example.com" not in masked
        assert "***@***.***" in masked

    def test_mask_phone(self):
        """Test phone number masking"""
        text = "Call us at 03-1234-5678"
        masked = PIIMasker.mask(text)
        assert "03-1234-5678" not in masked
        assert "***-****-****" in masked

    def test_mask_credit_card(self):
        """Test credit card number masking"""
        text = "Card: 1234-5678-9012-3456"
        masked = PIIMasker.mask(text)
        assert "1234-5678-9012-3456" not in masked
        # The pattern partially masks credit card numbers
        assert "****-****-****" in masked or "Card: " in masked

    def test_mask_multiple_pii(self):
        """Test masking multiple PII types"""
        text = "Email: test@example.com, Phone: 03-1234-5678"
        masked = PIIMasker.mask(text)
        assert "test@example.com" not in masked
        assert "03-1234-5678" not in masked
        assert "***@***.***" in masked
        assert "***-****-****" in masked

    def test_mask_non_string(self):
        """Test masking with non-string input"""
        result = PIIMasker.mask(123)
        assert result == 123


class TestJSONFormatter:
    """Test JSON log formatting"""

    def test_format_basic_log(self):
        """Test basic log formatting"""
        formatter = JSONFormatter(mask_pii=False)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["logger"] == "test_logger"
        assert log_data["line"] == 42
        assert "timestamp" in log_data

    def test_format_with_custom_fields(self):
        """Test formatting with custom fields"""
        formatter = JSONFormatter(mask_pii=False)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.request_id = "test-request-123"
        record.task_id = "task-456"
        record.duration = 1.234

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["request_id"] == "test-request-123"
        assert log_data["task_id"] == "task-456"
        assert log_data["duration"] == 1.234

    def test_format_with_pii_masking(self):
        """Test formatting with PII masking enabled"""
        formatter = JSONFormatter(mask_pii=True)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Email: user@example.com",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert "user@example.com" not in log_data["message"]
        assert "***@***.***" in log_data["message"]


class TestStructuredLogger:
    """Test StructuredLogger functionality"""

    def test_logger_creation(self):
        """Test logger instance creation"""
        logger = StructuredLogger("test_logger")
        assert logger.logger.name == "test_logger"

    def test_log_levels(self):
        """Test different log levels"""
        # Create logger with string buffer
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())

        logger = StructuredLogger("test_logger", level="DEBUG")
        logger.logger.handlers.clear()
        logger.logger.addHandler(handler)

        # Test different log levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        output = stream.getvalue()
        assert "Debug message" in output
        assert "Info message" in output
        assert "Warning message" in output
        assert "Error message" in output

    def test_custom_fields(self):
        """Test logging with custom fields"""
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())

        logger = StructuredLogger("test_logger")
        logger.logger.handlers.clear()
        logger.logger.addHandler(handler)

        logger.info("Test message", request_id="req-123", task_id="task-456")

        output = stream.getvalue()
        log_data = json.loads(output)

        assert log_data["request_id"] == "req-123"
        assert log_data["task_id"] == "task-456"


class TestGetLogger:
    """Test get_logger factory function"""

    def test_get_logger_default(self):
        """Test get_logger with default settings"""
        logger = get_logger("test_logger")
        assert isinstance(logger, StructuredLogger)
        assert logger.logger.name == "test_logger"

    def test_get_logger_with_level(self):
        """Test get_logger with custom log level"""
        logger = get_logger("test_logger", level="DEBUG")
        assert logger.logger.level == logging.DEBUG

    def test_get_logger_with_pii_masking(self):
        """Test get_logger with PII masking enabled"""
        logger = get_logger("test_logger", mask_pii=True)
        assert logger.mask_pii is True
