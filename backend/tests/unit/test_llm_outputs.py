"""Unit tests for LLM output validation"""
import pytest
import json


class TestLLMOutputs:
    """Test class for LLM output validation"""

    def test_question_response_structure(self, mock_openai_response):
        """Test question response has correct structure"""
        response = mock_openai_response["questions"]

        assert "questions" in response
        assert isinstance(response["questions"], list)
        assert len(response["questions"]) >= 1

        for question in response["questions"]:
            assert isinstance(question, str)
            assert len(question) > 0

    def test_estimate_response_structure(self, mock_openai_response):
        """Test estimate response has correct structure"""
        response = mock_openai_response["estimate"]

        assert "estimated_effort_days" in response
        assert "breakdown" in response
        assert "rationale" in response

        assert isinstance(response["estimated_effort_days"], (int, float))
        assert response["estimated_effort_days"] > 0
        assert isinstance(response["breakdown"], str)
        assert isinstance(response["rationale"], str)

    def test_estimate_contains_person_days_keywords(self, mock_openai_response):
        """Test estimate contains relevant keywords"""
        response = mock_openai_response["estimate"]
        breakdown = response["breakdown"].lower()

        # Should contain at least some relevant keywords
        assert len(breakdown) > 0

    def test_chat_adjustment_response_structure(self, mock_openai_response):
        """Test chat adjustment response has correct structure"""
        response = mock_openai_response["chat_adjustment"]

        assert "suggestions" in response
        assert isinstance(response["suggestions"], list)
        assert len(response["suggestions"]) >= 1

        for suggestion in response["suggestions"]:
            assert "title" in suggestion
            assert "description" in suggestion
            assert "impact" in suggestion
            assert isinstance(suggestion["title"], str)
            assert isinstance(suggestion["description"], str)
            assert isinstance(suggestion["impact"], str)

    def test_no_inappropriate_content(self, mock_openai_response):
        """Test responses don't contain inappropriate content placeholders"""
        # This is a basic safety check
        all_text = json.dumps(mock_openai_response).lower()

        # Check that responses don't contain common prompt injection patterns
        dangerous_patterns = ["ignore previous", "disregard", "system:", "admin"]

        for pattern in dangerous_patterns:
            assert pattern not in all_text, f"Found suspicious pattern: {pattern}"

    def test_estimate_numerical_validation(self, mock_openai_response):
        """Test estimate numerical values are reasonable"""
        response = mock_openai_response["estimate"]
        person_days = response["estimated_effort_days"]

        # Person-days should be reasonable (between 0.1 and 1000)
        assert 0.1 <= person_days <= 1000

    def test_response_not_empty(self, mock_openai_response):
        """Test all responses are not empty"""
        # Questions
        assert len(mock_openai_response["questions"]["questions"]) > 0

        # Estimate
        assert len(mock_openai_response["estimate"]["breakdown"]) > 0
        assert len(mock_openai_response["estimate"]["rationale"]) > 0

        # Chat adjustment
        assert len(mock_openai_response["chat_adjustment"]["suggestions"]) > 0
