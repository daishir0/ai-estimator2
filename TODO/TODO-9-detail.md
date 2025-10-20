# TODO-9: コスト管理・レート制限

## 📋 概要
- **目的**: OpenAI APIコストの管理とサービス拒否攻撃（DoS）の防止のため、レート制限とコスト追跡を実装する
- **期間**: Day 20
- **優先度**: 🔴 最高
- **依存関係**: TODO-7（監視・可観測性）

## 🎯 達成基準
- [ ] レート制限実装完了
- [ ] レート制限ミドルウェア実装完了
- [ ] OpenAI APIコスト追跡実装完了
- [ ] コスト上限チェック実装完了
- [ ] コスト管理エンドポイント実装完了
- [ ] 緊急停止手順文書作成完了（ja/en）
- [ ] 多言語対応（ja/en）
- [ ] テスト実装完了

---

## 📐 計画

### 1. 現状分析

**現在のリスク**:
- レート制限なし → DoS攻撃リスク
- コスト追跡なし → 予期せぬ高額請求リスク
- コスト上限なし → 緊急停止できない

**目標**:
- 時間あたりのリクエスト数制限
- OpenAI APIコストのリアルタイム追跡
- コスト上限到達時の自動停止

### 2. 実装内容

#### 2.1 レート制限 (app/core/rate_limiter.py)

```python
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional
import threading
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """レート制限クラス（スライディングウィンドウ方式）"""

    def __init__(
        self,
        max_requests: int = None,
        window_seconds: int = None
    ):
        self.max_requests = max_requests or settings.RATE_LIMIT_MAX_REQUESTS
        self.window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS
        self.requests = defaultdict(list)
        self.lock = threading.Lock()

    def check_limit(self, client_id: str) -> tuple[bool, Optional[int]]:
        """レート制限チェック

        Returns:
            (is_allowed: bool, retry_after: Optional[int])
        """
        with self.lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self.window_seconds)

            # 古いリクエストを削除
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > window_start
            ]

            # 制限チェック
            if len(self.requests[client_id]) >= self.max_requests:
                # 最古のリクエスト時刻から再試行可能時刻を計算
                oldest_request = self.requests[client_id][0]
                retry_after = int((oldest_request + timedelta(seconds=self.window_seconds) - now).total_seconds())

                logger.warning(
                    f"Rate limit exceeded for {client_id}",
                    client_id=client_id,
                    requests_count=len(self.requests[client_id]),
                    max_requests=self.max_requests,
                    retry_after=retry_after
                )

                return False, max(0, retry_after)

            # リクエスト記録
            self.requests[client_id].append(now)
            return True, None

    def reset_client(self, client_id: str):
        """クライアントのレート制限をリセット"""
        with self.lock:
            if client_id in self.requests:
                del self.requests[client_id]

    def get_remaining(self, client_id: str) -> int:
        """残りリクエスト数を取得"""
        with self.lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self.window_seconds)

            # 古いリクエストを除外
            recent_requests = [
                req_time for req_time in self.requests.get(client_id, [])
                if req_time > window_start
            ]

            return max(0, self.max_requests - len(recent_requests))

# グローバルインスタンス
rate_limiter = RateLimiter()
```

#### 2.2 レート制限ミドルウェア (app/middleware/rate_limit.py)

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.rate_limiter import rate_limiter
from app.core.i18n import t

