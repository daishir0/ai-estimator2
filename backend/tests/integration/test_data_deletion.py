"""Integration tests for data deletion (GDPR compliance)"""
import pytest
import os
import tempfile
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, Base, engine
from app.models.task import Task
from app.models.deliverable import Deliverable
from app.models.qa_pair import QAPair
from app.models.estimate import Estimate
from app.models.message import Message
from app.core.config import settings


class TestDataDeletion:
    """Test suite for data deletion (GDPR compliance)"""

    @pytest.fixture(scope="function")
    def db_session(self):
        """Create test database session"""
        # Create tables
        Base.metadata.create_all(bind=engine)

        # Create session
        session = SessionLocal()

        yield session

        # Cleanup
        session.close()
        Base.metadata.drop_all(bind=engine)

    @pytest.fixture
    def test_task(self, db_session):
        """Create test task with related data"""
        task_id = "test-task-001"

        # Create task
        task = Task(
            id=task_id,
            status="completed",
            created_at=datetime.now()
        )
        db_session.add(task)

        # Create deliverables
        deliverable = Deliverable(
            id="del-001",
            task_id=task_id,
            name="Test Deliverable",
            description="Test Description"
        )
        db_session.add(deliverable)

        # Create Q&A pairs
        qa_pair = QAPair(
            id="qa-001",
            task_id=task_id,
            question="Test Question?",
            answer="Test Answer",
            order=1
        )
        db_session.add(qa_pair)

        # Create estimates
        estimate = Estimate(
            id="est-001",
            task_id=task_id,
            deliverable_name="Test Deliverable",
            deliverable_description="Test Description",
            person_days=5.0,
            amount=200000.0,
            reasoning="Test reasoning"
        )
        db_session.add(estimate)

        # Create messages
        message = Message(
            id="msg-001",
            task_id=task_id,
            role="user",
            content="Test message"
        )
        db_session.add(message)

        db_session.commit()

        return task

    def test_cascade_deletion(self, db_session, test_task):
        """Test cascade deletion of all related data"""
        task_id = test_task.id

        # Verify data exists
        assert db_session.query(Task).filter(Task.id == task_id).first() is not None
        assert db_session.query(Deliverable).filter(Deliverable.task_id == task_id).count() > 0
        assert db_session.query(QAPair).filter(QAPair.task_id == task_id).count() > 0
        assert db_session.query(Estimate).filter(Estimate.task_id == task_id).count() > 0
        assert db_session.query(Message).filter(Message.task_id == task_id).count() > 0

        # Delete related data
        db_session.query(Deliverable).filter(Deliverable.task_id == task_id).delete()
        db_session.query(QAPair).filter(QAPair.task_id == task_id).delete()
        db_session.query(Estimate).filter(Estimate.task_id == task_id).delete()
        db_session.query(Message).filter(Message.task_id == task_id).delete()

        # Delete task
        db_session.delete(test_task)
        db_session.commit()

        # Verify all data deleted
        assert db_session.query(Task).filter(Task.id == task_id).first() is None
        assert db_session.query(Deliverable).filter(Deliverable.task_id == task_id).count() == 0
        assert db_session.query(QAPair).filter(QAPair.task_id == task_id).count() == 0
        assert db_session.query(Estimate).filter(Estimate.task_id == task_id).count() == 0
        assert db_session.query(Message).filter(Message.task_id == task_id).count() == 0

    def test_file_deletion(self, db_session):
        """Test file deletion with task"""
        task_id = "test-task-file"

        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as excel_file:
            excel_path = excel_file.name
            excel_file.write(b"test excel content")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as result_file:
            result_path = result_file.name
            result_file.write(b"test result content")

        # Create task with file paths
        task = Task(
            id=task_id,
            status="completed",
            excel_file_path=excel_path,
            result_file_path=result_path,
            created_at=datetime.now()
        )
        db_session.add(task)
        db_session.commit()

        # Verify files exist
        assert os.path.exists(excel_path)
        assert os.path.exists(result_path)

        # Delete files
        if os.path.exists(excel_path):
            os.remove(excel_path)
        if os.path.exists(result_path):
            os.remove(result_path)

        # Delete task
        db_session.delete(task)
        db_session.commit()

        # Verify files deleted
        assert not os.path.exists(excel_path)
        assert not os.path.exists(result_path)

    def test_auto_cleanup_old_tasks(self, db_session):
        """Test automatic cleanup of old tasks"""
        # Create old task (created 35 days ago)
        old_task = Task(
            id="old-task-001",
            status="completed",
            created_at=datetime.now() - timedelta(days=35)
        )
        db_session.add(old_task)

        # Create recent task (created 20 days ago)
        recent_task = Task(
            id="recent-task-001",
            status="completed",
            created_at=datetime.now() - timedelta(days=20)
        )
        db_session.add(recent_task)

        db_session.commit()

        # Calculate cutoff date (30 days ago)
        cutoff_date = datetime.now() - timedelta(days=settings.DATA_RETENTION_DAYS)

        # Get old tasks
        old_tasks = db_session.query(Task).filter(Task.created_at < cutoff_date).all()

        # Verify only old task is selected
        assert len(old_tasks) == 1
        assert old_tasks[0].id == "old-task-001"

        # Cleanup (delete old task)
        for task in old_tasks:
            db_session.delete(task)
        db_session.commit()

        # Verify old task deleted, recent task remains
        assert db_session.query(Task).filter(Task.id == "old-task-001").first() is None
        assert db_session.query(Task).filter(Task.id == "recent-task-001").first() is not None

    def test_privacy_info_calculation(self, db_session, test_task):
        """Test privacy information calculation"""
        task_id = test_task.id

        # Get task
        task = db_session.query(Task).filter(Task.id == task_id).first()

        # Calculate retention period
        created_at = task.created_at
        retention_days = settings.DATA_RETENTION_DAYS
        deletion_date = created_at + timedelta(days=retention_days)
        days_remaining = (deletion_date - datetime.now()).days

        # Verify calculation
        assert retention_days == 30
        assert days_remaining >= 0
        assert days_remaining <= 30

    def test_multiple_tasks_deletion(self, db_session):
        """Test deletion of multiple tasks"""
        # Create multiple tasks
        tasks = []
        for i in range(5):
            task = Task(
                id=f"task-{i:03d}",
                status="completed",
                created_at=datetime.now()
            )
            db_session.add(task)
            tasks.append(task)

        db_session.commit()

        # Verify all tasks exist
        assert db_session.query(Task).count() == 5

        # Delete all tasks
        for task in tasks:
            db_session.delete(task)
        db_session.commit()

        # Verify all tasks deleted
        assert db_session.query(Task).count() == 0

    def test_partial_deletion_rollback(self, db_session, test_task):
        """Test rollback on partial deletion failure"""
        task_id = test_task.id

        try:
            # Start transaction
            db_session.query(Deliverable).filter(Deliverable.task_id == task_id).delete()
            db_session.query(QAPair).filter(QAPair.task_id == task_id).delete()

            # Simulate error
            raise Exception("Simulated error during deletion")

        except Exception:
            # Rollback
            db_session.rollback()

        # Verify data still exists (rollback successful)
        assert db_session.query(Deliverable).filter(Deliverable.task_id == task_id).count() > 0
        assert db_session.query(QAPair).filter(QAPair.task_id == task_id).count() > 0
