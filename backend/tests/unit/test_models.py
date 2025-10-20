"""Unit tests for database models"""
import pytest
import uuid
from datetime import datetime

from app.models.task import Task, TaskStatus
from app.models.deliverable import Deliverable
from app.models.estimate import Estimate
from app.models.qa_pair import QAPair
from app.models.message import Message


class TestTaskModel:
    """Test class for Task model"""

    def test_create_task(self, db):
        """Test task creation"""
        task = Task(
            id=str(uuid.uuid4()),
            status=TaskStatus.PENDING.value,
            system_requirements="Web system development"
        )
        db.add(task)
        db.commit()

        retrieved = db.query(Task).filter(Task.id == task.id).first()
        assert retrieved is not None
        assert retrieved.status == TaskStatus.PENDING.value
        assert retrieved.system_requirements == "Web system development"

    def test_update_task_status(self, db):
        """Test task status update"""
        task = Task(
            id=str(uuid.uuid4()),
            status=TaskStatus.PENDING.value
        )
        db.add(task)
        db.commit()

        task.status = TaskStatus.COMPLETED.value
        db.commit()

        retrieved = db.query(Task).filter(Task.id == task.id).first()
        assert retrieved.status == TaskStatus.COMPLETED.value

    def test_task_with_error_message(self, db):
        """Test task with error message"""
        task = Task(
            id=str(uuid.uuid4()),
            status=TaskStatus.FAILED.value,
            error_message="Processing failed"
        )
        db.add(task)
        db.commit()

        retrieved = db.query(Task).filter(Task.id == task.id).first()
        assert retrieved.status == TaskStatus.FAILED.value
        assert retrieved.error_message == "Processing failed"


class TestDeliverableModel:
    """Test class for Deliverable model"""

    def test_create_deliverable(self, db):
        """Test deliverable creation"""
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.PENDING.value)
        db.add(task)
        db.commit()

        deliverable = Deliverable(
            id=str(uuid.uuid4()),
            task_id=task_id,
            name="Requirements Document",
            description="Define system requirements"
        )
        db.add(deliverable)
        db.commit()

        retrieved = db.query(Deliverable).filter(Deliverable.id == deliverable.id).first()
        assert retrieved is not None
        assert retrieved.name == "Requirements Document"
        assert retrieved.task_id == task_id

    def test_deliverable_cascade_delete(self, db):
        """Test cascade delete: deleting task should delete deliverables"""
        task_id = str(uuid.uuid4())
        deliverable_id = str(uuid.uuid4())

        task = Task(id=task_id, status=TaskStatus.PENDING.value)
        db.add(task)
        db.commit()

        deliverable = Deliverable(
            id=deliverable_id,
            task_id=task_id,
            name="Requirements Document"
        )
        db.add(deliverable)
        db.commit()

        # Delete task
        db.delete(task)
        db.commit()

        # Deliverable should also be deleted - use ID to query fresh from DB
        retrieved = db.query(Deliverable).filter(Deliverable.id == deliverable_id).first()
        assert retrieved is None


class TestEstimateModel:
    """Test class for Estimate model"""

    def test_create_estimate(self, db):
        """Test estimate creation"""
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.PENDING.value)
        db.add(task)
        db.commit()

        estimate = Estimate(
            id=str(uuid.uuid4()),
            task_id=task_id,
            deliverable_name="Requirements Document",
            deliverable_description="Requirements definition",
            person_days=5.0,
            amount=500000.0,
            reasoning_breakdown="Requirements: 2 days\nDesign: 3 days",
            reasoning_notes="Based on past projects"
        )
        db.add(estimate)
        db.commit()

        retrieved = db.query(Estimate).filter(Estimate.id == estimate.id).first()
        assert retrieved is not None
        assert retrieved.deliverable_name == "Requirements Document"
        assert retrieved.person_days == 5.0
        assert retrieved.amount == 500000.0

    def test_estimate_with_optional_fields(self, db):
        """Test estimate with optional fields"""
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.PENDING.value)
        db.add(task)
        db.commit()

        estimate = Estimate(
            id=str(uuid.uuid4()),
            task_id=task_id,
            deliverable_name="Basic Design Document",
            person_days=10.0,
            amount=1000000.0
        )
        db.add(estimate)
        db.commit()

        retrieved = db.query(Estimate).filter(Estimate.id == estimate.id).first()
        assert retrieved is not None
        assert retrieved.deliverable_description is None
        assert retrieved.reasoning is None

    def test_estimate_cascade_delete(self, db):
        """Test cascade delete: deleting task should delete estimates"""
        task_id = str(uuid.uuid4())
        estimate_id = str(uuid.uuid4())

        task = Task(id=task_id, status=TaskStatus.PENDING.value)
        db.add(task)
        db.commit()

        estimate = Estimate(
            id=estimate_id,
            task_id=task_id,
            deliverable_name="Requirements Document",
            person_days=5.0,
            amount=500000.0
        )
        db.add(estimate)
        db.commit()

        # Delete task
        db.delete(task)
        db.commit()

        # Estimate should also be deleted - use ID to query fresh from DB
        retrieved = db.query(Estimate).filter(Estimate.id == estimate_id).first()
        assert retrieved is None


