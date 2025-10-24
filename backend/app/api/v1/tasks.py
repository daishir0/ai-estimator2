"""タスクAPIエンドポイント"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from pydantic import BaseModel
from pydantic import BaseModel
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import shutil
import uuid

from app.db.database import get_db
from app.core.logging_config import get_logger

logger = get_logger(__name__)
from app.schemas.task import (
    TaskResponse,
    TaskStatusResponse,
    TaskResultResponse,
)
from app.schemas.estimate import EstimateResponse
from app.schemas.task import TaskResultResponse
from app.schemas.qa_pair import QAPairRequest
from app.services.task_service import TaskService
from app.services.question_service import QuestionService
from app.utils.reasoning_separator import auto_separate_reasoning
from app.services.input_service import InputService
from app.services.chat_service import ChatService
from app.services.safety_service import SafetyService
from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.core.i18n import get_i18n, t

router = APIRouter()


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    file: Optional[UploadFile] = File(None),
    deliverables_json: Optional[str] = Form(None),
    system_requirements: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    タスクを作成（Excel・CSV・Webフォーム対応）

    - **file**: Excel/CSVファイル（成果物一覧）
    - **deliverables_json**: Webフォームからの成果物JSON
    - **system_requirements**: システム要件（任意）
    """
    import json

    # Safety check for system_requirements
    safety_service = SafetyService()
    if system_requirements:
        safety_service.validate_and_reject(system_requirements, "system_requirements")

    # ファイルアップロードの場合
    if file:
        file_size = 0
        chunk_size = 1024 * 1024  # 1MB
        temp_file = f"{settings.UPLOAD_DIR}/temp_{file.filename}"

        try:
            with open(temp_file, "wb") as buffer:
                while chunk := await file.read(chunk_size):
                    file_size += len(chunk)
                    if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                        os.remove(temp_file)
                        raise HTTPException(
                            status_code=413,
                            detail=f"ファイルサイズが{settings.MAX_UPLOAD_SIZE_MB}MBを超えています",
                        )
                    buffer.write(chunk)

            # ファイル形式チェック
            if file.filename.endswith(".csv"):
                # CSV処理
                print(f"[API] CSV file uploaded: {file.filename}")
                pass  # CSVとして処理（後続でInputServiceが判断）
            elif file.filename.endswith((".xlsx", ".xls")):
                # Excel処理
                print(f"[API] Excel file uploaded: {file.filename}")
                pass  # Excelとして処理（後続でInputServiceが判断）
            else:
                os.remove(temp_file)
                raise HTTPException(
                    status_code=400, detail=t('messages.invalid_file_type')
                )

            # タスク作成
            task_service = TaskService(db)
            task = task_service.create_task(temp_file, system_requirements)

            return task

        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise HTTPException(status_code=500, detail=str(e))

    # Webフォームの場合
    elif deliverables_json:
        try:
            # JSONをパース
            deliverables_data = json.loads(deliverables_json)
            print(f"[API] Web form submitted: {len(deliverables_data)} deliverables")

            # 一時的なExcelファイルを作成（既存のフローを流用）
            import pandas as pd
            from datetime import datetime

            # DataFrameを作成
            df = pd.DataFrame(deliverables_data)

            # 一時Excelファイルに保存
            temp_file = f"{settings.UPLOAD_DIR}/temp_webform_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
            df.to_excel(temp_file, index=False, header=[t('excel.column_deliverable_name'), t('excel.column_description')], engine='openpyxl')

            # タスク作成
            task_service = TaskService(db)
            task = task_service.create_task(temp_file, system_requirements)

            return task

        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail=t('messages.json_parse_failed'))
        except Exception as e:
            if 'temp_file' in locals() and os.path.exists(temp_file):
                os.remove(temp_file)
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(
            status_code=400,
            detail=t('messages.file_or_data_required')
        )


