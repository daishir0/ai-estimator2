# セキュリティチェックリスト

**プロジェクト名**: AI見積りシステム
**作成日**: 2025-10-20
**最終更新**: 2025-10-20
**バージョン**: 1.0

---

## 📋 概要

このドキュメントは、AI見積りシステムの運用におけるセキュリティ対策の実施状況を確認するためのチェックリストです。
定期的にこのチェックリストを確認し、セキュリティ態勢を維持してください。

**チェック頻度**:
- 🟢 日次: システム監視、ログ確認
- 🟡 週次: セキュリティイベント確認、リソース監視
- 🔴 月次: 脆弱性スキャン、セキュリティレビュー

---

## 1. 認証・認可

### 1.1 ユーザー認証
- [ ] ユーザー認証実装（現状は未実装、将来的に検討）
- [ ] パスワードポリシー設定（実装時）
- [ ] 多要素認証（MFA）実装（実装時）

### 1.2 APIキー管理
- [x] OpenAI APIキーは環境変数で管理（`.env`ファイル）
- [x] `.env`ファイルは`.gitignore`に追加済み
- [x] APIキーは定期的にローテーション（手動）
- [ ] APIキーのアクセス権限を最小限に設定（OpenAI側で設定）

**確認方法**:
```bash
# .envファイルがGit管理外であることを確認
git check-ignore backend/.env

# APIキーが設定されていることを確認（値は表示されない）
grep -c "OPENAI_API_KEY" backend/.env
```

---

## 2. データ保護

### 2.1 機密情報管理
- [x] APIキーは`.env`ファイルで管理
- [x] `.gitignore`に`.env`追加済み
- [x] システムプロンプトはコード内に分離保存
- [ ] データベース暗号化（Data privacy implementationで検討予定）
- [ ] ログの機密情報マスキング（Monitoring and observabilityで実装予定）

### 2.2 データバックアップ
- [ ] データベースの定期バックアップ（運用時に設定）
- [ ] バックアップデータの暗号化（運用時に設定）
- [ ] バックアップからの復元テスト（運用時に実施）

**確認方法**:
```bash
# .envファイルの権限確認（600推奨）
ls -la backend/.env

# データベースファイルの存在確認
ls -la backend/estimation.db
```

---

## 3. 入力検証

### 3.1 ファイルアップロード
- [x] ファイルサイズ制限（`MAX_UPLOAD_SIZE_MB = 10`）
- [x] ファイル形式検証（Excel: `.xlsx`, CSV: `.csv`のみ許可）
- [x] ファイル内容の検証（列数、データ形式）
- [x] 一時ファイルの適切な削除

**確認方法**:
```bash
# 設定値の確認
grep "MAX_UPLOAD_SIZE_MB" backend/app/core/config.py
```

### 3.2 テキスト入力検証
- [x] 入力テキスト長制限（最大10,000文字）
- [x] 空白文字のみの入力を拒否
- [x] プロンプトインジェクション対策（SecurityService）
- [x] 入力サニタイゼーション（GuardrailsService）

**テスト実行**:
```bash
cd backend
pytest tests/unit/test_guardrails_service.py -v
pytest tests/unit/test_security_service.py -v
```

---

## 4. 出力検証

### 4.1 LLM出力検証
- [x] PII検出・マスキング（GuardrailsService）
- [x] 有害言語検出（GuardrailsService）
- [x] スキーマ検証（JSON形式チェック）
- [x] 出力内容の妥当性検証（金額、工数の範囲チェック）

### 4.2 エラーメッセージ
- [x] ユーザーへのエラーメッセージは最小限の情報のみ
- [x] 詳細なエラー情報はログに記録
- [ ] エラーログの定期レビュー（運用時に実施）

**テスト実行**:
```bash
cd backend
pytest tests/unit/test_guardrails_service.py::TestGuardrailsService::test_validate_output* -v
```

---

## 5. ネットワークセキュリティ

### 5.1 CORS設定
- [x] CORS設定済み（許可されたオリジンのみ）
- [x] 本番環境では適切なオリジンに制限

