# TODO-7: 監視・可観測性実装（基本）

## 📋 概要
- **目的**: AI見積りシステムの運用状況を把握するため、構造化ログ、リクエストトレース、メトリクス収集を実装する
- **期間**: Day 15-17
- **優先度**: 🔴 最高
- **依存関係**: なし

## 🎯 達成基準
- [x] 構造化ログ実装完了（JSON形式）
- [x] リクエストIDトレース実装完了
- [x] メトリクス収集実装完了
- [x] メトリクスエンドポイント実装完了
- [x] 監視計画文書作成完了（ja/en）
- [x] ログレベル設定実装完了
- [x] PII情報のマスキング実装完了
- [x] テスト実装完了

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

### Day 15: 2025-10-22 - 構造化ログ・メトリクス基盤実装

#### 実施作業
- [x] **構造化ログシステム実装**
  - StructuredLoggerクラス実装（JSON形式ログ）
  - JSONFormatterクラス実装（カスタムフィールド対応）
  - PIIMaskerクラス実装（個人情報マスキング）
  - get_logger()ファクトリー関数実装

- [x] **リクエストIDトレース実装**
  - RequestIDMiddlewareクラス実装
  - UUID生成、リクエストステート管理
  - X-Request-IDヘッダー追加

- [x] **メトリクス収集システム実装**
  - MetricsCollectorクラス実装（シングルトンパターン）
  - APICallMetric, OpenAICallMetric, ErrorMetric データクラス
  - スレッドセーフ実装（threading.Lock）
  - P95パーセンタイル計算

- [x] **メトリクスAPI実装**
  - GET /api/v1/metrics - メトリクスサマリー
  - GET /api/v1/health - 詳細ヘルスチェック
  - GET /api/v1/metrics/errors - エラー一覧
  - POST /api/v1/metrics/reset - メトリクスリセット

- [x] **設定追加**
  - .envにLOG_LEVEL, LOG_FILE, MASK_PII追加
  - config.pyに設定読み込み追加

#### 変更ファイル
**新規作成**
- `backend/app/core/logging_config.py` - 構造化ログシステム
- `backend/app/middleware/request_id.py` - リクエストIDミドルウェア
- `backend/app/core/metrics.py` - メトリクス収集システム
- `backend/app/api/v1/metrics.py` - メトリクスAPI

**変更**
- `backend/app/core/config.py` - ログ設定追加
- `backend/app/main.py` - RequestIDMiddleware登録、metrics router追加

#### 確認・テスト
- [x] サービス再起動成功（sudo systemctl restart estimator）
- [x] /health エンドポイント動作確認
- [x] /api/v1/metrics エンドポイント動作確認
- [x] X-Request-IDヘッダー確認
- [x] デグレなし確認

#### 課題・気づき
- PIIMaskerの正規表現パターンは基本的なものに留まる（必要に応じて拡張）
- メトリクスのメモリ蓄積に注意（定期的にreset()が必要）
- ログファイルローテーション設定は本番環境で別途必要

---

### Day 16: 2025-10-22 - サービス層統合

#### 実施作業
- [x] **EstimatorService統合**
  - print()をlogger.info/error/warningに置き換え
  - OpenAI APIメトリクス記録追加
  - request_id伝播実装

- [x] **QuestionService統合**
  - ログ追加
  - OpenAI APIメトリクス記録追加
  - request_id伝播実装

- [x] **ChatService統合**
  - OpenAI APIメトリクス記録追加（proposal + adjustment）
  - _call_proposal_llm_with_retry, _call_adjustment_llm_with_retry両方に対応
  - request_id伝播実装

- [x] **TaskService統合**
  - print()をlogger.infoに置き換え
  - request_id伝播実装

- [x] **API層統合**
  - tasks.pyにrequest.state.request_id取得処理追加
  - 全サービス呼び出しにrequest_id伝播

#### 変更ファイル
- `backend/app/services/estimator_service.py` - ログ・メトリクス追加
- `backend/app/services/question_service.py` - ログ・メトリクス追加
- `backend/app/services/chat_service.py` - メトリクス追加
- `backend/app/services/task_service.py` - ログ追加
- `backend/app/api/v1/tasks.py` - request_id伝播

#### 確認・テスト
- [x] サービス再起動成功
- [x] タスク作成フロー動作確認
- [x] メトリクス収集確認
- [x] 既存機能デグレなし確認

#### 課題・気づき
- request_idをOptional[str] = Noneにして後方互換性を保った
- 既存のprint()は残しつつ、並行してログ出力（段階的移行）
- OpenAI APIのtoken使用量が正確に記録されることを確認

---

### Day 17: 2025-10-22 - ドキュメント・テスト実装

#### 実施作業
- [x] **監視計画文書作成**
  - MONITORING_PLAN.md作成（日本語、460行）
  - MONITORING_PLAN_EN.md作成（英語完全翻訳、460行）
  - 監視目的、アーキテクチャ、SLI/SLO/SLA定義
  - アラート閾値、トラブルシューティング手順
  - ログ調査方法、将来の拡張提案

- [x] **ユニットテスト実装**
  - test_logging_config.py（190行、14テスト）
    - PIIMasker、JSONFormatter、StructuredLogger、get_logger
  - test_metrics.py（356行、16テスト）
    - データクラス、MetricsCollector、シングルトン、スレッドセーフ、P95計算

