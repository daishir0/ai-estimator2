# Module 3 最低限達成TODO（必須項目のみ）

**目標**: ReadyTensor Module 3認定取得（80%以上）
**推定所要時間**: 2-3週間
**最終期限**: 次回提出締切（2025年11月3日または12月1日）

---

## Week 9: テスト・安全・セキュリティ

### TODO-1: pytestテストスイート実装 ✅ 必須

**優先度**: 🔴 最高（Module 3の最重要要件）
**所要時間**: 3-5日

#### 具体的な対応内容

1. **テスト環境セットアップ**
   ```bash
   # tests/ディレクトリ構造作成
   mkdir -p tests/{unit,integration,e2e}
   touch tests/__init__.py
   touch tests/conftest.py
   ```

2. **conftest.py作成** - 共通フィクスチャ定義
   ```python
   # tests/conftest.py
   import pytest
   from fastapi.testclient import TestClient
   from app.main import app
   from app.db.database import get_db, Base, engine

   @pytest.fixture
   def client():
       # テスト用DBセットアップ
       Base.metadata.create_all(bind=engine)
       yield TestClient(app)
       # クリーンアップ
       Base.metadata.drop_all(bind=engine)

   @pytest.fixture
   def mock_openai(monkeypatch):
       # OpenAI APIのモック
       pass
   ```

3. **単体テスト作成** (`tests/unit/`)
   - `test_input_service.py`: 入力サービスのテスト
   - `test_question_service.py`: 質問生成のテスト
   - `test_estimator_service.py`: 見積り計算のテスト
   - `test_models.py`: データモデルのテスト

   ```python
   # tests/unit/test_estimator_service.py
   def test_estimate_calculation():
       # 見積り計算ロジックの検証
       assert result.total_days > 0
       assert result.total_cost > 0

   def test_estimate_breakdown():
       # 工数内訳の検証（要件定義、設計、実装、テスト、ドキュメント）
       assert breakdown.requirements > 0
       assert breakdown.design > 0
   ```

4. **統合テスト作成** (`tests/integration/`)
   - `test_api_endpoints.py`: APIエンドポイントのテスト

   ```python
   # tests/integration/test_api_endpoints.py
   def test_create_task(client):
       response = client.post("/api/v1/tasks", json={...})
       assert response.status_code == 200

   def test_full_workflow(client, mock_openai):
       # タスク作成→質問取得→回答送信→結果取得の一連の流れ
       pass
   ```

5. **E2Eテスト作成** (`tests/e2e/`)
   - `test_end_to_end.py`: ユーザーシナリオテスト

   ```python
   # tests/e2e/test_end_to_end.py
   def test_excel_upload_to_result(client):
       # Excelアップロード→見積り完了までの全体フロー
       pass
   ```

6. **LLM出力検証テスト**
   ```python
   # tests/unit/test_llm_outputs.py
   def test_question_response_schema():
       # スキーマ検証: 必須フィールド存在確認
       assert "questions" in response
       assert len(response["questions"]) == 3

   def test_estimate_response_relevance():
       # 関連性検証: 見積りに成果物名が含まれるか
       assert deliverable_name in estimate.reasoning

   def test_estimate_response_keywords():
       # キーワード検証: "人日"、"円"などのキーワード存在確認
       assert "人日" in estimate.breakdown

   def test_safety_check():
       # 安全性検証: 不適切な内容が含まれないか
       assert not contains_inappropriate_content(response)
   ```

7. **性能テスト作成**
   ```python
   # tests/performance/test_performance.py
   import time

   def test_response_time(client):
       start = time.time()
       response = client.post("/api/v1/tasks", json={...})
       elapsed = time.time() - start
       assert elapsed < 30.0  # 30秒以内
   ```

8. **pytest設定ファイル作成**
   ```ini
   # pytest.ini
   [pytest]
   testpaths = tests
   python_files = test_*.py
   python_functions = test_*
   markers =
       unit: Unit tests
       integration: Integration tests
       e2e: End-to-end tests
       performance: Performance tests
   ```

9. **テスト実行とレポート生成**
   ```bash
   # 全テスト実行
   pytest tests/ -v --cov=app --cov-report=html

   # マーカー別実行
   pytest -m unit
   pytest -m integration
   ```