class RateLimitMiddleware(BaseHTTPMiddleware):
    """レート制限ミドルウェア"""

    async def dispatch(self, request: Request, call_next):
        # クライアントID（IPアドレス）
        client_id = request.client.host

        # レート制限チェック
        is_allowed, retry_after = rate_limiter.check_limit(client_id)

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": t('messages.rate_limit_exceeded'),
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after)
                }
            )

        # レスポンスにレート制限情報を追加
        response = await call_next(request)
        remaining = rate_limiter.get_remaining(client_id)
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
```

#### 2.3 コスト追跡 (app/services/cost_tracker.py)

```python
from datetime import datetime, timedelta
from typing import Dict, Any
import threading
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class CostTracker:
    """OpenAI APIコスト追跡"""

    # GPT-4o-mini pricing（2025年10月時点）
    # https://openai.com/pricing
    PRICE_PER_1M_INPUT_TOKENS = 0.15  # $0.15 per 1M input tokens
    PRICE_PER_1M_OUTPUT_TOKENS = 0.60  # $0.60 per 1M output tokens

    def __init__(self):
        self.daily_cost = 0.0
        self.monthly_cost = 0.0
        self.daily_tokens = {"input": 0, "output": 0}
        self.monthly_tokens = {"input": 0, "output": 0}
        self.last_reset_date = datetime.utcnow().date()
        self.last_reset_month = datetime.utcnow().month
        self.lock = threading.Lock()

    def record_usage(self, input_tokens: int, output_tokens: int) -> Dict[str, Any]:
        """使用量記録とコスト計算

        Returns:
            コスト情報辞書
        """
        with self.lock:
            # 日次リセットチェック
            today = datetime.utcnow().date()
            if today != self.last_reset_date:
                self.reset_daily()
                self.last_reset_date = today

            # 月次リセットチェック
            current_month = datetime.utcnow().month
            if current_month != self.last_reset_month:
                self.reset_monthly()
                self.last_reset_month = current_month

            # コスト計算
            cost = (
                (input_tokens / 1_000_000) * self.PRICE_PER_1M_INPUT_TOKENS +
                (output_tokens / 1_000_000) * self.PRICE_PER_1M_OUTPUT_TOKENS
            )

            # 累積
            self.daily_cost += cost
            self.monthly_cost += cost
            self.daily_tokens["input"] += input_tokens
            self.daily_tokens["output"] += output_tokens
            self.monthly_tokens["input"] += input_tokens
            self.monthly_tokens["output"] += output_tokens

            # ログ記録
            logger.info(
                "OpenAI API usage recorded",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=round(cost, 4),
                daily_cost_usd=round(self.daily_cost, 4),
                monthly_cost_usd=round(self.monthly_cost, 4)
            )

            # コスト上限チェック（月次）
            if self.monthly_cost > settings.MONTHLY_COST_LIMIT:
                logger.critical(
                    "Monthly cost limit exceeded!",
                    monthly_cost_usd=self.monthly_cost,
                    limit_usd=settings.MONTHLY_COST_LIMIT
                )
                raise Exception(
                    f"Monthly OpenAI API cost limit exceeded: "
                    f"${self.monthly_cost:.2f} > ${settings.MONTHLY_COST_LIMIT}"
                )

            # 日次警告（80%到達）
            if self.daily_cost > settings.DAILY_COST_LIMIT * 0.8:
                logger.warning(
                    "Daily cost approaching limit (80%)",
                    daily_cost_usd=self.daily_cost,
                    limit_usd=settings.DAILY_COST_LIMIT
                )

            return {
                "cost_usd": round(cost, 4),
                "daily_cost_usd": round(self.daily_cost, 4),
                "monthly_cost_usd": round(self.monthly_cost, 4),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }

    def get_summary(self) -> Dict[str, Any]:
        """コストサマリーを取得"""
        with self.lock:
            return {
                "daily": {
                    "cost_usd": round(self.daily_cost, 4),
                    "limit_usd": settings.DAILY_COST_LIMIT,
                    "usage_percent": round((self.daily_cost / settings.DAILY_COST_LIMIT) * 100, 2),
                    "tokens": self.daily_tokens
                },
                "monthly": {
                    "cost_usd": round(self.monthly_cost, 4),
                    "limit_usd": settings.MONTHLY_COST_LIMIT,
                    "usage_percent": round((self.monthly_cost / settings.MONTHLY_COST_LIMIT) * 100, 2),
                    "tokens": self.monthly_tokens
                }
            }

    def reset_daily(self):
        """日次リセット"""
        self.daily_cost = 0.0
        self.daily_tokens = {"input": 0, "output": 0}
        logger.info("Daily cost tracker reset")

    def reset_monthly(self):
        """月次リセット"""
        self.monthly_cost = 0.0
        self.monthly_tokens = {"input": 0, "output": 0}
        logger.info("Monthly cost tracker reset")

# グローバルインスタンス
cost_tracker = CostTracker()
```

#### 2.4 EstimatorServiceへの統合

**app/services/estimator_service.py**:
```python
from app.services.cost_tracker import cost_tracker

class EstimatorService:
    def _call_llm_with_retry(self, ...):
        # ... LLM呼び出し ...

        response = self.client.chat.completions.create(...)

        # コスト記録
        if hasattr(response, 'usage'):
            cost_tracker.record_usage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens
            )

        return self._parse_llm_response(response, deliverable)
```

#### 2.5 コスト管理エンドポイント (app/api/v1/admin.py)

```python
from fastapi import APIRouter, Depends
from app.services.cost_tracker import cost_tracker
from app.core.rate_limiter import rate_limiter

