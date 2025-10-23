# ai-estimator2

## Overview
AI-powered project estimation system with an intelligent web interface. This production-ready system uses OpenAI to automatically generate accurate project estimates based on deliverables and system requirements. It features a 2-step UX flow for estimate adjustments, where users can request cost changes (e.g., "reduce by 300,000 yen") and receive AI-generated proposal cards with detailed change breakdowns.

### Evolution from Module 2

This system evolved from **DeliverableEstimatePro3**, a CLI-based estimation tool developed in Module 2 of the ReadyTensor Agentic AI Developer Certification program. The transformation from a command-line prototype to a production-ready web application represents a comprehensive journey through enterprise-grade system development:

- **Module 2 (DeliverableEstimatePro3)**: CLI tool for basic AI-powered project estimation
- **Module 3 (ai-estimator2)**: Full-stack web application with production features including comprehensive testing (87 tests, 100% pass rate), security guardrails, operational resilience, monitoring systems, and complete documentation

### Key Features

1. **Multiple Input Methods**
   - Excel file upload
   - CSV file upload
   - Web form input (tab-based UI)

2. **AI-Powered Estimation**
   - Automatic question generation based on deliverables
   - OpenAI-powered estimate calculation
   - Detailed reasoning and breakdown for each estimate

3. **Interactive Estimate Adjustment**
   - Natural language adjustment requests (e.g., "reduce by 300,000 yen")
   - AI-generated proposal cards (3 options)
   - One-click application of selected proposals
   - Real-time estimate updates

4. **Visual Results**
   - Bar chart visualization
   - Accordion-style detail view
   - Work breakdown display
   - Excel download

5. **Enterprise-Grade Resilience** 🆕
   - Retry with exponential backoff for API failures
   - Circuit breaker pattern for fault tolerance
   - Loop detection to prevent infinite loops
   - Resource limiting to prevent DoS attacks

6. **Monitoring & Observability** 🆕
   - Structured logging with request tracing
   - Real-time metrics collection (API calls, OpenAI usage, errors)
   - Performance monitoring (response times, P95 latency)
   - Admin dashboard endpoints

7. **Cost Management & Security** 🆕
   - OpenAI API cost tracking with daily/monthly limits
   - Automatic shutdown on cost overrun ($10/day, $200/month)
   - Rate limiting (100 requests/hour) for DoS prevention
   - Emergency shutdown procedures

8. **Data Privacy & GDPR Compliance** 🆕
   - Privacy policy and data handling guidelines
   - Automatic data deletion after retention period (30 days)
   - GDPR-compliant data deletion API
   - PII detection and masking in logs

### Technology Stack

- **Backend**: FastAPI, Python 3.11, SQLAlchemy 2.0, SQLite3
- **AI**: OpenAI API
- **Frontend**: Vanilla JavaScript (embedded static UI)
- **File Processing**: openpyxl, pandas
- **Testing**: pytest, pytest-asyncio, pytest-cov (87 tests, 100% pass rate)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/daishir0/ai-estimator2.git
cd ai-estimator2
```

### 2. Set up Python environment

```bash
# Activate your Python 3.11+ environment
# Example with conda:
# source /path/to/conda/bin/activate
# conda activate your-python-env

# Navigate to backend directory
cd backend
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.sample .env
```

Edit `.env` file and set your OpenAI API key:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Database
DATABASE_URL=sqlite:///./app.db

# Server Configuration
CORS_ORIGINS=http://localhost:8000,https://estimator.path-finder.jp
API_V1_STR=/api/v1

# File Upload
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10

# Pricing
UNIT_PRICE_PER_DAY=40000
DAILY_UNIT_COST_JPY=40000
DAILY_UNIT_COST_USD=500

# Language Setting
LANGUAGE=ja  # or 'en' for English

# Cost Management
DAILY_COST_LIMIT=10.0      # Daily OpenAI API cost limit in USD
MONTHLY_COST_LIMIT=200.0   # Monthly OpenAI API cost limit in USD

# Rate Limiting
RATE_LIMIT_MAX_REQUESTS=100      # Max requests per window
RATE_LIMIT_WINDOW_SECONDS=3600   # Rate limit window (1 hour)

# Resilience Settings
OPENAI_TIMEOUT=30                    # OpenAI API timeout in seconds
OPENAI_MAX_RETRIES=3                 # Maximum retry attempts
OPENAI_RETRY_INITIAL_DELAY=1.0       # Initial retry delay in seconds
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5  # Failures before opening circuit
MAX_CONCURRENT_ESTIMATES=5           # Max concurrent estimate operations

# Logging
LOG_LEVEL=INFO        # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=            # Log file path (empty = console only)
MASK_PII=false       # Enable PII masking in logs

# Privacy Settings
DATA_RETENTION_DAYS=30        # Task data retention period in days
AUTO_CLEANUP_ENABLED=true     # Enable automatic data cleanup
PRIVACY_POLICY_VERSION=1.0    # Privacy policy version
```

