"""
SafetyService: Integrated safety checking and rejection handling

This service provides:
- Input safety validation (combining Guardrails and Security checks)
- Output safety validation
- Rejection handling with user-friendly error messages
- Comprehensive logging for security auditing
"""

from typing import Tuple
import logging
from fastapi import HTTPException
from app.services.guardrails_service import GuardrailsService
from app.services.security_service import SecurityService
from app.core.i18n import t

logger = logging.getLogger(__name__)


class SafetyService:
    """Safety checking and rejection handling service"""

    def __init__(self):
        """Initialize with Guardrails and Security services"""
        self.guardrails = GuardrailsService()
        self.security = SecurityService()

    def check_input_safety(self, content: str, content_type: str = "input") -> Tuple[bool, str]:
        """
        Check input safety using both Guardrails and Security services

        Args:
            content: Input text to validate
            content_type: Type of content (for logging purposes)

        Returns:
            (is_safe: bool, message: str)
            - is_safe: True if content passes all checks
            - message: "OK" if safe, error message if not safe

        Raises:
            No exceptions raised - returns status tuple instead
        """
        try:
            # 1. Security check (prompt injection)
            self.security.check_prompt_injection(content)

            # 2. Guardrails check (toxic language, PII, length)
            self.guardrails.validate_input(content)

            logger.info(f"Safety check passed for {content_type}")
            return True, "OK"

        except ValueError as e:
            error_msg = str(e)
            logger.warning(f"Safety check failed ({content_type}): {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error in safety check ({content_type}): {error_msg}")
            return False, error_msg

    def check_output_safety(self, content: str) -> Tuple[bool, str]:
        """
        Check output safety using Guardrails service

        Args:
            content: Output text to validate

        Returns:
            (is_safe: bool, message: str)
            - is_safe: True if content passes all checks
            - message: "OK" if safe, error message if not safe

        Raises:
            No exceptions raised - returns status tuple instead
        """
        try:
            self.guardrails.validate_output(content)
            logger.info("Output safety check passed")
            return True, "OK"
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Output safety check failed: {error_msg}")
            return False, error_msg

    def handle_rejection(self, reason: str, content_type: str = "input") -> None:
        """
        Handle rejected input/output by logging and raising user-friendly exception

        Args:
            reason: Rejection reason (technical error message)
            content_type: Type of content that was rejected

        Raises:
            HTTPException: 400 Bad Request with user-friendly message
        """
        # Log rejection for security auditing
        logger.warning(f"Request rejected ({content_type}): {reason}")

        # Generate user-friendly error message
        user_message = self._get_user_friendly_message(reason)

        # Raise HTTP exception with user-friendly message
        raise HTTPException(
            status_code=400,
            detail=user_message
        )

    def _get_user_friendly_message(self, reason: str) -> str:
        """
        Convert technical error message to user-friendly message

        Args:
            reason: Technical error message

        Returns:
            User-friendly error message (translated)
        """
        reason_lower = reason.lower()

        # Map technical errors to user-friendly messages
        if "prompt_injection" in reason_lower or "prompt injection" in reason_lower:
            return t('messages.prompt_injection_detected')
        elif "toxic" in reason_lower or "inappropriate" in reason_lower:
            return t('messages.safety_toxic_content')
        elif "pii" in reason_lower or "personal information" in reason_lower:
            return t('messages.safety_pii_detected')
        elif "length" in reason_lower or "too long" in reason_lower:
            return t('messages.safety_length_exceeded')
        else:
            # Generic rejection message
            return t('messages.safety_general_rejection')

    def validate_and_reject(self, content: str, content_type: str = "input") -> None:
        """
        Convenience method: validate input and reject if unsafe

        Args:
            content: Input text to validate
            content_type: Type of content (for logging)

        Raises:
            HTTPException: 400 Bad Request if content is unsafe
        """
        is_safe, message = self.check_input_safety(content, content_type)
        if not is_safe:
            self.handle_rejection(message, content_type)