router = APIRouter()

@router.get("/admin/costs")
async def get_costs():
    """コスト状況取得（管理者用）"""
    return cost_tracker.get_summary()

@router.get("/admin/rate-limits")
async def get_rate_limits():
    """レート制限状況取得（管理者用）"""
    return {
        "max_requests": rate_limiter.max_requests,
        "window_seconds": rate_limiter.window_seconds,
        "active_clients": len(rate_limiter.requests)
    }

@router.post("/admin/reset-rate-limit/{client_id}")
async def reset_rate_limit(client_id: str):
    """特定クライアントのレート制限をリセット（管理者用）"""
    rate_limiter.reset_client(client_id)
    return {"message": f"Rate limit reset for {client_id}"}
```

#### 2.6 設定追加 (app/core/config.py)

```python
class Settings(BaseSettings):
    # ... 既存設定 ...

    # レート制限
    RATE_LIMIT_MAX_REQUESTS: int = 100  # 1時間あたり100リクエスト
    RATE_LIMIT_WINDOW_SECONDS: int = 3600  # 1時間

    # コスト上限
    DAILY_COST_LIMIT: float = 10.0  # $10/日
    MONTHLY_COST_LIMIT: float = 200.0  # $200/月
```

#### 2.7 緊急停止手順文書 (docs/operations/EMERGENCY_SHUTDOWN.md)

**目次**:
1. コスト超過時の緊急停止手順
2. 不正アクセス検出時の対応
3. 連絡先

### 3. 多言語対応

**翻訳追加** (app/locales/ja.json):
```json
{
  "messages": {
    "rate_limit_exceeded": "リクエスト数が上限に達しました。しばらくしてから再試行してください。"
  }
}
```

### 4. 技術スタック

- **Python collections.defaultdict**: レート制限記録
- **Python threading**: スレッドセーフ実装
- **datetime**: 時間管理

### 5. 影響範囲

**新規作成ファイル**
- `app/core/rate_limiter.py`
- `app/middleware/rate_limit.py`
- `app/services/cost_tracker.py`
- `app/api/v1/admin.py`
- `docs/operations/EMERGENCY_SHUTDOWN.md` (ja/en)

**変更ファイル**
- `app/core/config.py`
- `app/main.py` (ミドルウェア追加、adminルーター追加)
- `app/services/estimator_service.py`
- `app/services/question_service.py`
- `app/services/chat_service.py`
- `app/locales/ja.json`
- `app/locales/en.json`

**テストファイル追加**
- `backend/tests/unit/test_rate_limiter.py`
- `backend/tests/unit/test_cost_tracker.py`
- `backend/tests/integration/test_rate_limit_middleware.py`

### 6. リスクと対策

#### リスク1: レート制限の誤動作
- **対策**: 管理者用リセット機能、ログ記録

#### リスク2: コスト計算の誤差
- **対策**: OpenAIダッシュボードとの定期照合

#### リスク3: DoS攻撃の高度化
- **対策**: IP単位のブロック機能、監視強化

### 7. スケジュール

**Day 20**:
- RateLimiter実装
- RateLimitMiddleware実装
- CostTracker実装
- EstimatorService統合
- 管理者エンドポイント実装
- 緊急停止手順文書作成（ja/en）
- テスト実装
- ドキュメント更新

---

## 🔧 実施内容（実績）

### Day 20: [日付]
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

### コスト削減効果
- 削減効果（完了時にまとめ）

### 学び
- 学んだこと（完了時にまとめ）

---

## ✅ 完了チェックリスト
- [ ] レート制限実装完了
- [ ] レート制限ミドルウェア実装完了
- [ ] OpenAI APIコスト追跡実装完了
- [ ] コスト上限チェック動作確認
- [ ] コスト管理エンドポイント動作確認
- [ ] 緊急停止手順文書作成完了（ja/en）
- [ ] 多言語対応確認（ja/en）
- [ ] テスト実装完了
- [ ] ドキュメント更新完了

## 📚 参考資料
- todo.md (1269-1460行目): TODO-9詳細
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/43_resilience-in-agentic-ai-how-to-handle-failures-and-recover-gracefully-aaidc-week10-lesson4.md`
- OpenAI Pricing: https://openai.com/pricing

---

**作成日**: 2025-10-18
**最終更新**: 2025-10-18
**担当**: Claude Code
**ステータス**: 計画完了
