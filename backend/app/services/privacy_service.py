"""Privacy service for PII detection, masking, and GDPR compliance"""
import re
from typing import Dict, List, Tuple
from app.core.i18n import t
from app.core.logging_config import PIIMasker


class PrivacyService:
    """Privacy protection service with PII detection and GDPR compliance features"""

    # Extended PII detection patterns (in addition to PIIMasker)
    PII_PATTERNS = {
        "email": PIIMasker.EMAIL_PATTERN,
        "phone": PIIMasker.PHONE_PATTERN,
        "phone_intl": r'\b\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{4}\b',  # International phone
        "credit_card": PIIMasker.CREDIT_CARD_PATTERN,
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',  # US Social Security Number
        "my_number": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Japanese My Number
    }

    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """
        Detect PII (Personally Identifiable Information) in text

        Args:
            text: Text to scan for PII

        Returns:
            Dictionary of detected PII types and their matches
            Example: {"email": ["test@example.com"], "phone": ["090-1234-5678"]}
        """
        if not text:
            return {}

        detected = {}
        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                detected[pii_type] = matches

        return detected

    def mask_pii(self, text: str) -> str:
        """
        Mask PII in text with placeholder strings

        Args:
            text: Text containing potential PII

        Returns:
            Text with PII masked
            Example: "Contact: test@example.com" -> "Contact: [EMAIL_MASKED]"
        """
        if not text:
            return text

        masked_text = text
        for pii_type, pattern in self.PII_PATTERNS.items():
            masked_text = re.sub(
                pattern,
                f"[{pii_type.upper()}_MASKED]",
                masked_text,
                flags=re.IGNORECASE
            )

        return masked_text

    def check_pii_compliance(self, text: str) -> Tuple[bool, str]:
        """
        Check if text is compliant with PII policies

        Args:
            text: Text to check

        Returns:
            Tuple of (is_compliant: bool, message: str)
            - (True, "OK") if no PII detected
            - (False, "PII detected: email, phone") if PII found
        """
        detected = self.detect_pii(text)

        if detected:
            pii_types = ", ".join(detected.keys())
            return False, f"{t('messages.pii_detected')}: {pii_types}"

        return True, "OK"

    def sanitize_for_logging(self, text: str) -> str:
        """
        Sanitize text for safe logging (PII removal)

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text safe for logging
        """
        return self.mask_pii(text)

    def get_pii_summary(self, text: str) -> Dict[str, int]:
        """
        Get summary of PII occurrences

        Args:
            text: Text to analyze

        Returns:
            Dictionary of PII types and their counts
            Example: {"email": 2, "phone": 1}
        """
        detected = self.detect_pii(text)
        return {pii_type: len(matches) for pii_type, matches in detected.items()}
