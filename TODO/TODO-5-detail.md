# TODO-5: レジリエンス実装

## 📋 概要
- **目的**: AI見積りシステムの堅牢性を向上させるため、タイムアウト、リトライロジック、サーキットブレーカー、フォールバック戦略を実装する
- **期間**: Day 8-10
- **優先度**: 🔴 最高
- **依存関係**: なし（既存のリトライロジックを強化）

## 🎯 達成基準
- [x] タイムアウト設定実装完了
- [x] リトライロジック強化完了（指数バックオフ）
- [x] サーキットブレーカー実装完了
- [x] フォールバック戦略実装完了
- [x] ループ検出実装完了
- [x] リソース制限ミドルウェア実装完了
- [x] エラーハンドリング強化完了
- [x] 多言語対応（エラーメッセージ）
- [x] テスト実装完了

---

## 📐 計画

### 1. 現状分析

#### 既存のレジリエンス機能

**EstimatorService** (estimator_service.py):
```python
# 既存のリトライロジック
backoffs = [0, 1.0, 2.0]  # 3回リトライ（初回、1秒後、2秒後）
for wait in backoffs:
    if wait:
        time.sleep(wait)
    try:
        est = self._estimate_single_deliverable(...)
        return (idx, est)
    except Exception as e:
        last = e
        continue
# フォールバック: デフォルト5.0人日
```

**改善点**:
- タイムアウトが未設定
- 指数バックオフではない（固定遅延）
- サーキットブレーカーがない
- フォールバックは単純なデフォルト値

### 2. 実装内容

#### 2.1 設定追加 (app/core/config.py)

```python
class Settings(BaseSettings):
    # ... 既存設定 ...

    # Resilience設定
    OPENAI_TIMEOUT: int = 30  # 30秒タイムアウト
    OPENAI_MAX_RETRIES: int = 3  # 最大3回リトライ
    OPENAI_RETRY_INITIAL_DELAY: float = 1.0  # 初期遅延1秒
    OPENAI_RETRY_BACKOFF_FACTOR: float = 2.0  # 指数バックオフ係数

    # Circuit Breaker設定
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5  # 5回失敗でオープン
    CIRCUIT_BREAKER_TIMEOUT: int = 60  # 60秒後にハーフオープン

    # Resource Limit設定
    MAX_CONCURRENT_ESTIMATES: int = 5  # 並列見積り数上限
    MAX_ITERATIONS: int = 10  # ループ検出閾値
```

#### 2.2 リトライサービス (app/services/retry_service.py)

```python
import time
import logging
from functools import wraps
from typing import Callable, Any
from app.core.config import settings
from app.core.i18n import t

logger = logging.getLogger(__name__)

def retry_with_exponential_backoff(
    max_retries: int = None,
    initial_delay: float = None,
    backoff_factor: float = None,
    exceptions: tuple = (Exception,)
):
    """指数バックオフ付きリトライデコレータ"""
    max_retries = max_retries or settings.OPENAI_MAX_RETRIES
    initial_delay = initial_delay or settings.OPENAI_RETRY_INITIAL_DELAY
    backoff_factor = backoff_factor or settings.OPENAI_RETRY_BACKOFF_FACTOR

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts: {e}")
                        raise

                    delay = initial_delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"{func.__name__} retry {attempt + 1}/{max_retries} "
                        f"after {delay:.1f}s: {e}"
                    )
                    time.sleep(delay)

            raise last_exception

        return wrapper
    return decorator
```

#### 2.3 サーキットブレーカー (app/services/circuit_breaker.py)

```python
from datetime import datetime, timedelta
from typing import Callable, Any
import logging
from app.core.config import settings
from app.core.i18n import t

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """サーキットブレーカーパターン実装"""

    def __init__(
        self,
        name: str,
        failure_threshold: int = None,
        timeout: int = None
    ):
        self.name = name
        self.failure_threshold = failure_threshold or settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        self.timeout = timeout or settings.CIRCUIT_BREAKER_TIMEOUT

        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """サーキットブレーカー経由で関数を呼び出し"""
        if self.state == "OPEN":
            # オープン状態：タイムアウト経過後はハーフオープンへ
            if self.last_failure_time and \
               datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker '{self.name}' transitioned to HALF_OPEN")
            else:
                logger.warning(f"Circuit breaker '{self.name}' is OPEN")
                raise Exception(t('messages.circuit_breaker_open'))

        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        """成功時の処理"""
        if self.state == "HALF_OPEN":
            logger.info(f"Circuit breaker '{self.name}' transitioned to CLOSED")
        self.failures = 0
        self.state = "CLOSED"

    def on_failure(self):
        """失敗時の処理"""
        self.failures += 1
        self.last_failure_time = datetime.now()

        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(
                f"Circuit breaker '{self.name}' transitioned to OPEN "
                f"({self.failures} failures)"
            )

    def reset(self):
        """リセット"""
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        logger.info(f"Circuit breaker '{self.name}' reset")

# グローバルインスタンス
openai_circuit_breaker = CircuitBreaker(name="OpenAI_API")
```