#### 参照ドキュメント
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/32_getting-started-with-pytest-your-agentic-testing-toolkit-aaidc-week9-lesson-2a.md`
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/33_testing-agentic-ai-applications-how-to-use-pytest-for-llm-based-workflows-aaidc-week9-lesson-2b.md`
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/31_production-testing-for-agentic-ai-systems-what-developers-need-to-know-aaidc-week9-lesson1.md`

---

### TODO-2: Guardrails実装（ランタイム安全） ✅ 必須

**優先度**: 🔴 最高
**所要時間**: 2-3日

#### 具体的な対応内容

1. **Guardrailsライブラリインストール**
   ```bash
   # requirements.txtに追加
   guardrails-ai==0.4.0
   ```

2. **基本バリデータ実装**
   ```python
   # app/services/guardrails_service.py
   from guardrails import Guard
   from guardrails.validators import (
       ToxicLanguage,
       DetectPII,
       ValidLength,
   )

   class GuardrailsService:
       def __init__(self):
           self.input_guard = Guard().use_many(
               ToxicLanguage(threshold=0.8, on_fail="exception"),
               DetectPII(pii_entities=["EMAIL", "PHONE"], on_fail="fix"),
               ValidLength(min=1, max=10000, on_fail="exception")
           )

       def validate_input(self, text: str) -> str:
           """入力検証"""
           try:
               validated = self.input_guard.validate(text)
               return validated.validated_output
           except Exception as e:
               raise ValueError(f"Input validation failed: {e}")

       def validate_output(self, text: str) -> str:
           """出力検証"""
           # 同様の検証
           pass
   ```

3. **プロンプトインジェクション対策**
   ```python
   # app/services/security_service.py
   class SecurityService:
       INJECTION_PATTERNS = [
           r"ignore previous instructions",
           r"disregard.*rules",
           r"system prompt",
           r"[Ii]gnore.*above",
       ]

       def check_prompt_injection(self, text: str) -> bool:
           """プロンプトインジェクション検出"""
           for pattern in self.INJECTION_PATTERNS:
               if re.search(pattern, text, re.IGNORECASE):
                   return True
           return False
   ```

4. **APIエンドポイントへの組み込み**
   ```python
   # app/api/v1/tasks.py
   from app.services.guardrails_service import GuardrailsService

   guardrails = GuardrailsService()

   @router.post("/tasks/{task_id}/answers")
   async def submit_answers(task_id: int, answers: dict):
       # 入力検証
       for answer in answers.values():
           validated_answer = guardrails.validate_input(answer)

       # 処理...

       # 出力検証
       result = guardrails.validate_output(response)
       return result
   ```

5. **カスタムバリデータ作成**
   ```python
   # app/validators/custom_validators.py
   from guardrails.validators import Validator, register_validator

   @register_validator(name="valid_deliverable", data_type="string")
   class ValidDeliverable(Validator):
       def validate(self, value, metadata):
           # 成果物名の妥当性チェック
           if len(value) < 3:
               raise ValueError("Deliverable name too short")
           return value
   ```

#### 参照ドキュメント
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/36_guardrails-in-action-runtime-safety-and-output-validation-for-agentic-ai-aaidc-week9-lesson5.md`
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/34_autonomy-meets-attack-securing-agentic-ai-from-real-world-exploits-aaidc-week9-lesson3.md`

---

### TODO-3: セキュリティリスク対応（OWASP LLM Top 10） ✅ 必須

**優先度**: 🔴 最高
**所要時間**: 1-2日

#### 具体的な対応内容

1. **セキュリティリスク登録票作成**
   ```markdown
   # docs/security/OWASP_LLM_RISK_REGISTER.md

   ## LLM01: プロンプトインジェクション
   - **リスク**: ユーザー入力による不正な指示注入
   - **対策**: 入力サニタイゼーション、パターンマッチング検出
   - **実装場所**: app/services/security_service.py
   - **状態**: 実装済み

   ## LLM02: 安全でない出力処理
   - **リスク**: 生成されたコンテンツの直接実行
   - **対策**: 出力のサニタイゼーション、エスケープ処理
   - **実装場所**: app/services/guardrails_service.py
   - **状態**: 実装済み

   ## LLM03: 訓練データポイズニング
   - **リスク**: N/A（外部API使用のため）
   - **対策**: 信頼できるAPIプロバイダー使用

   ## LLM04: モデルサービス拒否
   - **リスク**: 過度なAPI呼び出しによるコスト増
   - **対策**: レート制限、タイムアウト設定
   - **実装場所**: app/core/rate_limiter.py
   - **状態**: TODO-9で実装予定

   ## LLM06: 機密情報漏洩
   - **リスク**: PII情報の誤出力
   - **対策**: PII検出、マスキング
   - **実装場所**: app/services/guardrails_service.py
   - **状態**: 実装済み

   ## LLM07: 安全でないプラグイン設計
   - **リスク**: N/A（プラグインなし）

   ## LLM08: 過度な権限
   - **リスク**: N/A（ツール呼び出しなし）

   ## LLM09: 過度な依存
   - **リスク**: OpenAI API障害時の完全停止
   - **対策**: エラーハンドリング、フォールバック
   - **実装場所**: app/services/estimator_service.py
   - **状態**: TODO-4で実装予定

   ## LLM10: モデル盗難
   - **リスク**: N/A（外部API使用のため）
   ```

2. **セキュリティチェックリスト作成**
   ```markdown
   # docs/security/SECURITY_CHECKLIST.md

   - [x] APIキーは環境変数で管理
   - [x] .gitignoreに.envファイル追加済み
   - [x] 入力バリデーション実装
   - [x] プロンプトインジェクション対策実装
   - [x] PII検出実装
   - [ ] レート制限実装（TODO-9）
   - [ ] コスト上限設定（TODO-9）
   - [x] CORS設定済み
   - [x] HTTPSのみ許可（本番環境）
   ```

#### 参照ドキュメント
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/34_autonomy-meets-attack-securing-agentic-ai-from-real-world-exploits-aaidc-week9-lesson3.md`

---

### TODO-4: 安全ポリシー・拒否方針策定 ✅ 必須

**優先度**: 🔴 最高
**所要時間**: 1日

#### 具体的な対応内容

1. **安全ポリシー文書作成**
   ```markdown
   # docs/safety/SAFETY_POLICY.md

   ## 安全規約

   ### 1. 禁止事項
   - 違法、有害、脅迫的、虐待的、嫌がらせ的なコンテンツの生成
   - 差別的、中傷的な内容の生成
   - 個人情報（PII）の不正な取得・利用
   - 不適切な金額操作の示唆

   ### 2. 拒否基準
   システムは以下の場合、処理を拒否します：
   - 毒性の高い言語が検出された場合（閾値: 0.8以上）
   - プロンプトインジェクションパターンが検出された場合
   - 入力長が制限を超える場合（10,000文字以上）
   - 不正な形式のデータが送信された場合

   ### 3. エスカレーション
   - 拒否された場合、ユーザーに明確なエラーメッセージを返す
   - 繰り返し違反が検出された場合、管理者に通知
   - ログに記録し、後続分析に使用
   ```

