# AI見積りシステム - プロジェクト概要 / AI Estimator System - Project Overview

## 📋 目次 / Table of Contents

### 日本語 (Japanese)
1. [プロジェクト概要](#プロジェクト概要)
2. [目的とスコープ](#目的とスコープ)
3. [システム構成図](#システム構成図)
4. [データフロー図](#データフロー図)
5. [主要機能](#主要機能)
6. [技術スタック](#技術スタック)
7. [データモデル](#データモデル)
8. [セットアップ手順](#セットアップ手順)
9. [操作方法](#操作方法)

### English
1. [Project Overview](#project-overview-1)
2. [Purpose and Scope](#purpose-and-scope)
3. [System Architecture](#system-architecture)
4. [Data Flow Diagram](#data-flow-diagram-1)
5. [Key Features](#key-features)
6. [Technology Stack](#technology-stack-1)
7. [Data Model](#data-model-1)
8. [Setup Instructions](#setup-instructions)
9. [How to Use](#how-to-use)

---

# 日本語版 (Japanese Version)

## プロジェクト概要

**AI見積りシステム**は、OpenAI GPT-4oを活用してプロジェクトの見積りを自動生成するWebアプリケーションです。成果物一覧とシステム要件を入力すると、AIが質問を生成し、回答に基づいて詳細な工数見積り・金額見積りを自動作成します。

### プロジェクト情報

| 項目 | 内容 |
|------|------|
| **プロジェクト名** | AI見積りシステム (AI Estimator System) |
| **バージョン** | 1.0 |
| **開発開始日** | 2024年 |
| **言語対応** | 日本語・英語 (切り替え可能) |
| **ライセンス** | MIT License |
| **リポジトリ** | https://github.com/daishir0/ai-estimator2 |
| **本番URL** | https://estimator.path-finder.jp/ |

---

## 目的とスコープ

### 目的

1. **見積り作業の効率化**
   - 従来の手作業による見積り作業を自動化
   - 見積り時間を75%削減（4時間 → 1時間）

2. **見積り精度の向上**
   - AIによる多角的な質問で要件を詳細化
   - 過去の実績データに基づく工数算出

3. **見積りプロセスの標準化**
   - 見積り担当者による品質のバラつきを解消
   - 一貫性のある見積りフォーマット

### スコープ

#### 対象範囲（In Scope）
- ✅ システム開発プロジェクトの見積り
- ✅ Webアプリケーション開発
- ✅ モバイルアプリ開発
- ✅ API開発
- ✅ 小〜中規模プロジェクト（〜500人日）

#### 対象外（Out of Scope）
- ❌ インフラ構築のみのプロジェクト
- ❌ ハードウェア開発
- ❌ 大規模プロジェクト（500人日超）
- ❌ 契約交渉・価格調整

---

## システム構成図

### 全体アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                        Internet                         │
│                    (HTTPS Port 443)                     │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────┐
│               Apache HTTPD (Reverse Proxy)              │
│  - SSL/TLS Termination (Let's Encrypt)                  │
│  - Basic Authentication                                 │
│  - ProxyPass to Backend (Port 8100)                     │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓ localhost:8100
┌─────────────────────────────────────────────────────────┐
│           systemd estimator.service                     │
│  - Auto-restart on failure                              │
│  - Log management (/var/log/estimator/)                 │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────┐
│               Uvicorn (ASGI Server)                     │
│  - Host: 127.0.0.1, Port: 8100                          │
│  - Async request processing                             │
│  - Timeout: 120s                                        │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────┐
│            FastAPI Application (Python 3.11)            │
│                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────┐ │
│  │ API Endpoints │  │ Business Logic│  │Middleware  │ │
│  │  /api/v1/     │  │   Services    │  │ Security   │ │
│  └───────────────┘  └───────────────┘  └────────────┘ │
│                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────┐ │
│  │  Data Models  │  │   Prompts     │  │   i18n     │ │
│  │  SQLAlchemy   │  │  LLM Prompts  │  │  ja/en     │ │
│  └───────────────┘  └───────────────┘  └────────────┘ │
└─────────┬───────────────────────────────────┬─────────┘
          │                                   │
          ↓                                   ↓
┌─────────────────────┐         ┌─────────────────────────┐
│  SQLite Database    │         │    OpenAI API           │
│  - tasks            │         │  - Model: gpt-4o-mini   │
│  - deliverables     │         │  - Question generation  │
│  - qa_pairs         │         │  - Estimate generation  │
│  - estimates        │         │  - Chat adjustment      │
│  - messages         │         └─────────────────────────┘
└─────────────────────┘
```

### コンポーネント説明

| コンポーネント | 役割 | 技術 |
|--------------|------|------|
| **Apache HTTPD** | リバースプロキシ、SSL/TLS終端 | Apache 2.4.62 |
| **systemd** | プロセス管理、自動再起動 | systemd |
| **Uvicorn** | ASGIサーバー | Uvicorn |
| **FastAPI** | Webフレームワーク、REST API | FastAPI |
| **SQLite** | データベース | SQLite 3.x |
| **OpenAI API** | AI推論エンジン | gpt-4o-mini |

---

## データフロー図

### 見積り作成フロー

```
[ユーザー]
   │
   ↓ 1. 成果物入力（Excel/CSV/Webフォーム）
[FastAPI: POST /api/v1/tasks]
   │
   ├→ 2. 安全性チェック (SafetyService)
   │   - プロンプトインジェクション検出
   │   - 不適切コンテンツフィルタリング
   │
   ├→ 3. ファイル処理 (InputService)
   │   - Excel/CSVパース
   │   - 成果物データ抽出
   │   │
   │   ↓ 4. タスク作成
   │   [SQLite: INSERT INTO tasks]
   │
   ↓ 5. 質問生成リクエスト
[FastAPI: GET /api/v1/tasks/{id}/questions]
   │
   ├→ 6. 質問生成 (QuestionService)
   │   │
   │   ↓ LLMプロンプト生成
   │   [OpenAI API: gpt-4o-mini]
   │   │
   │   ↓ AIが3つの質問を生成
   │   [SQLite: INSERT INTO qa_pairs]
   │
   ↓ 7. ユーザーが質問に回答
[FastAPI: POST /api/v1/tasks/{id}/answers]
   │
   ├→ 8. 回答保存
   │   [SQLite: UPDATE qa_pairs]
   │   │
   │   ↓ 9. 見積り生成 (TaskService)
   │   ├→ 成果物ごとにLLMプロンプト生成
   │   │   [OpenAI API: gpt-4o-mini] × N回（並列実行）
   │   │   │
   │   │   ↓ AIが工数・金額・根拠を生成
   │   │   [SQLite: INSERT INTO estimates]
   │   │
   │   ├→ 10. 合計金額計算（税込）
   │   │   [EstimatorService]
   │   │
   │   ├→ 11. Excelファイル生成
   │   │   [ExportService]
   │   │
   │   ↓ 12. 結果保存
   │   [SQLite: UPDATE tasks]
   │
   ↓ 13. 見積り結果取得
[FastAPI: GET /api/v1/tasks/{id}/result]
   │
   ↓ 14. Excel出力
[FastAPI: GET /api/v1/tasks/{id}/download]
   │
   ↓ Excelファイルダウンロード
[ユーザー]
```

### チャット調整フロー（オプション）

```
[ユーザー]
   │
   ↓ 1. 調整リクエスト（「30万円安くして」）
[FastAPI: POST /api/v1/tasks/{id}/chat]
   │
   ├→ 2. 安全性チェック (SafetyService)
   │
   ├→ 3. AI調整提案生成 (ChatService)
   │   │
   │   ↓ 現在の見積りを解析
   │   ↓ 調整プロンプト生成
   │   [OpenAI API: gpt-4o-mini]
   │   │
   │   ↓ AIが3つの調整案を生成
   │   [SQLite: INSERT INTO messages]
   │
   ↓ 4. 提案カード表示
[ユーザー]
   │
   ↓ 5. 提案を選択・適用
[FastAPI: POST /api/v1/tasks/{id}/apply]
   │
   ├→ 6. 見積り更新
   │   [SQLite: UPDATE estimates]
   │   │
   │   ↓ 7. 再計算・Excel再生成
   │   [ExportService]
   │
   ↓ 8. 更新された見積り結果
[ユーザー]
```

---

## 主要機能

### 1. 複数入力方式対応

#### Excel/CSVファイルアップロード
- **対応形式**: .xlsx, .xls, .csv
- **必須列**: 成果物名称、説明
- **最大ファイルサイズ**: 10MB（設定変更可能）
- **ドラッグ&ドロップ対応**

#### Webフォーム入力
- **タブベースUI**: 直感的な入力フォーム
- **動的行追加**: 成果物を自由に追加
- **リアルタイムバリデーション**

### 2. AI質問生成

- **自動質問生成**: 成果物とシステム要件から3つの質問を自動生成
- **質問例**:
  - 「想定しているユーザー数とアクセス頻度はどの程度ですか？」
  - 「既存システムとの連携要件はありますか？」
  - 「セキュリティ要件（認証・暗号化など）はありますか？」

### 3. AI見積り生成

- **成果物ごとの詳細見積り**:
  - 予想工数（人日）
  - 金額（円/ドル）
  - 工数内訳（要件定義、設計、実装、テスト、ドキュメント作成）
  - 根拠・備考

- **合計金額計算**:
  - 小計
  - 消費税（日本: 10%、英語圏: 0%）
  - 総額（税込）

### 4. インタラクティブ見積り調整

- **自然言語リクエスト**:
  - 「あと30万円ほど安くする案を教えて」
  - 「品質を上げつつ50万円高くする案は？」

- **AI調整提案**:
  - AIが3つの調整案を生成
  - 各案に詳細な変更内訳を表示
  - ワンクリックで適用

### 5. 視覚的な結果表示

- **棒グラフ**: 成果物ごとの工数を可視化
- **アコーディオン表示**: 詳細情報を展開・折りたたみ
- **工数内訳**: 5つのフェーズ別の内訳表示
- **Excel出力**: ダウンロード可能な見積り書

### 6. 多言語対応

- **対応言語**: 日本語・英語
- **切り替え**: 環境変数 `LANGUAGE=ja/en`
- **翻訳範囲**:
  - UI全体
  - AI生成コンテンツ
  - Excel出力
  - サンプルファイル

---

## 技術スタック

### バックエンド

| 技術 | バージョン | 用途 |
|------|-----------|------|
| **Python** | 3.11 | プログラミング言語 |
| **FastAPI** | 0.104+ | Webフレームワーク |
| **Uvicorn** | 0.24+ | ASGIサーバー |
| **SQLAlchemy** | 2.0+ | ORM |
| **Pydantic** | 2.0+ | データバリデーション |
| **OpenAI SDK** | 1.3+ | OpenAI API クライアント |
| **pandas** | 2.0+ | データ処理 |
| **openpyxl** | 3.1+ | Excelファイル処理 |

### フロントエンド

| 技術 | 用途 |
|------|------|
| **Vanilla JavaScript** | UI制御 |
| **Chart.js** | グラフ描画 |
| **HTML5/CSS3** | マークアップ・スタイリング |

### インフラ

| 技術 | バージョン | 用途 |
|------|-----------|------|
| **Apache HTTPD** | 2.4.62 | リバースプロキシ |
| **systemd** | - | プロセス管理 |
| **SQLite** | 3.x | データベース |
| **Let's Encrypt** | - | SSL/TLS証明書 |
| **Amazon EC2** | - | ホスティング |
| **Amazon Linux** | 2023 | OS |

### 外部サービス

| サービス | 用途 |
|---------|------|
| **OpenAI API** | AI推論 (gpt-4o-mini) |
| **Let's Encrypt** | SSL証明書 |

---

## データモデル

### ER図

```
┌─────────────────┐
│     tasks       │
├─────────────────┤
│ id (PK)         │◄──────┐
│ excel_file_path │       │
│ system_reqs     │       │
│ status          │       │
│ error_message   │       │
│ result_file     │       │
│ created_at      │       │
│ updated_at      │       │
└─────────────────┘       │
        │                 │
        │ 1               │
        │                 │
        │ N               │
        ↓                 │
┌─────────────────┐       │
│  deliverables   │       │
├─────────────────┤       │
│ id (PK)         │       │
│ task_id (FK)    │───────┘
│ name            │
│ description     │
│ created_at      │
└─────────────────┘
        │
        │ 1
        │
        │ N
        ↓
┌─────────────────┐
│   estimates     │
├─────────────────┤
│ id (PK)         │
│ deliverable_id  │
│ estimated_days  │
│ estimated_cost  │
│ breakdown       │
│ reasoning       │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│    qa_pairs     │
├─────────────────┤
│ id (PK)         │
│ task_id (FK)    │───────┐
│ question        │       │
│ answer          │       │
│ created_at      │       │
└─────────────────┘       │
                          │
                          │
┌─────────────────┐       │
│    messages     │       │
├─────────────────┤       │
│ id (PK)         │       │
│ task_id (FK)    │───────┘
│ role            │
│ content         │
│ created_at      │
└─────────────────┘
```

### テーブル定義

#### tasks テーブル
| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | String(36) | タスクID (UUID) |
| excel_file_path | String(500) | アップロードファイルパス |
| system_requirements | Text | システム要件 |
| status | String(20) | ステータス (pending/processing/completed/failed) |
| error_message | Text | エラーメッセージ |
| result_file_path | String(500) | 出力Excelファイルパス |
| created_at | DateTime | 作成日時 |
| updated_at | DateTime | 更新日時 |

#### deliverables テーブル
| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | String(36) | 成果物ID (UUID) |
| task_id | String(36) | タスクID (FK) |
| name | String(200) | 成果物名称 |
| description | Text | 説明 |
| created_at | DateTime | 作成日時 |

#### qa_pairs テーブル
| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | String(36) | 質問回答ID (UUID) |
| task_id | String(36) | タスクID (FK) |
| question | Text | 質問 |
| answer | Text | 回答 |
| created_at | DateTime | 作成日時 |

#### estimates テーブル
| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | String(36) | 見積りID (UUID) |
| deliverable_id | String(36) | 成果物ID (FK) |
| estimated_days | Float | 予想工数（人日） |
| estimated_cost | Float | 予想金額 |
| breakdown | JSON | 工数内訳 |
| reasoning | Text | 根拠・備考 |
| created_at | DateTime | 作成日時 |

#### messages テーブル
| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | String(36) | メッセージID (UUID) |
| task_id | String(36) | タスクID (FK) |
| role | String(20) | ロール (user/assistant) |
| content | Text | メッセージ内容 |
| created_at | DateTime | 作成日時 |

---

## セットアップ手順

詳細は[DEPLOYMENT.md](deployment/DEPLOYMENT.md)を参照してください。

### クイックスタート

```bash
# 1. リポジトリクローン
git clone https://github.com/daishir0/ai-estimator2.git
cd ai-estimator2/backend

# 2. Python環境セットアップ
conda create -n 311 python=3.11
conda activate 311
pip install -r requirements.txt

# 3. 環境変数設定
cp .env.sample .env
nano .env  # OPENAI_API_KEYを設定

# 4. サーバー起動
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 5. ブラウザでアクセス
# http://localhost:8000/ui
```

---

## 操作方法

### 基本的なワークフロー

#### ステップ1: 成果物入力

**方法A: Excelファイルアップロード**
1. サンプルExcelをダウンロード（http://localhost:8000/api/v1/sample-input）
2. 成果物名称・説明を記入
3. ドラッグ&ドロップでアップロード

**方法B: Webフォーム入力**
1. 「Webフォームで入力」タブを選択
2. 成果物名称・説明を入力
3. 必要に応じて行を追加

#### ステップ2: AI質問に回答

1. システムが3つの質問を自動生成
2. 各質問に詳細に回答
3. 「回答を送信」ボタンをクリック

#### ステップ3: 見積り確認

1. 成果物ごとの詳細見積りを確認
2. 棒グラフで工数を可視化
3. アコーディオンで詳細を展開

#### ステップ4: 見積り調整（オプション）

1. チャット欄に調整リクエストを入力
   - 例: 「あと30万円ほど安くする案を教えて」
2. AIが3つの提案カードを生成
3. 好みの提案を選択して「この案を適用する」

#### ステップ5: Excel出力

1. 「Excelでダウンロード」ボタンをクリック
2. 見積り書（.xlsx）がダウンロード
3. 必要に応じて編集・印刷

---

# English Version

## Project Overview

The **AI Estimator System** is a web application that automatically generates project estimates using OpenAI GPT-4o. By inputting a list of deliverables and system requirements, the AI generates questions and creates detailed effort and cost estimates based on the answers.

### Project Information

| Item | Details |
|------|---------|
| **Project Name** | AI Estimator System |
| **Version** | 1.0 |
| **Development Start** | 2024 |
| **Language Support** | Japanese & English (switchable) |
| **License** | MIT License |
| **Repository** | https://github.com/daishir0/ai-estimator2 |
| **Production URL** | https://estimator.path-finder.jp/ |

---

## Purpose and Scope

### Purpose

1. **Streamline Estimation Work**
   - Automate manual estimation tasks
   - Reduce estimation time by 75% (4 hours → 1 hour)

2. **Improve Estimation Accuracy**
   - Detailed requirements through multi-faceted AI questions
   - Effort calculation based on historical data

3. **Standardize Estimation Process**
   - Eliminate quality variations among estimators
   - Consistent estimation format

### Scope

#### In Scope
- ✅ System development project estimation
- ✅ Web application development
- ✅ Mobile app development
- ✅ API development
- ✅ Small to medium projects (up to 500 person-days)

#### Out of Scope
- ❌ Infrastructure-only projects
- ❌ Hardware development
- ❌ Large-scale projects (500+ person-days)
- ❌ Contract negotiation/pricing

---

## System Architecture

(See Japanese section for detailed architecture diagram)

---

## Data Flow Diagram

(See Japanese section for detailed data flow diagrams)

---

## Key Features

### 1. Multiple Input Methods

- Excel/CSV file upload
- Web form input
- Drag & drop support

### 2. AI Question Generation

- Automatic generation of 3 relevant questions
- Based on deliverables and system requirements

### 3. AI Estimate Generation

- Detailed estimates per deliverable
- Effort breakdown (requirements, design, implementation, testing, documentation)
- Cost calculation with tax

### 4. Interactive Estimate Adjustment

- Natural language adjustment requests
- AI-generated adjustment proposals (3 options)
- One-click application

### 5. Visual Results

- Bar chart visualization
- Accordion-style detail view
- Excel output

### 6. Multi-language Support

- Japanese & English
- Switch via `LANGUAGE=ja/en` environment variable

---

## Technology Stack

(See Japanese section for detailed technology stack)

---

## Data Model

(See Japanese section for ER diagram and table definitions)

---

## Setup Instructions

For details, see [DEPLOYMENT_EN.md](deployment/DEPLOYMENT_EN.md).

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/daishir0/ai-estimator2.git
cd ai-estimator2/backend

# 2. Python environment setup
conda create -n 311 python=3.11
conda activate 311
pip install -r requirements.txt

# 3. Environment variables
cp .env.sample .env
nano .env  # Set OPENAI_API_KEY

# 4. Start server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 5. Access in browser
# http://localhost:8000/ui
```

---

## How to Use

### Basic Workflow

#### Step 1: Input Deliverables

**Method A: Excel File Upload**
1. Download sample Excel (http://localhost:8000/api/v1/sample-input)
2. Fill in deliverable names and descriptions
3. Drag & drop to upload

**Method B: Web Form Input**
1. Select "Web Form Input" tab
2. Enter deliverable names and descriptions
3. Add rows as needed

#### Step 2: Answer AI Questions

1. System generates 3 questions automatically
2. Answer each question in detail
3. Click "Submit Answers"

#### Step 3: Review Estimates

1. Review detailed estimates per deliverable
2. Visualize effort in bar chart
3. Expand details in accordion

#### Step 4: Adjust Estimates (Optional)

1. Enter adjustment request in chat
   - Example: "Reduce by $3,000"
2. AI generates 3 proposal cards
3. Select preferred proposal and click "Apply"

#### Step 5: Export to Excel

1. Click "Download Excel" button
2. Estimate sheet (.xlsx) is downloaded
3. Edit/print as needed

---

## References

- [DEPLOYMENT.md](deployment/DEPLOYMENT.md) / [DEPLOYMENT_EN.md](deployment/DEPLOYMENT_EN.md) - Deployment Guide
- [RUNBOOK.md](operations/RUNBOOK.md) / [RUNBOOK_EN.md](operations/RUNBOOK_EN.md) - Operations Runbook
- [ARCHITECTURE.md](architecture/ARCHITECTURE.md) / [ARCHITECTURE_EN.md](architecture/ARCHITECTURE_EN.md) - Architecture Documentation
- [DEVELOPER_GUIDE.md](development/DEVELOPER_GUIDE.md) / [DEVELOPER_GUIDE_EN.md](development/DEVELOPER_GUIDE_EN.md) - Developer Guide
- [API_REFERENCE.md](development/API_REFERENCE.md) / [API_REFERENCE_EN.md](development/API_REFERENCE_EN.md) - API Reference

---

**Last Updated**: 2025-10-21
**Author**: Claude Code
**Version**: 1.0
