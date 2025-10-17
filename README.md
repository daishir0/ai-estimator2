# AI見積り作成システム Web版

**バージョン**: v2.0
**作成日**: 2025年10月10日
**参考システム**: GraspIt (22_pj-graspai)

---

## 📋 概要

CLIベースのAI見積りシステムを、FastAPIベースのWebアプリケーションにリニューアルしたシステムです（最小UIを内蔵、同期処理でスピナー表示）。

### 主要機能

1. **Excelファイルアップロード** (ドラッグ&ドロップ)
2. **システム要件入力** (自由記述)
3. **AI質問回答** (3問)
4. **自動見積もり生成** (OpenAI API)
5. **結果表示** (見やすいテーブル)
6. **Excelダウンロード** (ワンクリック)

---

## 🔧 技術スタック

### フロントエンド
- 最小シングルページUI（Vanilla JS, StaticFiles 提供）

### バックエンド
- FastAPI
- Python 3.11 (conda環境311)
- SQLAlchemy 2.0+
- SQLite3（デフォルト）
- OpenAI API (gpt-4o-mini)
- openpyxl

### インフラ
- SQLite3（単一ファイルDB）
- Apache/Nginx（任意, リバースプロキシ構成は別途）

---

## 🚀 セットアップ

### 1. 環境変数設定

```bash
cp .env.sample .env
# .envを編集してAPIキーなどを設定
```

### 2. データベース

SQLite3（`DATABASE_URL=sqlite:///./app.db`）がデフォルトです。追加の作業は不要です。

### 3. バックエンドセットアップ

```bash
cd backend
source /home/ec2-user/anaconda3/bin/activate && conda activate 311
pip install -r requirements.txt
```

### 4. フロントエンド

内蔵の最小UIを利用します（別途ビルド不要）。

### 5. 起動

```bash
# バックエンド
cd backend
conda activate 311
uvicorn app.main:app --reload --host 127.0.0.1 --port 8009

# 内蔵UIにアクセス（別途プロセス不要）
# ブラウザで http://localhost:8009/ui
```

### 6. アクセス

- 内蔵UI: http://localhost:8009/ui
- バックエンドAPI: http://localhost:8009/docs

---

## 🧪 テスト

### 単体テスト (バックエンド)

```bash
cd backend
conda activate 311
pytest
```

### 統合テスト

```bash
cd backend
conda activate 311
pytest tests/integration/
```

### E2Eテスト

```bash
cd tests
npx playwright test
```

---

## 📁 ディレクトリ構成

```
output2/
├── backend/           # FastAPI
│   ├── app/
│   │   ├── api/       # APIエンドポイント
│   │   ├── models/    # SQLAlchemyモデル
│   │   ├── services/  # ビジネスロジック
│   │   ├── static/    # 内蔵UI (index.html)
│   │   └── main.py
│   └── tests/         # テスト
├── database/          # PostgreSQL用スキーマ定義（SQLiteでは未使用）
├── tests/             # （任意）
├── services/          # （任意）
└── docs/              # ドキュメント
```

---

## 🔌 systemd サービス

### フロントエンド

```bash
sudo systemctl start estimator-frontend.service
sudo systemctl status estimator-frontend.service
```

### バックエンド

```bash
sudo systemctl start estimator-backend.service
sudo systemctl status estimator-backend.service
```

### 両方起動

```bash
sudo systemctl start estimator.target
```

---

## 📊 データベーススキーマ

### テーブル一覧

1. **tasks** - タスク管理
2. **deliverables** - 成果物
3. **estimates** - 見積もり結果
4. **qa_pairs** - 質問・回答ペア
5. **users** - ユーザー情報 (Phase 2)
6. **projects** - プロジェクト情報 (Phase 2)

---

## 🎯 開発ロードマップ

### Phase 1: コア機能 (完了)
- ✅ バックエンド基盤構築
- ✅ フロントエンド基盤構築
- ✅ 見積もり作成フロー (3ステップ)
- ✅ タスク実行・結果表示
- ✅ Excelダウンロード
- ✅ E2Eテスト全シナリオ成功

### Phase 2: 拡張機能 (予定)
- [ ] Google/GitHub SSO認証
- [ ] 見積履歴管理
- [ ] 管理画面
- [ ] CSV/Markdown出力

### Phase 3: 最適化 (予定)
- [ ] パフォーマンス改善
- [ ] セキュリティ対策
- [ ] 法務ページ

---

## 📝 ライセンス

MIT License

---

**作成者**: Claude + Gemini
**プロジェクト**: AI-Estimator Web版
**日付**: 2025年10月10日
