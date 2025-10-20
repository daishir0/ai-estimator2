"""End-to-end tests for complete user workflows"""
import pytest


class TestEndToEnd:
    """Test class for end-to-end user workflows"""

    def test_complete_workflow_excel_upload(self, client, sample_excel_file, mock_openai):
        """Test complete workflow: Excel upload -> Questions -> Answers -> Estimate -> Export"""
        # Step 1: Upload Excel file and create task
        with open(sample_excel_file, "rb") as f:
            files = {"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            data = {"system_requirements": "Web-based estimation system"}
            response = client.post("/api/v1/tasks", files=files, data=data)

        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data["id"]

        # Step 1.5: Get questions
        response = client.get(f"/api/v1/tasks/{task_id}/questions")
        assert response.status_code == 200
        questions = response.json()
        assert isinstance(questions, list)
        assert len(questions) == 3

        # Step 2: Get questions (duplicate removed)

        # Step 3: Submit answers
        # Get questions and prepare QA pairs
        response = client.get(f"/api/v1/tasks/{task_id}/questions")
        questions = response.json()
        qa_pairs = [
            {"question": questions[i] if i < len(questions) else f"Question {i+1}",
             "answer": answer}
            for i, answer in enumerate(["100 users", "3 months development", "Python with FastAPI"])
        ]
        response = client.post(f"/api/v1/tasks/{task_id}/answers", json=qa_pairs)
        assert response.status_code == 200

        # Step 4: Get estimate results
        response = client.get(f"/api/v1/tasks/{task_id}/result")
        assert response.status_code == 200
        result_data = response.json()
        assert "estimates" in result_data
        assert "subtotal" in result_data
        assert "tax" in result_data
        assert "total" in result_data
        assert len(result_data["estimates"]) > 0

        # Step 5: Export to Excel
        response = client.get(f"/api/v1/tasks/{task_id}/download")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def test_complete_workflow_web_form(self, client, mock_openai):
        """Test complete workflow: Web form -> Questions -> Answers -> Adjustment -> Export"""
        import json

        # Step 1: Create task with web form
        deliverables = [
            {"name": "Requirements Document", "description": "System requirements"},
            {"name": "Design Document", "description": "System design"},
            {"name": "Implementation", "description": "Code development"}
        ]

        request_data = {
            "system_requirements": "E-commerce platform development",
            "deliverables_json": json.dumps(deliverables)
        }
        response = client.post("/api/v1/tasks", data=request_data)
        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data["id"]

        # Step 2: Get questions and submit answers
        response = client.get(f"/api/v1/tasks/{task_id}/questions")
        questions = response.json()
        qa_pairs = [
            {"question": questions[i] if i < len(questions) else f"Question {i+1}",
             "answer": answer}
            for i, answer in enumerate(["1000 users", "6 months", "Python, React, PostgreSQL"])
        ]
        response = client.post(f"/api/v1/tasks/{task_id}/answers", json=qa_pairs)
        assert response.status_code == 200

        # Step 3: Get estimate results
        response = client.get(f"/api/v1/tasks/{task_id}/result")
        assert response.status_code == 200
        result_data = response.json()
        original_total = result_data["total"]

        # Step 4: Adjust estimate (fit to budget)
        adjustment_data = {
            "intent": "fit_budget",
            "params": {"cap": original_total * 0.8}  # Reduce by 20%
        }
        response = client.post(f"/api/v1/tasks/{task_id}/chat", json=adjustment_data)
        assert response.status_code == 200

        # Step 5: Get adjusted results
        response = client.get(f"/api/v1/tasks/{task_id}/result")
        assert response.status_code == 200
        adjusted_data = response.json()
        adjusted_total = adjusted_data["total"]
        assert adjusted_total < original_total

        # Step 6: Export to Excel
        response = client.get(f"/api/v1/tasks/{task_id}/download")
        assert response.status_code == 200

    def test_complete_workflow_csv_upload(self, client, sample_csv_file, mock_openai):
        """Test complete workflow: CSV upload -> Questions -> Answers -> Estimate"""
        # Step 1: Upload CSV file
        with open(sample_csv_file, "rb") as f:
            files = {"file": ("test.csv", f, "text/csv")}
            data = {"system_requirements": "Mobile app development"}
            response = client.post("/api/v1/tasks", files=files, data=data)

        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data["id"]

        # Step 2: Get questions and submit answers
        response = client.get(f"/api/v1/tasks/{task_id}/questions")
        questions = response.json()
        qa_pairs = [
            {"question": questions[i] if i < len(questions) else f"Question {i+1}",
             "answer": answer}
            for i, answer in enumerate(["500 users", "4 months", "React Native"])
        ]
        response = client.post(f"/api/v1/tasks/{task_id}/answers", json=qa_pairs)
        assert response.status_code == 200

        # Step 3: Get final results
        response = client.get(f"/api/v1/tasks/{task_id}/result")
        assert response.status_code == 200
        result_data = response.json()

        # Verify complete data structure
        assert "estimates" in result_data
        assert "subtotal" in result_data
        assert "tax" in result_data
        assert "total" in result_data
        assert result_data["subtotal"] > 0
        assert result_data["total"] > result_data["subtotal"]

    def test_workflow_with_multiple_adjustments(self, client, mock_openai):
        """Test workflow with multiple estimate adjustments"""
        import json

        # Create task
        deliverables = [
            {"name": "Doc1", "description": "Description 1"},
            {"name": "Doc2", "description": "Description 2"}
        ]

        request_data = {
            "system_requirements": "Test system",
            "deliverables_json": json.dumps(deliverables)
        }
        response = client.post("/api/v1/tasks", data=request_data)
        task_id = response.json()["id"]

        # Submit answers
        response = client.get(f"/api/v1/tasks/{task_id}/questions")
        questions = response.json()
        qa_pairs = [
            {"question": questions[i] if i < len(questions) else f"Question {i+1}",
             "answer": answer}
            for i, answer in enumerate(["100 users", "3 months", "Python"])
        ]
        client.post(f"/api/v1/tasks/{task_id}/answers", json=qa_pairs)

        # Get original estimate
        response = client.get(f"/api/v1/tasks/{task_id}/result")
        original_total = response.json()["total"]

        # Adjustment 1: Add risk buffer
        adjustment_data = {"intent": "risk_buffer", "params": {"percent": 10.0}}
        client.post(f"/api/v1/tasks/{task_id}/chat", json=adjustment_data)

        response = client.get(f"/api/v1/tasks/{task_id}/result")
        buffered_total = response.json()["total"]
        assert buffered_total > original_total

        # Adjustment 2: Change unit cost
        adjustment_data = {"intent": "unit_cost_change", "params": {"new_unit_cost": 50000.0}}
        client.post(f"/api/v1/tasks/{task_id}/chat", json=adjustment_data)

        response = client.get(f"/api/v1/tasks/{task_id}/result")
        final_data = response.json()

        # Verify final state has all adjustments recorded
        assert "estimates" in final_data
        assert len(final_data["estimates"]) == 2

    def test_error_handling_invalid_task_id(self, client):
        """Test error handling for invalid task ID"""
        invalid_task_id = "nonexistent-task-id"

        # Try to get non-existent task
        response = client.get(f"/api/v1/tasks/{invalid_task_id}")
        assert response.status_code == 404

        # Try to get questions for non-existent task
        response = client.get(f"/api/v1/tasks/{invalid_task_id}/questions")
        assert response.status_code == 404

        # Try to get results for non-existent task
        response = client.get(f"/api/v1/tasks/{invalid_task_id}/result")
        assert response.status_code == 404
