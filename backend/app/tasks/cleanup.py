"""Automatic data cleanup batch script for GDPR compliance

This script deletes tasks older than DATA_RETENTION_DAYS (default: 30 days)
to comply with data retention policies.

Usage:
    python -m app.tasks.cleanup
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.task import Task
from app.models.deliverable import Deliverable
from app.models.qa_pair import QAPair
from app.models.estimate import Estimate
from app.models.message import Message
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def cleanup_old_tasks():
    """Delete tasks older than DATA_RETENTION_DAYS"""
    db: Session = SessionLocal()

    try:
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=settings.DATA_RETENTION_DAYS)

        logger.info(
            f"Starting auto cleanup",
            retention_days=settings.DATA_RETENTION_DAYS,
            cutoff_date=cutoff_date.isoformat()
        )

        # Get old tasks
        try:
            old_tasks = db.query(Task).filter(Task.created_at < cutoff_date).all()
        except Exception as e:
            # Handle case where tables don't exist yet (fresh installation)
            if "no such table" in str(e).lower():
                logger.info("Database tables not initialized yet. No tasks to cleanup.")
                return
            raise

        if not old_tasks:
            logger.info("No tasks to cleanup")
            return

        logger.info(f"Found {len(old_tasks)} tasks to delete", task_count=len(old_tasks))

        deleted_count = 0
        file_deleted_count = 0

        for task in old_tasks:
            task_id = task.id
            logger.info(
                f"Deleting task",
                task_id=task_id,
                created_at=task.created_at.isoformat()
            )

            # Delete related data (cascade deletion)
            db.query(Deliverable).filter(Deliverable.task_id == task_id).delete()
            db.query(QAPair).filter(QAPair.task_id == task_id).delete()
            db.query(Estimate).filter(Estimate.task_id == task_id).delete()
            db.query(Message).filter(Message.task_id == task_id).delete()

            # Delete files (if exist)
            if task.excel_file_path and os.path.exists(task.excel_file_path):
                try:
                    os.remove(task.excel_file_path)
                    file_deleted_count += 1
                    logger.info(f"Deleted file: {task.excel_file_path}", task_id=task_id)
                except Exception as e:
                    logger.warning(
                        f"Failed to delete file: {task.excel_file_path}",
                        task_id=task_id,
                        error=str(e)
                    )

            if task.result_file_path and os.path.exists(task.result_file_path):
                try:
                    os.remove(task.result_file_path)
                    file_deleted_count += 1
                    logger.info(f"Deleted file: {task.result_file_path}", task_id=task_id)
                except Exception as e:
                    logger.warning(
                        f"Failed to delete file: {task.result_file_path}",
                        task_id=task_id,
                        error=str(e)
                    )

            # Delete task
            db.delete(task)
            deleted_count += 1

        # Commit all deletions
        db.commit()

        logger.info(
            f"Auto cleanup completed",
            deleted_tasks=deleted_count,
            deleted_files=file_deleted_count
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Auto cleanup failed", error=str(e))
        raise

    finally:
        db.close()


if __name__ == "__main__":
    if not settings.AUTO_CLEANUP_ENABLED:
        logger.warning("Auto cleanup is disabled in settings (AUTO_CLEANUP_ENABLED=False)")
        sys.exit(0)

    cleanup_old_tasks()
