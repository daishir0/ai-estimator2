"""Unit tests for InputService"""
import pytest
import pandas as pd
from pathlib import Path

from app.services.input_service import InputService


class TestInputService:
    """Test class for InputService"""

    def test_load_excel_data_success(self, sample_excel_file):
        """Test successful Excel file loading"""
        result = InputService.load_excel_data(sample_excel_file)

        assert len(result) == 3
        assert result[0]["name"] == "要件定義書"
        assert result[0]["description"] == "システム全体の要件を定義する文書"
        assert result[1]["name"] == "基本設計書"
        assert result[2]["name"] == "詳細設計書"

    def test_load_csv_data_success(self, sample_csv_file):
        """Test successful CSV file loading"""
        result = InputService.load_csv_data(sample_csv_file)

        assert len(result) == 2
        assert result[0]["name"] == "要件定義書"
        assert result[0]["description"] == "システム全体の要件を定義する文書"
        assert result[1]["name"] == "基本設計書"

    def test_load_excel_file_not_found(self):
        """Test FileNotFoundError when Excel file doesn't exist"""
        with pytest.raises(FileNotFoundError, match="が見つかりません"):
            InputService.load_excel_data("/path/to/nonexistent.xlsx")

    def test_load_csv_file_not_found(self):
        """Test FileNotFoundError when CSV file doesn't exist"""
        with pytest.raises(FileNotFoundError, match="が見つかりません"):
            InputService.load_csv_data("/path/to/nonexistent.csv")

    def test_load_excel_insufficient_columns(self, tmp_path):
        """Test ValueError when Excel has insufficient columns"""
        file_path = tmp_path / "insufficient.xlsx"
        df = pd.DataFrame({"成果物名称": ["要件定義書"]})
        df.to_excel(file_path, index=False, engine='openpyxl')

        with pytest.raises(ValueError, match="少なくとも2列"):
            InputService.load_excel_data(str(file_path))

    def test_load_csv_insufficient_columns(self, tmp_path):
        """Test ValueError when CSV has insufficient columns"""
        file_path = tmp_path / "insufficient.csv"
        df = pd.DataFrame({"成果物名称": ["要件定義書"]})
        df.to_csv(file_path, index=False)

        with pytest.raises(ValueError, match="少なくとも2列"):
            InputService.load_csv_data(str(file_path))

    def test_load_excel_with_nan_values(self, tmp_path):
        """Test Excel loading with NaN values (should convert to empty string)"""
        file_path = tmp_path / "with_nan.xlsx"
        df = pd.DataFrame({
            "成果物名称": ["要件定義書", "基本設計書"],
            "説明": ["説明あり", None]
        })
        df.to_excel(file_path, index=False, engine='openpyxl')

        result = InputService.load_excel_data(str(file_path))

        assert len(result) == 2
        assert result[0]["description"] == "説明あり"
        assert result[1]["description"] == ""  # NaN converted to empty string

    def test_load_csv_with_nan_values(self, tmp_path):
        """Test CSV loading with NaN values (should convert to empty string)"""
        file_path = tmp_path / "with_nan.csv"
        df = pd.DataFrame({
            "成果物名称": ["要件定義書", "基本設計書"],
            "説明": ["説明あり", None]
        })
        df.to_csv(file_path, index=False)

        result = InputService.load_csv_data(str(file_path))

        assert len(result) == 2
        assert result[0]["description"] == "説明あり"
        assert result[1]["description"] == ""  # NaN converted to empty string

    def test_load_excel_skip_empty_name(self, tmp_path):
        """Test Excel loading skips rows with empty deliverable names"""
        file_path = tmp_path / "with_empty.xlsx"
        df = pd.DataFrame({
            "成果物名称": ["要件定義書", "", "基本設計書"],
            "説明": ["説明1", "説明2", "説明3"]
        })
        df.to_excel(file_path, index=False, engine='openpyxl')

        result = InputService.load_excel_data(str(file_path))

        assert len(result) == 2
        assert result[0]["name"] == "要件定義書"
        assert result[1]["name"] == "基本設計書"

    def test_load_csv_skip_empty_name(self, tmp_path):
        """Test CSV loading skips rows with empty deliverable names"""
        file_path = tmp_path / "with_empty.csv"
        df = pd.DataFrame({
            "成果物名称": ["要件定義書", "", "基本設計書"],
            "説明": ["説明1", "説明2", "説明3"]
        })
        df.to_csv(file_path, index=False)

        result = InputService.load_csv_data(str(file_path))

        assert len(result) == 2
        assert result[0]["name"] == "要件定義書"
        assert result[1]["name"] == "基本設計書"

    def test_parse_deliverables_json_success(self, sample_deliverables):
        """Test successful JSON parsing"""
        result = InputService.parse_deliverables_json(sample_deliverables)

        assert len(result) == 3
        assert result[0]["name"] == "要件定義書"
        assert result[0]["description"] == "システム全体の要件を定義する文書"

    def test_parse_deliverables_json_with_whitespace(self):
        """Test JSON parsing strips whitespace from names and descriptions"""
        data = [
            {"name": "  要件定義書  ", "description": "  説明  "},
            {"name": "基本設計書", "description": "説明"}
        ]
        result = InputService.parse_deliverables_json(data)

        assert len(result) == 2
        assert result[0]["name"] == "要件定義書"  # Whitespace stripped
        assert result[0]["description"] == "説明"

    def test_parse_deliverables_json_skip_empty_name(self):
        """Test JSON parsing skips entries with empty names"""
        data = [
            {"name": "要件定義書", "description": "説明1"},
            {"name": "", "description": "説明2"},
            {"name": "  ", "description": "説明3"},
            {"name": "基本設計書", "description": "説明4"}
        ]
        result = InputService.parse_deliverables_json(data)

        assert len(result) == 2
        assert result[0]["name"] == "要件定義書"
        assert result[1]["name"] == "基本設計書"

    def test_parse_deliverables_json_empty_list(self):
        """Test JSON parsing raises ValueError for empty list"""
        with pytest.raises(ValueError, match="成果物が1件も登録されていません"):
            InputService.parse_deliverables_json([])

    def test_parse_deliverables_json_all_empty_names(self):
        """Test JSON parsing raises ValueError when all names are empty"""
        data = [
            {"name": "", "description": "説明1"},
            {"name": "  ", "description": "説明2"}
        ]
        with pytest.raises(ValueError, match="成果物が1件も登録されていません"):
            InputService.parse_deliverables_json(data)

    def test_parse_deliverables_json_missing_keys(self):
        """Test JSON parsing handles missing keys gracefully"""
        data = [
            {"name": "要件定義書"},  # Missing description
            {"description": "説明のみ"},  # Missing name
            {"name": "基本設計書", "description": "説明あり"}
        ]
        result = InputService.parse_deliverables_json(data)

        assert len(result) == 2
        assert result[0]["name"] == "要件定義書"
        assert result[0]["description"] == ""
        assert result[1]["name"] == "基本設計書"