**確認方法**:
```bash
# CORS設定の確認
grep -A 5 "CORSMiddleware" backend/app/main.py
```

### 5.2 HTTPS通信
- [x] 本番環境でHTTPS強制
- [x] OpenAI APIとの通信はHTTPS
- [ ] SSL/TLS証明書の有効期限監視（運用時に設定）

**確認方法**:
```bash
# 本番環境のURL確認
curl -I https://your-production-domain.com
```

### 5.3 レート制限
- [ ] レート制限実装（Cost management and rate limitingで実装予定）
- [ ] IPアドレスベースの制限（Cost management and rate limitingで実装予定）
- [ ] ユーザーごとの制限（Cost management and rate limitingで実装予定）

---

## 6. API セキュリティ

### 6.1 OpenAI API
- [x] OpenAI APIキー保護（環境変数）
- [x] API呼び出しのエラーハンドリング
- [ ] APIコスト上限設定（Cost management and rate limitingで実装予定）
- [ ] API呼び出しのタイムアウト設定（Resilience implementationで実装予定）
- [ ] APIレスポンスのログ記録（Monitoring and observabilityで実装予定）

### 6.2 API監視
- [ ] API呼び出し回数の監視（Monitoring and observabilityで実装予定）
- [ ] APIエラー率の監視（Monitoring and observabilityで実装予定）
- [ ] APIコストの監視（Cost management and rate limitingで実装予定）

**確認方法**:
```bash
# OpenAI APIキーの存在確認（値は表示されない）
grep -c "OPENAI_API_KEY" backend/.env
```

---

## 7. 依存関係管理

### 7.1 パッケージ管理
- [x] `requirements.txt`でバージョン固定
- [x] 脆弱性のあるパッケージを最新版にアップデート（Securityで実施）
- [ ] 定期的な脆弱性スキャン（月次推奨）

**脆弱性スキャン実施**:
```bash
cd backend
pip-audit --desc
```

### 7.2 アップデート記録
- [x] fastapi: 0.104.1 → 0.109.1（2025-10-20）
- [x] python-multipart: 0.0.6 → 0.0.18（2025-10-20）
- [x] starlette: 0.27.0 → 0.35.1（2025-10-20）

### 7.3 次回スキャン予定
- [ ] **次回予定**: 2025-11-20

---

## 8. ログ・監視

### 8.1 ログ管理
- [x] アプリケーションログの出力
- [ ] 構造化ログ実装（Monitoring and observabilityで実装予定）
- [ ] ログの機密情報マスキング（Monitoring and observabilityで実装予定）
- [ ] ログローテーション設定（運用時に設定）
- [ ] ログの長期保存（運用時に設定）

### 8.2 セキュリティイベント監視
- [ ] セキュリティイベント監視（Monitoring and observabilityで実装予定）
- [ ] 異常検知アラート（Monitoring and observabilityで実装予定）
- [ ] インシデント対応手順（Documentationで文書化予定）

**ログ確認**:
```bash
# アプリケーションログの確認
tail -f /path/to/application.log

# エラーログの確認
grep ERROR /path/to/application.log
```

---

## 9. インシデント対応

### 9.1 エラーハンドリング
- [x] API呼び出しのエラーハンドリング
- [ ] エラーハンドリング強化（Resilience implementationで実装予定）
- [ ] フォールバック処理（Resilience implementationで実装予定）

### 9.2 インシデント対応計画
- [ ] インシデント対応手順書作成（Documentationで作成予定）
- [ ] エスカレーションフロー定義（Documentationで定義予定）
- [ ] インシデント対応訓練（運用時に実施）

---

## 10. テストとカバレッジ

### 10.1 テスト実施
- [x] ユニットテスト実装（Testingで実装完了）
- [x] 統合テスト実装（Testingで実装完了）
- [x] E2Eテスト実装（Testingで実装完了）
- [x] セキュリティテスト実装（Testingで実装完了）

### 10.2 テストカバレッジ
- [x] カバレッジ70%達成（Testingで達成）
- [x] 全152テストPASS

**テスト実行**:
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

