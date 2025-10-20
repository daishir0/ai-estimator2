# TODO-7: 監視・可観測性実装（基本）

## 📋 概要
- **目的**: AI見積りシステムの運用状況を把握するため、構造化ログ、リクエストトレース、メトリクス収集を実装する
- **期間**: Day 15-17
- **優先度**: 🔴 最高
- **依存関係**: なし

## 🎯 達成基準
- [ ] 構造化ログ実装完了（JSON形式）
- [ ] リクエストIDトレース実装完了
- [ ] メトリクス収集実装完了
- [ ] メトリクスエンドポイント実装完了
- [ ] 監視計画文書作成完了（ja/en）
- [ ] ログレベル設定実装完了
- [ ] PII情報のマスキング実装完了
- [ ] テスト実装完了

---

## 📐 計画

### 1. 現状分析

**既存のログ実装**:
- `print()`文による標準出力
- 構造化されていない
- リクエストトレース不可
- メトリクス未収集

**改善点**:
- JSON形式の構造化ログ
- リクエストID追跡
- メトリクス自動収集
- ログレベル管理

### 2. 実装内容

#### 2.1 構造化ログ (app/core/logging_config.py)

```python
import logging
import json
from datetime import datetime
from typing import Any, Dict
from app.core.config import settings

class StructuredLogger:
    """構造化ログ（JSON形式）"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))

        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.JSONFormatter())
        self.logger.addHandler(console_handler)

        # ファイルハンドラー（本番環境）
        if settings.LOG_FILE:
            file_handler = logging.FileHandler(settings.LOG_FILE)
            file_handler.setFormatter(self.JSONFormatter())
            self.logger.addHandler(file_handler)

    class JSONFormatter(logging.Formatter):
        """JSON形式フォーマッター"""

        def format(self, record: logging.LogRecord) -> str:
            log_data = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            # カスタムフィールド追加
            for key in ["request_id", "task_id", "user_id", "duration", "status_code"]:
                if hasattr(record, key):
                    log_data[key] = getattr(record, key)

            # 例外情報
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)

            return json.dumps(log_data, ensure_ascii=False)

    def info(self, message: str, **kwargs):
        """INFOレベルログ"""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """WARNINGレベルログ"""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """ERRORレベルログ"""
        self.logger.error(message, extra=kwargs)

    def debug(self, message: str, **kwargs):
        """DEBUGレベルログ"""
        self.logger.debug(message, extra=kwargs)

# グローバルロガーインスタンス
def get_logger(name: str) -> StructuredLogger:
    """ロガーを取得"""
    return StructuredLogger(name)
```

#### 2.2 リクエストIDミドルウェア (app/middleware/request_id.py)

```python
import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """リクエストID追跡ミドルウェア"""

    async def dispatch(self, request: Request, call_next):
        # リクエストID生成
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 開始時刻
        start_time = time.perf_counter()

        # リクエスト処理
        try:
            response = await call_next(request)

            # 処理時間計算
            duration = time.perf_counter() - start_time

            # アクセスログ
            logger.info(
                f"{request.method} {request.url.path}",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=round(duration, 3)
            )

            # レスポンスヘッダーにリクエストID追加
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration=round(duration, 3)
            )
            raise
```

#### 2.3 メトリクス収集 (app/core/metrics.py)

