"""Security service for detecting malicious inputs and prompt injection attacks"""
import re
from typing import List
from app.core.i18n import t


class SecurityService:
    """
    Service for detecting and preventing security threats including:
    - Prompt injection attacks
    - Command injection patterns
    - SQL injection patterns
    """

    # Prompt injection patterns (English)
    INJECTION_PATTERNS_EN = [
        r"ignore\s+(previous|all|the)\s+instructions?",
        r"disregard\s+.*\s+rules?",
        r"system\s+prompt",
        r"forget\s+(everything|all|your)",
        r"new\s+instructions?:",
        r"override\s+.*\s+settings?",
        r"you\s+are\s+now",
        r"pretend\s+(you\s+are|to\s+be)",
        r"act\s+as\s+if",
        r"from\s+now\s+on",
        r"[Ii]gnore.*above",
        r"[Dd]isregard.*earlier",
        r"[Ff]orget.*previous",
    ]

    # Prompt injection patterns (Japanese)
    INJECTION_PATTERNS_JA = [
        r"以前の指示を無視",
        r"指示を忘れ",
        r"システムプロンプト",
        r"ルールを無視",
        r"新しい指示",
        r"今から.*になって",
        r".*として振る舞",
        r".*のフリをし",
        r"上記を無視",
        r"前述の.*を忘れ",
    ]

    # Command injection patterns
    COMMAND_PATTERNS = [
        r";\s*rm\s+-rf",
        r"&&\s*cat",
        r"\|\s*nc\s+",
        r"'\s*;\s*DROP\s+TABLE",
        r"UNION\s+SELECT",
        r"<script",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
    ]

    # SQL injection patterns
    SQL_PATTERNS = [
        r"'\s*OR\s+'1'\s*=\s*'1",
        r"--\s*$",
        r"/\*.*\*/",
        r";\s*DROP\s+",
        r";\s*DELETE\s+FROM",
        r";\s*UPDATE\s+",
    ]

    def check_prompt_injection(self, text: str) -> None:
        """
        Check for prompt injection attacks

        This method scans user input for malicious patterns that could
        manipulate the LLM's behavior or extract sensitive information.

        Args:
            text: User input text to validate

        Raises:
            ValueError: If a malicious pattern is detected
        """
        if not text:
            return

        # Check English prompt injection patterns
        for pattern in self.INJECTION_PATTERNS_EN:
            if re.search(pattern, text, re.IGNORECASE):
                print(f"[SECURITY] Prompt injection detected (EN): {pattern}")
                raise ValueError(t('messages.prompt_injection_detected'))

        # Check Japanese prompt injection patterns
        for pattern in self.INJECTION_PATTERNS_JA:
            if re.search(pattern, text):
                print(f"[SECURITY] Prompt injection detected (JA): {pattern}")
                raise ValueError(t('messages.prompt_injection_detected'))

        # Check command injection patterns
        for pattern in self.COMMAND_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                print(f"[SECURITY] Command injection detected: {pattern}")
                raise ValueError(t('messages.command_injection_detected'))

        # Check SQL injection patterns
        for pattern in self.SQL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                print(f"[SECURITY] SQL injection detected: {pattern}")
                raise ValueError(t('messages.sql_injection_detected'))

    def is_suspicious(self, text: str) -> bool:
        """
        Non-blocking check for suspicious patterns

        This method checks if the text contains suspicious patterns
        without raising an exception. Useful for logging and monitoring.

        Args:
            text: User input text to check

        Returns:
            bool: True if suspicious patterns found, False otherwise
        """
        try:
            self.check_prompt_injection(text)
            return False
        except ValueError:
            return True

    def sanitize_input(self, text: str) -> str:
        """
        Sanitize user input by removing potentially dangerous characters

        Args:
            text: Input text to sanitize

        Returns:
            str: Sanitized text
        """
        if not text:
            return text

        # Remove script tags content first (before removing other HTML tags)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove null bytes
        text = text.replace('\x00', '')

        return text.strip()
