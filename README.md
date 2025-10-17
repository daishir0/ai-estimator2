# ai-estimator2

## Overview
AI-powered project estimation system with an intelligent web interface. This system uses OpenAI GPT-4 to automatically generate accurate project estimates based on deliverables and system requirements. It features a 2-step UX flow for estimate adjustments, where users can request cost changes (e.g., "reduce by 300,000 yen") and receive AI-generated proposal cards with detailed change breakdowns.

### Key Features

1. **Multiple Input Methods**
   - Excel file upload (drag & drop)
   - CSV file upload
   - Web form input (tab-based UI)

2. **AI-Powered Estimation**
   - Automatic question generation based on deliverables
   - GPT-4o-mini powered estimate calculation
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

### Technology Stack

- **Backend**: FastAPI, Python 3.11, SQLAlchemy 2.0, SQLite3
- **AI**: OpenAI API (GPT-4o-mini)
- **Frontend**: Vanilla JavaScript (embedded static UI)
- **File Processing**: openpyxl, pandas

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/daishir0/ai-estimator2.git
cd ai-estimator2
```

### 2. Set up Python environment

```bash
# Activate conda environment (Python 3.11)
source /home/ec2-user/anaconda3/bin/activate
conda activate 311

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
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///./app.db
CORS_ORIGINS=http://localhost:8000,https://estimator.path-finder.jp
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10
UNIT_PRICE_PER_DAY=40000
API_V1_STR=/api/v1
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

- `POST /api/v1/tasks` - Create new estimation task
- `GET /api/v1/tasks/{task_id}/questions` - Get AI-generated questions
- `POST /api/v1/tasks/{task_id}/answers` - Submit answers and generate estimates
- `GET /api/v1/tasks/{task_id}/result` - Get estimation results
- `POST /api/v1/tasks/{task_id}/chat` - Adjust estimates with AI proposals
- `POST /api/v1/tasks/{task_id}/apply` - Apply adjusted estimates
- `GET /api/v1/tasks/{task_id}/download` - Download Excel file

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
- The system uses GPT-4o-mini for cost-effective AI operations
- Adjustment amounts are calculated by comparing actual estimate changes, not relying on GPT-4's target_amount_change

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

# ai-estimator2

## 概要
AIを活用したプロジェクト見積りシステムです。OpenAI GPT-4を使用して成果物とシステム要件から自動的に正確なプロジェクト見積りを生成します。見積り調整の2ステップUXフローを搭載し、「30万円安くして」のようなリクエストに対してAIが詳細な変更内訳を含む提案カードを3つ生成します。

### 主要機能

1. **複数の入力方式**
   - Excelファイルアップロード（ドラッグ&ドロップ）
   - CSVファイルアップロード
   - Webフォーム入力（タブベースUI）

2. **AI自動見積り**
   - 成果物に基づく自動質問生成
   - GPT-4o-miniによる見積り計算
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

### 技術スタック

- **バックエンド**: FastAPI, Python 3.11, SQLAlchemy 2.0, SQLite3
- **AI**: OpenAI API (GPT-4o-mini)
- **フロントエンド**: Vanilla JavaScript（内蔵静的UI）
- **ファイル処理**: openpyxl, pandas

## インストール方法

### 1. リポジトリのクローン

```bash
git clone https://github.com/daishir0/ai-estimator2.git
cd ai-estimator2
```

### 2. Python環境のセットアップ

```bash
# conda環境をアクティベート（Python 3.11）
source /home/ec2-user/anaconda3/bin/activate
conda activate 311

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
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///./app.db
CORS_ORIGINS=http://localhost:8000,https://estimator.path-finder.jp
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10
UNIT_PRICE_PER_DAY=40000
API_V1_STR=/api/v1
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

- `POST /api/v1/tasks` - 新規見積りタスクの作成
- `GET /api/v1/tasks/{task_id}/questions` - AI生成質問の取得
- `POST /api/v1/tasks/{task_id}/answers` - 回答送信と見積り生成
- `GET /api/v1/tasks/{task_id}/result` - 見積り結果の取得
- `POST /api/v1/tasks/{task_id}/chat` - AI提案による見積り調整
- `POST /api/v1/tasks/{task_id}/apply` - 調整後の見積りを適用
- `GET /api/v1/tasks/{task_id}/download` - Excelファイルのダウンロード

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
- システムはコスト効率の良いGPT-4o-miniを使用しています
- 調整額はGPT-4のtarget_amount_changeではなく、実際の見積り差分を計算して算出します

## ライセンス
このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルを参照してください。