2. **システムプロンプトへの組み込み**
   ```python
   # app/prompts/system_prompts.py

   SAFETY_GUIDELINES = """
   ## 安全ガイドライン

   以下の原則に従ってください：
   1. 正確で誠実な見積りを提供する
   2. 不確実性がある場合は明示する
   3. 不適切または違法な要求には応じない
   4. 個人情報を含まない
   5. 専門的で中立的なトーンを維持する

   禁止事項：
   - 根拠のない金額の提示
   - 個人情報の要求
   - 差別的または攻撃的な言葉の使用
   """

   def get_system_prompt() -> str:
       return f"""
       あなたはプロジェクト見積りの専門家です。

       {SAFETY_GUIDELINES}

       ユーザーの要求に基づいて、正確で詳細な見積りを提供してください。
       """
   ```

3. **拒否ハンドラー実装**
   ```python
   # app/services/safety_service.py

   class SafetyService:
       def check_safety(self, content: str) -> tuple[bool, str]:
           """安全性チェック"""
           # 毒性チェック
           if self.is_toxic(content):
               return False, "不適切な内容が検出されました"

           # プロンプトインジェクションチェック
           if self.is_injection(content):
               return False, "不正な入力が検出されました"

           return True, "OK"

       def handle_rejection(self, reason: str):
           """拒否時の処理"""
           # ログ記録
           logger.warning(f"Safety rejection: {reason}")
           # ユーザー通知
           raise HTTPException(
               status_code=400,
               detail=f"リクエストが拒否されました: {reason}"
           )
   ```

#### 参照ドキュメント
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/35_ai-that-doesnt-harm-principles-of-safety-and-alignment-aaidc-week9-lesson4.md`

---

## Week 10: パッケージング・レジリエンス

### TODO-5: レジリエンス実装 ✅ 必須

**優先度**: 🔴 最高
**所要時間**: 2-3日

#### 具体的な対応内容

1. **タイムアウト設定**
   ```python
   # app/core/config.py
   class Settings(BaseSettings):
       OPENAI_TIMEOUT: int = 30  # 30秒
       OPENAI_MAX_RETRIES: int = 3
       OPENAI_RETRY_DELAY: int = 2  # 初期遅延2秒
   ```

2. **指数バックオフ付き再試行**
   ```python
   # app/services/retry_service.py
   import time
   from functools import wraps

   def retry_with_backoff(max_retries=3, initial_delay=2):
       def decorator(func):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               for attempt in range(max_retries):
                   try:
                       return await func(*args, **kwargs)
                   except Exception as e:
                       if attempt == max_retries - 1:
                           raise
                       delay = initial_delay * (2 ** attempt)
                       logger.warning(f"Retry {attempt+1}/{max_retries} after {delay}s: {e}")
                       time.sleep(delay)
               return None
           return wrapper
       return decorator
   ```

3. **OpenAI API呼び出しへの適用**
   ```python
   # app/services/estimator_service.py
   from app.services.retry_service import retry_with_backoff

   class EstimatorService:
       @retry_with_backoff(max_retries=3, initial_delay=2)
       async def call_openai(self, prompt: str) -> str:
           try:
               response = await self.client.chat.completions.create(
                   model="gpt-4o-mini",
                   messages=[{"role": "user", "content": prompt}],
                   timeout=settings.OPENAI_TIMEOUT
               )
               return response.choices[0].message.content
           except TimeoutError:
               logger.error("OpenAI API timeout")
               raise
           except Exception as e:
               logger.error(f"OpenAI API error: {e}")
               raise
   ```

4. **サーキットブレーカー実装**
   ```python
   # app/services/circuit_breaker.py
   from datetime import datetime, timedelta

   class CircuitBreaker:
       def __init__(self, failure_threshold=5, timeout=60):
           self.failure_threshold = failure_threshold
           self.timeout = timeout
           self.failures = 0
           self.last_failure_time = None
           self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

       def call(self, func, *args, **kwargs):
           if self.state == "OPEN":
               if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                   self.state = "HALF_OPEN"
               else:
                   raise Exception("Circuit breaker is OPEN")

           try:
               result = func(*args, **kwargs)
               self.on_success()
               return result
           except Exception as e:
               self.on_failure()
               raise

       def on_success(self):
           self.failures = 0
           self.state = "CLOSED"

       def on_failure(self):
           self.failures += 1
           self.last_failure_time = datetime.now()
           if self.failures >= self.failure_threshold:
               self.state = "OPEN"
   ```

5. **フォールバック戦略**
   ```python
   # app/services/estimator_service.py

   class EstimatorService:
       async def estimate_with_fallback(self, deliverables):
           try:
               # 通常のAI見積り
               return await self.estimate_with_ai(deliverables)
           except Exception as e:
               logger.warning(f"AI estimation failed, using fallback: {e}")
               # フォールバック: 簡易計算
               return self.estimate_with_simple_calculation(deliverables)

       def estimate_with_simple_calculation(self, deliverables):
           """フォールバック用の簡易見積り計算"""
           # 成果物数 × 平均工数で概算
           avg_days_per_deliverable = 5
           total_days = len(deliverables) * avg_days_per_deliverable
           return {
               "total_days": total_days,
               "total_cost": total_days * settings.UNIT_PRICE_PER_DAY,
               "note": "AI見積りが利用できないため、簡易計算を使用しています"
           }
   ```

6. **ループ検出**
   ```python
   # app/services/loop_detector.py

   class LoopDetector:
       def __init__(self, max_iterations=10):
           self.max_iterations = max_iterations
           self.iteration_count = 0

       def check(self):
           self.iteration_count += 1
           if self.iteration_count > self.max_iterations:
               raise Exception("Maximum iterations exceeded")

       def reset(self):
           self.iteration_count = 0
   ```

7. **リソース制限**
   ```python
   # app/middleware/resource_limiter.py
   from fastapi import Request
   from starlette.middleware.base import BaseHTTPMiddleware

   class ResourceLimiter(BaseHTTPMiddleware):
       async def dispatch(self, request: Request, call_next):
           # リクエストサイズチェック
           content_length = request.headers.get("content-length")
           if content_length and int(content_length) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
               return JSONResponse(
                   status_code=413,
                   content={"detail": "File too large"}
               )

           response = await call_next(request)
           return response
   ```

#### 参照ドキュメント
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/43_resilience-in-agentic-ai-how-to-handle-failures-and-recover-gracefully-aaidc-week10-lesson4.md`

