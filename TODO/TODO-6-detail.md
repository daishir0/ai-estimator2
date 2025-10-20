# TODO-6: 引継ぎドキュメント作成

## 📋 概要
- **目的**: AI見積りシステムの運用・保守・開発を円滑にするため、包括的な引継ぎドキュメントを作成する
- **期間**: Day 11-13
- **優先度**: 🔴 最高
- **依存関係**: TODO-1〜TODO-5の実装内容を反映

## 🎯 達成基準
- [ ] デプロイメント文書作成完了（ja/en）
- [ ] プロジェクト文書作成完了（ja/en）
- [ ] 開発者向けガイド作成完了（ja/en）
- [ ] トラブルシューティングガイド作成完了（ja/en）
- [ ] APIドキュメント作成完了（ja/en）
- [ ] アーキテクチャ図作成完了
- [ ] 運用Runbook作成完了（ja/en）
- [ ] README.md更新完了

---

## 📐 計画

### 1. ドキュメント構成

```
output3/docs/
├── deployment/
│   ├── DEPLOYMENT.md (日本語版)
│   └── DEPLOYMENT_EN.md (英語版)
├── development/
│   ├── DEVELOPER_GUIDE.md (日本語版)
│   ├── DEVELOPER_GUIDE_EN.md (英語版)
│   ├── API_REFERENCE.md (日本語版)
│   └── API_REFERENCE_EN.md (英語版)
├── operations/
│   ├── TROUBLESHOOTING.md (日本語版)
│   ├── TROUBLESHOOTING_EN.md (英語版)
│   ├── RUNBOOK.md (日本語版)
│   └── RUNBOOK_EN.md (英語版)
├── architecture/
│   ├── ARCHITECTURE.md (日本語版)
│   ├── ARCHITECTURE_EN.md (英語版)
│   └── diagrams/
│       ├── system_architecture.png
│       ├── data_flow.png
│       └── sequence_diagram.png
├── security/ (TODO-3で作成済み)
│   ├── OWASP_LLM_RISK_REGISTER.md
│   └── SECURITY_CHECKLIST.md
├── safety/ (TODO-4で作成済み)
│   └── SAFETY_POLICY.md
└── PROJECT.md (プロジェクト概要)
```

### 2. ドキュメント内容

#### 2.1 デプロイメント文書 (docs/deployment/DEPLOYMENT.md)

**目次**:
1. インフラ構成
2. 環境変数
3. 秘密管理
4. 起動・停止手順
5. スケーリング戦略
6. バックアップ・復旧
7. モニタリング
8. コスト管理

**主要内容**:
- **アーキテクチャ図**: ユーザー → Nginx → FastAPI → SQLite/OpenAI API
- **環境変数一覧**: 全設定項目と説明
- **systemd設定**: サービスファイルの完全版
- **デプロイ手順**: ステップバイステップガイド
- **ロールバック手順**: 問題発生時の復旧方法
- **スケーリング**: 垂直/水平スケーリング戦略

#### 2.2 プロジェクト文書 (docs/PROJECT.md)

**目次**:
1. プロジェクト概要
2. 目的とスコープ
3. システム構成図
4. データフロー図
5. 主要機能
6. 技術スタック
7. データモデル
8. セットアップ手順
9. 操作方法

**主要内容**:
- **システム構成図**: 詳細なコンポーネント図
- **データフロー図**: 入力→処理→出力の流れ
- **ER図**: Task, Deliverable, QAPair, Estimate, Messageの関連
- **シーケンス図**: タスク作成〜見積り完了までの流れ
- **多言語対応**: 仕組みと実装方法

#### 2.3 開発者向けガイド (docs/development/DEVELOPER_GUIDE.md)

**目次**:
1. 開発環境セットアップ
2. ディレクトリ構造
3. コーディング規約
4. テスト実行方法
5. デバッグ方法
6. 新機能追加手順
7. 多言語対応の追加方法
8. よくある問題と解決方法

