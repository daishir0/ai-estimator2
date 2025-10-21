"""タスクAPIエンドポイント"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from pydantic import BaseModel
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import shutil
import uuid

from app.db.database import get_db
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
                    status_code=400, detail="Excel（.xlsx, .xls）またはCSV（.csv）ファイルのみアップロード可能です"
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
            raise HTTPException(status_code=400, detail="成果物データのJSON解析に失敗しました")
        except Exception as e:
            if 'temp_file' in locals() and os.path.exists(temp_file):
                os.remove(temp_file)
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(
            status_code=400,
            detail="ファイルまたは成果物データを指定してください"
        )


@router.get("/tasks/{task_id}/questions", response_model=List[str])
async def get_questions(task_id: str, db: Session = Depends(get_db)):
    """
    タスクに対する質問を生成

    - **task_id**: タスクID
    """
    task_service = TaskService(db)
    task = task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    try:
        # ファイルから成果物読み込み (Excel/CSV auto-detect)
        input_service = InputService()
        if task.excel_file_path.endswith('.csv'):
            deliverables = input_service.load_csv_data(task.excel_file_path)
        else:
            deliverables = input_service.load_excel_data(task.excel_file_path)

        # 質問生成
        question_service = QuestionService()
        questions = question_service.generate_questions(
            deliverables, task.system_requirements or ""
        )

        return questions

    except Exception as e:
        import traceback
        print(f"[API] /answers ERROR task_id={task_id}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/answers")
async def submit_answers(
    task_id: str, qa_pairs: List[QAPairRequest], db: Session = Depends(get_db)
):
    """
    質問への回答を登録してタスク処理を開始

    - **task_id**: タスクID
    - **qa_pairs**: 質問と回答のペアリスト
    """
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
        print(f"[API] /answers start task_id={task_id} qa_count={len(qa_pairs)}")
        # Q&Aペアを保存
        questions = [qa.question for qa in qa_pairs]
        answers = [qa.answer for qa in qa_pairs]
        task_service.save_qa_pairs(task_id, questions, answers)

        # タスク処理を実行
        task_service.process_task(task_id)
        print(f"[API] /answers done task_id={task_id}")

        return {"message": "タスク処理を開始しました", "task_id": task_id}

    except Exception as e:
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
            status_code=400, detail=f"タスクは完了していません（ステータス: {task.status}）"
        )

    # 見積り取得
    estimates = task_service.get_task_estimates(task_id)
    estimate_items = [
        EstimateResponse(
            deliverable_name=est.deliverable_name,
            deliverable_description=est.deliverable_description,
            person_days=est.person_days,
            amount=est.amount,
            reasoning=est.reasoning,
            reasoning_breakdown=est.reasoning_breakdown,
            reasoning_notes=est.reasoning_notes,
        )
        for est in estimates
    ]

    # 合計計算
    subtotal = sum(est.amount for est in estimate_items)
    tax = subtotal * 0.1
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
    resp_items = [
        {
            "deliverable_name": e["deliverable_name"],
            "deliverable_description": e.get("deliverable_description"),
            "person_days": float(e["person_days"]),
            "amount": float(e["amount"]),
            "reasoning": e.get("reasoning"),
            "reasoning_breakdown": e.get("reasoning_breakdown"),
            "reasoning_notes": e.get("reasoning_notes"),
        }
        for e in estimates
    ]

    # Save adjusted estimates to database
    if estimates:
        from app.models.estimate import Estimate
        # Delete old estimates
        db.query(Estimate).filter(Estimate.task_id == task_id).delete()
        # Save new estimates
        for e in estimates:
            estimate = Estimate(
                id=str(uuid.uuid4()),
                task_id=task_id,
                deliverable_name=e["deliverable_name"],
                deliverable_description=e.get("deliverable_description"),
                person_days=float(e["person_days"]),
                amount=float(e["amount"]),
                reasoning=e.get("reasoning"),
                reasoning_breakdown=e.get("reasoning_breakdown"),
                reasoning_notes=e.get("reasoning_notes"),
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
    """フロントエンド用の翻訳データを返す"""
    i18n = get_i18n()
    return {
        "language": i18n.language,
        "translations": i18n.translations
    }
