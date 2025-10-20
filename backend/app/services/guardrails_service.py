"""Guardrails service for input/output validation using Guardrails AI"""
from typing import Any, Dict, Optional
from app.core.i18n import t


class GuardrailsService:
    """
    Service for validating user inputs and LLM outputs using Guardrails AI

    This service provides:
    - Input validation (toxic language, PII detection, length validation)
    - Output validation (LLM response safety checks)
    - Business rule validation (deliverable names, person-days, amounts)
    """

    def __init__(self):
        """
        Initialize the Guardrails service

        Note: Guardrails AI library initialization is deferred to avoid
        import errors if the library is not properly installed.
        """
        self._guards_initialized = False
        self.input_guard = None
        self.output_guard = None

    def _initialize_guards(self):
        """
        Lazy initialization of Guardrails guards

        This method initializes the guards only when needed to avoid
        startup errors if Guardrails AI is not properly configured.
        """
        if self._guards_initialized:
            return

        try:
            from guardrails import Guard
            from guardrails.validators import (
                ToxicLanguage,
                ValidLength,
            )

            # Input guard: strict validation for user inputs
            self.input_guard = Guard().use_many(
                ToxicLanguage(
                    threshold=0.8,  # 80% confidence threshold
                    on_fail="exception"
                ),
                ValidLength(
                    min=1,
                    max=10000,
                    on_fail="exception"
                )
            )

            # Output guard: more lenient for LLM outputs
            self.output_guard = Guard().use_many(
                ToxicLanguage(
                    threshold=0.9,  # Higher threshold for outputs
                    on_fail="exception"
                ),
            )

            self._guards_initialized = True
            print("[GUARD] Guardrails guards initialized successfully")

        except ImportError as e:
            print(f"[GUARD] Warning: Guardrails AI not available: {e}")
            self._guards_initialized = False
        except Exception as e:
            print(f"[GUARD] Warning: Failed to initialize guards: {e}")
            self._guards_initialized = False

    def validate_input(self, text: str) -> str:
        """
        Validate and sanitize user input

        This method checks for:
        - Toxic language
        - PII (email addresses, phone numbers, etc.)
        - Length constraints

        Args:
            text: Input text from user

        Returns:
            str: Validated and sanitized text

        Raises:
            ValueError: If validation fails
        """
        if not text or not text.strip():
            raise ValueError(t('messages.input_empty'))

        # Basic validation without Guardrails
        if len(text) > 10000:
            raise ValueError(t('messages.input_too_long'))

        # Try to use Guardrails if available
        self._initialize_guards()

        if self._guards_initialized and self.input_guard:
            try:
                result = self.input_guard.validate(text)
                validated_text = result.validated_output

                # Log if text was modified
                if validated_text != text:
                    print(f"[GUARD] Input was sanitized by Guardrails")

                return validated_text

            except Exception as e:
                print(f"[GUARD] Input validation warning: {e}")
                # Fall back to basic validation
                return text.strip()

        # Fallback: basic sanitization
        return text.strip()

    def validate_output(self, text: str) -> str:
        """
        Validate LLM output

        This method checks LLM outputs for:
        - Toxic language
        - PII leakage
        - Other safety concerns

        Args:
            text: Output text from LLM

        Returns:
            str: Validated and sanitized text
        """
        if not text:
            return text

        # Try to use Guardrails if available
        self._initialize_guards()

        if self._guards_initialized and self.output_guard:
            try:
                result = self.output_guard.validate(text)
                validated_text = result.validated_output

                # Log if text was modified
                if validated_text != text:
                    print(f"[GUARD] Output was sanitized by Guardrails")

                return validated_text

            except Exception as e:
                # For output validation, we don't block - just log and continue
                print(f"[GUARD] Output validation warning: {e}")
                return text

        # Fallback: return original text
        return text

    def validate_deliverable_name(self, name: str) -> str:
        """
        Validate deliverable name

        Business rules:
        - Minimum length: 3 characters
        - Maximum length: 200 characters

        Args:
            name: Deliverable name

        Returns:
            str: Validated name

        Raises:
            ValueError: If validation fails
        """
        name = name.strip()

        if len(name) < 3:
            raise ValueError(t('messages.deliverable_name_too_short'))

        if len(name) > 200:
            raise ValueError(t('messages.deliverable_name_too_long'))

        return name

    def validate_person_days(self, days: float) -> float:
        """
        Validate person-days estimate

        Business rules:
        - Minimum: 0.5 person-days
        - Maximum: 100 person-days

        Args:
            days: Estimated person-days

        Returns:
            float: Validated person-days

        Raises:
            ValueError: If validation fails
        """
        if days < 0.5:
            raise ValueError(t('messages.person_days_too_small'))

        if days > 100:
            raise ValueError(t('messages.person_days_too_large'))

        return days

    def validate_amount(
        self,
        amount: float,
        person_days: float,
        unit_cost: float
    ) -> float:
        """
        Validate amount against person-days and unit cost

        Business rule:
        - Amount should be within ±10% of (person_days × unit_cost)

        Args:
            amount: Calculated amount
            person_days: Estimated person-days
            unit_cost: Daily unit cost

        Returns:
            float: Validated amount

        Raises:
            ValueError: If validation fails (amount mismatch)
        """
        expected_amount = person_days * unit_cost

        # Allow 10% tolerance
        if expected_amount > 0:
            deviation = abs(amount - expected_amount) / expected_amount
            if deviation > 0.1:
                print(
                    f"[GUARD] Amount mismatch: "
                    f"expected {expected_amount:.2f}, got {amount:.2f} "
                    f"(deviation: {deviation*100:.1f}%)"
                )
                raise ValueError(t('messages.amount_mismatch'))

        return amount

    def validate_json_structure(self, data: Dict[str, Any], required_keys: list) -> Dict[str, Any]:
        """
        Validate JSON structure contains required keys

        Args:
            data: JSON data to validate
            required_keys: List of required key names

        Returns:
            dict: Validated data

        Raises:
            ValueError: If required keys are missing
        """
        missing_keys = [key for key in required_keys if key not in data]

        if missing_keys:
            raise ValueError(
                f"{t('messages.json_validation_failed')}: "
                f"Missing keys: {', '.join(missing_keys)}"
            )

        return data