**主要内容**:
```markdown
## 開発環境セットアップ

### 必要なツール
- Python 3.11+
- conda (推奨) または venv
- Git
- VSCode (推奨)

### セットアップ手順
1. リポジトリクローン
   ```bash
   git clone https://github.com/your-org/ai-estimator2.git
   cd ai-estimator2
   ```

2. 仮想環境作成・アクティベート
   ```bash
   conda create -n estimator python=3.11
   conda activate estimator
   ```

3. 依存関係インストール
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. 環境変数設定
   ```bash
   cp .env.sample .env
   # .envを編集してOPENAI_API_KEYを設定
   ```

5. サーバー起動
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

## ディレクトリ構造

```
output3/backend/
├── app/
│   ├── main.py                # FastAPIアプリケーション
│   ├── api/v1/tasks.py        # APIエンドポイント
│   ├── models/                # データモデル（SQLAlchemy）
│   ├── schemas/               # Pydanticスキーマ
│   ├── services/              # ビジネスロジック
│   ├── core/                  # 設定・共通機能
│   ├── db/                    # データベース接続
│   ├── prompts/               # LLMプロンプト
│   ├── middleware/            # ミドルウェア
│   └── locales/               # 多言語翻訳ファイル
├── tests/                     # テストコード
│   ├── unit/                  # ユニットテスト
│   ├── integration/           # 統合テスト
│   └── e2e/                   # E2Eテスト
├── docs/                      # ドキュメント
└── requirements.txt           # 依存関係
```

## コーディング規約

### Python コードスタイル
- PEP 8準拠
- Black formatterで自動整形
- 型ヒント（Type Hints）を使用
- Docstringsを記述（Google スタイル）

### 命名規則
- クラス: PascalCase（例: EstimatorService）
- 関数・変数: snake_case（例: get_estimate）
- 定数: UPPER_SNAKE_CASE（例: MAX_RETRIES）

### Import 順序
1. 標準ライブラリ
2. サードパーティライブラリ
3. ローカルモジュール

## テスト実行方法

### すべてのテスト実行
```bash
pytest tests/ -v --cov=app --cov-report=html
```

### ユニットテストのみ
```bash
pytest tests/unit/ -v
```

### カバレッジレポート確認
```bash
# ブラウザでhtmlcov/index.htmlを開く
open htmlcov/index.html
```

## 新機能追加手順

### 1. 機能設計
- 要件定義
- API設計
- データモデル設計

### 2. 実装
- モデル作成/更新
- サービス層実装
- APIエンドポイント追加
- テスト実装

### 3. 多言語対応
- ja.json/en.jsonに翻訳追加
- t()関数で翻訳取得
- 両言語でテスト

### 4. レビュー・マージ
- コードレビュー
- テスト成功確認
- ドキュメント更新
- マージ

## 多言語対応の追加方法

詳細はCLAUDE.mdの「多言語対応」セクションを参照。

簡易手順:
1. `backend/app/locales/ja.json`に翻訳キー追加
2. `backend/app/locales/en.json`に英語翻訳追加
3. コード内で`t('key.path')`で翻訳取得
4. LANGUAGE=ja/en両方でテスト
```

#### 2.4 APIリファレンス (docs/development/API_REFERENCE.md)

**目次**:
1. 認証
2. エンドポイント一覧
3. リクエスト/レスポンス例
4. エラーコード
5. レート制限

**主要内容**:
- **全エンドポイント**: 詳細な仕様とサンプル
- **スキーマ定義**: Pydanticモデルの説明
- **エラーハンドリング**: 各エラーコードの意味と対処法

#### 2.5 トラブルシューティングガイド (docs/operations/TROUBLESHOOTING.md)

**目次**:
1. よくある問題
2. ログ確認方法
3. エラーコード別対処法
4. パフォーマンス問題
5. OpenAI API関連問題
6. データベース問題

**主要内容**:
```markdown
## よくある問題

### 問題1: サーバーが起動しない

**症状**: `uvicorn app.main:app`実行時にエラー

**原因**:
- 環境変数未設定（OPENAI_API_KEY）
- ポートが既に使用中
- 依存関係未インストール

**対処法**:
1. 環境変数確認
   ```bash
   cat .env | grep OPENAI_API_KEY
   ```

2. ポート使用状況確認
   ```bash
   lsof -i :8000
   ```

3. 依存関係再インストール
   ```bash
   pip install -r requirements.txt
   ```

### 問題2: 見積り生成が失敗する

**症状**: 「OpenAI API error」が表示される

**原因**:
- APIキーが無効
- API利用上限に達した
- ネットワーク問題

**対処法**:
1. OpenAI API状態確認: https://status.openai.com/
2. APIキー確認: https://platform.openai.com/api-keys
3. 利用状況確認: https://platform.openai.com/usage
4. ログ確認:
   ```bash
   journalctl -u estimator.service -n 100
   ```

### 問題3: ファイルアップロードが失敗する

**症状**: 「File too large」エラー

**対処法**:
- ファイルサイズを10MB以下に削減
- 設定変更（.env）:
  ```
  MAX_UPLOAD_SIZE_MB=20
  ```
- サービス再起動

## ログ確認方法

### 開発環境
```bash
# コンソールに直接出力
uvicorn app.main:app --reload --log-level debug
```

### 本番環境（systemd）
```bash
# リアルタイムログ
journalctl -u estimator.service -f

