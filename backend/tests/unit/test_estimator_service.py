"""Unit tests for EstimatorService"""
import pytest
from unittest.mock import Mock, patch
from app.services.estimator_service import EstimatorService


class TestEstimatorService:
    """Test class for EstimatorService"""

    def test_generate_estimates_success(self, mock_openai, sample_deliverables, sample_qa_pairs):
        """Test successful estimate generation"""
        service = EstimatorService()
        result = service.generate_estimates(
            sample_deliverables,
            "Web-based estimation system",
            sample_qa_pairs
        )

        assert isinstance(result, list)
        assert len(result) == len(sample_deliverables)

        for estimate in result:
            assert "name" in estimate
            assert "person_days" in estimate
            assert "amount" in estimate
            assert estimate["person_days"] > 0
            assert estimate["amount"] > 0

    def test_generate_estimates_with_single_deliverable(self, mock_openai, sample_qa_pairs):
        """Test estimate generation with single deliverable"""
        service = EstimatorService()
        deliverables = [{"name": "Requirements", "description": "Requirements document"}]

        result = service.generate_estimates(
            deliverables,
            "Web system",
            sample_qa_pairs
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "Requirements"

    def test_generate_estimates_api_error_fallback(self, monkeypatch, sample_deliverables, sample_qa_pairs):
        """Test fallback to keyword-based estimate when API fails"""
        def mock_create_error(**kwargs):
            raise Exception("API Error")

        service = EstimatorService()
        monkeypatch.setattr(service.client.chat.completions, "create", mock_create_error)

        result = service.generate_estimates(
            sample_deliverables,
            "Test system",
            sample_qa_pairs
        )

        # Should return fallback estimates (keyword-based: 5.0-30.0 person-days)
        assert isinstance(result, list)
        assert len(result) == len(sample_deliverables)

        # Verify keyword-based fallback works correctly
        # sample_deliverables contains: 要件定義書, 基本設計書, 詳細設計書
        for estimate in result:
            # All fallback estimates should be reasonable (between 5.0 and 30.0)
            assert 5.0 <= estimate["person_days"] <= 30.0
            # Verify amount is calculated correctly
            assert estimate["amount"] == estimate["person_days"] * service.daily_unit_cost

        # Check specific keyword-based estimates
        requirements_estimate = next(e for e in result if "要件" in e["name"])
        assert requirements_estimate["person_days"] == 10.0  # Requirements keyword

        design_estimates = [e for e in result if "設計" in e["name"]]
        for design_est in design_estimates:
            assert design_est["person_days"] == 15.0  # Design keyword

    def test_amount_calculation(self, mock_openai, sample_qa_pairs):
        """Test that amount is calculated correctly from person_days"""
        service = EstimatorService()
        deliverables = [{"name": "Test", "description": "Test doc"}]

        result = service.generate_estimates(
            deliverables,
            "Test system",
            sample_qa_pairs
        )

        assert len(result) == 1
        estimate = result[0]
        expected_amount = estimate["person_days"] * service.daily_unit_cost
        # Allow for small floating point differences
        assert abs(estimate["amount"] - expected_amount) < 0.01
