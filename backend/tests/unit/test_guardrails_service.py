"""Unit tests for GuardrailsService"""
import pytest
from app.services.guardrails_service import GuardrailsService


class TestGuardrailsService:
    """Test cases for GuardrailsService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = GuardrailsService()

    # Test: Input Validation - Basic Cases

    def test_validate_input_normal_text(self):
        """Test validation of normal input text"""
        normal_input = "Build an e-commerce website for 100 users with payment functionality."

        validated = self.service.validate_input(normal_input)

        assert validated is not None
        assert len(validated) > 0

    def test_validate_input_japanese_text(self):
        """Test validation of Japanese input text"""
        japanese_input = "100名規模のECサイトを構築します。決済機能とユーザー管理が必要です。"

        validated = self.service.validate_input(japanese_input)

        assert validated is not None
        assert len(validated) > 0

    def test_validate_input_empty_string_raises_error(self):
        """Test that empty string raises ValueError"""
        empty_input = ""

        with pytest.raises(ValueError):
            self.service.validate_input(empty_input)

    def test_validate_input_whitespace_only_raises_error(self):
        """Test that whitespace-only string raises ValueError"""
        whitespace_input = "   \n\t   "

        with pytest.raises(ValueError):
            self.service.validate_input(whitespace_input)

    def test_validate_input_too_long_raises_error(self):
        """Test that input longer than 10000 characters raises ValueError"""
        long_input = "A" * 10001

        with pytest.raises(ValueError):
            self.service.validate_input(long_input)

    def test_validate_input_at_max_length_passes(self):
        """Test that input at exactly 10000 characters passes"""
        max_length_input = "A" * 10000

        validated = self.service.validate_input(max_length_input)

        assert validated is not None

    # Test: Output Validation

    def test_validate_output_normal_text(self):
        """Test validation of normal output text"""
        normal_output = "The estimated effort is 10 person-days. This includes design, implementation, and testing."

        validated = self.service.validate_output(normal_output)

        assert validated is not None
        assert len(validated) > 0

    def test_validate_output_empty_string_returns_empty(self):
        """Test that empty string output is returned as-is"""
        empty_output = ""

        validated = self.service.validate_output(empty_output)

        assert validated == ""

    def test_validate_output_does_not_raise_on_invalid(self):
        """Test that output validation does not raise exceptions"""
        # Even if output validation fails, it should not raise
        # (outputs are more lenient than inputs)
        potentially_problematic_output = "Some output text"

        # Should not raise
        validated = self.service.validate_output(potentially_problematic_output)

        assert validated is not None

    # Test: Deliverable Name Validation

    def test_validate_deliverable_name_normal(self):
        """Test validation of normal deliverable name"""
        normal_name = "Requirements Document"

        validated = self.service.validate_deliverable_name(normal_name)

        assert validated == "Requirements Document"

    def test_validate_deliverable_name_japanese(self):
        """Test validation of Japanese deliverable name"""
        japanese_name = "要件定義書"

        validated = self.service.validate_deliverable_name(japanese_name)

        assert validated == "要件定義書"

    def test_validate_deliverable_name_too_short_raises_error(self):
        """Test that deliverable name shorter than 3 characters raises ValueError"""
        short_name = "AB"

        with pytest.raises(ValueError):
            self.service.validate_deliverable_name(short_name)

    def test_validate_deliverable_name_too_long_raises_error(self):
        """Test that deliverable name longer than 200 characters raises ValueError"""
        long_name = "A" * 201

        with pytest.raises(ValueError):
            self.service.validate_deliverable_name(long_name)

    def test_validate_deliverable_name_at_min_length_passes(self):
        """Test that deliverable name at exactly 3 characters passes"""
        min_length_name = "ABC"

        validated = self.service.validate_deliverable_name(min_length_name)

        assert validated == "ABC"

    def test_validate_deliverable_name_at_max_length_passes(self):
        """Test that deliverable name at exactly 200 characters passes"""
        max_length_name = "A" * 200

        validated = self.service.validate_deliverable_name(max_length_name)

        assert len(validated) == 200

    def test_validate_deliverable_name_strips_whitespace(self):
        """Test that deliverable name validation strips whitespace"""
        name_with_whitespace = "   Requirements Document   "

        validated = self.service.validate_deliverable_name(name_with_whitespace)

        assert validated == "Requirements Document"

    # Test: Person-Days Validation

    def test_validate_person_days_normal(self):
        """Test validation of normal person-days value"""
        normal_days = 10.5

        validated = self.service.validate_person_days(normal_days)

        assert validated == 10.5

    def test_validate_person_days_minimum(self):
        """Test validation of minimum person-days value (0.5)"""
        min_days = 0.5

        validated = self.service.validate_person_days(min_days)

        assert validated == 0.5

    def test_validate_person_days_maximum(self):
        """Test validation of maximum person-days value (100)"""
        max_days = 100.0

        validated = self.service.validate_person_days(max_days)

        assert validated == 100.0

    def test_validate_person_days_too_small_raises_error(self):
        """Test that person-days smaller than 0.5 raises ValueError"""
        too_small = 0.4

        with pytest.raises(ValueError):
            self.service.validate_person_days(too_small)

    def test_validate_person_days_too_large_raises_error(self):
        """Test that person-days larger than 100 raises ValueError"""
        too_large = 100.1

        with pytest.raises(ValueError):
            self.service.validate_person_days(too_large)

    def test_validate_person_days_zero_raises_error(self):
        """Test that zero person-days raises ValueError"""
        zero_days = 0.0

        with pytest.raises(ValueError):
            self.service.validate_person_days(zero_days)

    def test_validate_person_days_negative_raises_error(self):
        """Test that negative person-days raises ValueError"""
        negative_days = -5.0

        with pytest.raises(ValueError):
            self.service.validate_person_days(negative_days)

    # Test: Amount Validation

    def test_validate_amount_exact_match(self):
        """Test validation when amount exactly matches expected"""
        amount = 500000.0  # 10 days × 50000/day
        person_days = 10.0
        unit_cost = 50000.0

        validated = self.service.validate_amount(amount, person_days, unit_cost)

        assert validated == 500000.0

    def test_validate_amount_within_tolerance(self):
        """Test validation when amount is within 10% tolerance"""
        amount = 510000.0  # 2% deviation
        person_days = 10.0
        unit_cost = 50000.0

        validated = self.service.validate_amount(amount, person_days, unit_cost)

        assert validated == 510000.0

    def test_validate_amount_at_upper_tolerance_limit(self):
        """Test validation when amount is at upper 10% tolerance limit"""
        amount = 550000.0  # Exactly 10% above
        person_days = 10.0
        unit_cost = 50000.0

        # This should pass (10% tolerance)
        validated = self.service.validate_amount(amount, person_days, unit_cost)

        assert validated == 550000.0

    def test_validate_amount_at_lower_tolerance_limit(self):
        """Test validation when amount is at lower 10% tolerance limit"""
        amount = 450000.0  # Exactly 10% below
        person_days = 10.0
        unit_cost = 50000.0

        # This should pass (10% tolerance)
        validated = self.service.validate_amount(amount, person_days, unit_cost)

        assert validated == 450000.0

    def test_validate_amount_exceeds_tolerance_raises_error(self):
        """Test that amount exceeding 10% tolerance raises ValueError"""
        amount = 560000.0  # 12% above
        person_days = 10.0
        unit_cost = 50000.0

        with pytest.raises(ValueError):
            self.service.validate_amount(amount, person_days, unit_cost)

    def test_validate_amount_below_tolerance_raises_error(self):
        """Test that amount below 10% tolerance raises ValueError"""
        amount = 440000.0  # 12% below
        person_days = 10.0
        unit_cost = 50000.0

        with pytest.raises(ValueError):
            self.service.validate_amount(amount, person_days, unit_cost)

    # Test: JSON Structure Validation

    def test_validate_json_structure_with_all_required_keys(self):
        """Test JSON validation when all required keys are present"""
        data = {
            "name": "Requirements",
            "description": "Requirements document",
            "person_days": 10.0
        }
        required_keys = ["name", "description", "person_days"]

        validated = self.service.validate_json_structure(data, required_keys)

        assert validated == data

    def test_validate_json_structure_with_missing_key_raises_error(self):
        """Test JSON validation when required key is missing"""
        data = {
            "name": "Requirements",
            "description": "Requirements document"
        }
        required_keys = ["name", "description", "person_days"]

        with pytest.raises(ValueError):
            self.service.validate_json_structure(data, required_keys)

    def test_validate_json_structure_with_multiple_missing_keys_raises_error(self):
        """Test JSON validation when multiple required keys are missing"""
        data = {
            "name": "Requirements"
        }
        required_keys = ["name", "description", "person_days", "amount"]

        with pytest.raises(ValueError):
            self.service.validate_json_structure(data, required_keys)

    def test_validate_json_structure_with_extra_keys_passes(self):
        """Test JSON validation when extra keys are present (should pass)"""
        data = {
            "name": "Requirements",
            "description": "Requirements document",
            "person_days": 10.0,
            "extra_key": "extra value"
        }
        required_keys = ["name", "description", "person_days"]

        validated = self.service.validate_json_structure(data, required_keys)

        assert validated == data

    def test_validate_json_structure_with_empty_required_keys(self):
        """Test JSON validation when no keys are required"""
        data = {"any": "data"}
        required_keys = []

        validated = self.service.validate_json_structure(data, required_keys)

        assert validated == data

    # Test: Integration Scenarios

    def test_full_validation_pipeline_valid_input(self):
        """Test full validation pipeline with valid input"""
        input_text = "Build a web application"
        validated_input = self.service.validate_input(input_text)

        deliverable_name = "Web Application Development"
        validated_name = self.service.validate_deliverable_name(deliverable_name)

        person_days = 15.0
        validated_days = self.service.validate_person_days(person_days)

        amount = 750000.0
        unit_cost = 50000.0
        validated_amount = self.service.validate_amount(amount, person_days, unit_cost)

        assert validated_input is not None
        assert validated_name == "Web Application Development"
        assert validated_days == 15.0
        assert validated_amount == 750000.0

    def test_validation_preserves_unicode_characters(self):
        """Test that validation preserves Unicode characters"""
        japanese_input = "日本語の入力テスト：特殊文字「」『』【】を含む"

        validated = self.service.validate_input(japanese_input)

        assert "日本語" in validated
        assert "特殊文字" in validated