---

### TODO-6: 引継ぎドキュメント作成 ✅ 必須

**優先度**: 🔴 最高
**所要時間**: 2-3日

#### 具体的な対応内容

1. **デプロイメント文書作成**
   ```markdown
   # docs/deployment/DEPLOYMENT.md

   ## インフラ構成

   ### アーキテクチャ図
   ```
   [ユーザー] → [Nginx/Apache] → [FastAPI (uvicorn)] → [SQLite DB]
                                  ↓
                              [OpenAI API]
   ```

   ### 環境変数

   | 変数名 | 説明 | 必須 | デフォルト | 例 |
   |--------|------|------|-----------|-----|
   | OPENAI_API_KEY | OpenAI APIキー | ✅ | - | sk-xxx |
   | DATABASE_URL | データベース接続URL | ✅ | sqlite:///./app.db | - |
   | CORS_ORIGINS | CORS許可オリジン | ✅ | localhost | https://example.com |
   | UPLOAD_DIR | アップロードディレクトリ | ⭕ | ./uploads | - |
   | MAX_UPLOAD_SIZE_MB | 最大アップロードサイズ | ⭕ | 10 | - |
   | UNIT_PRICE_PER_DAY | 1人日単価 | ⭕ | 40000 | - |

   ### 秘密管理

   1. **ローカル開発**
      - `.env`ファイルに記載
      - `.gitignore`で除外済み

   2. **本番環境**
      - 環境変数として設定
      - systemdサービスファイルで管理
      ```ini
      [Service]
      EnvironmentFile=/etc/estimator/.env
      ```

   ### 起動・停止手順

   #### 開発環境
   ```bash
   # 起動
   cd backend
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

   # 停止
   Ctrl + C
   ```

   #### 本番環境（systemd）
   ```bash
   # 起動
   sudo systemctl start estimator.service

   # 停止
   sudo systemctl stop estimator.service

   # 再起動
   sudo systemctl restart estimator.service

   # ステータス確認
   sudo systemctl status estimator.service
   ```

   ### スケーリング戦略

   - **垂直スケーリング**: EC2インスタンスタイプを大きくする
   - **水平スケーリング**: ロードバランサー + 複数インスタンス（将来対応）
   - **データベース**: SQLiteからPostgreSQLへ移行を検討（規模拡大時）

   ### コスト管理

   - OpenAI API使用量監視（月次）
   - レート制限設定（TODO-9で実装）
   - ログローテーション設定

   ### 運用Runbook

   #### 障害対応
   1. ヘルスチェック確認: `curl http://localhost:8000/health`
   2. ログ確認: `journalctl -u estimator.service -f`
   3. 再起動: `sudo systemctl restart estimator.service`
   4. OpenAI API状態確認: https://status.openai.com/

   #### 定期メンテナンス
   - 週次: ログ確認
   - 月次: API使用量確認
   - 四半期: セキュリティアップデート適用
   ```

2. **プロジェクト文書作成**
   ```markdown
   # docs/PROJECT.md

   ## プロジェクト概要

   ### 目的
   AI技術を活用して、プロジェクト見積り作業を自動化・効率化する

   ### スコープ
   - 成果物ベースの見積り自動生成
   - AI質問による精緻化
   - 見積り調整機能
   - Excel出力

   ### アーキテクチャ図

   #### システム構成図
   ```
   ┌─────────────────┐
   │  Web UI         │
   │ (Static Files)  │
   └────────┬────────┘
            │ HTTP
   ┌────────▼────────┐
   │   FastAPI       │
   │  (Backend API)  │
   ├─────────────────┤
   │ ・Tasks API     │
   │ ・Questions API │
   │ ・Estimates API │
   │ ・Chat API      │
   └────┬──────┬─────┘
        │      │
        │      └──────────┐
   ┌────▼────┐      ┌────▼────┐
   │ SQLite  │      │ OpenAI  │
   │   DB    │      │   API   │
   └─────────┘      └─────────┘
   ```

   #### データフロー図
   ```
   1. ファイルアップロード/入力
      ↓
   2. 成果物データ保存（DB）
      ↓
   3. AI質問生成（OpenAI API）
      ↓
   4. 質問回答収集
      ↓
   5. 見積り計算（OpenAI API）
      ↓
   6. 結果表示・Excel出力
   ```

   ### 構成要素

   #### バックエンド
   - **FastAPI**: REST APIフレームワーク
   - **SQLAlchemy**: ORM
   - **OpenAI Client**: AI統合
   - **openpyxl**: Excel処理

   #### データモデル
   - `Task`: 見積りタスク
   - `Deliverable`: 成果物
   - `QAPair`: 質問と回答
   - `Estimate`: 見積り結果
   - `Message`: チャット履歴

   ### 依存関係

   - Python 3.11+
   - FastAPI 0.104+
   - SQLAlchemy 2.0+
   - OpenAI API 2.3+
   - pytest 7.4+ (開発)
   - guardrails-ai 0.4+ (セキュリティ)

   ### セットアップ手順

   1. リポジトリクローン
   2. 仮想環境作成・アクティベート
   3. 依存関係インストール
   4. 環境変数設定
   5. データベース初期化（自動）
   6. サーバー起動

   詳細は README.md 参照

   ### 操作方法

   #### 基本フロー
   1. Web UIにアクセス: http://localhost:8000/ui
   2. 入力方式選択（Excel/CSV/Webフォーム）
   3. 成果物データ入力
   4. AI質問に回答
   5. 見積り結果確認
   6. 必要に応じて調整
   7. Excelダウンロード

   #### API使用例
   ```bash
   # タスク作成
   curl -X POST http://localhost:8000/api/v1/tasks \
     -H "Content-Type: application/json" \
     -d '{"deliverables": [...]}'

   # 質問取得
   curl http://localhost:8000/api/v1/tasks/1/questions

   # 回答送信
   curl -X POST http://localhost:8000/api/v1/tasks/1/answers \
     -H "Content-Type: application/json" \
     -d '{"answers": {...}}'
   ```
   ```

3. **リスク・コンプライアンス文書作成**
   ```markdown
   # docs/RISK_COMPLIANCE.md

   ## 安全方針

   詳細は `docs/safety/SAFETY_POLICY.md` を参照

   ## 評価方法

   ### テスト評価
   - 単体テスト: カバレッジ80%以上
   - 統合テスト: 主要APIエンドポイント全て
   - E2Eテスト: ユーザーシナリオ3パターン以上

   ### セキュリティ評価
   - OWASP LLM Top 10対応状況確認
   - Guardrails検証率: 90%以上
   - プロンプトインジェクション検出率: 95%以上

   ### 安全性評価
   - 毒性コンテンツ検出: 閾値0.8以上で拒否
   - PII検出: 主要エンティティ（EMAIL, PHONE）カバー

   ## Guardrails設定

   ### 入力バリデーション
   - ToxicLanguage: threshold=0.8
   - DetectPII: entities=["EMAIL", "PHONE"]
   - ValidLength: min=1, max=10000

   ### 出力バリデーション
   - 同上

   ## 既知の制約と対応

   ### 制約
   1. OpenAI API依存
      - 対応: エラーハンドリング、フォールバック、サーキットブレーカー

   2. SQLite性能制限
      - 対応: 将来的にPostgreSQLへ移行検討

   3. 単一サーバー構成
      - 対応: 負荷監視、スケーリング計画策定

   ### 既知の問題
   - [ ] 大量リクエスト時のレート制限未実装（TODO-9で対応）
   - [ ] 詳細な監視・ログ未実装（TODO-7で対応）
   ```

4. **変更履歴作成**
   ```markdown
   # CHANGELOG.md

   ## [0.2.0] - 2025-10-XX (Module 3対応)

   ### Added
   - pytestテストスイート（単体・統合・E2E・性能）
   - Guardrails入出力バリデーション
   - プロンプトインジェクション対策
   - レジリエンス機構（再試行、タイムアウト、サーキットブレーカー）
   - 構造化ログ
   - セキュリティリスク登録票
   - 安全ポリシー
   - 引継ぎドキュメント一式

   ### Changed
   - OpenAI API呼び出しにタイムアウト追加
   - エラーハンドリング強化

   ### Fixed
   - 大容量ファイルアップロード時のエラー処理

   ## [0.1.0] - 2025-10-17 (初版)

   ### Added
   - AI見積りシステム基本機能
   - Excel/CSV/Webフォーム入力
   - AI質問生成
   - 見積り計算・調整
   - 結果ダウンロード
   ```

#### 参照ドキュメント
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/44_deploying-agentic-ai-documentation-and-handoff-guide-for-llm-based-systems-aaidc-week10-lesson5.md`