# 直近100行
journalctl -u estimator.service -n 100

# エラーのみ
journalctl -u estimator.service -p err
```
```

#### 2.6 運用Runbook (docs/operations/RUNBOOK.md)

**目次**:
1. 日次運用
2. 週次運用
3. 月次運用
4. 障害対応
5. メンテナンス手順
6. エスカレーション

**主要内容**:
- **ヘルスチェック**: curl http://localhost:8000/health
- **ログローテーション**: logrotate設定
- **バックアップ**: データベースバックアップ手順
- **監視**: 監視項目とアラート設定

### 3. アーキテクチャ図作成

**ツール**: Mermaid (Markdown内に記述)またはdraw.io

**必要な図**:
1. **システム構成図**: 全体像
2. **データフロー図**: 処理の流れ
3. **シーケンス図**: タスク作成〜見積り完了
4. **ER図**: データモデルの関連

### 4. 技術スタック

- **Markdown**: ドキュメント記述
- **Mermaid**: 図の記述

### 5. 影響範囲

**新規作成ファイル**
- `docs/deployment/DEPLOYMENT.md` (ja/en)
- `docs/development/DEVELOPER_GUIDE.md` (ja/en)
- `docs/development/API_REFERENCE.md` (ja/en)
- `docs/operations/TROUBLESHOOTING.md` (ja/en)
- `docs/operations/RUNBOOK.md` (ja/en)
- `docs/architecture/ARCHITECTURE.md` (ja/en)
- `docs/PROJECT.md`

**変更ファイル**
- `README.md` (ドキュメントリンク追加)

### 6. リスクと対策

#### リスク1: ドキュメントの陳腐化
- **対策**: コード変更時にドキュメント更新を必須化、定期レビュー

#### リスク2: 翻訳の不整合
- **対策**: 両言語の並行更新、翻訳レビュー

#### リスク3: 図の更新漏れ
- **対策**: Mermaid使用（コードで図を記述）、変更時の自動更新

### 7. スケジュール

**Day 11**:
- デプロイメント文書作成（ja/en）
- 運用Runbook作成（ja/en）

**Day 12**:
- プロジェクト文書作成（ja/en）
- アーキテクチャ図作成
- トラブルシューティングガイド作成（ja/en）

**Day 13**:
- 開発者向けガイド作成（ja/en）
- APIリファレンス作成（ja/en）
- README.md更新
- ドキュメント全体レビュー

---

## 🔧 実施内容（実績）

### Day 11-13: [日付]
#### 実施作業
- [ ] 作業内容（実装時に記録）

#### 作成ファイル
- ファイル一覧（実装時に記録）

#### レビュー結果
- レビュー結果（実装時に記録）

#### 課題・気づき
- 課題・気づき（実装時に記録）

---

## 📊 実績

### 達成した成果
- 成果内容（完了時にまとめ）

### ドキュメント品質
- 品質評価（完了時にまとめ）

### 学び
- 学んだこと（完了時にまとめ）

---

## ✅ 完了チェックリスト
- [ ] すべてのドキュメント作成完了（ja/en）
- [ ] アーキテクチャ図作成完了
- [ ] README.md更新完了
- [ ] ドキュメント相互リンク確認
- [ ] 多言語対応確認（ja/en）
- [ ] ドキュメント全体レビュー完了
- [ ] 実際の運用手順での動作確認

## 📚 参考資料
- todo.md (602-910行目): TODO-6詳細
- CLAUDE.md: プロジェクト開発ガイド
- README.md: 既存ドキュメント

---

**作成日**: 2025-10-18
**最終更新**: 2025-10-18
**担当**: Claude Code
**ステータス**: 計画完了
