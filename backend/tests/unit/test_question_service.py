"""Unit tests for QuestionService"""
import pytest
from unittest.mock import Mock, patch
from app.services.question_service import QuestionService


class TestQuestionService:
    """Test class for QuestionService"""

    def test_generate_questions_success(self, mock_openai, sample_deliverables):
        """Test successful question generation"""
        service = QuestionService()
        result = service.generate_questions(
            sample_deliverables,
            "Web-based estimation system"
        )

        assert isinstance(result, list)
        assert len(result) == 3
        for question in result:
            assert isinstance(question, str)
            assert len(question) > 0

    def test_generate_questions_with_empty_deliverables(self, mock_openai):
        """Test question generation with empty deliverables"""
        service = QuestionService()
        result = service.generate_questions([], "Web system")

        assert isinstance(result, list)
        assert len(result) == 3

    def test_generate_questions_api_error_fallback(self, monkeypatch):
        """Test fallback to default questions when API fails"""
        def mock_create_error(**kwargs):
            raise Exception("API Error")

        service = QuestionService()
        monkeypatch.setattr(service.client.chat.completions, "create", mock_create_error)

        result = service.generate_questions(
            [{"name": "Test", "description": "Test doc"}],
            "Test system"
        )

        # Should return default questions
        assert isinstance(result, list)
        assert len(result) == 3

    def test_get_default_questions(self, mock_language_ja):
        """Test getting default questions"""
        service = QuestionService()
        result = service._get_default_questions()

        assert isinstance(result, list)
        assert len(result) == 3
        for question in result:
            assert isinstance(question, str)
            assert len(question) > 0