```python
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import statistics

@dataclass
class APICallMetric:
    """API呼び出しメトリクス"""
    endpoint: str
    method: str
    status_code: int
    duration: float
    timestamp: str
    request_id: str

@dataclass
class OpenAICallMetric:
    """OpenAI API呼び出しメトリクス"""
    model: str
    tokens: int
    duration: float
    success: bool
    timestamp: str
    request_id: str

class MetricsCollector:
    """メトリクス収集クラス"""

    def __init__(self):
        self.api_calls: List[APICallMetric] = []
        self.openai_calls: List[OpenAICallMetric] = []
        self.errors: List[Dict[str, Any]] = []

    def record_api_call(self, endpoint: str, method: str, status_code: int,
                       duration: float, request_id: str):
        """API呼び出しを記録"""
        metric = APICallMetric(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration=duration,
            timestamp=datetime.utcnow().isoformat() + "Z",
            request_id=request_id
        )
        self.api_calls.append(metric)

    def record_openai_call(self, model: str, tokens: int, duration: float,
                           success: bool, request_id: str):
        """OpenAI API呼び出しを記録"""
        metric = OpenAICallMetric(
            model=model,
            tokens=tokens,
            duration=duration,
            success=success,
            timestamp=datetime.utcnow().isoformat() + "Z",
            request_id=request_id
        )
        self.openai_calls.append(metric)

    def record_error(self, error_type: str, message: str, request_id: str):
        """エラーを記録"""
        self.errors.append({
            "error_type": error_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id
        })

    def get_summary(self) -> Dict[str, Any]:
        """メトリクスサマリーを取得"""
        if not self.api_calls:
            return {
                "total_api_calls": 0,
                "total_openai_calls": 0,
                "total_errors": 0
            }

        # API呼び出し統計
        durations = [call.duration for call in self.api_calls]
        status_codes = [call.status_code for call in self.api_calls]

        # OpenAI統計
        openai_success = sum(1 for call in self.openai_calls if call.success)
        openai_total = len(self.openai_calls)
        total_tokens = sum(call.tokens for call in self.openai_calls)

        return {
            "total_api_calls": len(self.api_calls),
            "avg_response_time": round(statistics.mean(durations), 3) if durations else 0,
            "p95_response_time": round(statistics.quantiles(durations, n=20)[18], 3) if len(durations) >= 20 else 0,
            "success_rate": round(sum(1 for s in status_codes if 200 <= s < 300) / len(status_codes) * 100, 2),
            "total_openai_calls": openai_total,
            "openai_success_rate": round(openai_success / openai_total * 100, 2) if openai_total > 0 else 0,
            "total_tokens_used": total_tokens,
            "total_errors": len(self.errors),
            "error_rate": round(len(self.errors) / len(self.api_calls) * 100, 2) if self.api_calls else 0
        }

    def reset(self):
        """メトリクスをリセット"""
        self.api_calls.clear()
        self.openai_calls.clear()
        self.errors.clear()

# グローバルインスタンス
metrics_collector = MetricsCollector()
```

#### 2.4 メトリクスエンドポイント (app/api/v1/metrics.py)

```python
from fastapi import APIRouter
from app.core.metrics import metrics_collector

router = APIRouter()

@router.get("/metrics")
async def get_metrics():
    """メトリクスサマリーを取得"""
    return metrics_collector.get_summary()

@router.get("/health")
async def health_check():
    """ヘルスチェック"""
    summary = metrics_collector.get_summary()
    status = "healthy"

    # エラー率が5%を超えたらunhealthy
    if summary.get("error_rate", 0) > 5:
        status = "unhealthy"

    # OpenAI成功率が90%未満ならdegraded
    if summary.get("openai_success_rate", 100) < 90:
        status = "degraded"

    return {
        "status": status,
        "metrics": summary
    }
```

#### 2.5 サービス層へのログ追加

**EstimatorService** (app/services/estimator_service.py):
```python
from app.core.logging_config import get_logger
from app.core.metrics import metrics_collector

logger = get_logger(__name__)

class EstimatorService:
    def generate_estimates(self, deliverables, system_requirements, qa_pairs, request_id):
        logger.info(
            "Starting batch estimation",
            request_id=request_id,
            deliverable_count=len(deliverables)
        )

        # ... 既存処理 ...

        # OpenAI呼び出しメトリクス記録
        metrics_collector.record_openai_call(
            model=self.model,
            tokens=response.usage.total_tokens,
            duration=duration,
            success=True,
            request_id=request_id
        )

        logger.info(
            "Batch estimation completed",
            request_id=request_id,
            total_estimates=len(results)
        )
```

#### 2.6 設定追加 (app/core/config.py)

```python
class Settings(BaseSettings):
    # ... 既存設定 ...

    # Logging設定
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE: str = ""  # ファイルログパス（空の場合はコンソールのみ）
```

#### 2.7 PIIマスキング (app/core/logging_config.py)