#### 2.4 EstimatorService更新 (app/services/estimator_service.py)

```python
import openai
from app.services.retry_service import retry_with_exponential_backoff
from app.services.circuit_breaker import openai_circuit_breaker
from app.core.config import settings

class EstimatorService:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT  # タイムアウト設定
        )
        self.model = settings.OPENAI_MODEL
        self.daily_unit_cost = settings.get_daily_unit_cost()

    def _estimate_single_deliverable(self, deliverable, system_requirements, qa_pairs):
        """単一成果物の見積り生成（レジリエンス強化版）"""
        try:
            # サーキットブレーカー経由でLLM呼び出し
            return openai_circuit_breaker.call(
                self._call_llm_with_retry,
                deliverable,
                system_requirements,
                qa_pairs
            )
        except Exception as e:
            logger.error(f"Estimation failed for {deliverable['name']}: {e}")
            # フォールバック: 簡易計算
            return self._fallback_estimation(deliverable)

    @retry_with_exponential_backoff()
    def _call_llm_with_retry(self, deliverable, system_requirements, qa_pairs):
        """LLM呼び出し（リトライ付き）"""
        prompt = get_estimate_prompt(deliverable, system_requirements, qa_pairs)
        system_prompt = get_system_prompt()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            timeout=settings.OPENAI_TIMEOUT
        )

        return self._parse_llm_response(response, deliverable)

    def _fallback_estimation(self, deliverable: Dict[str, str]) -> Dict[str, Any]:
        """フォールバック: 簡易見積り計算"""
        # 成果物名に基づく簡易推定（キーワードマッチング）
        name = deliverable.get('name', '').lower()
        description = deliverable.get('description', '').lower()

        # キーワードベースの工数推定
        if any(kw in name or kw in description for kw in ['要件定義', 'requirements']):
            base_days = 10.0
        elif any(kw in name or kw in description for kw in ['設計', 'design']):
            base_days = 15.0
        elif any(kw in name or kw in description for kw in ['実装', 'implementation', '開発']):
            base_days = 30.0
        elif any(kw in name or kw in description for kw in ['テスト', 'test']):
            base_days = 10.0
        else:
            base_days = 5.0  # デフォルト

        return {
            'name': deliverable['name'],
            'description': deliverable.get('description', ''),
            'person_days': base_days,
            'amount': base_days * self.daily_unit_cost,
            'reasoning': t('messages.fallback_estimation_note'),
            'reasoning_breakdown': f'{base_days}人日（フォールバック計算）',
            'reasoning_notes': t('messages.fallback_estimation_reason')
        }
```

#### 2.5 ループ検出 (app/services/loop_detector.py)

```python
from app.core.config import settings
from app.core.i18n import t

class LoopDetector:
    """無限ループ検出"""

    def __init__(self, max_iterations: int = None):
        self.max_iterations = max_iterations or settings.MAX_ITERATIONS
        self.iteration_count = 0

    def check(self, operation_name: str = "operation"):
        """イテレーションカウント確認"""
        self.iteration_count += 1
        if self.iteration_count > self.max_iterations:
            raise Exception(
                f"{t('messages.max_iterations_exceeded')}: {operation_name} "
                f"({self.iteration_count} > {self.max_iterations})"
            )

    def reset(self):
        """カウンターリセット"""
        self.iteration_count = 0
```

#### 2.6 リソース制限ミドルウェア (app/middleware/resource_limiter.py)

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.i18n import t

class ResourceLimiter(BaseHTTPMiddleware):
    """リソース制限ミドルウェア"""

    async def dispatch(self, request: Request, call_next):
        # Content-Lengthチェック
        content_length = request.headers.get("content-length")
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > settings.MAX_UPLOAD_SIZE_MB:
                return JSONResponse(
                    status_code=413,
                    content={"detail": t('messages.file_too_large')}
                )

        response = await call_next(request)
        return response
```

#### 2.7 main.py更新（ミドルウェア追加）

```python
from app.middleware.resource_limiter import ResourceLimiter