@router.get("/tasks/{task_id}/questions", response_model=List[str])
async def get_questions(task_id: str, request: Request, db: Session = Depends(get_db)):
    """
    タスクに対する質問を生成

    - **task_id**: タスクID
    """
    request_id = getattr(request.state, 'request_id', None)
    task_service = TaskService(db)
    task = task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    try:
        logger.info("Starting question generation", request_id=request_id, task_id=task_id)
        # ファイルから成果物読み込み (Excel/CSV auto-detect)
        input_service = InputService()
        if task.excel_file_path.endswith('.csv'):
            deliverables = input_service.load_csv_data(task.excel_file_path)
        else:
            deliverables = input_service.load_excel_data(task.excel_file_path)

        # 質問生成
        question_service = QuestionService()
        questions = question_service.generate_questions(
            deliverables, task.system_requirements or "", request_id
        )

        logger.info("Question generation completed", request_id=request_id, task_id=task_id, question_count=len(questions))
        return questions

    except Exception as e:
        logger.error("Question generation failed", request_id=request_id, task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/answers")
async def submit_answers(
    task_id: str, qa_pairs: List[QAPairRequest], request: Request, db: Session = Depends(get_db)
):
    """
    質問への回答を登録してタスク処理を開始

    - **task_id**: タスクID
    - **qa_pairs**: 質問と回答のペアリスト
    """
    request_id = getattr(request.state, 'request_id', None)
    task_service = TaskService(db)
    task = task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    # Safety check for all answers
    safety_service = SafetyService()
    for i, qa in enumerate(qa_pairs):
        if qa.answer:
            safety_service.validate_and_reject(qa.answer, f"answer_{i+1}")

    try:
        logger.info("Starting answer submission", request_id=request_id, task_id=task_id, qa_count=len(qa_pairs))
        # Q&Aペアを保存
        questions = [qa.question for qa in qa_pairs]
        answers = [qa.answer for qa in qa_pairs]
        task_service.save_qa_pairs(task_id, questions, answers)

        # タスク処理を実行
        task_service.process_task(task_id, request_id)
        logger.info("Answer submission completed", request_id=request_id, task_id=task_id)

        return {"message": t('messages.task_processing_started'), "task_id": task_id}

    except Exception as e:
        logger.error("Answer submission failed", request_id=request_id, task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """
    タスクのステータスを取得

    - **task_id**: タスクID
    """
    task_service = TaskService(db)
    task = task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    return task


@router.get("/tasks/{task_id}/result", response_model=TaskResultResponse)
async def get_task_result(task_id: str, db: Session = Depends(get_db)):
    """
    タスクの結果を取得

    - **task_id**: タスクID
    """
    task_service = TaskService(db)
    task = task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    if task.status != "completed":
        print(f"[API] /result not ready task_id={task_id} status={task.status}")
        raise HTTPException(
            status_code=400, detail=t('messages.task_not_completed').replace('{status}', task.status)
        )

    # 見積り取得
    estimates = task_service.get_task_estimates(task_id)
    estimate_items = []
    for i, est in enumerate(estimates):
        # Auto-separate reasoning_breakdown and reasoning_notes for existing data
        breakdown, notes = auto_separate_reasoning(
            est.reasoning_breakdown or "",
            est.reasoning_notes or ""
        )

        estimate_items.append(
            EstimateResponse(
                deliverable_name=est.deliverable_name,
                deliverable_description=est.deliverable_description,
                person_days=est.person_days,
                amount=est.amount,
                reasoning=est.reasoning,
                reasoning_breakdown=breakdown,
                reasoning_notes=notes,
            )
        )

    # 合計計算
    subtotal = sum(est.amount for est in estimate_items)
    tax = subtotal * settings.get_tax_rate()
    total = subtotal + tax

    print(f"[API] /result OK task_id={task.id} estimates={len(estimate_items)}")
    return TaskResultResponse(
        id=task.id,
        status=task.status,
        estimates=estimate_items,
        subtotal=subtotal,
        tax=tax,
        total=total,
        error_message=task.error_message,
    )


@router.get("/tasks/{task_id}/download")
async def download_result(task_id: str, db: Session = Depends(get_db)):
    """
    見積り結果をExcelファイルとしてダウンロード

    - **task_id**: タスクID
    """
    task_service = TaskService(db)
    task = task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    if not task.result_file_path or not os.path.exists(task.result_file_path):
        raise HTTPException(status_code=404, detail="結果ファイルが見つかりません")

    filename = os.path.basename(task.result_file_path)

    return FileResponse(
        task.result_file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )


@router.get("/sample-input")
async def download_sample_input():
    """
    サンプルのExcel入力ファイルをダウンロード（言語設定に応じて動的生成）
    """
    import pandas as pd
    from datetime import datetime

    # 翻訳データからサンプルデータを取得
    sample_data = t('sample_excel')

    # DataFrameを作成
    df = pd.DataFrame(sample_data)

    # 一時ファイルに保存
    temp_file = os.path.join(
        settings.UPLOAD_DIR,
        f"sample_input_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    )
    df.to_excel(
        temp_file,
        index=False,
        header=[t('excel.column_deliverable_name'), t('excel.column_description')],
        engine='openpyxl'
    )

    return FileResponse(
        temp_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="sample_input.xlsx",
    )


@router.get("/sample-input-csv")
async def download_sample_input_csv():
    """
    サンプルのCSV入力ファイルをダウンロード（言語設定に応じて動的生成）
    """
    import pandas as pd
    from datetime import datetime

    # 翻訳データからサンプルデータを取得
    sample_data = t('sample_csv')

    # DataFrameを作成
    df = pd.DataFrame(sample_data)

    # 一時ファイルに保存
    temp_file = os.path.join(
        settings.UPLOAD_DIR,
        f"sample_input_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    )
    df.to_csv(
        temp_file,
        index=False,
        header=[t('excel.column_deliverable_name'), t('excel.column_description')],
        encoding='utf-8-sig'  # BOM付きUTF-8でExcel互換性向上
    )

    return FileResponse(
        temp_file,
        media_type="text/csv",
        filename="sample_input.csv",
    )


@router.post("/tasks/{task_id}/chat", response_model=ChatResponse)
async def chat_adjust(task_id: str, req: ChatRequest, db: Session = Depends(get_db)):
    """
    見積り調整のチャットAPI（フェーズ1: クイックアクション中心）
    - intent: fit_budget, scope_reduce, unit_cost_change, risk_buffer
    - params: intentに応じたパラメータ
    - message: 自由入力（会話履歴保存）
    """
    task_service = TaskService(db)
    if not task_service.get_task(task_id):
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    # 受信ログ（デバッグ用）
    try:
        msg_head = (req.message or "").strip()
        if len(msg_head) > 40:
            msg_head = msg_head[:40] + "..."
        est_count = len(req.estimates or [])
        print(f"[API] /chat start task_id={task_id} intent={req.intent} msg='{msg_head}' ests={est_count}")
    except Exception:
        pass

    svc = ChatService(db)
    result = svc.process(task_id, req.message, req.intent, req.params, provided_estimates=req.estimates)
    # 整形
    estimates = result.get("estimates") or []
    resp_items = []
    for i, e in enumerate(estimates):
        # Auto-separate reasoning_breakdown and reasoning_notes (same as /result endpoint)
        breakdown, notes = auto_separate_reasoning(
            e.get("reasoning_breakdown") or "",
            e.get("reasoning_notes") or ""
        )

        resp_items.append({
            "deliverable_name": e["deliverable_name"],
            "deliverable_description": e.get("deliverable_description"),
            "person_days": float(e["person_days"]),
            "amount": float(e["amount"]),
            "reasoning": e.get("reasoning"),
            "reasoning_breakdown": breakdown,
            "reasoning_notes": notes,
        })

    # Save adjusted estimates to database (use resp_items which has auto-separated data)
    if resp_items:
        from app.models.estimate import Estimate
        # Delete old estimates
        db.query(Estimate).filter(Estimate.task_id == task_id).delete()
        # Save new estimates (from resp_items, not estimates)
        for i, e in enumerate(resp_items):
            estimate = Estimate(
                id=str(uuid.uuid4()),
                task_id=task_id,
                deliverable_name=e["deliverable_name"],
                deliverable_description=e.get("deliverable_description"),
                person_days=float(e["person_days"]),
                amount=float(e["amount"]),
                reasoning=e.get("reasoning"),
                reasoning_breakdown=e["reasoning_breakdown"],  # ← From resp_items (auto-separated)
                reasoning_notes=e["reasoning_notes"],          # ← From resp_items (auto-separated)
            )
            db.add(estimate)
        db.commit()
    resp = ChatResponse(
        reply_md=result.get("reply_md", ""),
        suggestions=result.get("suggestions"),
        proposals=result.get("proposals"),  # 提案カード（2ステップUX）
        estimates=resp_items,
        totals=result.get("totals"),
        version=result.get("version"),
    )
    try:
        print(f"[API] /chat done task_id={task_id} ests={len(resp_items)} subtotal={int(result.get('totals',{}).get('subtotal',0))}")
    except Exception:
        pass
    return resp


class ApplyRequest(BaseModel):
    estimates: List[EstimateResponse]


@router.post("/tasks/{task_id}/apply", response_model=TaskResultResponse)
async def apply_adjusted_estimates(task_id: str, req: ApplyRequest, db: Session = Depends(get_db)):
    """
    調整後の見積りを適用してDB保存し、Excelを再出力する
    """
    task_service = TaskService(db)
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    # 保存
    # Convert to dict list compatible
    new_ests = [
        {
            "deliverable_name": e.deliverable_name,
            "deliverable_description": e.deliverable_description,
            "person_days": e.person_days,
            "amount": e.amount,
            "reasoning": e.reasoning,
            "reasoning_breakdown": e.reasoning_breakdown,
            "reasoning_notes": e.reasoning_notes,
        }
        for e in req.estimates
    ]
    task_service.replace_estimates(task_id, new_ests)

    # 合計
    from app.services.estimator_service import EstimatorService
    est = EstimatorService()
    # EstimatorService.calculate_totals expects list of dict with 'amount'
    totals = est.calculate_totals([
        {
            'name': x.get('deliverable_name'),
            'description': x.get('deliverable_description'),
            'person_days': x.get('person_days'),
            'amount': x.get('amount'),
            'reasoning': x.get('reasoning')
        } for x in new_ests
    ])

    # Excel再出力
    qa_pairs_db = task_service.get_task_qa_pairs(task_id)
    qa_pairs = [{"question": q.question, "answer": q.answer or ""} for q in qa_pairs_db]
    from app.services.export_service import ExportService
    exporter = ExportService()
    result_file_path = exporter.write_excel_output(
        task.excel_file_path,
        [
            {
                'name': x.get('deliverable_name'),
                'description': x.get('deliverable_description'),
                'person_days': x.get('person_days'),
                'amount': x.get('amount'),
                'reasoning': x.get('reasoning')
            } for x in new_ests
        ],
        totals,
        qa_pairs,
        settings.UPLOAD_DIR,
    )

    task.result_file_path = result_file_path
    db.commit()

    # レスポンス用に読み直し
    estimates_rows = task_service.get_task_estimates(task_id)
    estimate_items = [
        EstimateResponse(
            deliverable_name=est_row.deliverable_name,
            deliverable_description=est_row.deliverable_description,
            person_days=est_row.person_days,
            amount=est_row.amount,
            reasoning=est_row.reasoning,
            reasoning_breakdown=est_row.reasoning_breakdown,
            reasoning_notes=est_row.reasoning_notes,
        )
        for est_row in estimates_rows
    ]

    return TaskResultResponse(
        id=task.id,
        status=task.status,
        estimates=estimate_items,
        subtotal=totals['subtotal'],
        tax=totals['tax'],
        total=totals['total'],
        error_message=task.error_message,
    )


@router.get("/translations")
async def get_translations():
    """フロントエンド用の翻訳データを返す（税率を動的に置換）"""
    i18n = get_i18n()
    tax_rate = int(settings.get_tax_rate() * 100)  # 0.1 → 10, 0.0 → 0

    # 翻訳データをコピーして税率を置換
    import copy
    translations = copy.deepcopy(i18n.translations)

    # ui.label_tax の {tax_rate} を実際の税率に置換
    if 'ui' in translations and 'label_tax' in translations['ui']:
        translations['ui']['label_tax'] = translations['ui']['label_tax'].replace('{tax_rate}', str(tax_rate))

    # excel.label_tax の {tax_rate} を実際の税率に置換
    if 'excel' in translations and 'label_tax' in translations['excel']:
        translations['excel']['label_tax'] = translations['excel']['label_tax'].replace('{tax_rate}', str(tax_rate))

    return {
        "language": i18n.language,
        "tax_rate": tax_rate,
        "translations": translations
    }


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """
    Delete task and all related data (GDPR compliance)

    - **task_id**: Task ID to delete

    Returns:
        Success message
    """
    from app.models.task import Task
    from app.models.deliverable import Deliverable
    from app.models.qa_pair import QAPair
    from app.models.estimate import Estimate
    from app.models.message import Message

    # Check if task exists
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail=t('messages.task_not_found'))

    # Delete related data (cascade deletion)
    db.query(Deliverable).filter(Deliverable.task_id == task_id).delete()
    db.query(QAPair).filter(QAPair.task_id == task_id).delete()
    db.query(Estimate).filter(Estimate.task_id == task_id).delete()
    db.query(Message).filter(Message.task_id == task_id).delete()

    # Delete files (if exist)
    if task.excel_file_path and os.path.exists(task.excel_file_path):
        try:
            os.remove(task.excel_file_path)
            logger.info(f"Deleted file: {task.excel_file_path}", task_id=task_id)
        except Exception as e:
            logger.warning(f"Failed to delete file: {task.excel_file_path}", task_id=task_id, error=str(e))

    if task.result_file_path and os.path.exists(task.result_file_path):
        try:
            os.remove(task.result_file_path)
            logger.info(f"Deleted file: {task.result_file_path}", task_id=task_id)
        except Exception as e:
            logger.warning(f"Failed to delete file: {task.result_file_path}", task_id=task_id, error=str(e))

    # Delete task
    db.delete(task)
    db.commit()

    logger.info(f"Task and all related data deleted (GDPR compliance)", task_id=task_id)

    return {"message": t('messages.task_deleted_successfully'), "task_id": task_id}


@router.get("/tasks/{task_id}/privacy")
async def get_task_privacy_info(task_id: str, db: Session = Depends(get_db)):
    """
    Get privacy information for a task

    - **task_id**: Task ID

    Returns:
        Privacy information including data retention and auto-deletion schedule
    """
    from app.models.task import Task
    from datetime import datetime, timedelta

    # Check if task exists
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail=t('messages.task_not_found'))

    # Calculate data retention period
    created_at = task.created_at
    retention_days = settings.DATA_RETENTION_DAYS
    deletion_date = created_at + timedelta(days=retention_days)
    days_remaining = (deletion_date - datetime.now()).days

    # Check if PII exists in task data
    from app.services.privacy_service import PrivacyService
    privacy_service = PrivacyService()

    has_pii = False
    if task.system_requirements:
        is_compliant, _ = privacy_service.check_pii_compliance(task.system_requirements)
        has_pii = not is_compliant

    return {
        "task_id": task_id,
        "created_at": created_at.isoformat(),
        "retention_days": retention_days,
        "auto_deletion_date": deletion_date.isoformat(),
        "days_remaining": max(0, days_remaining),
        "can_delete": True,
        "has_pii": has_pii,
        "auto_cleanup_enabled": settings.AUTO_CLEANUP_ENABLED,
        "privacy_policy_version": settings.PRIVACY_POLICY_VERSION,
    }
