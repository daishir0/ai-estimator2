"""Unit tests for ChatService"""
import pytest
import uuid
from app.services.chat_service import ChatService
from app.models.estimate import Estimate
from app.models.task import Task, TaskStatus


class TestChatService:
    """Test class for ChatService"""

    def test_fit_budget_reduces_estimates(self, db):
        """Test budget fit reduces estimates proportionally"""
        # Create task and estimates
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.COMPLETED.value)
        db.add(task)
        db.commit()  # Commit task first before adding estimates

        estimates = [
            Estimate(id=str(uuid.uuid4()), task_id=task_id, deliverable_name="Item 1",
                    person_days=10.0, amount=1000000.0),
            Estimate(id=str(uuid.uuid4()), task_id=task_id, deliverable_name="Item 2",
                    person_days=5.0, amount=500000.0)
        ]
        db.add_all(estimates)
        db.commit()

        service = ChatService(db)
        est_dicts = service._as_dicts(estimates)

        # Fit to 1000000 budget (from ~1650000 with tax)
        result, note = service._fit_budget(est_dicts, 1000000.0)

        assert isinstance(result, list)
        assert len(result) == 2
        assert "上限" in note
        # Total should be reduced
        totals = service._calc_totals(result)
        assert totals["total"] <= 1000000.0

    def test_unit_cost_change(self, db):
        """Test unit cost change recalculates amounts"""
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.COMPLETED.value)
        db.add(task)
        db.commit()  # Commit task first before adding estimates

        estimates = [
            Estimate(id=str(uuid.uuid4()), task_id=task_id, deliverable_name="Item 1",
                    person_days=10.0, amount=1000000.0)
        ]
        db.add_all(estimates)
        db.commit()

        service = ChatService(db)
        est_dicts = service._as_dicts(estimates)

        # Change unit cost to 50000
        result, note = service._unit_cost_change(est_dicts, 50000.0)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["amount"] == 10.0 * 50000.0
        assert "単価" in note

    def test_risk_buffer(self, db):
        """Test risk buffer adds percentage to amounts"""
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.COMPLETED.value)
        db.add(task)
        db.commit()  # Commit task first before adding estimates

        estimates = [
            Estimate(id=str(uuid.uuid4()), task_id=task_id, deliverable_name="Item 1",
                    person_days=10.0, amount=1000000.0)
        ]
        db.add_all(estimates)
        db.commit()

        service = ChatService(db)
        est_dicts = service._as_dicts(estimates)

        # Add 10% buffer
        result, note = service._risk_buffer(est_dicts, 10.0)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["amount"] == 1000000.0 * 1.1
        assert "リスク" in note

    def test_scope_reduce(self, db):
        """Test scope reduction removes matching items"""
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.COMPLETED.value)
        db.add(task)
        db.commit()  # Commit task first before adding estimates

        estimates = [
            Estimate(id=str(uuid.uuid4()), task_id=task_id, deliverable_name="要件定義書",
                    person_days=5.0, amount=500000.0),
            Estimate(id=str(uuid.uuid4()), task_id=task_id, deliverable_name="基本設計書",
                    person_days=10.0, amount=1000000.0)
        ]
        db.add_all(estimates)
        db.commit()

        service = ChatService(db)
        est_dicts = service._as_dicts(estimates)

        # Remove items with "要件" keyword
        result, note = service._scope_reduce(est_dicts, ["要件"])

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["deliverable_name"] == "基本設計書"

    def test_save_messages(self, db):
        """Test saving user and assistant messages"""
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.PENDING.value)
        db.add(task)
        db.commit()

        service = ChatService(db)

        # Save user message
        service.save_user_message(task_id, "Please reduce budget")
        # Save assistant message
        service.save_assistant_message(task_id, "Budget reduced by 20%")

        # Verify messages were saved
        from app.models.message import Message
        messages = db.query(Message).filter(Message.task_id == task_id).all()

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Please reduce budget"
        assert messages[1].role == "assistant"
        assert messages[1].content == "Budget reduced by 20%"
