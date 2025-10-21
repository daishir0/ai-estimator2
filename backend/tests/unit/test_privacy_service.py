"""Unit tests for PrivacyService"""
import pytest
from app.services.privacy_service import PrivacyService


class TestPrivacyService:
    """Test suite for PrivacyService"""

    @pytest.fixture
    def privacy_service(self):
        """Create PrivacyService instance"""
        return PrivacyService()

    def test_detect_pii_email(self, privacy_service):
        """Test email detection"""
        text = "Contact us at support@example.com"
        detected = privacy_service.detect_pii(text)

        assert "email" in detected
        assert "support@example.com" in detected["email"]

    def test_detect_pii_phone(self, privacy_service):
        """Test phone number detection"""
        text = "Please call 090-1234-5678"
        detected = privacy_service.detect_pii(text)

        assert "phone" in detected
        assert "090-1234-5678" in detected["phone"]

    def test_detect_pii_credit_card(self, privacy_service):
        """Test credit card detection"""
        text = "Credit card: 1234-5678-9012-3456"
        detected = privacy_service.detect_pii(text)

        assert "credit_card" in detected
        assert "1234-5678-9012-3456" in detected["credit_card"]

    def test_detect_pii_my_number(self, privacy_service):
        """Test Japanese My Number detection"""
        text = "My Number: 1234-5678-9012"
        detected = privacy_service.detect_pii(text)

        assert "my_number" in detected
        assert "1234-5678-9012" in detected["my_number"]

    def test_detect_pii_multiple(self, privacy_service):
        """Test detection of multiple PII types"""
        text = "Contact: test@example.com, phone: 090-1234-5678"
        detected = privacy_service.detect_pii(text)

        assert "email" in detected
        assert "phone" in detected
        assert len(detected) == 2

    def test_detect_pii_no_pii(self, privacy_service):
        """Test text with no PII"""
        text = "This is a clean text with no personal information."
        detected = privacy_service.detect_pii(text)

        assert detected == {}

    def test_detect_pii_empty_string(self, privacy_service):
        """Test empty string"""
        detected = privacy_service.detect_pii("")

        assert detected == {}

    def test_detect_pii_none(self, privacy_service):
        """Test None input"""
        detected = privacy_service.detect_pii(None)

        assert detected == {}

    def test_mask_pii_email(self, privacy_service):
        """Test email masking"""
        text = "Contact us at support@example.com"
        masked = privacy_service.mask_pii(text)

        assert "support@example.com" not in masked
        assert "[EMAIL_MASKED]" in masked

    def test_mask_pii_phone(self, privacy_service):
        """Test phone number masking"""
        text = "Please call 090-1234-5678"
        masked = privacy_service.mask_pii(text)

        assert "090-1234-5678" not in masked
        assert "[PHONE_MASKED]" in masked

    def test_mask_pii_multiple(self, privacy_service):
        """Test masking of multiple PII types"""
        text = "Contact: test@example.com, phone: 090-1234-5678"
        masked = privacy_service.mask_pii(text)

        assert "test@example.com" not in masked
        assert "090-1234-5678" not in masked
        assert "[EMAIL_MASKED]" in masked
        assert "[PHONE_MASKED]" in masked

    def test_mask_pii_no_pii(self, privacy_service):
        """Test masking text with no PII"""
        text = "This is a clean text."
        masked = privacy_service.mask_pii(text)

        assert masked == text

    def test_mask_pii_empty_string(self, privacy_service):
        """Test masking empty string"""
        masked = privacy_service.mask_pii("")

        assert masked == ""

    def test_mask_pii_none(self, privacy_service):
        """Test masking None input"""
        masked = privacy_service.mask_pii(None)

        assert masked is None

    def test_check_pii_compliance_no_pii(self, privacy_service):
        """Test compliance check with no PII"""
        text = "This is a clean text."
        is_compliant, message = privacy_service.check_pii_compliance(text)

        assert is_compliant is True
        assert message == "OK"

    def test_check_pii_compliance_with_pii(self, privacy_service):
        """Test compliance check with PII"""
        text = "Contact: test@example.com"
        is_compliant, message = privacy_service.check_pii_compliance(text)

        assert is_compliant is False
        assert "email" in message

    def test_sanitize_for_logging(self, privacy_service):
        """Test log sanitization"""
        text = "User email: test@example.com, phone: 090-1234-5678"
        sanitized = privacy_service.sanitize_for_logging(text)

        assert "test@example.com" not in sanitized
        assert "090-1234-5678" not in sanitized
        assert "[EMAIL_MASKED]" in sanitized
        assert "[PHONE_MASKED]" in sanitized

    def test_get_pii_summary_no_pii(self, privacy_service):
        """Test PII summary with no PII"""
        text = "This is a clean text."
        summary = privacy_service.get_pii_summary(text)

        assert summary == {}

    def test_get_pii_summary_with_pii(self, privacy_service):
        """Test PII summary with PII"""
        text = "Contact: test@example.com, support@example.com, phone: 090-1234-5678"
        summary = privacy_service.get_pii_summary(text)

        assert summary["email"] == 2
        assert summary["phone"] == 1

    def test_international_phone(self, privacy_service):
        """Test international phone number detection"""
        text = "International: +81-90-1234-5678"
        detected = privacy_service.detect_pii(text)

        assert "phone_intl" in detected

    def test_ssn_detection(self, privacy_service):
        """Test US SSN detection"""
        text = "SSN: 123-45-6789"
        detected = privacy_service.detect_pii(text)

        assert "ssn" in detected
        assert "123-45-6789" in detected["ssn"]