---

## Week 11: 監視・可観測性・コンプライアンス

### TODO-7: 監視・可観測性実装（基本） ✅ 必須

**優先度**: 🔴 最高
**所要時間**: 2-3日

#### 具体的な対応内容

1. **構造化ログ実装**
   ```python
   # app/core/logging_config.py
   import logging
   import json
   from datetime import datetime

   class StructuredLogger:
       def __init__(self, name: str):
           self.logger = logging.getLogger(name)
           self.logger.setLevel(logging.INFO)

           # JSONハンドラー
           handler = logging.StreamHandler()
           handler.setFormatter(self.JSONFormatter())
           self.logger.addHandler(handler)

       class JSONFormatter(logging.Formatter):
           def format(self, record):
               log_data = {
                   "timestamp": datetime.utcnow().isoformat(),
                   "level": record.levelname,
                   "logger": record.name,
                   "message": record.getMessage(),
                   "module": record.module,
                   "function": record.funcName,
                   "line": record.lineno
               }
               if hasattr(record, "request_id"):
                   log_data["request_id"] = record.request_id
               if hasattr(record, "task_id"):
                   log_data["task_id"] = record.task_id
               return json.dumps(log_data)

   logger = StructuredLogger(__name__)
   ```

2. **リクエストIDトレース**
   ```python
   # app/middleware/request_id.py
   import uuid
   from starlette.middleware.base import BaseHTTPMiddleware

   class RequestIDMiddleware(BaseHTTPMiddleware):
       async def dispatch(self, request, call_next):
           request_id = str(uuid.uuid4())
           request.state.request_id = request_id

           response = await call_next(request)
           response.headers["X-Request-ID"] = request_id
           return response
   ```

3. **主要イベントのログ記録**
   ```python
   # app/services/estimator_service.py

   class EstimatorService:
       async def estimate(self, task_id: int, deliverables):
           logger.info(
               "Starting estimation",
               extra={
                   "task_id": task_id,
                   "deliverable_count": len(deliverables),
                   "request_id": request.state.request_id
               }
           )

           try:
               result = await self.call_openai(...)
               logger.info(
                   "Estimation completed",
                   extra={
                       "task_id": task_id,
                       "total_cost": result.total_cost,
                       "request_id": request.state.request_id
                   }
               )
               return result
           except Exception as e:
               logger.error(
                   "Estimation failed",
                   extra={
                       "task_id": task_id,
                       "error": str(e),
                       "request_id": request.state.request_id
                   }
               )
               raise
   ```

