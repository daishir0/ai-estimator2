"""Integration tests for API endpoints"""
import pytest
import json
from io import BytesIO


class TestAPIEndpoints:
    """Test class for API endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_translations_endpoint(self, client, mock_language_ja):
        """Test translations API endpoint"""
        response = client.get("/api/v1/translations")
        assert response.status_code == 200
        data = response.json()
        assert "language" in data
        assert "translations" in data
        assert data["language"] == "ja"

    def test_sample_input_download(self, client, mock_language_ja):
        """Test sample input Excel download"""
        response = client.get("/api/v1/sample-input")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def test_sample_input_csv_download(self, client, mock_language_ja):
        """Test sample input CSV download"""
        response = client.get("/api/v1/sample-input-csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_create_task_with_web_form(self, client, mock_openai):
        """Test task creation with web form data"""
        import json

        deliverables = [
            {"name": "Requirements Document", "description": "Define requirements"},
            {"name": "Design Document", "description": "System design"}
        ]

        request_data = {
            "system_requirements": "Web-based estimation system",
            "deliverables_json": json.dumps(deliverables)
        }

        # Create task
        response = client.post("/api/v1/tasks", data=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        task_id = data["id"]

        # Get questions for the created task
        response = client.get(f"/api/v1/tasks/{task_id}/questions")
        assert response.status_code == 200
        questions = response.json()
        assert isinstance(questions, list)
        assert len(questions) == 3

    def test_create_task_with_excel_upload(self, client, sample_excel_file, mock_openai):
        """Test task creation with Excel file upload"""
        with open(sample_excel_file, "rb") as f:
            files = {"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            data = {"system_requirements": "Test system"}

            response = client.post("/api/v1/tasks", files=files, data=data)

        assert response.status_code == 200
        response_data = response.json()
        assert "id" in response_data
        task_id = response_data["id"]

        # Get questions
        response = client.get(f"/api/v1/tasks/{task_id}/questions")
        assert response.status_code == 200
        questions = response.json()
        assert isinstance(questions, list)

    def test_get_task_status(self, client, mock_openai):
        """Test getting task status"""
        import json

        # Create task first
        deliverables = [{"name": "Test", "description": "Test doc"}]
        request_data = {
            "system_requirements": "Test system",
            "deliverables_json": json.dumps(deliverables)
        }
        create_response = client.post("/api/v1/tasks", data=request_data)
        task_id = create_response.json()["id"]

        # Get task status
        response = client.get(f"/api/v1/tasks/{task_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["pending", "processing", "completed", "failed"]

    def test_get_questions(self, client, mock_openai):
        """Test getting questions for a task"""
        import json

        # Create task
        deliverables = [{"name": "Test", "description": "Test doc"}]
        request_data = {
            "system_requirements": "Test system",
            "deliverables_json": json.dumps(deliverables)
        }
        create_response = client.post("/api/v1/tasks", data=request_data)
        task_id = create_response.json()["id"]

        # Get questions
        response = client.get(f"/api/v1/tasks/{task_id}/questions")
        assert response.status_code == 200
        questions = response.json()
        assert isinstance(questions, list)
        assert len(questions) > 0

    def test_submit_answers_and_generate_estimate(self, client, mock_openai):
        """Test submitting answers and generating estimates"""
        import json

        # Create task
        deliverables = [{"name": "Test", "description": "Test doc"}]
        request_data = {
            "system_requirements": "Test system",
            "deliverables_json": json.dumps(deliverables)
        }
        create_response = client.post("/api/v1/tasks", data=request_data)
        task_id = create_response.json()["id"]

        # Get questions first
        response = client.get(f"/api/v1/tasks/{task_id}/questions")
        questions = response.json()

        # Submit answers with QAPairRequest format
        qa_pairs = [
            {"question": questions[i] if i < len(questions) else f"Question {i+1}",
             "answer": answer}
            for i, answer in enumerate(["100 users", "3 months", "Python, FastAPI"])
        ]
        response = client.post(f"/api/v1/tasks/{task_id}/answers", json=qa_pairs)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_get_estimate_result(self, client, mock_openai):
        """Test getting estimate results"""
        import json

        # Create task and submit answers
        deliverables = [{"name": "Test", "description": "Test doc"}]
        request_data = {
            "system_requirements": "Test system",
            "deliverables_json": json.dumps(deliverables)
        }
        create_response = client.post("/api/v1/tasks", data=request_data)
        task_id = create_response.json()["id"]

        # Get questions and submit answers
        response = client.get(f"/api/v1/tasks/{task_id}/questions")
        questions = response.json()
        qa_pairs = [
            {"question": questions[i] if i < len(questions) else f"Question {i+1}",
             "answer": answer}
            for i, answer in enumerate(["100 users", "3 months", "Python"])
        ]
        client.post(f"/api/v1/tasks/{task_id}/answers", json=qa_pairs)

        # Get result
        response = client.get(f"/api/v1/tasks/{task_id}/result")
        assert response.status_code == 200
        data = response.json()
        assert "estimates" in data

    def test_export_to_excel(self, client, mock_openai, tmp_path):
        """Test Excel export endpoint"""
        import json

        # Create task and complete estimation
        deliverables = [{"name": "Test", "description": "Test doc"}]
        request_data = {
            "system_requirements": "Test system",
            "deliverables_json": json.dumps(deliverables)
        }
        create_response = client.post("/api/v1/tasks", data=request_data)
        task_id = create_response.json()["id"]

        # Get questions and submit answers
        response = client.get(f"/api/v1/tasks/{task_id}/questions")
        questions = response.json()
        qa_pairs = [
            {"question": questions[i] if i < len(questions) else f"Question {i+1}",
             "answer": answer}
            for i, answer in enumerate(["100 users", "3 months", "Python"])
        ]
        client.post(f"/api/v1/tasks/{task_id}/answers", json=qa_pairs)

        # Export
        response = client.get(f"/api/v1/tasks/{task_id}/download")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