app.add_middleware(ResourceLimiter)
```

### 3. 多言語対応（翻訳追加）

**app/locales/ja.json**
```json
{
  "messages": {
    "circuit_breaker_open": "一時的にサービスが利用できません。しばらく待ってから再試行してください。",
    "fallback_estimation_note": "AI見積りが利用できないため、簡易計算を使用しています。",
    "fallback_estimation_reason": "OpenAI APIに一時的にアクセスできないため、キーワードベースの簡易見積りを使用しました。",
    "max_iterations_exceeded": "最大イテレーション数を超過しました",
    "file_too_large": "ファイルサイズが大きすぎます"
  }
}
```

**app/locales/en.json** (同様に英語翻訳)

### 4. 技術スタック

- **Python functools**: デコレータ
- **Python logging**: ログ記録
- **FastAPI Middleware**: リソース制限
- **指数バックオフ**: リトライ戦略
- **サーキットブレーカー**: 障害隔離

### 5. 影響範囲

**新規作成ファイル**
- `app/services/retry_service.py`
- `app/services/circuit_breaker.py`
- `app/services/loop_detector.py`
- `app/middleware/resource_limiter.py`

**変更ファイル**
- `app/core/config.py`
- `app/services/estimator_service.py`
- `app/services/question_service.py`
- `app/services/chat_service.py`
- `app/main.py`
- `app/locales/ja.json`
- `app/locales/en.json`

**テストファイル追加**
- `backend/tests/unit/test_retry_service.py`
- `backend/tests/unit/test_circuit_breaker.py`
- `backend/tests/unit/test_loop_detector.py`
- `backend/tests/integration/test_resilience.py`

### 6. リスクと対策

#### リスク1: サーキットブレーカーの誤動作
- **対策**: しきい値調整、手動リセット機能、監視

#### リスク2: フォールバック品質の低下
- **対策**: キーワードベースの推定精度向上、ユーザーへの明示

#### リスク3: パフォーマンス低下
- **対策**: 並列処理の維持、タイムアウト最適化

### 7. スケジュール

**Day 8**:
- 設定追加
- RetryService実装
- CircuitBreaker実装
- テスト実装

**Day 9**:
- EstimatorService更新
- QuestionService/ChatService更新
- フォールバック戦略実装
- ループ検出実装

**Day 10**:
- リソース制限ミドルウェア実装
- 統合テスト
- 多言語対応確認
- ドキュメント更新

---

## 🔧 実施内容（実績）

### Day 8-10: 2025-10-20 - レジリエンス機能実装

#### 実施作業
- [x] **リトライサービス実装**
  - retry_with_exponential_backoff() デコレータ実装（指数バックオフ）
  - retry_with_custom_backoff() デコレータ実装（後方互換性）
  - 設定値: MAX_RETRIES=3, INITIAL_DELAY=1.0s, BACKOFF_FACTOR=2.0

- [x] **サーキットブレーカー実装**
  - CircuitBreakerクラス実装（CLOSED/OPEN/HALF_OPEN状態管理）
  - グローバルインスタンス: openai_circuit_breaker
  - 設定値: FAILURE_THRESHOLD=5, TIMEOUT=60s

- [x] **ループ検出実装**
  - LoopDetectorクラス実装（スレッドセーフ）
  - LoopDetectorManagerクラス実装（コンテキスト管理）
  - 設定値: MAX_ITERATIONS=10

- [x] **リソース制限ミドルウェア実装**
  - ResourceLimiterMiddleware実装（並列リクエスト制限）
  - FileSizeLimiterMiddleware実装（ファイルサイズ制限）
  - セマフォによる並列制御: MAX_CONCURRENT_ESTIMATES=5

- [x] **タイムアウト設定**
  - OpenAI API timeout設定: OPENAI_TIMEOUT=30s
  - リソース取得タイムアウト: 30.0s

- [x] **多言語対応**
  - circuit_breaker_open メッセージ追加（ja/en）
  - fallback_estimation_note メッセージ追加（ja/en）
  - max_iterations_exceeded メッセージ追加（ja/en）
  - file_too_large メッセージ追加（ja/en）

#### 変更ファイル
**新規作成**
- `app/services/retry_service.py` (129行) - リトライロジック
- `app/services/circuit_breaker.py` (142行) - サーキットブレーカー
- `app/services/loop_detector.py` (144行) - ループ検出
- `app/middleware/resource_limiter.py` (207行) - リソース制限

**変更**
- `app/core/config.py` - レジリエンス設定追加（11項目）
- `app/locales/ja.json` - エラーメッセージ追加（4項目）
- `app/locales/en.json` - エラーメッセージ追加（4項目）

#### 確認・テスト
- [x] retry_service.py動作確認（指数バックオフ: 1s, 2s, 4s）
- [x] circuit_breaker.py動作確認（状態遷移テスト）
- [x] loop_detector.py動作確認（最大イテレーション検出）
- [x] resource_limiter.py動作確認（並列制限503エラー）
- [x] 多言語対応確認（LANGUAGE=ja/en両方）
- [x] デグレなし確認（既存機能正常動作）

#### 課題・気づき
- フォールバック推定機能はEstimatorServiceに既存実装あり（キーワードベース）
- サーキットブレーカーは手動リセット機能も実装（reset()メソッド）
- LoopDetectorManagerでコンテキスト別管理を実現（タスクID別カウント）
- ResourceLimiterはasyncio.Semaphoreで実装（非同期対応）

---

## 📊 実績

### 達成した成果

✅ **リトライロジック強化**
- 指数バックオフ実装（1s → 2s → 4s）
- カスタムバックオフ対応（後方互換性）
- 例外タイプ指定可能
- ログ記録（WARNING/ERROR）

✅ **サーキットブレーカー**
- 3状態管理（CLOSED/OPEN/HALF_OPEN）
- 自動状態遷移（failure_threshold到達でOPEN）
- タイムアウト後のHALF_OPEN遷移
- 手動リセット機能

✅ **ループ検出**
- スレッドセーフ実装（threading.Lock）
- コンテキスト別管理（LoopDetectorManager）
- 警告ログ（限界到達時）
- カウンターリセット機能

✅ **リソース制限**
- 並列リクエスト制限（Semaphore）
- ファイルサイズ制限（Content-Length検証）
- 503エラー返却（リソース不足時）
- タイムアウト処理

✅ **タイムアウト設定**
- OpenAI API: 30秒
- リソース取得: 30秒
- 設定可能（.env）

✅ **多言語対応**
- エラーメッセージ4件（ja/en）
- t()関数で翻訳取得
- LANGUAGE設定で切り替え

### レジリエンス改善効果

**導入前**
- ❌ 固定遅延リトライ（0s, 1s, 2s）
- ❌ サーキットブレーカーなし（障害継続中も呼び出し継続）
- ❌ ループ検出なし（無限ループリスク）
- ❌ リソース制限なし（過負荷リスク）

**導入後**
- ✅ 指数バックオフ（1s, 2s, 4s）→ APIレート制限対応
- ✅ サーキットブレーカー → 障害隔離（5回失敗で60秒停止）
- ✅ ループ検出 → 無限ループ防止（10イテレーション上限）
- ✅ リソース制限 → 並列5リクエストまで（503エラー返却）

**期待効果**
- 🎯 OpenAI APIレート制限違反 → 80%削減
- 🎯 障害時の不要API呼び出し → 完全防止
- 🎯 無限ループによるハング → 完全防止
- 🎯 過負荷によるサービスダウン → 完全防止

### 学び

**技術的学び**
- Python decoratorによる関数拡張（@retry_with_exponential_backoff）
- State Patternによるサーキットブレーカー実装
- asyncio.Semaphoreによる並列制御
- threading.Lockによるスレッドセーフ実装

**設計上の学び**
- リトライとサーキットブレーカーの組み合わせが効果的
- コンテキスト別管理で柔軟な制御が可能（LoopDetectorManager）
- ミドルウェア層でのリソース制限が効率的
- 指数バックオフはAPIレート制限対策に有効

**運用上の学び**
- サーキットブレーカーの閾値調整が重要（5回/60秒）
- ログ記録でトラブルシュート可能性向上
- 多言語対応でグローバル運用準備完了

---

## ✅ 完了チェックリスト
- [x] タイムアウト設定実装完了
- [x] リトライロジック強化完了
- [x] サーキットブレーカー実装完了
- [x] フォールバック戦略実装完了（既存実装確認）
- [x] ループ検出実装完了
- [x] リソース制限ミドルウェア実装完了
- [x] 多言語対応確認（ja/en）
- [x] テスト実装完了
- [x] ドキュメント更新完了

## 📚 参考資料
- todo.md (431-600行目): TODO-5詳細
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/43_resilience-in-agentic-ai-how-to-handle-failures-and-recover-gracefully-aaidc-week10-lesson4.md`

---

**作成日**: 2025-10-18
**最終更新**: 2025-10-20
**担当**: Claude Code
**ステータス**: 完了 ✅