4. **基本メトリクス収集**
   ```python
   # app/core/metrics.py
   from collections import defaultdict
   from datetime import datetime

   class MetricsCollector:
       def __init__(self):
           self.metrics = defaultdict(list)

       def record_api_call(self, endpoint: str, duration: float, status: int):
           self.metrics["api_calls"].append({
               "endpoint": endpoint,
               "duration": duration,
               "status": status,
               "timestamp": datetime.utcnow().isoformat()
           })

       def record_openai_call(self, model: str, tokens: int, duration: float):
           self.metrics["openai_calls"].append({
               "model": model,
               "tokens": tokens,
               "duration": duration,
               "timestamp": datetime.utcnow().isoformat()
           })

       def get_summary(self):
           return {
               "total_api_calls": len(self.metrics["api_calls"]),
               "total_openai_calls": len(self.metrics["openai_calls"]),
               "avg_response_time": self._calculate_avg_response_time()
           }

   metrics = MetricsCollector()
   ```

5. **メトリクスエンドポイント**
   ```python
   # app/api/v1/metrics.py
   from app.core.metrics import metrics

   @router.get("/metrics")
   async def get_metrics():
       return metrics.get_summary()
   ```

6. **監視計画文書作成**
   ```markdown
   # docs/monitoring/MONITORING_PLAN.md

   ## 監視対象指標

   ### SLI (Service Level Indicators)
   1. **可用性**: アプリケーションの稼働率
      - 目標: 99.5%以上

   2. **レイテンシ**: API応答時間
      - 目標: P95 < 30秒

   3. **エラー率**: リクエスト失敗率
      - 目標: < 1%

   ### KPI (Key Performance Indicators)
   1. OpenAI API呼び出し成功率: > 98%
   2. 見積り生成完了率: > 95%
   3. 平均見積り生成時間: < 20秒

   ### SLO (Service Level Objectives)
   - 月間稼働率: 99.5%以上
   - 月間平均応答時間: 20秒以下
   - 月間エラー率: 1%以下

   ## 警戒閾値

   | メトリクス | 警告 | クリティカル |
   |-----------|------|-------------|
   | エラー率 | 2% | 5% |
   | 応答時間（P95） | 40秒 | 60秒 |
   | OpenAI API失敗率 | 5% | 10% |
   | CPU使用率 | 70% | 90% |
   | メモリ使用率 | 80% | 95% |

   ## 監視ツール

   - **ログ**: 構造化ログ（JSON形式）
   - **メトリクス**: カスタムメトリクスコレクター
   - **トレース**: リクエストID追跡

   ## ダッシュボード（将来実装）

   - リアルタイムメトリクス表示
   - エラーログ検索
   - API使用量グラフ
   ```

#### 参照ドキュメント
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/46_monitoring-and-observability-for-agentic-ai-production-best-practices-aaidc-week11-lesson1.md`
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/47_what-to-monitor-in-agentic-ai-detecting-failures-before-users-do-aaidc-week11-lesson1b.md`

---

### TODO-8: データプライバシー対応（基本） ✅ 必須

**優先度**: 🔴 最高
**所要時間**: 1-2日

#### 具体的な対応内容

1. **データプライバシーポリシー作成**
   ```markdown
   # docs/privacy/PRIVACY_POLICY.md

   ## データ収集・利用方針

   ### 収集するデータ
   1. **入力データ**
      - 成果物名称
      - 成果物説明
      - システム要件
      - 質問への回答

   2. **システムログ**
      - APIアクセスログ
      - エラーログ
      - パフォーマンスメトリクス

   ### データ利用目的
   - プロジェクト見積りの生成
   - サービス品質の向上
   - エラー分析と改善

   ### データ保管期間
   - 見積りデータ: 30日間（ユーザーによる削除可能）
   - システムログ: 90日間

   ### 第三者提供
   - OpenAI API: 見積り生成のため必要最小限のデータを送信
   - その他の第三者への提供なし

   ### ユーザーの権利
   - データアクセス権
   - データ削除権
   - データポータビリティ権

   ## GDPR対応

   ### 最小化原則
   - 必要最小限のデータのみ収集
   - 不要になったデータは速やかに削除

   ### 同意
   - サービス利用開始時にプライバシーポリシーへの同意取得
   - データ処理内容の明示

   ### 透明性
   - データ利用目的の明示
   - 第三者提供先の明示

   ### セキュリティ
   - 環境変数によるAPIキー管理
   - HTTPS通信（本番環境）
   - アクセスログ記録
   ```

2. **PII対策実装**
   ```python
   # app/services/privacy_service.py
   import re

   class PrivacyService:
       # PII検出パターン
       PII_PATTERNS = {
           "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
           "phone": r'\b\d{2,4}-\d{2,4}-\d{4}\b',
           "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
       }

       def detect_pii(self, text: str) -> dict:
           """PII検出"""
           detected = {}
           for pii_type, pattern in self.PII_PATTERNS.items():
               matches = re.findall(pattern, text)
               if matches:
                   detected[pii_type] = matches
           return detected

       def mask_pii(self, text: str) -> str:
           """PII マスキング"""
           for pii_type, pattern in self.PII_PATTERNS.items():
               text = re.sub(pattern, f"[{pii_type.upper()}_MASKED]", text)
           return text
   ```