### 5. Initialize database

The SQLite database will be created automatically on first startup. No additional setup required.

### 6. Start the server

```bash
# Development mode
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Production mode (using systemd)
sudo systemctl start estimator.service
```

### 7. Access the application

- Web UI: http://localhost:8000/ui
- API Documentation: http://localhost:8000/docs
- Production URL: https://estimator.path-finder.jp/

## Usage

### Basic Workflow

1. **Upload Deliverables**
   - Choose input method (Excel/CSV/Web form)
   - Upload file or enter deliverables manually
   - Optionally add system requirements

2. **Answer AI Questions**
   - System generates 3 relevant questions
   - Answer questions to refine estimates
   - Submit answers to proceed

3. **Review Estimates**
   - View detailed estimates with reasoning
   - Check work breakdown (requirements, design, implementation, testing, documentation)
   - Review total cost with tax

4. **Adjust Estimates (Optional)**
   - Type adjustment request: "あと30万円ほど安くする案を教えて"
   - Review 3 AI-generated proposal cards
   - Click "この案を適用する" to apply selected proposal
   - Download Excel file with final estimates

### API Endpoints

#### Core Estimation Endpoints
- `POST /api/v1/tasks` - Create new estimation task
- `GET /api/v1/tasks/{task_id}/questions` - Get AI-generated questions
- `POST /api/v1/tasks/{task_id}/answers` - Submit answers and generate estimates
- `GET /api/v1/tasks/{task_id}/result` - Get estimation results
- `POST /api/v1/tasks/{task_id}/chat` - Adjust estimates with AI proposals
- `POST /api/v1/tasks/{task_id}/apply` - Apply adjusted estimates
- `GET /api/v1/tasks/{task_id}/download` - Download Excel file
- `DELETE /api/v1/tasks/{task_id}` - Delete task data (GDPR compliance) 🆕

#### Monitoring & Admin Endpoints 🆕
- `GET /api/v1/metrics` - Get system metrics (API calls, performance, errors)
- `GET /api/v1/admin/costs` - Get OpenAI API cost summary
- `GET /api/v1/admin/rate-limits` - Get rate limiting status
- `GET /api/v1/admin/metrics` - Get comprehensive system metrics
- `POST /api/v1/admin/reset-rate-limit/{client_id}` - Reset rate limit for client

#### Utility Endpoints
- `GET /api/v1/sample-input` - Download sample Excel file
- `GET /api/v1/sample-input-csv` - Download sample CSV file
- `GET /api/v1/translations` - Get UI translations (i18n support)

### Sample Input Files

- Sample Excel: http://localhost:8000/api/v1/sample-input
- Sample CSV: http://localhost:8000/api/v1/sample-input-csv

## Notes

- OpenAI API key is required for AI-powered features
- Default unit price is 40,000 yen per person-day (configurable in .env)
- Maximum upload file size is 10MB (configurable)
- Excel files must have columns: 成果物名称, 説明
- CSV files must be UTF-8 encoded
- Proposal cache is shared across all instances using class variables
- The system uses gpt-4o-mini for cost-effective AI operations
- Adjustment amounts are calculated by comparing actual estimate changes, not relying on AI's target_amount_change

## Documentation

Comprehensive documentation is available in the `docs/` directory:

### For Users and Operators

- **[Project Overview](docs/PROJECT.md)** - System overview, architecture diagrams, and getting started guide
- **[Deployment Guide](docs/deployment/DEPLOYMENT_EN.md)** - Complete deployment instructions for production environment
- **[Operations Runbook](docs/operations/RUNBOOK_EN.md)** - Daily operations, monitoring, maintenance procedures
- **[Troubleshooting Guide](docs/operations/TROUBLESHOOTING_EN.md)** - Common issues and solutions, log checking methods
- **[Emergency Shutdown Procedure](docs/operations/EMERGENCY_SHUTDOWN.en.md)** 🆕 - Emergency response for cost overruns and security incidents
- **[Monitoring Plan](docs/monitoring/MONITORING_PLAN_EN.md)** 🆕 - Comprehensive monitoring strategy and alert configuration

### For Developers

