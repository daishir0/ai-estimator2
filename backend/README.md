# ai-estimator2

## Overview
AI-powered cost estimation system for software development projects. This system uses OpenAI's GPT models to automatically generate accurate cost estimates based on deliverable lists in Excel format.

### Key Features
- **Automated AI Estimation**: Generates cost estimates for each deliverable using GPT-4o-mini
- **Excel Integration**: Import deliverable lists and export detailed estimation results
- **Parallel Processing**: Fast estimation with concurrent API calls (max 5 workers)
- **Interactive Adjustment**: Real-time estimation adjustment via chat interface
- **Detailed Breakdown**: Split reasoning into "Work Breakdown" and "Notes/Remarks" columns
- **Visualization**: Chart.js-based cost distribution charts
- **Question-Answer Flow**: Improves estimation accuracy through contextual questions

### Tech Stack
- **Backend**: FastAPI + SQLAlchemy (SQLite)
- **AI**: OpenAI API (GPT-4o-mini)
- **Frontend**: HTML + Tailwind CSS + Chart.js
- **Excel Processing**: openpyxl + pandas
- **Markdown Rendering**: Marked.js + DOMPurify

## Installation

### Prerequisites
- Python 3.11+
- OpenAI API key
- Git

### Step 1: Clone the repository
```bash
git clone https://github.com/daishir0/ai-estimator2
cd ai-estimator2
```

### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Set up environment variables
Create a `.env` file in the project root:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Daily Unit Cost (JPY)
DAILY_UNIT_COST=80000

# File Upload Settings
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10

# Parallel Processing Settings
MAX_PARALLEL_ESTIMATES=5

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Basic Auth (Optional)
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=password
```

**Important**: Replace `your_openai_api_key_here` with your actual OpenAI API key.

### Step 4: Create upload directory
```bash
mkdir -p uploads
```

### Step 5: Start the application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at: `http://localhost:8000`

## Usage

### Basic Flow

1. **Access the application**
   - Open your browser and navigate to `http://localhost:8000`

2. **Upload Excel file**
   - Prepare an Excel file with two columns:
     - Column A: Deliverable name
     - Column B: Deliverable description
   - Optionally enter system requirements
   - Click "アップロード" (Upload)

3. **Answer questions**
   - The system generates 3 contextual questions to improve estimation accuracy
   - Answer each question and click "見積りを実行" (Execute Estimation)

4. **Review results**
   - View the estimation table with:
     - Deliverable name and description
     - Estimated person-days and cost
     - Work breakdown (by phase)
     - Notes and assumptions
   - Check the cost distribution chart

5. **Adjust estimates (Optional)**
   - Use the chat interface to adjust estimates interactively
   - Apply changes and regenerate the Excel file

6. **Download results**
   - Click "Excelダウンロード" to download the detailed estimation report

### API Endpoints

- `POST /api/v1/tasks` - Create new estimation task
- `GET /api/v1/tasks/{task_id}/questions` - Generate contextual questions
- `POST /api/v1/tasks/{task_id}/answers` - Submit answers and start estimation
- `GET /api/v1/tasks/{task_id}/status` - Check task status
- `GET /api/v1/tasks/{task_id}/result` - Get estimation results
- `GET /api/v1/tasks/{task_id}/download` - Download Excel report
- `POST /api/v1/tasks/{task_id}/chat` - Interactive estimation adjustment
- `POST /api/v1/tasks/{task_id}/apply` - Apply adjusted estimates

## Notes

- **OpenAI API Key Required**: This system requires a valid OpenAI API key. API usage will incur costs based on OpenAI's pricing.
- **Cost Calculation**: Default daily unit cost is 80,000 JPY. Adjust `DAILY_UNIT_COST` in `.env` as needed.
- **File Size Limit**: Excel files larger than 10MB (default) will be rejected. Adjust `MAX_UPLOAD_SIZE_MB` if needed.
- **Browser Compatibility**: Modern browsers (Chrome, Firefox, Safari, Edge) recommended for proper Markdown rendering.
- **Database**: Uses SQLite by default. Database file (`app.db`) is created automatically on first run.
- **Parallel Processing**: Adjust `MAX_PARALLEL_ESTIMATES` based on your OpenAI API rate limits.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

# ai-estimator2

## 概要
ソフトウェア開発プロジェクトのAI見積もりシステム。OpenAIのGPTモデルを使用して、Excelフォーマットの成果物一覧から自動的に正確な工数・金額見積もりを生成します。