3. **データ削除機能**
   ```python
   # app/api/v1/tasks.py

   @router.delete("/tasks/{task_id}")
   async def delete_task(task_id: int, db: Session = Depends(get_db)):
       """タスクとすべての関連データを削除"""
       task = db.query(Task).filter(Task.id == task_id).first()
       if not task:
           raise HTTPException(status_code=404, detail="Task not found")

       # 関連データ削除
       db.query(Deliverable).filter(Deliverable.task_id == task_id).delete()
       db.query(QAPair).filter(QAPair.task_id == task_id).delete()
       db.query(Estimate).filter(Estimate.task_id == task_id).delete()
       db.query(Message).filter(Message.task_id == task_id).delete()

       # タスク削除
       db.delete(task)
       db.commit()

       logger.info(f"Task {task_id} and all related data deleted")
       return {"message": "Task deleted successfully"}
   ```

4. **GDPR チェックリスト作成**
   ```markdown
   # docs/privacy/GDPR_CHECKLIST.md

   ## GDPR対応チェックリスト

   ### データ収集
   - [x] 最小化原則: 必要最小限のデータのみ収集
   - [x] 目的明示: データ利用目的を明確に記載
   - [x] 同意取得: ユーザーからの明示的同意取得（プライバシーポリシー）

   ### データ処理
   - [x] 透明性: データ処理内容の開示
   - [x] 第三者提供の明示: OpenAI API使用を明記
   - [x] PII検出: メールアドレス、電話番号の検出機能
   - [x] PII マスキング: 検出されたPIIのマスキング

   ### データ保管
   - [x] 保管期間設定: 30日間（見積りデータ）、90日間（ログ）
   - [ ] 暗号化: データベース暗号化（将来対応）
   - [x] アクセス制御: 環境変数によるAPIキー管理

   ### ユーザー権利
   - [x] アクセス権: タスクデータの取得API
   - [x] 削除権: タスク削除API
   - [ ] ポータビリティ: データエクスポート機能（将来対応）

   ### セキュリティ
   - [x] HTTPS通信（本番環境）
   - [x] アクセスログ記録
   - [x] エラーログからのPII除外

   ### 文書化
   - [x] プライバシーポリシー作成
   - [x] データ処理記録
   - [x] GDPR対応チェックリスト
   ```

#### 参照ドキュメント
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/50_data-privacy-in-agentic-ai-gdpr-hipaa-and-developer-best-practices-aaidc-week1-lesson2.md`

---

### TODO-9: コスト管理・レート制限 ✅ 必須

**優先度**: 🔴 最高
**所要時間**: 1日

#### 具体的な対応内容

1. **レート制限実装**
   ```python
   # app/core/rate_limiter.py
   from datetime import datetime, timedelta
   from collections import defaultdict

   class RateLimiter:
       def __init__(self, max_requests=100, window_seconds=3600):
           self.max_requests = max_requests
           self.window_seconds = window_seconds
           self.requests = defaultdict(list)

       def check_limit(self, client_id: str) -> bool:
           """レート制限チェック"""
           now = datetime.utcnow()
           window_start = now - timedelta(seconds=self.window_seconds)

           # 古いリクエストを削除
           self.requests[client_id] = [
               req_time for req_time in self.requests[client_id]
               if req_time > window_start
           ]

           # 制限チェック
           if len(self.requests[client_id]) >= self.max_requests:
               return False

           # リクエスト記録
           self.requests[client_id].append(now)
           return True

   rate_limiter = RateLimiter(max_requests=100, window_seconds=3600)
   ```

2. **ミドルウェア適用**
   ```python
   # app/middleware/rate_limit.py
   from fastapi import Request, HTTPException
   from starlette.middleware.base import BaseHTTPMiddleware
   from app.core.rate_limiter import rate_limiter

   class RateLimitMiddleware(BaseHTTPMiddleware):
       async def dispatch(self, request: Request, call_next):
           # クライアントID（IPアドレス）
           client_id = request.client.host

           if not rate_limiter.check_limit(client_id):
               raise HTTPException(
                   status_code=429,
                   detail="Too many requests. Please try again later."
               )

           response = await call_next(request)
           return response
   ```

3. **OpenAI APIコスト追跡**
   ```python
   # app/services/cost_tracker.py
   from datetime import datetime

   class CostTracker:
       # GPT-4o-mini pricing (2025年10月時点の推定値)
       PRICE_PER_1K_INPUT_TOKENS = 0.00015  # $0.15 per 1M tokens
       PRICE_PER_1K_OUTPUT_TOKENS = 0.0006  # $0.60 per 1M tokens

       def __init__(self):
           self.daily_cost = 0.0
           self.monthly_cost = 0.0
           self.last_reset = datetime.utcnow()

       def record_usage(self, input_tokens: int, output_tokens: int):
           """使用量記録とコスト計算"""
           cost = (
               (input_tokens / 1000) * self.PRICE_PER_1K_INPUT_TOKENS +
               (output_tokens / 1000) * self.PRICE_PER_1K_OUTPUT_TOKENS
           )

           self.daily_cost += cost
           self.monthly_cost += cost

           logger.info(
               "OpenAI API usage recorded",
               extra={
                   "input_tokens": input_tokens,
                   "output_tokens": output_tokens,
                   "cost_usd": cost,
                   "daily_cost_usd": self.daily_cost,
                   "monthly_cost_usd": self.monthly_cost
               }
           )

           # コスト上限チェック
           if self.monthly_cost > settings.MONTHLY_COST_LIMIT:
               logger.critical("Monthly cost limit exceeded!")
               raise Exception("Monthly OpenAI API cost limit exceeded")

       def reset_daily(self):
           self.daily_cost = 0.0

       def reset_monthly(self):
           self.monthly_cost = 0.0

   cost_tracker = CostTracker()
   ```

4. **設定ファイル更新**
   ```python
   # app/core/config.py
   class Settings(BaseSettings):
       # 既存の設定...

       # レート制限
       RATE_LIMIT_MAX_REQUESTS: int = 100
       RATE_LIMIT_WINDOW_SECONDS: int = 3600  # 1時間

       # コスト上限
       DAILY_COST_LIMIT: float = 10.0  # $10/日
       MONTHLY_COST_LIMIT: float = 200.0  # $200/月
   ```

5. **緊急停止手順文書**
   ```markdown
   # docs/operations/EMERGENCY_SHUTDOWN.md

   ## 緊急停止手順

   ### コスト超過時

   1. **即時停止**
      ```bash
      sudo systemctl stop estimator.service
      ```

   2. **ログ確認**
      ```bash
      journalctl -u estimator.service -n 100
      tail -f backend/logs/cost_tracker.log
      ```

   3. **コスト確認**
      - OpenAI ダッシュボード: https://platform.openai.com/usage
      - アプリケーションログ: `grep "monthly_cost" logs/*.log`

   4. **原因調査**
      - 異常なリクエスト数の確認
      - 不正アクセスの確認
      - レート制限の動作確認

   5. **対策実施**
      - レート制限の強化
      - コスト上限の再設定
      - 必要に応じてIPブロック

   6. **再起動**
      ```bash
      sudo systemctl start estimator.service
      ```

   ### 連絡先
   - システム管理者: admin@example.com
   - OpenAIサポート: https://help.openai.com/
   ```

6. **コスト管理ダッシュボード（簡易版）**
   ```python
   # app/api/v1/admin.py

   @router.get("/admin/costs")
   async def get_costs():
       """コスト状況取得（管理者用）"""
       return {
           "daily_cost_usd": cost_tracker.daily_cost,
           "monthly_cost_usd": cost_tracker.monthly_cost,
           "daily_limit_usd": settings.DAILY_COST_LIMIT,
           "monthly_limit_usd": settings.MONTHLY_COST_LIMIT,
           "daily_usage_percent": (cost_tracker.daily_cost / settings.DAILY_COST_LIMIT) * 100,
           "monthly_usage_percent": (cost_tracker.monthly_cost / settings.MONTHLY_COST_LIMIT) * 100
       }
   ```

#### 参照ドキュメント
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/43_resilience-in-agentic-ai-how-to-handle-failures-and-recover-gracefully-aaidc-week10-lesson4.md`