- **[Developer Guide](docs/development/DEVELOPER_GUIDE_EN.md)** - Development environment setup, coding standards, testing
- **[API Reference](docs/development/API_REFERENCE_EN.md)** - Complete REST API documentation with examples
- **[Architecture Documentation](docs/architecture/ARCHITECTURE_EN.md)** - System architecture, data models, sequence diagrams

### Security, Privacy & Compliance

- **[Security Checklist](docs/security/SECURITY_CHECKLIST_EN.md)** - Security best practices and validation
- **[Safety Policy](docs/safety/SAFETY_POLICY_EN.md)** - LLM usage policy and data handling guidelines
- **[Privacy Policy](docs/privacy/PRIVACY_POLICY.en.md)** 🆕 - Data collection, usage, and retention policies
- **[GDPR Checklist](docs/privacy/GDPR_CHECKLIST.en.md)** 🆕 - GDPR compliance verification and requirements

### Japanese Documentation

All documents are also available in Japanese (日本語版):

- [プロジェクト概要](docs/PROJECT.md) (Bilingual)
- [デプロイメントガイド](docs/deployment/DEPLOYMENT.md)
- [運用手順書](docs/operations/RUNBOOK.md)
- [トラブルシューティングガイド](docs/operations/TROUBLESHOOTING.md)
- [緊急停止手順書](docs/operations/EMERGENCY_SHUTDOWN.ja.md) 🆕
- [監視計画](docs/monitoring/MONITORING_PLAN.md) 🆕
- [開発者ガイド](docs/development/DEVELOPER_GUIDE.md)
- [API リファレンス](docs/development/API_REFERENCE.md)
- [アーキテクチャドキュメント](docs/architecture/ARCHITECTURE.md)
- [プライバシーポリシー](docs/privacy/PRIVACY_POLICY.ja.md) 🆕
- [GDPRチェックリスト](docs/privacy/GDPR_CHECKLIST.ja.md) 🆕

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

# ai-estimator2

## 概要
AIを活用したプロジェクト見積りシステムです。本番環境対応のこのシステムはOpenAIを使用して成果物とシステム要件から自動的に正確なプロジェクト見積りを生成します。見積り調整の2ステップUXフローを搭載し、「30万円安くして」のようなリクエストに対してAIが詳細な変更内訳を含む提案カードを3つ生成します。

### Module 2からの進化

本システムはReadyTensor Agentic AI Developer Certification ProgramのModule 2で開発した**DeliverableEstimatePro3**（CLIベースの見積りツール）を進化させたものです。コマンドラインのプロトタイプから本番環境対応のWebアプリケーションへの変革は、エンタープライズグレードのシステム開発における包括的な旅路を表しています：

- **Module 2（DeliverableEstimatePro3）**: 基本的なAI駆動プロジェクト見積りCLIツール
- **Module 3（ai-estimator2）**: 本番機能を備えたフルスタックWebアプリケーション（包括的なテスト（87テスト、100%合格率）、セキュリティガードレール、運用レジリエンス、監視システム、完全なドキュメント）

### 主要機能

1. **複数の入力方式**
   - Excelファイルアップロード
   - CSVファイルアップロード
   - Webフォーム入力（タブベースUI）

2. **AI自動見積り**
   - 成果物に基づく自動質問生成
   - OpenAIによる見積り計算
   - 各見積りの詳細な根拠と内訳表示

3. **インタラクティブな見積り調整**
   - 自然言語での調整リクエスト（例：「30万円安くして」）
   - AIによる提案カード生成（3案）
   - ワンクリックで提案を適用
   - リアルタイム見積り更新

4. **視覚的な結果表示**
   - 棒グラフによる可視化
   - アコーディオン形式の詳細表示
   - 工数内訳の表示
   - Excelダウンロード

5. **エンタープライズグレードのレジリエンス** 🆕
   - API障害時のエクスポネンシャルバックオフリトライ
   - フォールトトレランスのためのサーキットブレーカーパターン
   - 無限ループ防止のためのループ検出
   - DoS攻撃防止のためのリソース制限

6. **監視・可観測性** 🆕
   - リクエストトレーシング付き構造化ログ
   - リアルタイムメトリクス収集（API呼び出し、OpenAI使用状況、エラー）
   - パフォーマンス監視（レスポンスタイム、P95レイテンシ）
   - 管理者ダッシュボードエンドポイント

7. **コスト管理・セキュリティ** 🆕
   - OpenAI APIコスト追跡（日次・月次上限付き）
   - コスト超過時の自動停止（$10/日、$200/月）
   - レート制限（100リクエスト/時）によるDoS攻撃防止
   - 緊急停止手順書