### 主な機能
- **AI自動見積もり**: GPT-4o-miniを使用した成果物ごとの工数・金額見積もり生成
- **Excel連携**: 成果物一覧のインポートと詳細見積もり結果のエクスポート
- **並列処理**: 最大5並列のAPI呼び出しによる高速見積もり生成
- **インタラクティブ調整**: チャットインターフェースによるリアルタイム見積もり調整
- **詳細内訳**: 「工数内訳」と「根拠・備考」の2列による詳細な見積もり説明
- **可視化**: Chart.jsによる工数・金額分布チャート表示
- **質問回答フロー**: 文脈に応じた質問により見積もり精度を向上

### 技術スタック
- **バックエンド**: FastAPI + SQLAlchemy (SQLite)
- **AI**: OpenAI API (GPT-4o-mini)
- **フロントエンド**: HTML + Tailwind CSS + Chart.js
- **Excel処理**: openpyxl + pandas
- **Markdown表示**: Marked.js + DOMPurify

## インストール方法

### 前提条件
- Python 3.11以上
- OpenAI APIキー
- Git

### ステップ1: リポジトリのクローン
```bash
git clone https://github.com/daishir0/ai-estimator2
cd ai-estimator2
```

### ステップ2: 依存関係のインストール
```bash
pip install -r requirements.txt
```

### ステップ3: 環境変数の設定
プロジェクトルートに `.env` ファイルを作成:

```bash
# OpenAI API設定
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# 人日単価（円）
DAILY_UNIT_COST=80000

# ファイルアップロード設定
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10

# 並列処理設定
MAX_PARALLEL_ESTIMATES=5

# CORS設定
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Basic認証（オプション）
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=password
```

**重要**: `your_openai_api_key_here` を実際のOpenAI APIキーに置き換えてください。

### ステップ4: アップロードディレクトリの作成
```bash
mkdir -p uploads
```

### ステップ5: アプリケーションの起動
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

アプリケーションは `http://localhost:8000` でアクセス可能になります。

## 使い方

### 基本的な流れ

1. **アプリケーションへのアクセス**
   - ブラウザで `http://localhost:8000` を開く

2. **Excelファイルのアップロード**
   - 2列構成のExcelファイルを用意:
     - A列: 成果物名
     - B列: 成果物説明
   - 任意でシステム要件を入力
   - 「アップロード」ボタンをクリック

3. **質問への回答**
   - システムが見積もり精度向上のための3つの質問を生成
   - 各質問に回答して「見積りを実行」をクリック

4. **結果の確認**
   - 見積もりテーブルで以下を確認:
     - 成果物名と説明
     - 予想工数（人日）と金額
     - 工数内訳（工程別）
     - 根拠・備考（前提条件やリスク）
   - 工数・金額分布チャートを確認

5. **見積もりの調整（オプション）**
   - チャットインターフェースで見積もりをインタラクティブに調整
   - 変更を適用してExcelファイルを再生成

6. **結果のダウンロード**
   - 「Excelダウンロード」をクリックして詳細見積もりレポートをダウンロード

### APIエンドポイント

- `POST /api/v1/tasks` - 新規見積もりタスク作成
- `GET /api/v1/tasks/{task_id}/questions` - 文脈質問の生成
- `POST /api/v1/tasks/{task_id}/answers` - 回答送信と見積もり実行
- `GET /api/v1/tasks/{task_id}/status` - タスクステータス確認
- `GET /api/v1/tasks/{task_id}/result` - 見積もり結果取得
- `GET /api/v1/tasks/{task_id}/download` - Excelレポートダウンロード
- `POST /api/v1/tasks/{task_id}/chat` - インタラクティブ見積もり調整
- `POST /api/v1/tasks/{task_id}/apply` - 調整後見積もりの適用

## 注意点

- **OpenAI APIキー必須**: このシステムは有効なOpenAI APIキーが必要です。API使用にはOpenAIの料金が発生します。
- **単価設定**: デフォルトの人日単価は80,000円です。必要に応じて `.env` の `DAILY_UNIT_COST` を調整してください。
- **ファイルサイズ制限**: デフォルトでは10MB以上のExcelファイルは拒否されます。必要に応じて `MAX_UPLOAD_SIZE_MB` を調整してください。
- **ブラウザ互換性**: Markdownの適切なレンダリングには、モダンブラウザ（Chrome、Firefox、Safari、Edge）を推奨します。
- **データベース**: デフォルトでSQLiteを使用します。データベースファイル（`app.db`）は初回起動時に自動作成されます。
- **並列処理**: OpenAI APIのレート制限に応じて `MAX_PARALLEL_ESTIMATES` を調整してください。

## ライセンス
このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルを参照してください。
