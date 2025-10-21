"""Structured logging configuration with JSON formatting"""
import logging
import json
import re
from datetime import datetime
from typing import Any, Dict, Optional


class PIIMasker:
    """PII (Personally Identifiable Information) masking utility"""

    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PHONE_PATTERN = r'\b\d{2,4}-\d{2,4}-\d{4}\b'
    CREDIT_CARD_PATTERN = r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'

    @staticmethod
    def mask(text: str) -> str:
        """Mask PII information in text"""
        if not isinstance(text, str):
            return text

        text = re.sub(PIIMasker.EMAIL_PATTERN, '***@***.***', text)
        text = re.sub(PIIMasker.PHONE_PATTERN, '***-****-****', text)
        text = re.sub(PIIMasker.CREDIT_CARD_PATTERN, '****-****-****-****', text)
        return text


class JSONFormatter(logging.Formatter):
    """JSON format formatter for structured logging"""

    def __init__(self, mask_pii: bool = False):
        super().__init__()
        self.mask_pii = mask_pii

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Apply PII masking if enabled
        if self.mask_pii:
            log_data["message"] = PIIMasker.mask(log_data["message"])

        # Add custom fields
        for key in ["request_id", "task_id", "user_id", "duration", "status_code",
                    "deliverable_count", "max_workers", "model", "tokens", "operation"]:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        # Add exception information
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """Structured logger with JSON output"""

    def __init__(self, name: str, level: str = "INFO", log_file: Optional[str] = None, mask_pii: bool = False):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self.mask_pii = mask_pii

        # Avoid duplicate handlers
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(JSONFormatter(mask_pii=mask_pii))
            self.logger.addHandler(console_handler)

            # File handler (if specified)
            if log_file:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(JSONFormatter(mask_pii=mask_pii))
                self.logger.addHandler(file_handler)

    def info(self, message: str, **kwargs):
        """Log INFO level message"""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log WARNING level message"""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log ERROR level message"""
        self.logger.error(message, extra=kwargs)

    def debug(self, message: str, **kwargs):
        """Log DEBUG level message"""
        self.logger.debug(message, extra=kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra=kwargs)


def get_logger(name: str, level: Optional[str] = None, log_file: Optional[str] = None,
               mask_pii: bool = False) -> StructuredLogger:
    """
    Get structured logger instance

    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        mask_pii: Enable PII masking

    Returns:
        StructuredLogger instance
    """
    from app.core.config import settings

    # Use settings if not explicitly specified
    if level is None:
        level = getattr(settings, 'LOG_LEVEL', 'INFO')
    if log_file is None:
        log_file = getattr(settings, 'LOG_FILE', None)

    return StructuredLogger(name, level=level, log_file=log_file, mask_pii=mask_pii)