8. **データプライバシー・GDPR準拠** 🆕
   - プライバシーポリシーとデータ取扱ガイドライン
   - 保持期間（30日）後の自動データ削除
   - GDPR準拠のデータ削除API
   - ログのPII検出・マスキング

### 技術スタック

- **バックエンド**: FastAPI, Python 3.11, SQLAlchemy 2.0, SQLite3
- **AI**: OpenAI API
- **フロントエンド**: Vanilla JavaScript（内蔵静的UI）
- **ファイル処理**: openpyxl, pandas
- **テスト**: pytest, pytest-asyncio, pytest-cov（87テスト、100%合格率）

## インストール方法

### 1. リポジトリのクローン

```bash
git clone https://github.com/daishir0/ai-estimator2.git
cd ai-estimator2
```

### 2. Python環境のセットアップ

```bash
# Python 3.11以上の環境をアクティベート
# condaの例：
# source /path/to/conda/bin/activate
# conda activate your-python-env

# backendディレクトリに移動
cd backend
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

```bash
cp .env.sample .env
```

`.env`ファイルを編集してOpenAI APIキーを設定：

```bash
# OpenAI API設定
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# データベース
DATABASE_URL=sqlite:///./app.db

# サーバー設定
CORS_ORIGINS=http://localhost:8000,https://estimator.path-finder.jp
API_V1_STR=/api/v1

# ファイルアップロード
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10

# 単価設定
UNIT_PRICE_PER_DAY=40000
DAILY_UNIT_COST_JPY=40000
DAILY_UNIT_COST_USD=500

# 言語設定
LANGUAGE=ja  # または 'en' で英語

# コスト管理
DAILY_COST_LIMIT=10.0      # OpenAI API日次コスト上限（USD）
MONTHLY_COST_LIMIT=200.0   # OpenAI API月次コスト上限（USD）

# レート制限
RATE_LIMIT_MAX_REQUESTS=100      # ウィンドウあたりの最大リクエスト数
RATE_LIMIT_WINDOW_SECONDS=3600   # レート制限ウィンドウ（1時間）

# レジリエンス設定
OPENAI_TIMEOUT=30                    # OpenAI APIタイムアウト（秒）
OPENAI_MAX_RETRIES=3                 # 最大リトライ回数
OPENAI_RETRY_INITIAL_DELAY=1.0       # 初回リトライ遅延（秒）
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5  # サーキットブレーカー開放までの失敗回数
MAX_CONCURRENT_ESTIMATES=5           # 最大並行見積り処理数

# ロギング
LOG_LEVEL=INFO        # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=            # ログファイルパス（空=コンソールのみ）
MASK_PII=false       # ログのPIIマスキング有効化

