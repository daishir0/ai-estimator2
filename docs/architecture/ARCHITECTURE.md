# アーキテクチャドキュメント

## 📋 目次

1. [概要](#概要)
2. [システムアーキテクチャ](#システムアーキテクチャ)
3. [データフロー](#データフロー)
4. [シーケンス図](#シーケンス図)
5. [データモデル](#データモデル)
6. [ディレクトリ構造](#ディレクトリ構造)
7. [セキュリティアーキテクチャ](#セキュリティアーキテクチャ)
8. [レジリエンスアーキテクチャ](#レジリエンスアーキテクチャ)
9. [多言語アーキテクチャ](#多言語アーキテクチャ)
10. [パフォーマンス最適化](#パフォーマンス最適化)

---

## 概要

### アーキテクチャの設計原則

1. **シンプルさ**: 必要最小限のコンポーネントで構成
2. **拡張性**: 将来的なスケーリングに対応
3. **保守性**: 理解しやすく、修正しやすい構造
4. **セキュリティ**: 多層防御による安全性確保
5. **レジリエンス**: 障害に強い自動復旧機能

### 主要技術決定

| 技術選定 | 理由 |
|---------|------|
| **FastAPI** | 高速、型安全、自動API文書生成 |
| **SQLite** | シンプル、ファイルベース、依存関係なし |
| **Uvicorn** | 高速ASGI、非同期対応 |
| **Apache HTTPD** | 実績豊富、SSL/TLS対応、Basic認証 |
| **OpenAI API** | 高精度AI、コスト効率的（gpt-4o-mini） |
| **systemd** | 標準的なプロセス管理、自動再起動 |

---

## システムアーキテクチャ

### 全体構成図

```mermaid
graph TB
    subgraph "Internet"
        User[ユーザー<br/>Webブラウザ]
    end

    subgraph "EC2 Instance"
        subgraph "Apache HTTPD Layer"
            Apache[Apache HTTPD 2.4.62<br/>Port 443/80<br/>- SSL/TLS Termination<br/>- Basic Authentication<br/>- Reverse Proxy]
        end

        subgraph "Application Layer"
            SystemD[systemd<br/>estimator.service<br/>- Auto-restart<br/>- Log management]

            Uvicorn[Uvicorn ASGI Server<br/>127.0.0.1:8100<br/>- Async processing<br/>- Timeout: 120s]

            FastAPI[FastAPI Application<br/>Python 3.11<br/>- REST API<br/>- Multi-language ja/en]
        end

        subgraph "Service Layer"
            TaskSvc[TaskService<br/>タスク管理]
            QuestionSvc[QuestionService<br/>質問生成]
            EstimateSvc[EstimatorService<br/>見積り計算]
            ChatSvc[ChatService<br/>調整提案]
            SafetySvc[SafetyService<br/>安全性検証]
            InputSvc[InputService<br/>ファイル処理]
            ExportSvc[ExportService<br/>Excel出力]
        end

        subgraph "Data Layer"
            SQLite[(SQLite Database<br/>app.db<br/>- tasks<br/>- deliverables<br/>- qa_pairs<br/>- estimates<br/>- messages)]
        end
    end

    subgraph "External Services"
        OpenAI[OpenAI API<br/>OpenAI<br/>- Question generation<br/>- Estimate generation<br/>- Chat adjustment]
    end

    User -->|HTTPS| Apache
    Apache -->|HTTP| SystemD
    SystemD -->|Process| Uvicorn
    Uvicorn -->|ASGI| FastAPI

    FastAPI --> TaskSvc
    FastAPI --> QuestionSvc
    FastAPI --> EstimateSvc
    FastAPI --> ChatSvc
    FastAPI --> SafetySvc
    FastAPI --> InputSvc
    FastAPI --> ExportSvc

    TaskSvc --> SQLite
    QuestionSvc --> SQLite
    QuestionSvc --> OpenAI
    EstimateSvc --> SQLite
    EstimateSvc --> OpenAI
    ChatSvc --> SQLite
    ChatSvc --> OpenAI
    InputSvc --> SQLite
    ExportSvc --> SQLite
```

### レイヤー詳細

#### 1. フロントエンドレイヤー

**構成**:
- Vanilla JavaScript
- Chart.js (グラフ描画)
- HTML5/CSS3

**責務**:
- ユーザーインターフェース表示
- ユーザー入力の収集
- API呼び出し
- 結果の視覚化

#### 2. プロキシレイヤー (Apache HTTPD)

**責務**:
- SSL/TLS終端
- Basic認証
- リバースプロキシ
- HTTP→HTTPSリダイレクト

**設定**:
```apache
ProxyPass /api/ http://127.0.0.1:8100/api/ timeout=600
ProxyPass /static/ http://127.0.0.1:8100/static/ timeout=600
ProxyPass / http://127.0.0.1:8100/ui/ timeout=600
```

#### 3. アプリケーションレイヤー (FastAPI)

**責務**:
- REST APIエンドポイント提供
- リクエストバリデーション
- ビジネスロジック実行
- レスポンス生成

**主要エンドポイント**:
- `POST /api/v1/tasks` - タスク作成
- `GET /api/v1/tasks/{id}/questions` - 質問取得
- `POST /api/v1/tasks/{id}/answers` - 回答送信
- `GET /api/v1/tasks/{id}/result` - 結果取得
- `POST /api/v1/tasks/{id}/chat` - 調整リクエスト

#### 4. サービスレイヤー

**TaskService**:
- タスクライフサイクル管理
- 見積りプロセス全体の制御

**QuestionService**:
- AI質問生成
- OpenAI APIとの連携

**EstimatorService**:
- 見積り計算ロジック
- 工数・金額算出

**ChatService**:
- 調整提案生成
- AI対話制御

**SafetyService**:
- プロンプトインジェクション検出
- 不適切コンテンツフィルタリング

**InputService**:
- Excel/CSVパース
- データ抽出・バリデーション

**ExportService**:
- Excelファイル生成
- フォーマット整形

#### 5. データレイヤー (SQLite)

**責務**:
- データ永続化
- トランザクション管理
- クエリ実行

---

## データフロー

### タスク作成〜見積り生成フロー

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant UI as Web UI
    participant API as FastAPI
    participant Safety as SafetyService
    participant Input as InputService
    participant Task as TaskService
    participant Question as QuestionService
    participant Estimator as EstimatorService
    participant Export as ExportService
    participant DB as SQLite
    participant OpenAI as OpenAI API

    User->>UI: 1. 成果物入力<br/>(Excel/CSV/Webフォーム)
    UI->>API: POST /api/v1/tasks

    API->>Safety: 2. 安全性チェック
    Safety-->>API: OK

    API->>Input: 3. ファイル処理
    Input->>Input: Excel/CSVパース
    Input->>DB: 4. タスク作成
    DB-->>Input: task_id
    Input->>DB: 5. 成果物保存
    Input-->>API: task
    API-->>UI: TaskResponse

    UI->>API: 6. GET /tasks/{id}/questions
    API->>Question: 質問生成リクエスト
    Question->>DB: 成果物・要件取得
    DB-->>Question: deliverables, requirements

    Question->>OpenAI: 7. LLMプロンプト送信<br/>(質問生成)
    OpenAI-->>Question: 3つの質問

    Question->>DB: 8. 質問保存
    Question-->>API: questions
    API-->>UI: QuestionsResponse

    UI->>User: 9. 質問表示
    User->>UI: 10. 回答入力
    UI->>API: POST /tasks/{id}/answers

    API->>DB: 11. 回答保存
    API->>Task: 12. 見積り生成開始

    loop 各成果物
        Task->>Estimator: 見積り生成
        Estimator->>OpenAI: LLMプロンプト送信<br/>(見積り生成)
        OpenAI-->>Estimator: 工数・金額・根拠
        Estimator->>DB: 見積り保存
    end

    Task->>Estimator: 13. 合計計算
    Estimator->>Estimator: 小計・税額・総額計算

    Task->>Export: 14. Excel生成
    Export->>DB: データ取得
    DB-->>Export: estimates, qa_pairs
    Export->>Export: Excelファイル作成
    Export-->>Task: file_path

    Task->>DB: 15. 結果保存
    Task-->>API: success
    API-->>UI: AnswersResponse

    UI->>API: 16. GET /tasks/{id}/result
    API->>DB: 結果取得
    DB-->>API: estimates, totals
    API-->>UI: ResultResponse
    UI->>User: 17. 見積り表示
```

### チャット調整フロー

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant UI as Web UI
    participant API as FastAPI
    participant Safety as SafetyService
    participant Chat as ChatService
    participant DB as SQLite
    participant OpenAI as OpenAI API

    User->>UI: 1. 調整リクエスト入力<br/>("30万円安くして")
    UI->>API: POST /tasks/{id}/chat

    API->>Safety: 2. 安全性チェック
    Safety-->>API: OK

    API->>Chat: 3. 調整提案生成
    Chat->>DB: 現在の見積り取得
    DB-->>Chat: current_estimates

    Chat->>Chat: 4. 調整プロンプト生成<br/>(direction, amount)
    Chat->>OpenAI: 5. LLMプロンプト送信<br/>(調整提案)
    OpenAI-->>Chat: 3つの提案

    Chat->>DB: 6. メッセージ保存
    Chat-->>API: proposals
    API-->>UI: ChatResponse

    UI->>User: 7. 提案カード表示
    User->>UI: 8. 提案選択
    UI->>API: POST /tasks/{id}/apply

    API->>DB: 9. 見積り更新
    API->>DB: 10. Excel再生成
    API-->>UI: success
    UI->>User: 11. 更新完了
```

---

## シーケンス図

### タスク作成詳細シーケンス

```mermaid
sequenceDiagram
    participant Client as クライアント
    participant API as API Layer
    participant Safety as SafetyService
    participant Input as InputService
    participant Task as TaskService
    participant DB as Database

    Client->>API: POST /api/v1/tasks<br/>(file OR deliverables_json)

    alt ファイルアップロード
        API->>API: ファイルサイズチェック<br/>(< 10MB)
        API->>API: ファイル形式チェック<br/>(.xlsx, .xls, .csv)
    end

    API->>Safety: validate_and_reject()<br/>(system_requirements)

    alt Guardrailsチェック
        Safety->>Safety: プロンプトインジェクション検出
        Safety->>Safety: 不適切コンテンツ検出
        alt 検出された場合
            Safety-->>API: HTTPException(400)
            API-->>Client: Error Response
        end
    end

    alt ファイルの場合
        API->>Input: load_excel_data(file_path)
        Input->>Input: openpyxl/pandasでパース
        Input-->>API: deliverables_list
    else Webフォームの場合
        API->>API: JSON.parse(deliverables_json)
    end

    API->>Task: create_task(file_path, system_reqs)
    Task->>DB: INSERT INTO tasks
    DB-->>Task: task_id

    loop 各成果物
        Task->>DB: INSERT INTO deliverables
    end

    Task-->>API: TaskResponse
    API-->>Client: 200 OK + TaskResponse
```

### 見積り生成詳細シーケンス

```mermaid
sequenceDiagram
    participant API as API Layer
    participant Task as TaskService
    participant Question as QuestionService
    participant Estimator as EstimatorService
    participant Circuit as CircuitBreaker
    participant Retry as RetryLogic
    participant OpenAI as OpenAI API
    participant DB as Database

    API->>Task: process_task(task_id, answers)
    Task->>DB: UPDATE qa_pairs SET answer

    Task->>DB: SELECT deliverables
    DB-->>Task: deliverables_list

    loop 各成果物（並列実行）
        Task->>Estimator: estimate_deliverable()
        Estimator->>Circuit: check_state()

        alt CircuitBreaker CLOSED
            Circuit-->>Estimator: OK

            Estimator->>Retry: with_retry()
            loop 最大3回リトライ
                Retry->>OpenAI: create_completion()

                alt 成功
                    OpenAI-->>Retry: response
                    Retry-->>Estimator: result
                else タイムアウト/エラー
                    OpenAI-->>Retry: Error
                    Retry->>Retry: wait & retry
                end
            end

            alt 3回とも失敗
                Retry-->>Estimator: Error
                Estimator->>Circuit: record_failure()
                Circuit->>Circuit: increment_failure_count
            end

        else CircuitBreaker OPEN
            Circuit-->>Estimator: CircuitOpenError
            Estimator-->>Task: Fallback処理
        end

        Estimator->>DB: INSERT INTO estimates
    end

    Task->>Estimator: calculate_totals()
    Estimator-->>Task: subtotal, tax, total

    Task->>DB: UPDATE tasks SET status=completed
    Task-->>API: success
```

---

## データモデル

### ER図

```mermaid
erDiagram
    tasks ||--o{ deliverables : "has many"
    tasks ||--o{ qa_pairs : "has many"
    tasks ||--o{ messages : "has many"
    deliverables ||--o{ estimates : "has many"

    tasks {
        string id PK "UUID"
        string excel_file_path "アップロードファイルパス"
        text system_requirements "システム要件"
        string status "pending/processing/completed/failed"
        text error_message "エラーメッセージ"
        string result_file_path "出力Excelパス"
        datetime created_at
        datetime updated_at
    }

    deliverables {
        string id PK "UUID"
        string task_id FK "タスクID"
        string name "成果物名称"
        text description "説明"
        datetime created_at
    }

    qa_pairs {
        string id PK "UUID"
        string task_id FK "タスクID"
        text question "質問"
        text answer "回答"
        datetime created_at
    }

    estimates {
        string id PK "UUID"
        string deliverable_id FK "成果物ID"
        float estimated_days "予想工数(人日)"
        float estimated_cost "予想金額"
        json breakdown "工数内訳"
        text reasoning "根拠・備考"
        datetime created_at
    }

    messages {
        string id PK "UUID"
        string task_id FK "タスクID"
        string role "user/assistant"
        text content "メッセージ内容"
        datetime created_at
    }
```

### データモデル関連

```mermaid
classDiagram
    class Task {
        +String id
        +String excel_file_path
        +Text system_requirements
        +TaskStatus status
        +Text error_message
        +String result_file_path
        +DateTime created_at
        +DateTime updated_at
        +List~Deliverable~ deliverables
        +List~QAPair~ qa_pairs
        +List~Message~ messages
    }

    class Deliverable {
        +String id
        +String task_id
        +String name
        +Text description
        +DateTime created_at
        +Task task
        +List~Estimate~ estimates
    }

    class QAPair {
        +String id
        +String task_id
        +Text question
        +Text answer
        +DateTime created_at
        +Task task
    }

    class Estimate {
        +String id
        +String deliverable_id
        +Float estimated_days
        +Float estimated_cost
        +JSON breakdown
        +Text reasoning
        +DateTime created_at
        +Deliverable deliverable
    }

    class Message {
        +String id
        +String task_id
        +String role
        +Text content
        +DateTime created_at
        +Task task
    }

    class TaskStatus {
        <<enumeration>>
        PENDING
        PROCESSING
        COMPLETED
        FAILED
    }

    Task "1" --> "*" Deliverable
    Task "1" --> "*" QAPair
    Task "1" --> "*" Message
    Deliverable "1" --> "*" Estimate
    Task --> TaskStatus
```

---

## ディレクトリ構造

```
output3/backend/
├── app/
│   ├── main.py                    # FastAPIアプリケーション
│   │
│   ├── api/                       # APIエンドポイント
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── tasks.py           # タスク関連API
│   │
│   ├── models/                    # SQLAlchemyモデル
│   │   ├── __init__.py
│   │   ├── task.py               # Taskモデル
│   │   ├── deliverable.py        # Deliverableモデル
│   │   ├── qa_pair.py            # QAPairモデル
│   │   ├── estimate.py           # Estimateモデル
│   │   └── message.py            # Messageモデル
│   │
│   ├── schemas/                   # Pydanticスキーマ
│   │   ├── __init__.py
│   │   ├── task.py               # タスク関連スキーマ
│   │   ├── estimate.py           # 見積り関連スキーマ
│   │   ├── qa_pair.py            # QA関連スキーマ
│   │   └── chat.py               # チャット関連スキーマ
│   │
│   ├── services/                  # ビジネスロジック
│   │   ├── __init__.py
│   │   ├── task_service.py       # タスク管理サービス
│   │   ├── question_service.py   # 質問生成サービス
│   │   ├── estimator_service.py  # 見積り計算サービス
│   │   ├── chat_service.py       # チャット調整サービス
│   │   ├── safety_service.py     # 安全性検証サービス
│   │   ├── input_service.py      # ファイル入力サービス
│   │   └── export_service.py     # Excel出力サービス
│   │
│   ├── core/                      # 共通機能・設定
│   │   ├── __init__.py
│   │   ├── config.py             # 設定管理
│   │   └── i18n.py               # 多言語対応
│   │
│   ├── db/                        # データベース
│   │   ├── __init__.py
│   │   └── database.py           # DB接続・セッション管理
│   │
│   ├── prompts/                   # LLMプロンプト
│   │   ├── __init__.py
│   │   ├── question_prompts.py   # 質問生成プロンプト
│   │   ├── estimate_prompts.py   # 見積り生成プロンプト
│   │   └── chat_prompts.py       # チャット調整プロンプト
│   │
│   ├── middleware/                # ミドルウェア
│   │   ├── __init__.py
│   │   ├── circuit_breaker.py    # サーキットブレーカー
│   │   ├── loop_detector.py      # ループ検出
│   │   └── resource_limiter.py   # リソース制限
│   │
│   ├── utils/                     # ユーティリティ
│   │   ├── __init__.py
│   │   └── retry.py              # リトライロジック
│   │
│   ├── locales/                   # 多言語翻訳ファイル
│   │   ├── ja.json               # 日本語翻訳
│   │   └── en.json               # 英語翻訳
│   │
│   └── static/                    # 静的ファイル
│       ├── index.html            # メインUI
│       ├── styles.css            # スタイルシート
│       └── script.js             # クライアントサイドJS
│
├── tests/                         # テストコード
│   ├── __init__.py
│   ├── conftest.py               # pytestフィクスチャ
│   ├── unit/                     # ユニットテスト
│   │   ├── test_task_service.py
│   │   ├── test_estimator_service.py
│   │   └── test_safety_service.py
│   ├── integration/              # 統合テスト
│   │   ├── test_api_tasks.py
│   │   └── test_database.py
│   └── e2e/                      # E2Eテスト
│       └── test_full_workflow.py
│
├── .env                          # 環境変数
├── .env.sample                   # 環境変数サンプル
├── requirements.txt              # Python依存関係
├── pytest.ini                    # pytest設定
└── app.db                        # SQLiteデータベース
```

---

## セキュリティアーキテクチャ

### 多層防御

```mermaid
graph TB
    subgraph "Layer 1: ネットワーク"
        SSL[SSL/TLS暗号化<br/>Let's Encrypt]
        BasicAuth[Basic認証<br/>.htpasswd]
    end

    subgraph "Layer 2: アプリケーション"
        CORS[CORS制限<br/>許可オリジンのみ]
        FileSizeLimit[ファイルサイズ制限<br/>10MB]
        ResourceLimit[リソース制限<br/>同時リクエスト数]
    end

    subgraph "Layer 3: ビジネスロジック"
        Safety[SafetyService<br/>Guardrails]
        InputValidation[入力検証<br/>Pydantic]
        SQLInjection[SQLインジェクション対策<br/>SQLAlchemy ORM]
    end

    subgraph "Layer 4: データ"
        EnvVars[環境変数分離<br/>.env]
        FilePermission[ファイルパーミッション<br/>600]
        DBIsolation[データベース分離<br/>ユーザーごと]
    end

    SSL --> CORS
    BasicAuth --> FileSizeLimit
    CORS --> Safety
    FileSizeLimit --> InputValidation
    ResourceLimit --> SQLInjection
    Safety --> EnvVars
    InputValidation --> FilePermission
    SQLInjection --> DBIsolation
```

### Guardrails実装

```mermaid
graph LR
    Input[ユーザー入力] --> Safety[SafetyService]

    Safety --> PI[プロンプトインジェクション検出]
    Safety --> IC[不適切コンテンツ検出]
    Safety --> LL[長さ制限チェック]

    PI --> |検出| Reject[HTTPException 400]
    IC --> |検出| Reject
    LL --> |超過| Reject

    PI --> |安全| Process[処理続行]
    IC --> |安全| Process
    LL --> |安全| Process

    Process --> LLM[LLM API呼び出し]
```

**実装箇所**:
- `app/services/safety_service.py`
- `app/api/v1/tasks.py` (create_task, chat)

---

## レジリエンスアーキテクチャ

### CircuitBreaker パターン

```mermaid
stateDiagram-v2
    [*] --> CLOSED: 初期状態

    CLOSED --> OPEN: 連続5回失敗
    OPEN --> HALF_OPEN: 60秒経過
    HALF_OPEN --> CLOSED: 成功
    HALF_OPEN --> OPEN: 失敗

    CLOSED: CircuitBreaker CLOSED<br/>通常動作<br/>- リクエスト通過<br/>- 失敗カウント

    OPEN: CircuitBreaker OPEN<br/>即座に失敗<br/>- リクエストブロック<br/>- フォールバック実行

    HALF_OPEN: CircuitBreaker HALF_OPEN<br/>試験動作<br/>- 1リクエストのみ通過<br/>- 成功で復旧、失敗でOPEN
```

**設定**:
- 失敗閾値: 5回
- タイムアウト: 60秒
- ハーフオープン試行回数: 1回

**実装**: `app/middleware/circuit_breaker.py`

### Retry ロジック

```mermaid
graph TB
    Start[API呼び出し開始] --> Try1[1回目試行]

    Try1 --> |成功| Success[成功]
    Try1 --> |失敗| Wait1[1秒待機]

    Wait1 --> Try2[2回目試行]
    Try2 --> |成功| Success
    Try2 --> |失敗| Wait2[2秒待機<br/>Exponential Backoff]

    Wait2 --> Try3[3回目試行]
    Try3 --> |成功| Success
    Try3 --> |失敗| Failure[失敗<br/>CircuitBreakerへ記録]

    Success --> [*]
    Failure --> [*]
```

**設定**:
- 最大リトライ回数: 3回
- バックオフ戦略: Exponential (1秒, 2秒, 4秒)
- リトライ対象エラー: Timeout, RateLimitError, APIConnectionError

**実装**: `app/utils/retry.py`

### Loop Detector

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant LoopDetector
    participant Cache

    Client->>API: Request (prompt_hash)
    API->>LoopDetector: check_loop(task_id, prompt_hash)

    LoopDetector->>Cache: get(task_id)
    Cache-->>LoopDetector: history[]

    alt 同じprompt_hashが3回以上
        LoopDetector-->>API: LoopDetectedError
        API-->>Client: 400 Bad Request<br/>"ループが検出されました"
    else 正常
        LoopDetector->>Cache: append(prompt_hash)
        LoopDetector-->>API: OK
        API->>API: 処理続行
    end
```

**設定**:
- ループ検出閾値: 3回
- キャッシュ保持時間: 1時間

**実装**: `app/middleware/loop_detector.py`

### Resource Limiter

```mermaid
graph TB
    Request[リクエスト受信] --> Check[同時実行数チェック]

    Check --> |< MAX_CONCURRENT| Acquire[セマフォ取得]
    Check --> |>= MAX_CONCURRENT| Wait[キューで待機<br/>最大30秒]

    Wait --> |タイムアウト| Reject[503 Service Unavailable]
    Wait --> |取得可能| Acquire

    Acquire --> Process[処理実行]
    Process --> Release[セマフォ解放]
    Release --> Response[レスポンス返却]

    Reject --> [*]
    Response --> [*]
```

**設定**:
- 最大同時実行数: 5
- タイムアウト: 30秒

**実装**: `app/middleware/resource_limiter.py`

---

## 多言語アーキテクチャ

### 翻訳システム

```mermaid
graph TB
    subgraph "環境変数"
        ENV[.env<br/>LANGUAGE=ja/en]
    end

    subgraph "翻訳ファイル"
        JA[locales/ja.json<br/>日本語翻訳]
        EN[locales/en.json<br/>英語翻訳]
    end

    subgraph "アプリケーション"
        I18N[i18n.py<br/>翻訳エンジン]
        Services[Services<br/>ビジネスロジック]
        Prompts[Prompts<br/>LLMプロンプト]
        API[API Endpoints]
    end

    subgraph "出力"
        UI[UIテキスト]
        Excel[Excel出力]
        LLMOutput[LLM生成コンテンツ]
    end

    ENV --> I18N
    JA --> I18N
    EN --> I18N

    I18N --> Services
    I18N --> Prompts
    I18N --> API

    Services --> UI
    Prompts --> LLMOutput
    API --> Excel
```

**翻訳関数**:
```python
from app.core.i18n import t

# UIテキスト
title = t('ui.app_title')

# LLMプロンプト
language_instruction = t('prompts.language_instruction')

# Excel列名
column_name = t('excel.column_deliverable_name')
```

**翻訳ファイル構造**:
```json
{
  "ui": { "app_title": "..." },
  "prompts": { "language_instruction": "..." },
  "excel": { "column_deliverable_name": "..." },
  "messages": { "error_message": "..." }
}
```

---

## パフォーマンス最適化

### 並列処理

```mermaid
graph TB
    Start[見積り開始] --> Split[成果物分割]

    Split --> P1[成果物1<br/>LLM API呼び出し]
    Split --> P2[成果物2<br/>LLM API呼び出し]
    Split --> P3[成果物3<br/>LLM API呼び出し]
    Split --> PN[成果物N<br/>LLM API呼び出し]

    P1 --> |ThreadPoolExecutor| Join[結果統合]
    P2 --> |ThreadPoolExecutor| Join
    P3 --> |ThreadPoolExecutor| Join
    PN --> |ThreadPoolExecutor| Join

    Join --> Calculate[合計金額計算]
    Calculate --> Excel[Excel生成]
    Excel --> End[完了]
```

**実装**: `app/services/task_service.py`
- `ThreadPoolExecutor` で並列実行
- 最大ワーカー数: 10

### キャッシング

```mermaid
graph LR
    Request[リクエスト] --> CheckCache{キャッシュ確認}

    CheckCache --> |HIT| CacheReturn[キャッシュ返却]
    CheckCache --> |MISS| Process[処理実行]

    Process --> LLM[LLM API呼び出し]
    LLM --> SaveCache[キャッシュ保存]
    SaveCache --> Return[結果返却]

    CacheReturn --> [*]
    Return --> [*]
```

**キャッシュ対象**:
- 質問生成結果（タスクIDごと）
- 調整提案（タスクID + リクエストハッシュ）

**TTL**: 1時間

---

## 参考資料

- [DEPLOYMENT.md](../deployment/DEPLOYMENT.md) - デプロイメントガイド
- [DEVELOPER_GUIDE.md](../development/DEVELOPER_GUIDE.md) - 開発者ガイド
- [API_REFERENCE.md](../development/API_REFERENCE.md) - APIリファレンス
- [SECURITY_CHECKLIST.md](../security/SECURITY_CHECKLIST.md) - セキュリティチェックリスト

---

**最終更新**: 2025-10-21
**作成者**: Claude Code
**バージョン**: 1.0
