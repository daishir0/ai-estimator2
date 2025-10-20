"""Integration tests for database operations"""
import pytest
import uuid
from app.models.task import Task, TaskStatus
from app.models.deliverable import Deliverable
from app.models.estimate import Estimate
from app.models.qa_pair import QAPair
from app.models.message import Message


class TestDatabaseIntegration:
    """Test class for database integration"""

    def test_task_crud_operations(self, db):
        """Test CRUD operations for Task"""
        # Create
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.PENDING.value, system_requirements="Test")
        db.add(task)
        db.commit()

        # Read
        retrieved = db.query(Task).filter(Task.id == task_id).first()
        assert retrieved is not None
        assert retrieved.system_requirements == "Test"

        # Update
        retrieved.status = TaskStatus.COMPLETED.value
        db.commit()
        updated = db.query(Task).filter(Task.id == task_id).first()
        assert updated.status == TaskStatus.COMPLETED.value

        # Delete
        db.delete(updated)
        db.commit()
        deleted = db.query(Task).filter(Task.id == task_id).first()
        assert deleted is None

    def test_task_with_related_data(self, db):
        """Test task with all related data (deliverables, estimates, Q&A, messages)"""
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.PENDING.value)
        db.add(task)
        db.commit()  # Commit task first before adding related data

        # Add deliverable
        deliverable = Deliverable(
            id=str(uuid.uuid4()),
            task_id=task_id,
            name="Test Deliverable",
            description="Test Description"
        )
        db.add(deliverable)

        # Add estimate
        estimate = Estimate(
            id=str(uuid.uuid4()),
            task_id=task_id,
            deliverable_name="Test Deliverable",
            person_days=5.0,
            amount=500000.0
        )
        db.add(estimate)

        # Add Q&A pair
        qa_pair = QAPair(
            id=str(uuid.uuid4()),
            task_id=task_id,
            question="Test Question",
            answer="Test Answer",
            order=1
        )
        db.add(qa_pair)

        # Add message
        message = Message(
            id=str(uuid.uuid4()),
            task_id=task_id,
            role="user",
            content="Test Message"
        )
        db.add(message)

        db.commit()

        # Verify all related data
        assert db.query(Deliverable).filter(Deliverable.task_id == task_id).count() == 1
        assert db.query(Estimate).filter(Estimate.task_id == task_id).count() == 1
        assert db.query(QAPair).filter(QAPair.task_id == task_id).count() == 1
        assert db.query(Message).filter(Message.task_id == task_id).count() == 1

    def test_cascade_delete(self, db):
        """Test cascade delete removes all related data"""
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.PENDING.value)
        db.add(task)
        db.commit()  # Commit task first before adding related data

        deliverable = Deliverable(id=str(uuid.uuid4()), task_id=task_id, name="Test")
        estimate = Estimate(id=str(uuid.uuid4()), task_id=task_id, deliverable_name="Test", person_days=5.0, amount=500000.0)
        qa_pair = QAPair(id=str(uuid.uuid4()), task_id=task_id, question="Q", order=1)

        db.add_all([deliverable, estimate, qa_pair])
        db.commit()

        # Delete task
        db.delete(task)
        db.commit()

        # Verify all related data is deleted
        assert db.query(Deliverable).filter(Deliverable.task_id == task_id).count() == 0
        assert db.query(Estimate).filter(Estimate.task_id == task_id).count() == 0
        assert db.query(QAPair).filter(QAPair.task_id == task_id).count() == 0

    def test_transaction_rollback(self, db):
        """Test transaction rollback on error"""
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, status=TaskStatus.PENDING.value)
        db.add(task)
        db.commit()

        try:
            # Attempt to add estimate with invalid data (this should fail)
            # Create a scenario where commit would fail
            db.add(Task(id=task_id, status=TaskStatus.PENDING.value))  # Duplicate ID
            db.commit()
            assert False, "Should have raised an error"
        except Exception:
            db.rollback()
            # Verify original task still exists
            retrieved = db.query(Task).filter(Task.id == task_id).first()
            assert retrieved is not None

    def test_multiple_tasks_isolation(self, db):
        """Test data isolation between multiple tasks"""
        task_id_1 = str(uuid.uuid4())
        task_id_2 = str(uuid.uuid4())

        task1 = Task(id=task_id_1, status=TaskStatus.PENDING.value)
        task2 = Task(id=task_id_2, status=TaskStatus.PENDING.value)
        db.add_all([task1, task2])
        db.commit()  # Commit tasks first before adding related data

        estimate1 = Estimate(id=str(uuid.uuid4()), task_id=task_id_1, deliverable_name="Test1", person_days=5.0, amount=500000.0)
        estimate2 = Estimate(id=str(uuid.uuid4()), task_id=task_id_2, deliverable_name="Test2", person_days=10.0, amount=1000000.0)
        db.add_all([estimate1, estimate2])
        db.commit()

        # Verify estimates are isolated
        task1_estimates = db.query(Estimate).filter(Estimate.task_id == task_id_1).all()
        task2_estimates = db.query(Estimate).filter(Estimate.task_id == task_id_2).all()

        assert len(task1_estimates) == 1
        assert len(task2_estimates) == 1
        assert task1_estimates[0].deliverable_name == "Test1"
        assert task2_estimates[0].deliverable_name == "Test2"