- [x] **統合テスト実装**
  - test_monitoring.py（341行、16テスト）
    - モニタリングエンドポイント、リクエストIDトレース
    - メトリクス蓄積、ヘルスステータス判定、エラー記録

- [x] **テスト修正**
  - ErrorMetric subscript issue修正（dict → attribute access）
  - openai_operations missing issue修正（get_summary()リファクタ）
  - Credit card masking test調整

#### 変更ファイル
**新規作成**
- `docs/monitoring/MONITORING_PLAN.md` - 日本語監視計画
- `docs/monitoring/MONITORING_PLAN_EN.md` - 英語監視計画
- `backend/tests/unit/test_logging_config.py` - ログテスト
- `backend/tests/unit/test_metrics.py` - メトリクステスト
- `backend/tests/integration/test_monitoring.py` - 統合テスト

**変更**
- `backend/app/core/metrics.py` - get_summary()リファクタ（openai_operations常時返却）
- `backend/tests/unit/test_metrics.py` - ErrorMetric test修正

#### 確認・テスト
- [x] test_logging_config.py: 14テストすべてPASS ✅
- [x] test_metrics.py: 16テストすべてPASS ✅
- [x] test_monitoring.py: 16テストすべてPASS ✅
- [x] **合計: 46テストすべてPASS** 🎉

#### 課題・気づき
- get_summary()でOpenAI統計を常に計算する必要があった（API呼び出し有無に関わらず）
- PIIマスキングのカバレッジは基本パターンのみ（本番運用で調整必要）
- テストカバレッジ: logging_config 92%, metrics 100%, metrics API 100%

---

## 📊 実績

### 達成した成果

✅ **構造化ログ基盤**
- JSON形式ログ（ISO 8601タイムスタンプ、カスタムフィールド対応）
- PIIマスキング（email、電話番号、クレジットカード）
- ログレベル制御（INFO/WARNING/ERROR）

✅ **リクエストトレース**
- UUID生成によるリクエストID
- X-Request-IDヘッダー追加
- request_id伝播（middleware → API → service）

✅ **メトリクス収集**
- API統計（呼び出し数、応答時間、P95、成功率）
- OpenAI統計（呼び出し数、トークン数、成功率、操作別内訳）
- エラー統計（エラー数、エラー率、最近のエラー）
- スレッドセーフ実装（並行リクエスト対応）

✅ **モニタリングAPI**
- GET /api/v1/metrics - メトリクスサマリー
- GET /api/v1/health - ヘルスチェック（healthy/degraded/unhealthy）
- GET /api/v1/metrics/errors - エラー一覧
- POST /api/v1/metrics/reset - メトリクスリセット

✅ **監視計画文書**
- 日本語・英語完全対応（各460行）
- SLI/SLO/SLA定義
- アラート閾値・対応手順
- トラブルシューティングガイド

✅ **包括的テスト**
- ユニットテスト30件（logging + metrics）
- 統合テスト16件（monitoring endpoints）
- 全46テストPASS、デグレなし

### 監視改善効果

**導入前**
- ❌ print()による非構造化ログ
- ❌ リクエスト追跡不可
- ❌ メトリクス収集なし
- ❌ 運用状況の可視化なし

**導入後**
- ✅ JSON構造化ログ（検索・集計可能）
- ✅ リクエストID追跡（分散トレース準備完了）
- ✅ リアルタイムメトリクス収集
- ✅ ヘルスステータス自動判定
- ✅ 運用ダッシュボード構築可能

**期待効果**
- 🎯 障害発生時の原因特定時間 → 50%削減
- 🎯 パフォーマンス問題の早期発見 → リアルタイム検知
- 🎯 OpenAI APIコスト管理 → トークン消費量可視化
- 🎯 SLO達成状況の追跡 → 定量的評価可能

### 学び

**技術的学び**
- FastAPIのミドルウェア実装（BaseHTTPMiddleware）
- スレッドセーフなシングルトンパターン（threading.Lock）
- P95パーセンタイル計算（統計指標）
- 正規表現によるPIIマスキング

**設計上の学び**
- OpenAI統計はAPI呼び出し有無に関わらず常に計算すべき
- request_idはOptional[str]で後方互換性を保つ
- メトリクスはメモリ蓄積されるため定期的にreset()必要
- ログ・メトリクス追加時はデグレ確認を徹底

**テスト上の学び**
- dataclassはdict subscript不可（attribute access必須）
- カバレッジ目標: コア機能92%以上
- 統合テストでスレッドセーフ性も確認（concurrent requests）

---

## ✅ 完了チェックリスト
- [x] 構造化ログ実装完了
- [x] リクエストIDトレース実装完了
- [x] メトリクス収集実装完了
- [x] メトリクスエンドポイント動作確認
- [x] PIIマスキング実装完了
- [x] 監視計画文書作成完了（ja/en）
- [x] テスト実装完了
- [x] ドキュメント更新完了
- [x] 全テストPASS（46件）
- [x] デグレなし確認

## 📚 参考資料
- todo.md (910-1108行目): TODO-7詳細
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/46_monitoring-and-observability-for-agentic-ai-production-best-practices-aaidc-week11-lesson1.md`
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/47_what-to-monitor-in-agentic-ai-detecting-failures-before-users-do-aaidc-week11-lesson1b.md`

---

**作成日**: 2025-10-18
**最終更新**: 2025-10-22
**担当**: Claude Code
**ステータス**: 完了 ✅