class TestQAPairModel:
    """Test class for QAPair model"""

    def test_create_qa_pair(self, db):
        """Test Q&A pair creation"""
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.PENDING.value)
        db.add(task)
        db.commit()

        qa_pair = QAPair(
            id=str(uuid.uuid4()),
            task_id=task_id,
            question="How many users?",
            answer="About 100 users",
            order=1
        )
        db.add(qa_pair)
        db.commit()

        retrieved = db.query(QAPair).filter(QAPair.id == qa_pair.id).first()
        assert retrieved is not None
        assert retrieved.question == "How many users?"
        assert retrieved.answer == "About 100 users"
        assert retrieved.order == 1

    def test_qa_pair_order(self, db):
        """Test Q&A pair ordering"""
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.PENDING.value)
        db.add(task)
        db.commit()

        qa1 = QAPair(id=str(uuid.uuid4()), task_id=task_id, question="Question 1", order=1)
        qa2 = QAPair(id=str(uuid.uuid4()), task_id=task_id, question="Question 2", order=2)
        qa3 = QAPair(id=str(uuid.uuid4()), task_id=task_id, question="Question 3", order=3)
        db.add_all([qa1, qa2, qa3])
        db.commit()

        retrieved = db.query(QAPair).filter(QAPair.task_id == task_id).order_by(QAPair.order).all()
        assert len(retrieved) == 3
        assert retrieved[0].question == "Question 1"
        assert retrieved[1].question == "Question 2"
        assert retrieved[2].question == "Question 3"

    def test_qa_pair_without_answer(self, db):
        """Test Q&A pair without answer"""
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.PENDING.value)
        db.add(task)
        db.commit()

        qa_pair = QAPair(
            id=str(uuid.uuid4()),
            task_id=task_id,
            question="Unanswered question",
            order=1
        )
        db.add(qa_pair)
        db.commit()

        retrieved = db.query(QAPair).filter(QAPair.id == qa_pair.id).first()
        assert retrieved is not None
        assert retrieved.answer is None

    def test_qa_pair_cascade_delete(self, db):
        """Test cascade delete: deleting task should delete Q&A pairs"""
        task_id = str(uuid.uuid4())
        qa_pair_id = str(uuid.uuid4())

        task = Task(id=task_id, status=TaskStatus.PENDING.value)
        db.add(task)
        db.commit()

        qa_pair = QAPair(
            id=qa_pair_id,
            task_id=task_id,
            question="Question",
            order=1
        )
        db.add(qa_pair)
        db.commit()

        # Delete task
        db.delete(task)
        db.commit()

        # Q&A pair should also be deleted - use ID to query fresh from DB
        retrieved = db.query(QAPair).filter(QAPair.id == qa_pair_id).first()
        assert retrieved is None


class TestMessageModel:
    """Test class for Message model"""

    def test_create_message(self, db):
        """Test message creation"""
        task_id = str(uuid.uuid4())
        message = Message(
            id=str(uuid.uuid4()),
            task_id=task_id,
            role="user",
            content="Please reduce the budget"
        )
        db.add(message)
        db.commit()

        retrieved = db.query(Message).filter(Message.id == message.id).first()
        assert retrieved is not None
        assert retrieved.role == "user"
        assert retrieved.content == "Please reduce the budget"

    def test_message_roles(self, db):
        """Test message roles (user, assistant, agent)"""
        task_id = str(uuid.uuid4())

        user_msg = Message(id=str(uuid.uuid4()), task_id=task_id, role="user", content="User message")
        assistant_msg = Message(id=str(uuid.uuid4()), task_id=task_id, role="assistant", content="Assistant message")
        agent_msg = Message(id=str(uuid.uuid4()), task_id=task_id, role="agent", content="Agent message")

        db.add_all([user_msg, assistant_msg, agent_msg])
        db.commit()

        retrieved = db.query(Message).filter(Message.task_id == task_id).all()
        assert len(retrieved) == 3
        roles = [msg.role for msg in retrieved]
        assert "user" in roles
        assert "assistant" in roles
        assert "agent" in roles

    def test_message_created_at(self, db):
        """Test message created_at timestamp"""
        message = Message(
            id=str(uuid.uuid4()),
            task_id=str(uuid.uuid4()),
            role="user",
            content="Test"
        )
        db.add(message)
        db.commit()

        retrieved = db.query(Message).filter(Message.id == message.id).first()
        assert retrieved.created_at is not None
        assert isinstance(retrieved.created_at, datetime)
