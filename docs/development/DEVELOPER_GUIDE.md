# 開発者ガイド

## 📋 目次

1. [開発環境セットアップ](#開発環境セットアップ)
2. [ディレクトリ構造](#ディレクトリ構造)
3. [コーディング規約](#コーディング規約)
4. [テスト実行方法](#テスト実行方法)
5. [デバッグ方法](#デバッグ方法)
6. [新機能追加手順](#新機能追加手順)
7. [多言語対応の追加方法](#多言語対応の追加方法)
8. [よくある問題と解決方法](#よくある問題と解決方法)

---

## 開発環境セットアップ

### 必要なツール

| ツール | バージョン | 用途 |
|-------|-----------|------|
| Python | 3.11+ | プログラミング言語 |
| conda | latest | Python環境管理 |
| Git | 2.x+ | バージョン管理 |
| VSCode | latest | エディタ（推奨） |
| SQLite | 3.x+ | データベース |

### セットアップ手順

#### 1. リポジトリクローン

```bash
git clone https://github.com/daishir0/ai-estimator2.git
cd ai-estimator2/backend
```

#### 2. Python仮想環境作成

```bash
# conda環境作成
source /home/ec2-user/anaconda3/bin/activate
conda create -n 311 python=3.11
conda activate 311
```

#### 3. 依存関係インストール

```bash
pip install -r requirements.txt
```

#### 4. 環境変数設定

```bash
# .envファイル作成
cp .env.sample .env

# 編集
nano .env
```

**.envファイル内容**:
```bash
# OpenAI API Key（必須）
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx

# Database
DATABASE_URL=sqlite:///./app.db

# Language (ja or en)
LANGUAGE=ja

# その他の設定...
```

#### 5. データベース初期化

```bash
# 初回起動時に自動作成される
# 手動で初期化する場合:
rm app.db
uvicorn app.main:app --reload
```

#### 6. サーバー起動

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### 7. ブラウザでアクセス

- UI: http://localhost:8000/ui
- API Docs: http://localhost:8000/docs

### VSCode推奨設定

**.vscode/settings.json**:
```json
{
  "python.defaultInterpreterPath": "/home/ec2-user/anaconda3/envs/311/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"]
}
```

---

## ディレクトリ構造

```
backend/
├── app/
│   ├── main.py                    # FastAPIアプリケーション
│   │
│   ├── api/                       # APIエンドポイント
│   │   └── v1/
│   │       └── tasks.py           # タスク関連API
│   │
│   ├── models/                    # SQLAlchemyモデル
│   │   ├── task.py
│   │   ├── deliverable.py
│   │   ├── qa_pair.py
│   │   ├── estimate.py
│   │   └── message.py
│   │
│   ├── schemas/                   # Pydanticスキーマ
│   │   ├── task.py
│   │   ├── estimate.py
│   │   ├── qa_pair.py
│   │   └── chat.py
│   │
│   ├── services/                  # ビジネスロジック
│   │   ├── task_service.py       # タスク管理
│   │   ├── question_service.py   # 質問生成
│   │   ├── estimator_service.py  # 見積り計算
│   │   ├── chat_service.py       # チャット調整
│   │   ├── safety_service.py     # 安全性検証
│   │   ├── input_service.py      # ファイル入力
│   │   └── export_service.py     # Excel出力
│   │
│   ├── core/                      # 共通機能
│   │   ├── config.py             # 設定管理
│   │   └── i18n.py               # 多言語対応
│   │
│   ├── db/                        # データベース
│   │   └── database.py           # DB接続
│   │
│   ├── prompts/                   # LLMプロンプト
│   │   ├── question_prompts.py
│   │   ├── estimate_prompts.py
│   │   └── chat_prompts.py
│   │
│   ├── middleware/                # ミドルウェア
│   │   ├── circuit_breaker.py
│   │   ├── loop_detector.py
│   │   └── resource_limiter.py
│   │
│   ├── utils/                     # ユーティリティ
│   │   └── retry.py
│   │
│   ├── locales/                   # 翻訳ファイル
│   │   ├── ja.json
│   │   └── en.json
│   │
│   └── static/                    # 静的ファイル
│       ├── index.html
│       ├── styles.css
│       └── script.js
│
├── tests/                         # テストコード
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .env                          # 環境変数
├── requirements.txt              # Python依存関係
└── app.db                        # SQLiteデータベース
```

---

## コーディング規約

### Python コードスタイル

**基本方針**: PEP 8準拠

#### フォーマッター

```bash
# Black使用（自動整形）
pip install black
black app/

# flake8使用（Lint）
pip install flake8
flake8 app/
```

#### 型ヒント

**必須**: すべての関数に型ヒントを付ける

```python
# Good
def get_task(task_id: str) -> Task:
    return db.query(Task).filter(Task.id == task_id).first()

# Bad
def get_task(task_id):
    return db.query(Task).filter(Task.id == task_id).first()
```

#### Docstrings

**スタイル**: Google Style

```python
def estimate_deliverable(deliverable: Deliverable, qa_pairs: List[QAPair]) -> Estimate:
    """Generate estimate for a single deliverable.

    Args:
        deliverable: Deliverable object to estimate
        qa_pairs: List of question-answer pairs for context

    Returns:
        Estimate object with calculated effort and cost

    Raises:
        OpenAIError: If API call fails
        ValidationError: If deliverable data is invalid
    """
    # Implementation...
```

### 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| クラス | PascalCase | `EstimatorService` |
| 関数・変数 | snake_case | `get_estimate`, `task_id` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| プライベート | _先頭アンダースコア | `_internal_method` |

### Import 順序

```python
# 1. 標準ライブラリ
import os
import sys
from typing import List, Optional

# 2. サードパーティライブラリ
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 3. ローカルモジュール
from app.models.task import Task
from app.services.task_service import TaskService
```

### コメント

**英語で記述**: すべてのコメント・Docstringは英語

```python
# Good
def calculate_total(estimates: List[Estimate]) -> float:
    """Calculate total cost from estimates."""
    # Sum all estimated costs
    subtotal = sum(e.estimated_cost for e in estimates)
    # Add tax (10% for Japan, 0% for English)
    tax = subtotal * (TAX_RATE / 100)
    return subtotal + tax

# Bad
def calculate_total(estimates: List[Estimate]) -> float:
    """見積りの合計を計算"""
    # 全見積りの合計
    subtotal = sum(e.estimated_cost for e in estimates)
    # 消費税を追加
    tax = subtotal * (TAX_RATE / 100)
    return subtotal + tax
```

---

## テスト実行方法

### すべてのテスト実行

```bash
pytest tests/ -v --cov=app --cov-report=html
```

### ユニットテストのみ

```bash
pytest tests/unit/ -v
```

### 統合テストのみ

```bash
pytest tests/integration/ -v
```

### E2Eテストのみ

```bash
pytest tests/e2e/ -v
```

### 特定のテストファイル

```bash
pytest tests/unit/test_task_service.py -v
```

### カバレッジレポート確認

```bash
# HTMLレポート生成
pytest tests/ --cov=app --cov-report=html

# ブラウザで開く
open htmlcov/index.html
```

### テスト実行オプション

| オプション | 説明 |
|-----------|------|
| `-v` | Verbose出力 |
| `-s` | print文の出力を表示 |
| `-x` | 最初の失敗で停止 |
| `-k <pattern>` | パターンマッチしたテストのみ実行 |
| `--lf` | 前回失敗したテストのみ実行 |

---

## デバッグ方法

### ログレベル設定

```bash
# DEBUG レベルで起動
uvicorn app.main:app --reload --log-level debug
```

### ブレークポイント

```python
# pdbを使用
import pdb; pdb.set_trace()

# または Python 3.7+
breakpoint()
```

### VSCodeデバッグ設定

**.vscode/launch.json**:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "127.0.0.1",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

### ログ出力

```python
import logging

logger = logging.getLogger(__name__)

def some_function():
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
```

---

## 新機能追加手順

### ステップ1: 機能設計

1. **要件定義**
   - 機能の目的・スコープを明確化
   - ユースケース作成

2. **API設計**
   - エンドポイント設計
   - リクエスト・レスポンススキーマ定義

3. **データモデル設計**
   - 必要なテーブル・カラムの設計
   - リレーションシップの定義

### ステップ2: 実装

#### 2-1. モデル作成/更新

**新規テーブルの場合**:

```python
# app/models/new_model.py
from sqlalchemy import Column, String, Text
from app.db.database import Base

class NewModel(Base):
    __tablename__ = "new_models"

    id = Column(String(36), primary_key=True)
    name = Column(String(200))
    description = Column(Text)
```

#### 2-2. スキーマ作成

```python
# app/schemas/new_schema.py
from pydantic import BaseModel

class NewModelCreate(BaseModel):
    name: str
    description: str

class NewModelResponse(BaseModel):
    id: str
    name: str
    description: str

    class Config:
        from_attributes = True
```

#### 2-3. サービス層実装

```python
# app/services/new_service.py
from sqlalchemy.orm import Session
from app.models.new_model import NewModel

class NewService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> NewModel:
        """Create new model instance."""
        model = NewModel(**data)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model
```

#### 2-4. APIエンドポイント追加

```python
# app/api/v1/new_endpoint.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.new_service import NewService
from app.schemas.new_schema import NewModelCreate, NewModelResponse

router = APIRouter()

@router.post("/new-models", response_model=NewModelResponse)
def create_new_model(
    data: NewModelCreate,
    db: Session = Depends(get_db)
):
    """Create new model."""
    service = NewService(db)
    model = service.create(data.dict())
    return model
```

#### 2-5. ルーター登録

```python
# app/main.py
from app.api.v1 import new_endpoint

app.include_router(
    new_endpoint.router,
    prefix="/api/v1",
    tags=["new_models"]
)
```

### ステップ3: テスト実装

```python
# tests/unit/test_new_service.py
import pytest
from app.services.new_service import NewService

def test_create_new_model(db_session):
    """Test creating new model."""
    service = NewService(db_session)
    data = {"name": "Test", "description": "Test desc"}
    model = service.create(data)

    assert model.id is not None
    assert model.name == "Test"
    assert model.description == "Test desc"
```

### ステップ4: 多言語対応

**ja.json / en.json に翻訳追加**:

```json
{
  "ui": {
    "new_feature_title": "新機能タイトル"
  },
  "messages": {
    "new_feature_created": "新機能が作成されました"
  }
}
```

**コード内で使用**:

```python
from app.core.i18n import t

title = t('ui.new_feature_title')
message = t('messages.new_feature_created')
```

### ステップ5: ドキュメント更新

- API_REFERENCE.md に新エンドポイント追加
- README.md の機能一覧更新
- CHANGELOG.md に変更内容記載

---

## 多言語対応の追加方法

詳細は [CLAUDE.md](../../CLAUDE.md#多言語対応) を参照。

### 簡易手順

#### 1. 翻訳ファイルに追加

**backend/app/locales/ja.json**:
```json
{
  "ui": {
    "new_button": "新しいボタン"
  }
}
```

**backend/app/locales/en.json**:
```json
{
  "ui": {
    "new_button": "New Button"
  }
}
```

#### 2. コード内で翻訳取得

```python
from app.core.i18n import t

button_text = t('ui.new_button')
```

#### 3. 両言語でテスト

```bash
# 日本語
nano backend/.env
# LANGUAGE=ja
sudo systemctl restart estimator

# 英語
nano backend/.env
# LANGUAGE=en
sudo systemctl restart estimator
```

---

## よくある問題と解決方法

### Q1: ImportError: cannot import name 'xxx'

**原因**: モジュールの循環参照

**解決**:
- `__init__.py` を確認
- 遅延インポート（関数内でimport）

### Q2: SQLAlchemy relationship エラー

**原因**: リレーションシップの定義ミス

**解決**:
```python
# モデルAからモデルBへの参照
class ModelA(Base):
    model_b_id = Column(String(36), ForeignKey("model_bs.id"))
    model_b = relationship("ModelB", back_populates="model_as")

class ModelB(Base):
    model_as = relationship("ModelA", back_populates="model_b")
```

### Q3: Pydantic validation error

**原因**: スキーマとモデルの不一致

**解決**:
```python
class MySchema(BaseModel):
    class Config:
        from_attributes = True  # SQLAlchemyモデルをPydanticに変換
```

### Q4: 翻訳が反映されない

**原因**: サービス未再起動

**解決**:
```bash
sudo systemctl restart estimator
```

---

## 参考資料

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [SQLAlchemy公式ドキュメント](https://docs.sqlalchemy.org/)
- [Pydantic公式ドキュメント](https://docs.pydantic.dev/)
- [pytest公式ドキュメント](https://docs.pytest.org/)

---

**最終更新**: 2025-10-21
**作成者**: Claude Code
**バージョン**: 1.0