# プライバシー設定
DATA_RETENTION_DAYS=30        # タスクデータ保持期間（日数）
AUTO_CLEANUP_ENABLED=true     # 自動データクリーンアップ有効化
PRIVACY_POLICY_VERSION=1.0    # プライバシーポリシーバージョン
```

### 5. データベースの初期化

SQLiteデータベースは初回起動時に自動的に作成されます。追加の設定は不要です。

### 6. サーバーの起動

```bash
# 開発モード
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 本番モード（systemd使用）
sudo systemctl start estimator.service
```

### 7. アプリケーションへのアクセス

- Web UI: http://localhost:8000/ui
- APIドキュメント: http://localhost:8000/docs
- 本番環境URL: https://estimator.path-finder.jp/

## 使い方

### 基本的なワークフロー

1. **成果物のアップロード**
   - 入力方式を選択（Excel/CSV/Webフォーム）
   - ファイルをアップロードまたは手動入力
   - 必要に応じてシステム要件を追加

2. **AI質問への回答**
   - システムが3つの関連質問を生成
   - 質問に回答して見積りを精緻化
   - 回答を送信して次へ進む

3. **見積りの確認**
   - 根拠付きの詳細見積りを表示
   - 工数内訳を確認（要件定義、設計、実装、テスト、ドキュメント作成）
   - 税込み合計金額を確認

4. **見積りの調整（オプション）**
   - 調整リクエストを入力：「あと30万円ほど安くする案を教えて」
   - AIが生成した3つの提案カードを確認
   - 「この案を適用する」をクリックして選択した提案を適用
   - 最終見積りをExcelファイルでダウンロード

### APIエンドポイント

#### コア見積りエンドポイント
- `POST /api/v1/tasks` - 新規見積りタスクの作成
- `GET /api/v1/tasks/{task_id}/questions` - AI生成質問の取得
- `POST /api/v1/tasks/{task_id}/answers` - 回答送信と見積り生成
- `GET /api/v1/tasks/{task_id}/result` - 見積り結果の取得
- `POST /api/v1/tasks/{task_id}/chat` - AI提案による見積り調整
- `POST /api/v1/tasks/{task_id}/apply` - 調整後の見積りを適用
- `GET /api/v1/tasks/{task_id}/download` - Excelファイルのダウンロード
- `DELETE /api/v1/tasks/{task_id}` - タスクデータ削除（GDPR準拠） 🆕

#### 監視・管理者エンドポイント 🆕
- `GET /api/v1/metrics` - システムメトリクス取得（API呼び出し、パフォーマンス、エラー）
- `GET /api/v1/admin/costs` - OpenAI APIコスト状況取得
- `GET /api/v1/admin/rate-limits` - レート制限状況取得
- `GET /api/v1/admin/metrics` - 総合システムメトリクス取得
- `POST /api/v1/admin/reset-rate-limit/{client_id}` - クライアントのレート制限リセット

#### ユーティリティエンドポイント
- `GET /api/v1/sample-input` - サンプルExcelファイルダウンロード
- `GET /api/v1/sample-input-csv` - サンプルCSVファイルダウンロード
- `GET /api/v1/translations` - UI翻訳データ取得（i18n対応）

### サンプル入力ファイル

- サンプルExcel: http://localhost:8000/api/v1/sample-input
- サンプルCSV: http://localhost:8000/api/v1/sample-input-csv

## 注意点

- AI機能を使用するにはOpenAI APIキーが必要です
- デフォルトの単価は1人日あたり40,000円です（.envで変更可能）
- アップロードファイルの最大サイズは10MBです（変更可能）
- Excelファイルには「成果物名称」「説明」の列が必要です
- CSVファイルはUTF-8エンコードである必要があります
- 提案キャッシュはクラス変数を使用して全インスタンス間で共有されます
- システムはコスト効率の良いgpt-4o-miniを使用しています
- 調整額はAIのtarget_amount_changeではなく、実際の見積り差分を計算して算出します

## ドキュメント

`docs/`ディレクトリに包括的なドキュメントが用意されています：

### ユーザー・運用担当者向け

- **[プロジェクト概要](docs/PROJECT.md)** - システム概要、アーキテクチャ図、開始ガイド（日英両言語）
- **[デプロイメントガイド](docs/deployment/DEPLOYMENT.md)** - 本番環境への完全なデプロイ手順
- **[運用手順書](docs/operations/RUNBOOK.md)** - 日次運用、監視、保守手順
- **[トラブルシューティングガイド](docs/operations/TROUBLESHOOTING.md)** - よくある問題と解決方法、ログ確認方法
- **[緊急停止手順書](docs/operations/EMERGENCY_SHUTDOWN.ja.md)** 🆕 - コスト超過・セキュリティインシデント発生時の緊急対応
- **[監視計画](docs/monitoring/MONITORING_PLAN.md)** 🆕 - 包括的な監視戦略とアラート設定

### 開発者向け

- **[開発者ガイド](docs/development/DEVELOPER_GUIDE.md)** - 開発環境セットアップ、コーディング規約、テスト
- **[API リファレンス](docs/development/API_REFERENCE.md)** - 完全なREST APIドキュメントと使用例
- **[アーキテクチャドキュメント](docs/architecture/ARCHITECTURE.md)** - システムアーキテクチャ、データモデル、シーケンス図

### セキュリティ・プライバシー・コンプライアンス

- **[セキュリティチェックリスト](docs/security/SECURITY_CHECKLIST.md)** - セキュリティのベストプラクティスと検証
- **[安全性ポリシー](docs/safety/SAFETY_POLICY.md)** - LLM使用ポリシーとデータ取扱ガイドライン
- **[プライバシーポリシー](docs/privacy/PRIVACY_POLICY.ja.md)** 🆕 - データ収集、利用、保持に関するポリシー
- **[GDPRチェックリスト](docs/privacy/GDPR_CHECKLIST.ja.md)** 🆕 - GDPR準拠の検証と要件

### 英語版ドキュメント

すべてのドキュメントは英語版も提供されています（English version）：

- [Project Overview](docs/PROJECT.md) (Bilingual)
- [Deployment Guide](docs/deployment/DEPLOYMENT_EN.md)
- [Operations Runbook](docs/operations/RUNBOOK_EN.md)
- [Troubleshooting Guide](docs/operations/TROUBLESHOOTING_EN.md)
- [Developer Guide](docs/development/DEVELOPER_GUIDE_EN.md)
- [API Reference](docs/development/API_REFERENCE_EN.md)
- [Architecture Documentation](docs/architecture/ARCHITECTURE_EN.md)

## ライセンス
このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルを参照してください。