```python
import re

class PIIMasker:
    """PII情報マスキング"""

    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PHONE_PATTERN = r'\b\d{2,4}-\d{2,4}-\d{4}\b'
    CREDIT_CARD_PATTERN = r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'

    @staticmethod
    def mask(text: str) -> str:
        """PII情報をマスキング"""
        text = re.sub(PIIMasker.EMAIL_PATTERN, '***@***.***', text)
        text = re.sub(PIIMasker.PHONE_PATTERN, '***-****-****', text)
        text = re.sub(PIIMasker.CREDIT_CARD_PATTERN, '****-****-****-****', text)
        return text
```

#### 2.8 監視計画文書 (docs/monitoring/MONITORING_PLAN.md)

**目次**:
1. 監視対象指標
2. SLI/SLO/SLA
3. 警戒閾値
4. アラート設定
5. ダッシュボード（将来）

### 3. 多言語対応

**翻訳追加**:
- ログメッセージは翻訳不要（技術者向けのため英語）
- ドキュメントは多言語対応（ja/en）

### 4. 技術スタック

- **Python logging**: 構造化ログ
- **JSON**: ログフォーマット
- **UUID**: リクエストID生成
- **statistics**: メトリクス統計

### 5. 影響範囲

**新規作成ファイル**
- `app/core/logging_config.py`
- `app/middleware/request_id.py`
- `app/core/metrics.py`
- `app/api/v1/metrics.py`
- `docs/monitoring/MONITORING_PLAN.md` (ja/en)

**変更ファイル**
- `app/core/config.py`
- `app/main.py` (ミドルウェア追加、ログ初期化)
- `app/services/estimator_service.py`
- `app/services/question_service.py`
- `app/services/chat_service.py`
- `app/api/v1/tasks.py`

**テストファイル追加**
- `backend/tests/unit/test_logging_config.py`
- `backend/tests/unit/test_metrics.py`
- `backend/tests/integration/test_monitoring.py`

### 6. リスクと対策

#### リスク1: ログ量の増大
- **対策**: ログローテーション設定、ログレベル調整

#### リスク2: パフォーマンス低下
- **対策**: 非同期ログ、メトリクス定期リセット

#### リスク3: PII漏洩
- **対策**: PIIマスキング、ログレビュー

### 7. スケジュール

**Day 15**:
- 構造化ログ実装
- リクエストIDミドルウェア実装
- 設定追加

**Day 16**:
- メトリクス収集実装
- メトリクスエンドポイント実装
- サービス層ログ追加

**Day 17**:
- PIIマスキング実装
- 監視計画文書作成（ja/en）
- テスト実装
- ドキュメント更新

---

## 🔧 実施内容（実績）

### Day 15-17: [日付]
#### 実施作業
- [ ] 作業内容（実装時に記録）

#### 変更ファイル
- ファイル一覧（実装時に記録）

#### 確認・テスト
- [ ] テスト結果（実装時に記録）

#### 課題・気づき
- 課題・気づき（実装時に記録）

---

## 📊 実績

### 達成した成果
- 成果内容（完了時にまとめ）

### 監視改善効果
- 改善効果（完了時にまとめ）

### 学び
- 学んだこと（完了時にまとめ）

---

## ✅ 完了チェックリスト
- [ ] 構造化ログ実装完了
- [ ] リクエストIDトレース実装完了
- [ ] メトリクス収集実装完了
- [ ] メトリクスエンドポイント動作確認
- [ ] PIIマスキング実装完了
- [ ] 監視計画文書作成完了（ja/en）
- [ ] テスト実装完了
- [ ] ドキュメント更新完了

## 📚 参考資料
- todo.md (910-1108行目): TODO-7詳細
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/46_monitoring-and-observability-for-agentic-ai-production-best-practices-aaidc-week11-lesson1.md`
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/47_what-to-monitor-in-agentic-ai-detecting-failures-before-users-do-aaidc-week11-lesson1b.md`

---

**作成日**: 2025-10-18
**最終更新**: 2025-10-18
**担当**: Claude Code
**ステータス**: 計画完了
