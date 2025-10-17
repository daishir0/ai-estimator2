"""タスク管理サービス"""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

from app.models.task import Task, TaskStatus
from app.models.deliverable import Deliverable
from app.models.estimate import Estimate
from app.models.qa_pair import QAPair
from app.services.input_service import InputService
from app.services.question_service import QuestionService
from app.services.estimator_service import EstimatorService
from app.services.export_service import ExportService
from app.core.config import settings


class TaskService:
    """タスク管理サービス"""

    def __init__(self, db: Session):
        self.db = db

    def create_task(
        self, excel_file_path: str, system_requirements: Optional[str]
    ) -> Task:
        """タスクを作成"""
        task = Task(
            id=str(uuid.uuid4()),
            excel_file_path=excel_file_path,
            system_requirements=system_requirements,
            status=TaskStatus.PENDING.value,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """タスクを取得"""
        return self.db.query(Task).filter(Task.id == task_id).first()

    def update_task_status(
        self, task_id: str, status: TaskStatus, error_message: Optional[str] = None
    ) -> None:
        """タスクステータスを更新"""
        task = self.get_task(task_id)
        if task:
            task.status = status.value if hasattr(status, "value") else str(status)
            task.error_message = error_message
            task.updated_at = datetime.utcnow()
            self.db.commit()

    def save_deliverables(
        self, task_id: str, deliverables: List[Dict[str, str]]
    ) -> None:
        """成果物を保存"""
        for deliverable_data in deliverables:
            deliverable = Deliverable(
                id=str(uuid.uuid4()),
                task_id=task_id,
                name=deliverable_data["name"],
                description=deliverable_data.get("description"),
            )
            self.db.add(deliverable)
        self.db.commit()

    def save_qa_pairs(
        self, task_id: str, questions: List[str], answers: List[str]
    ) -> None:
        """Q&Aペアを保存"""
        for i, (question, answer) in enumerate(zip(questions, answers)):
            qa_pair = QAPair(
                id=str(uuid.uuid4()),
                task_id=task_id,
                question=question,
                answer=answer,
                order=i,
            )
            self.db.add(qa_pair)
        self.db.commit()

    def save_estimates(
        self, task_id: str, estimates: List[Dict[str, Any]]
    ) -> None:
        """見積りを保存"""
        for estimate_data in estimates:
            estimate = Estimate(
                id=str(uuid.uuid4()),
                task_id=task_id,
                deliverable_name=estimate_data["name"],
                deliverable_description=estimate_data.get("description"),
                person_days=estimate_data["person_days"],
                amount=estimate_data["amount"],
                reasoning=estimate_data.get("reasoning"),
                reasoning_breakdown=estimate_data.get("reasoning_breakdown"),
                reasoning_notes=estimate_data.get("reasoning_notes"),
            )
            self.db.add(estimate)
        self.db.commit()

    def get_task_estimates(self, task_id: str) -> List[Estimate]:
        """タスクの見積り一覧を取得"""
        return self.db.query(Estimate).filter(Estimate.task_id == task_id).all()

    def get_task_qa_pairs(self, task_id: str) -> List[QAPair]:
        """タスクのQ&Aペア一覧を取得"""
        return (
            self.db.query(QAPair)
            .filter(QAPair.task_id == task_id)
            .order_by(QAPair.order)
            .all()
        )

    def replace_estimates(self, task_id: str, estimates: List[Dict[str, Any]]) -> None:
        """既存見積りを削除して新しい見積りで置き換える"""
        # 既存削除
        self.db.query(Estimate).filter(Estimate.task_id == task_id).delete()
        # 追加
        for e in estimates:
            est = Estimate(
                id=str(uuid.uuid4()),
                task_id=task_id,
                deliverable_name=e.get("deliverable_name") or e.get("name"),
                deliverable_description=e.get("deliverable_description") or e.get("description"),
                person_days=e.get("person_days", 0.0),
                amount=e.get("amount", 0.0),
                reasoning=e.get("reasoning"),
                reasoning_breakdown=e.get("reasoning_breakdown"),
                reasoning_notes=e.get("reasoning_notes"),
            )
            self.db.add(est)
        self.db.commit()

    def process_task(self, task_id: str) -> None:
        """タスクを処理する（見積り実行）"""
        try:
            print(f"[TS] process_task start task_id={task_id}")
            task = self.get_task(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            # ステータスを処理中に更新
            self.update_task_status(task_id, TaskStatus.PROCESSING)
            print(f"[TS] status=processing task_id={task_id}")

            # Excelファイルから成果物を読み込み
            input_service = InputService()
            deliverables = input_service.load_excel_data(task.excel_file_path)
            print(f"[TS] loaded deliverables n={len(deliverables)} task_id={task_id}")

            # 成果物を保存
            self.save_deliverables(task_id, deliverables)

            # Q&Aペアを取得
            qa_pairs_db = self.get_task_qa_pairs(task_id)
            qa_pairs = [
                {"question": qa.question, "answer": qa.answer} for qa in qa_pairs_db
            ]

            # 見積り実行
            estimator = EstimatorService()
            print(f"[TS] estimating... task_id={task_id}")
            estimates = estimator.generate_estimates(
                deliverables, task.system_requirements or "", qa_pairs
            )
            print(f"[TS] estimates ready n={len(estimates)} task_id={task_id}")

            # 見積りを保存
            self.save_estimates(task_id, estimates)

            # 合計計算
            totals = estimator.calculate_totals(estimates)
            print(f"[TS] totals subtotal={totals['subtotal']:.0f} task_id={task_id}")

            # Excel出力
            export_service = ExportService()
            result_file_path = export_service.write_excel_output(
                task.excel_file_path, estimates, totals, qa_pairs, settings.UPLOAD_DIR
            )
            print(f"[TS] excel written path={result_file_path} task_id={task_id}")

            # タスク更新
            task.result_file_path = result_file_path
            task.status = TaskStatus.COMPLETED
            task.updated_at = datetime.utcnow()
            self.db.commit()
            print(f"[TS] process_task completed task_id={task_id}")

        except Exception as e:
            import traceback
            print(f"[TS] タスク処理エラー task_id={task_id}: {e}")
            traceback.print_exc()
            self.update_task_status(task_id, TaskStatus.FAILED, str(e))
            raise
