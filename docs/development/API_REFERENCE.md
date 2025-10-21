# API リファレンス

## 📋 目次

1. [概要](#概要)
2. [認証](#認証)
3. [エンドポイント一覧](#エンドポイント一覧)
4. [データモデル](#データモデル)
5. [エラーコード](#エラーコード)
6. [使用例](#使用例)

---

## 概要

### ベースURL

```
https://estimator.path-finder.jp/api/v1
```

**開発環境**:
```
http://localhost:8000/api/v1
```

### プロトコル

- **HTTPS**: 本番環境では必須
- **HTTP**: ローカル開発環境のみ

### リクエスト形式

- **Content-Type**: `application/json` または `multipart/form-data`（ファイルアップロード時）
- **エンコーディング**: UTF-8

### レスポンス形式

- **Content-Type**: `application/json`
- **エンコーディング**: UTF-8
- **日時形式**: ISO 8601 (`YYYY-MM-DDTHH:MM:SS`)

---

## 認証

### Basic認証

すべてのエンドポイントはBasic認証で保護されています（本番環境）。

**認証ヘッダー**:
```http
Authorization: Basic <base64(username:password)>
```

**例**:
```bash
curl -u username:password https://estimator.path-finder.jp/api/v1/tasks
```

### 開発環境

ローカル開発環境では認証不要です。

---

## エンドポイント一覧

### タスク管理

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/tasks` | タスク作成 |
| GET | `/tasks/{task_id}/questions` | 質問取得 |
| POST | `/tasks/{task_id}/answers` | 回答提出 |
| GET | `/tasks/{task_id}/status` | ステータス取得 |
| GET | `/tasks/{task_id}/result` | 結果取得 |
| GET | `/tasks/{task_id}/download` | Excel結果ダウンロード |

### チャット調整

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/tasks/{task_id}/chat` | チャット調整 |
| POST | `/tasks/{task_id}/apply` | 調整後見積り適用 |

### サンプルファイル

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/sample-input` | サンプルExcelダウンロード |
| GET | `/sample-input-csv` | サンプルCSVダウンロード |

### 多言語対応

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/translations` | 翻訳データ取得 |

---

## エンドポイント詳細

### 1. タスク作成

新しい見積りタスクを作成します。

**エンドポイント**:
```http
POST /api/v1/tasks
```

**リクエスト形式**: `multipart/form-data`

**パラメータ**:

| 名前 | 型 | 必須 | 説明 |
|------|-----|------|------|
| `file` | File | No | Excel/CSVファイル（成果物一覧） |
| `deliverables_json` | String | No | Webフォームからの成果物JSON配列 |
| `system_requirements` | String | No | システム要件（任意） |

**注意**: `file` または `deliverables_json` のいずれかを必須で指定してください。

**リクエスト例（ファイルアップロード）**:
```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks \
  -u username:password \
  -F "file=@input.xlsx" \
  -F "system_requirements=要件定義済み、開発期間3ヶ月"
```

**リクエスト例（Webフォーム）**:
```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks \
  -u username:password \
  -F "deliverables_json=[{\"name\":\"要件定義書\",\"description\":\"システム要件を整理\"}]" \
  -F "system_requirements=要件定義済み"
```

**レスポンス** (`TaskResponse`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2025-01-17T10:30:00",
  "updated_at": null,
  "error_message": null,
  "result_file_path": null
}
```

**ステータス値**:
- `pending`: 作成済み、質問待ち
- `in_progress`: 処理中
- `completed`: 完了
- `failed`: エラー

**エラーレスポンス**:
- `400 Bad Request`: パラメータ不正、ファイル形式不正
- `413 Payload Too Large`: ファイルサイズ超過（10MB超）
- `500 Internal Server Error`: サーバーエラー

---

### 2. 質問取得

タスクに対する質問を生成します（AI生成）。

**エンドポイント**:
```http
GET /api/v1/tasks/{task_id}/questions
```

**パスパラメータ**:

| 名前 | 型 | 説明 |
|------|-----|------|
| `task_id` | String(UUID) | タスクID |

**リクエスト例**:
```bash
curl https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/questions \
  -u username:password
```

**レスポンス** (String配列):
```json
[
  "想定しているユーザー数とアクセス頻度はどの程度ですか？",
  "開発環境やインフラの制約はありますか？",
  "既存システムとの連携は必要ですか？",
  "セキュリティ要件（認証・認可、暗号化など）はありますか？",
  "納期や予算の制約はありますか？"
]
```

**エラーレスポンス**:
- `404 Not Found`: タスクが見つからない
- `500 Internal Server Error`: OpenAI APIエラー、ファイル読み込みエラー

---

### 3. 回答提出

質問への回答を提出し、見積り処理を開始します。

**エンドポイント**:
```http
POST /api/v1/tasks/{task_id}/answers
```

**パスパラメータ**:

| 名前 | 型 | 説明 |
|------|-----|------|
| `task_id` | String(UUID) | タスクID |

**リクエストボディ** (JSON):
```json
[
  {
    "question": "想定しているユーザー数とアクセス頻度はどの程度ですか？",
    "answer": "想定ユーザー数は1000人、アクセス頻度は1日あたり平均100回です。"
  },
  {
    "question": "開発環境やインフラの制約はありますか？",
    "answer": "AWS上でDockerを使用した開発を想定しています。"
  }
]
```

**リクエスト例**:
```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/answers \
  -u username:password \
  -H "Content-Type: application/json" \
  -d '[
    {"question":"想定しているユーザー数は？","answer":"1000人"},
    {"question":"開発環境の制約は？","answer":"AWS + Docker"}
  ]'
```

**レスポンス**:
```json
{
  "message": "タスク処理を開始しました",
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**処理の流れ**:
1. 回答をデータベースに保存
2. バックグラウンドで各成果物の見積り生成（並列実行）
3. Excel結果ファイル生成
4. タスクステータスを`completed`に更新

**エラーレスポンス**:
- `404 Not Found`: タスクが見つからない
- `500 Internal Server Error`: 見積り生成エラー、データベースエラー

---

### 4. ステータス取得

タスクの処理状況を取得します。

**エンドポイント**:
```http
GET /api/v1/tasks/{task_id}/status
```

**パスパラメータ**:

| 名前 | 型 | 説明 |
|------|-----|------|
| `task_id` | String(UUID) | タスクID |

**リクエスト例**:
```bash
curl https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/status \
  -u username:password
```

**レスポンス** (`TaskStatusResponse`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2025-01-17T10:30:00",
  "updated_at": "2025-01-17T10:35:00",
  "error_message": null
}
```

**ステータス値**:
- `pending`: 質問待ち
- `in_progress`: 見積り生成中
- `completed`: 完了（結果取得可能）
- `failed`: エラー発生

**エラーレスポンス**:
- `404 Not Found`: タスクが見つからない

---

### 5. 結果取得

見積り結果を取得します（完了後のみ）。

**エンドポイント**:
```http
GET /api/v1/tasks/{task_id}/result
```

**パスパラメータ**:

| 名前 | 型 | 説明 |
|------|-----|------|
| `task_id` | String(UUID) | タスクID |

**リクエスト例**:
```bash
curl https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/result \
  -u username:password
```

**レスポンス** (`TaskResultResponse`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "estimates": [
    {
      "deliverable_name": "要件定義書",
      "deliverable_description": "システム全体の要件を整理",
      "person_days": 5.0,
      "amount": 200000.0,
      "reasoning": "要件定義フェーズ",
      "reasoning_breakdown": "設計: 2日、レビュー: 1日、文書化: 2日",
      "reasoning_notes": "既存要件の整理と新規要件の追加"
    },
    {
      "deliverable_name": "基本設計書",
      "deliverable_description": "システムアーキテクチャを設計",
      "person_days": 8.0,
      "amount": 320000.0,
      "reasoning": "基本設計フェーズ",
      "reasoning_breakdown": "設計: 4日、レビュー: 2日、文書化: 2日",
      "reasoning_notes": "アーキテクチャ図、ER図、シーケンス図を作成"
    }
  ],
  "subtotal": 520000.0,
  "tax": 52000.0,
  "total": 572000.0,
  "error_message": null
}
```

**エラーレスポンス**:
- `400 Bad Request`: タスクが完了していない
- `404 Not Found`: タスクが見つからない

---

### 6. Excel結果ダウンロード

見積り結果をExcelファイルとしてダウンロードします。

**エンドポイント**:
```http
GET /api/v1/tasks/{task_id}/download
```

**パスパラメータ**:

| 名前 | 型 | 説明 |
|------|-----|------|
| `task_id` | String(UUID) | タスクID |

**リクエスト例**:
```bash
curl -O https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/download \
  -u username:password
```

**レスポンス**:
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- ファイル名: `estimate_result_YYYYMMDD_HHMMSS.xlsx`

**Excelファイル構成**:

**シート1: 見積り**
- 成果物一覧（成果物名称、説明、予想工数、金額、工数内訳、根拠・備考）
- 合計（小計、税額、総額）
- Q&Aセクション

**エラーレスポンス**:
- `404 Not Found`: タスクまたは結果ファイルが見つからない

---

### 7. チャット調整

見積りを対話的に調整します（AI提案生成）。

**エンドポイント**:
```http
POST /api/v1/tasks/{task_id}/chat
```

**パスパラメータ**:

| 名前 | 型 | 説明 |
|------|-----|------|
| `task_id` | String(UUID) | タスクID |

**リクエストボディ** (`ChatRequest`):
```json
{
  "message": "予算50万円に収めたい",
  "intent": "fit_budget",
  "params": {
    "target_budget": 500000
  },
  "estimates": [
    {
      "deliverable_name": "要件定義書",
      "deliverable_description": "システム全体の要件を整理",
      "person_days": 5.0,
      "amount": 200000.0,
      "reasoning": "..."
    }
  ]
}
```

**リクエストパラメータ**:

| 名前 | 型 | 必須 | 説明 |
|------|-----|------|------|
| `message` | String | No | ユーザーメッセージ |
| `intent` | String | No | 調整意図（fit_budget, scope_reduce, unit_cost_change, risk_buffer） |
| `params` | Object | No | 意図別パラメータ |
| `estimates` | Array | No | 現在の見積りデータ |

**intent別パラメータ**:

**fit_budget**: 予算に合わせる
```json
{"target_budget": 500000}
```

**scope_reduce**: スコープを絞る
```json
{"keywords": ["API", "管理画面"]}
```

**unit_cost_change**: 単価変更
```json
{"new_daily_cost": 35000}
```

**risk_buffer**: リスクバッファ追加
```json
{"risk_percentage": 20}
```

**リクエスト例**:
```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/chat \
  -u username:password \
  -H "Content-Type: application/json" \
  -d '{
    "message": "予算50万円に収めたい",
    "intent": "fit_budget",
    "params": {"target_budget": 500000}
  }'
```

**レスポンス** (`ChatResponse`):
```json
{
  "reply_md": "予算50万円に収めるため、3つの調整案を生成しました。",
  "suggestions": null,
  "proposals": [
    {
      "title": "案1: 基本機能に絞り込み",
      "description": "管理画面を簡易化し、基本的なCRUD機能のみ実装",
      "delta": -72000,
      "estimated_total": 500000
    },
    {
      "title": "案2: 外部サービス活用",
      "description": "認証機能をAuth0等の外部サービスに委託",
      "delta": -68000,
      "estimated_total": 504000
    },
    {
      "title": "案3: フェーズ分割",
      "description": "MVP（最小限の機能）をフェーズ1として分離",
      "delta": -100000,
      "estimated_total": 472000
    }
  ],
  "estimates": [
    {
      "deliverable_name": "要件定義書",
      "deliverable_description": "システム全体の要件を整理（簡易版）",
      "person_days": 3.0,
      "amount": 120000.0,
      "reasoning": "基本機能に絞り込み"
    }
  ],
  "totals": {
    "subtotal": 454545.45,
    "tax": 45454.55,
    "total": 500000.0
  },
  "version": 1
}
```

**エラーレスポンス**:
- `404 Not Found`: タスクが見つからない
- `500 Internal Server Error`: AI生成エラー

---

### 8. 調整後見積り適用

チャット調整で生成した見積りをデータベースに保存し、Excelを再生成します。

**エンドポイント**:
```http
POST /api/v1/tasks/{task_id}/apply
```

**パスパラメータ**:

| 名前 | 型 | 説明 |
|------|-----|------|
| `task_id` | String(UUID) | タスクID |

**リクエストボディ**:
```json
{
  "estimates": [
    {
      "deliverable_name": "要件定義書",
      "deliverable_description": "システム全体の要件を整理（簡易版）",
      "person_days": 3.0,
      "amount": 120000.0,
      "reasoning": "基本機能に絞り込み",
      "reasoning_breakdown": "設計: 1日、レビュー: 0.5日、文書化: 1.5日",
      "reasoning_notes": "MVP版のみ"
    }
  ]
}
```

**リクエスト例**:
```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/apply \
  -u username:password \
  -H "Content-Type: application/json" \
  -d '{
    "estimates": [...]
  }'
```

**レスポンス** (`TaskResultResponse`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "estimates": [...],
  "subtotal": 454545.45,
  "tax": 45454.55,
  "total": 500000.0,
  "error_message": null
}
```

**エラーレスポンス**:
- `404 Not Found`: タスクが見つからない
- `500 Internal Server Error`: データベースエラー、Excel生成エラー

---

### 9. サンプルExcelダウンロード

入力用のサンプルExcelファイルをダウンロードします（言語設定に応じて動的生成）。

**エンドポイント**:
```http
GET /api/v1/sample-input
```

**リクエスト例**:
```bash
curl -O https://estimator.path-finder.jp/api/v1/sample-input \
  -u username:password
```

**レスポンス**:
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- ファイル名: `sample_input.xlsx`

**ファイル内容**（日本語設定の場合）:

| 成果物名称 | 説明 |
|-----------|------|
| 要件定義書 | システム全体の要件を整理・明文化した文書 |
| 基本設計書 | システムアーキテクチャと主要機能を設計 |
| 詳細設計書 | 各機能の詳細仕様を記述 |

---

### 10. サンプルCSVダウンロード

入力用のサンプルCSVファイルをダウンロードします（言語設定に応じて動的生成）。

**エンドポイント**:
```http
GET /api/v1/sample-input-csv
```

**リクエスト例**:
```bash
curl -O https://estimator.path-finder.jp/api/v1/sample-input-csv \
  -u username:password
```

**レスポンス**:
- Content-Type: `text/csv`
- ファイル名: `sample_input.csv`
- エンコーディング: UTF-8 BOM付き（Excel互換）

---

### 11. 翻訳データ取得

フロントエンド用の翻訳データを取得します。

**エンドポイント**:
```http
GET /api/v1/translations
```

**リクエスト例**:
```bash
curl https://estimator.path-finder.jp/api/v1/translations \
  -u username:password
```

**レスポンス**:
```json
{
  "language": "ja",
  "translations": {
    "ui": {
      "app_title": "AI見積りシステム",
      "button_create_task": "タスク作成"
    },
    "prompts": {
      "language_instruction": "必ず日本語で回答してください。"
    },
    "excel": {
      "sheet_name": "見積り",
      "column_deliverable_name": "成果物名称"
    }
  }
}
```

**言語設定**:
- サーバー側の`LANGUAGE`環境変数（`ja` / `en`）に基づいて返却
- 翻訳ファイル: `backend/app/locales/ja.json`, `en.json`

---

## データモデル

### TaskResponse

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `id` | String(UUID) | Yes | タスクID |
| `status` | String | Yes | ステータス（pending, in_progress, completed, failed） |
| `created_at` | DateTime | Yes | 作成日時（ISO 8601） |
| `updated_at` | DateTime | No | 更新日時（ISO 8601） |
| `error_message` | String | No | エラーメッセージ |
| `result_file_path` | String | No | 結果ファイルパス |

### TaskStatusResponse

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `id` | String(UUID) | Yes | タスクID |
| `status` | String | Yes | ステータス |
| `created_at` | DateTime | Yes | 作成日時 |
| `updated_at` | DateTime | No | 更新日時 |
| `error_message` | String | No | エラーメッセージ |

### TaskResultResponse

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `id` | String(UUID) | Yes | タスクID |
| `status` | String | Yes | ステータス |
| `estimates` | Array[EstimateResponse] | Yes | 見積り一覧 |
| `subtotal` | Float | Yes | 小計 |
| `tax` | Float | Yes | 税額 |
| `total` | Float | Yes | 総額 |
| `error_message` | String | No | エラーメッセージ |

### EstimateResponse

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `deliverable_name` | String | Yes | 成果物名称 |
| `deliverable_description` | String | No | 成果物説明 |
| `person_days` | Float | Yes | 予想工数（人日） |
| `amount` | Float | Yes | 金額 |
| `reasoning` | String | No | 見積り根拠（レガシー） |
| `reasoning_breakdown` | String | No | 工数内訳 |
| `reasoning_notes` | String | No | 根拠・備考 |

### QAPairRequest

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `question` | String | Yes | 質問 |
| `answer` | String | Yes | 回答 |

### ChatRequest

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `message` | String | No | ユーザーメッセージ |
| `intent` | String | No | 調整意図 |
| `params` | Object | No | 意図別パラメータ |
| `estimates` | Array | No | 現在の見積り |

**intent値**:
- `fit_budget`: 予算に合わせる
- `scope_reduce`: スコープを絞る
- `unit_cost_change`: 単価変更
- `risk_buffer`: リスクバッファ追加

### ChatResponse

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `reply_md` | String | Yes | AIの返信（Markdown） |
| `suggestions` | Array | No | 提案候補 |
| `proposals` | Array | No | 提案カード（2ステップUX） |
| `estimates` | Array[ChatEstimateItem] | No | 調整後見積り |
| `totals` | Object | No | 合計（subtotal, tax, total） |
| `version` | Integer | No | バージョン番号 |

---

## エラーコード

### HTTPステータスコード

| コード | 意味 | 対応方法 |
|-------|------|---------|
| 200 | OK | 成功 |
| 400 | Bad Request | リクエストパラメータを確認、Guardrails検証 |
| 401 | Unauthorized | Basic認証情報を確認 |
| 404 | Not Found | タスクIDを確認 |
| 413 | Payload Too Large | ファイルサイズを10MB以下に削減 |
| 422 | Unprocessable Entity | リクエストボディのバリデーションエラー |
| 500 | Internal Server Error | サーバーログを確認、OpenAI APIステータス確認 |
| 502 | Bad Gateway | バックエンドサービス（Uvicorn）を確認 |
| 503 | Service Unavailable | リソース制限、同時接続数を確認 |
| 504 | Gateway Timeout | タイムアウト設定を確認、処理を最適化 |

### エラーレスポンス形式

```json
{
  "detail": "エラーメッセージの詳細"
}
```

### よくあるエラー

#### 1. ファイルサイズ超過

**レスポンス**:
```json
{
  "detail": "ファイルサイズが10MBを超えています"
}
```

**対応**: ファイルを10MB以下に削減

#### 2. ファイル形式不正

**レスポンス**:
```json
{
  "detail": "Excel（.xlsx, .xls）またはCSV（.csv）ファイルのみアップロード可能です"
}
```

**対応**: Excel（.xlsx, .xls）またはCSV（.csv）ファイルを使用

#### 3. タスク未完了

**レスポンス**:
```json
{
  "detail": "タスクは完了していません（ステータス: in_progress）"
}
```

**対応**: `/tasks/{task_id}/status`でステータスを確認し、完了を待つ

#### 4. OpenAI APIエラー

**レスポンス**:
```json
{
  "detail": "OpenAI API error: Rate limit exceeded"
}
```

**対応**:
- OpenAIのレート制限を確認
- API使用量を確認
- リトライロジックが自動実行（最大3回）

#### 5. Guardrails検証エラー

**レスポンス**:
```json
{
  "detail": "Input validation failed: Potential prompt injection detected in system_requirements"
}
```

**対応**: プロンプトインジェクション攻撃の可能性があるため、入力内容を修正

---

## レート制限

### 同時接続数

- 最大同時リクエスト数: **5**
- キュー待機タイムアウト: **30秒**

### OpenAI API制限

- リトライロジック: **最大3回**（指数バックオフ: 1秒、2秒、4秒）
- CircuitBreaker: 連続5回失敗で60秒間オープン状態

### タイムアウト設定

- Apache ProxyTimeout: **600秒**
- Uvicorn keep-alive timeout: **120秒**

---

## 使用例

### シナリオ1: Excelファイルからタスク作成〜結果取得

#### ステップ1: タスク作成

```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks \
  -u username:password \
  -F "file=@input.xlsx" \
  -F "system_requirements=要件定義済み、開発期間3ヶ月"
```

**レスポンス**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  ...
}
```

#### ステップ2: 質問取得

```bash
curl https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/questions \
  -u username:password
```

**レスポンス**:
```json
[
  "想定しているユーザー数とアクセス頻度はどの程度ですか？",
  "開発環境やインフラの制約はありますか？",
  ...
]
```

#### ステップ3: 回答提出

```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/answers \
  -u username:password \
  -H "Content-Type: application/json" \
  -d '[
    {"question":"想定しているユーザー数は？","answer":"1000人、1日100アクセス"},
    {"question":"開発環境の制約は？","answer":"AWS + Docker"}
  ]'
```

#### ステップ4: ステータス確認（ポーリング）

```bash
curl https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/status \
  -u username:password
```

**レスポンス（処理中）**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  ...
}
```

**レスポンス（完了）**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  ...
}
```

#### ステップ5: 結果取得

```bash
curl https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/result \
  -u username:password
```

**レスポンス**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "estimates": [...],
  "subtotal": 520000.0,
  "tax": 52000.0,
  "total": 572000.0
}
```

#### ステップ6: Excelダウンロード

```bash
curl -O https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/download \
  -u username:password
```

---

### シナリオ2: チャット調整で予算に合わせる

#### ステップ1: チャット調整リクエスト

```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/chat \
  -u username:password \
  -H "Content-Type: application/json" \
  -d '{
    "message": "予算50万円に収めたい",
    "intent": "fit_budget",
    "params": {"target_budget": 500000},
    "estimates": [...]
  }'
```

**レスポンス**:
```json
{
  "reply_md": "予算50万円に収めるため、3つの調整案を生成しました。",
  "proposals": [
    {
      "title": "案1: 基本機能に絞り込み",
      "description": "...",
      "delta": -72000,
      "estimated_total": 500000
    }
  ],
  "estimates": [...],
  "totals": {...}
}
```

#### ステップ2: 調整後見積り適用

```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/apply \
  -u username:password \
  -H "Content-Type: application/json" \
  -d '{
    "estimates": [...]
  }'
```

**レスポンス**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "estimates": [...],
  "subtotal": 454545.45,
  "tax": 45454.55,
  "total": 500000.0
}
```

#### ステップ3: 更新されたExcelダウンロード

```bash
curl -O https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/download \
  -u username:password
```

---

### シナリオ3: Webフォームからタスク作成

#### JavaScriptからのリクエスト例

```javascript
const formData = new FormData();
formData.append('deliverables_json', JSON.stringify([
  {
    "name": "要件定義書",
    "description": "システム全体の要件を整理"
  },
  {
    "name": "基本設計書",
    "description": "システムアーキテクチャを設計"
  }
]));
formData.append('system_requirements', '要件定義済み、開発期間3ヶ月');

const response = await fetch('https://estimator.path-finder.jp/api/v1/tasks', {
  method: 'POST',
  headers: {
    'Authorization': 'Basic ' + btoa('username:password')
  },
  body: formData
});

const task = await response.json();
console.log('Task ID:', task.id);
```

---

## セキュリティ

### Guardrails（安全性検証）

すべてのユーザー入力は`SafetyService`で検証されます。

**検証項目**:
1. **プロンプトインジェクション検出**: 疑わしいパターンをチェック
2. **不適切なコンテンツ検出**: 有害コンテンツをフィルタリング
3. **長さ制限チェック**: 最大入力長を強制

**検証対象**:
- `system_requirements`（タスク作成時）
- `answer`（回答提出時、各回答）

**検証失敗時**:
- HTTPステータス: `400 Bad Request`
- エラーメッセージ: 詳細な理由を含む

### CORS

- 許可オリジン: 設定された`ALLOWED_ORIGINS`のみ
- 許可メソッド: GET, POST
- 許可ヘッダー: Content-Type, Authorization

### ファイルアップロード

- 最大ファイルサイズ: **10MB**
- 許可形式: Excel（.xlsx, .xls）、CSV（.csv）
- チャンク処理: 1MBずつストリーミング

---

## 多言語対応

### 言語設定

サーバー側の`.env`ファイルで言語を設定：

```bash
LANGUAGE=ja  # または en
```

### 影響範囲

- AI生成コンテンツ（質問、見積り根拠、チャット応答）
- Excel出力（列名、ラベル、日時フォーマット）
- サンプルファイル（Excel/CSV）
- エラーメッセージ（一部）

### 翻訳データ取得

`/api/v1/translations`エンドポイントでフロントエンド用翻訳データを取得可能。

---

## 参考資料

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - 開発者ガイド
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - アーキテクチャドキュメント

---

**最終更新**: 2025-10-21
**作成者**: Claude Code
**バージョン**: 1.0