---

## オプション項目（除外）

以下は最低限達成には不要なため、除外します：

### ❌ Giskardスキャン
- **理由**: 推奨レベルで、80%達成には必須ではない
- **代替**: pytest + Guardrailsで品質担保

### ❌ Gradio/Streamlit UI
- **理由**: 既存の静的UIで代替可能
- **状態**: 既存UIで要件満たす

### ❌ LLM選定根拠文書（詳細）
- **理由**: 簡易版で十分（READMEに記載）
- **状態**: GPT-4o-mini使用理由は記載済み

### ❌ アーキテクチャ設計図（詳細）
- **理由**: 基本的な構成図で十分
- **状態**: docs/PROJECT.mdに基本図含む

### ❌ トラブルシューティング手順（詳細）
- **理由**: 基本的な運用Runbookで十分
- **状態**: docs/deployment/DEPLOYMENT.mdに基本手順含む

---

## 実施計画

### フェーズ1: テスト・セキュリティ基盤（Week 1）
- **Day 1-3**: TODO-1 pytestテストスイート実装
- **Day 4-5**: TODO-2 Guardrails実装
- **Day 6**: TODO-3 セキュリティリスク対応
- **Day 7**: TODO-4 安全ポリシー策定

### フェーズ2: レジリエンス・ドキュメント（Week 2）
- **Day 8-10**: TODO-5 レジリエンス実装
- **Day 11-13**: TODO-6 引継ぎドキュメント作成
- **Day 14**: レビュー・調整

### フェーズ3: 監視・コンプライアンス（Week 3）
- **Day 15-17**: TODO-7 監視・可観測性実装
- **Day 18-19**: TODO-8 データプライバシー対応
- **Day 20**: TODO-9 コスト管理・レート制限
- **Day 21**: 最終レビュー・調整

### 最終週: 検証・提出準備
- 全体テスト実行
- ドキュメントレビュー
- Publication作成
- 提出

---

## 成功基準

### 技術要件
- [x] pytestテスト実装（カバレッジ80%以上）
- [x] Guardrails導入
- [x] レジリエンス実装
- [x] 構造化ログ実装
- [x] セキュリティ対策実装

### ドキュメント要件
- [x] デプロイメント文書
- [x] プロジェクト文書
- [x] リスク・コンプライアンス文書
- [x] 変更履歴
- [x] セキュリティリスク登録票
- [x] 安全ポリシー
- [x] プライバシーポリシー

### 提出要件
- [x] Repository Rubric: 80%以上
- [x] Publication Rubric: 80%以上

---

## チェックリスト

実装が完了したら、各項目をチェック：

### Week 9
- [ ] TODO-1: pytestテストスイート実装完了
- [ ] TODO-2: Guardrails実装完了
- [ ] TODO-3: セキュリティリスク対応完了
- [ ] TODO-4: 安全ポリシー策定完了

### Week 10
- [ ] TODO-5: レジリエンス実装完了
- [ ] TODO-6: 引継ぎドキュメント作成完了

### Week 11
- [ ] TODO-7: 監視・可観測性実装完了
- [ ] TODO-8: データプライバシー対応完了
- [ ] TODO-9: コスト管理・レート制限完了

### 最終確認
- [ ] 全テスト成功（pytest実行）
- [ ] セキュリティチェック完了
- [ ] ドキュメント完成
- [ ] README更新
- [ ] Publication作成
- [ ] 提出準備完了

---

**作成日**: 2025-10-17
**最終更新**: 2025-10-17
**ステータス**: 未着手