**カバレッジ確認**:
```bash
# HTMLレポート確認
open htmlcov/index.html
```

---

## 11. 多言語対応セキュリティ

### 11.1 翻訳ファイル
- [x] 翻訳ファイルの整合性確認（ja.json / en.json）
- [x] セキュリティメッセージの多言語対応
- [x] エラーメッセージの多言語対応

**確認方法**:
```bash
# 翻訳ファイルの存在確認
ls backend/app/locales/ja.json backend/app/locales/en.json

# 翻訳キーの整合性確認
diff <(jq -S 'keys' backend/app/locales/ja.json) <(jq -S 'keys' backend/app/locales/en.json)
```

---

## 12. システムアップデート

### 12.1 定期アップデート
- [ ] Pythonバージョンアップデート（半年ごと推奨）
- [ ] 依存パッケージアップデート（月次推奨）
- [ ] OSセキュリティパッチ適用（月次推奨）

### 12.2 アップデート前のチェック
- [ ] バックアップ取得
- [ ] テスト環境での動作確認
- [ ] ロールバック手順の確認

---

## 13. ドキュメント

### 13.1 セキュリティドキュメント
- [x] OWASP LLM Top 10リスク登録票（ja/en）
- [x] セキュリティチェックリスト（ja/en）
- [x] 脆弱性スキャン結果
- [ ] インシデント対応手順書（Documentationで作成予定）
- [ ] 運用手順書（Documentationで作成予定）

### 13.2 ドキュメント更新
- [ ] 定期レビュー（四半期ごと推奨）
- [ ] 重大な変更時の即時更新
- [ ] バージョン管理

---

## 📊 チェック結果サマリー

### 実装済み（✅）
- **認証・認可**: APIキー管理
- **データ保護**: 機密情報管理、Gitignore設定
- **入力検証**: ファイル・テキスト入力検証、プロンプトインジェクション対策
- **出力検証**: PII検出、有害言語検出、スキーマ検証
- **ネットワーク**: CORS設定、HTTPS強制
- **API**: OpenAI APIキー保護、エラーハンドリング
- **依存関係**: バージョン管理、脆弱性対応
- **テスト**: ユニット/統合/E2E/セキュリティテスト、カバレッジ70%

### 実装予定（📅）
- : エラーハンドリング強化、フォールバック処理、タイムアウト設定
- : インシデント対応手順書、運用手順書
- : 構造化ログ、セキュリティイベント監視、ログマスキング
- : データベース暗号化検討
- : レート制限、APIコスト上限設定

### 運用時に設定（🔧）
- データバックアップ
- ログローテーション
- SSL/TLS証明書監視
- インシデント対応訓練
- 定期レビュー

---

## 🔄 定期チェックスケジュール

### 日次チェック（🟢）
- [ ] システム稼働状況確認
- [ ] エラーログ確認
- [ ] API呼び出し状況確認

### 週次チェック（🟡）
- [ ] セキュリティイベント確認
- [ ] リソース使用状況確認
- [ ] API コスト確認

### 月次チェック（🔴）
- [ ] 脆弱性スキャン実施（pip-audit）
- [ ] セキュリティパッチ適用
- [ ] セキュリティドキュメント更新
- [ ] テスト実行（全テスト）
- [ ] カバレッジ確認

### 四半期チェック（🔵）
- [ ] セキュリティレビュー実施
- [ ] OWASP LLM Top 10リスク評価更新
- [ ] ドキュメント全体レビュー
- [ ] インシデント対応訓練

---

## 📚 参考資料

- `docs/security/OWASP_LLM_RISK_REGISTER.md` - OWASP LLM Top 10リスク登録票
- `docs/security/VULNERABILITY_SCAN.md` - 脆弱性スキャン結果
- `TODO/Testing-detail.md` - テスト実装詳細
- `TODO/Guardrails-detail.md` - Guardrails実装詳細
- `TODO/Security-detail.md` - セキュリティリスク対応詳細

---

**Document Version**: 1.0
**Last Updated**: 2025-10-20
**Status**: Active
**Next Review**: 2025-11-20
