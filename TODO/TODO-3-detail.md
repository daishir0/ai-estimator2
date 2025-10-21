# TODO-3: セキュリティリスク対応（OWASP LLM Top 10）

## 📋 概要
- **目的**: OWASP LLM Top 10に基づくセキュリティリスクを評価し、リスク登録票とセキュリティチェックリストを作成する
- **期間**: Day 6
- **優先度**: 🔴 最高
- **依存関係**: TODO-2（Guardrails実装）完了後

## 🎯 達成基準
- [ ] OWASP LLM Top 10リスク登録票作成完了
- [ ] セキュリティチェックリスト作成完了
- [ ] 各リスクの対策状況を明記
- [ ] 未対応リスクのTODO明確化
- [ ] ドキュメント多言語対応（ja/en）
- [ ] レビュー完了

---

## 📐 計画

### 1. OWASP LLM Top 10 分析

#### システムへの該当性評価

| ID | リスク名 | 該当性 | 深刻度 | 対策状況 |
|----|---------|--------|--------|---------|
| LLM01 | プロンプトインジェクション | ✅ 該当 | 高 | TODO-2で実装 |
| LLM02 | 安全でない出力処理 | ✅ 該当 | 中 | TODO-2で実装 |
| LLM03 | 訓練データポイズニング | ❌ 非該当 | - | 外部API使用 |
| LLM04 | モデルサービス拒否（DoS） | ✅ 該当 | 中 | TODO-9で実装予定 |
| LLM05 | サプライチェーン脆弱性 | ✅ 該当 | 低 | 依存管理で対応 |
| LLM06 | 機密情報漏洩 | ✅ 該当 | 高 | TODO-2で実装 |
| LLM07 | 安全でないプラグイン設計 | ❌ 非該当 | - | プラグインなし |
| LLM08 | 過度な権限 | ❌ 非該当 | - | ツール呼び出しなし |
| LLM09 | 過度な依存 | ✅ 該当 | 中 | TODO-5で対応予定 |
| LLM10 | モデル盗難 | ❌ 非該当 | - | 外部API使用 |

### 2. ドキュメント構成

#### 2.1 リスク登録票（docs/security/OWASP_LLM_RISK_REGISTER.md）

**構成**:
```markdown
# OWASP LLM Top 10 リスク登録票

## 概要
このドキュメントは、AI見積りシステムにおけるOWASP LLM Top 10に基づくセキュリティリスクの評価と対策状況を記録します。

## リスク一覧

### LLM01: プロンプトインジェクション
**該当性**: ✅ 該当
**深刻度**: 🔴 高
**説明**: ユーザー入力（システム要件、回答）を通じて、LLMに不正な指示を注入される可能性
**影響**:
- 不適切な見積り生成
- 機密情報の漏洩
- システムの誤動作

**対策**:
1. SecurityServiceによるパターンマッチング検出（TODO-2）
2. GuardrailsServiceによる入力検証（TODO-2）
3. プロンプトテンプレートの分離（実装済み）

**実装場所**:
- `app/services/security_service.py`
- `app/services/guardrails_service.py`
- `app/api/v1/tasks.py`

**検証方法**:
- プロンプトインジェクション攻撃シミュレーション
- セキュリティテスト（TODO-1）

**状態**: ✅ 実装済み（TODO-2）

---

### LLM02: 安全でない出力処理
**該当性**: ✅ 該当
**深刻度**: 🟡 中
**説明**: LLM生成コンテンツに有害な内容やPII情報が含まれる可能性
**影響**:
- ユーザーへの不適切な情報提供
- プライバシー侵害

**対策**:
1. GuardrailsServiceによる出力検証（TODO-2）
2. PII検出・マスキング（TODO-2）
3. 有害言語検出（TODO-2）

**実装場所**:
- `app/services/guardrails_service.py`
- `app/services/question_service.py`
- `app/services/estimator_service.py`
- `app/services/chat_service.py`

**検証方法**:
- LLM出力検証テスト（TODO-1）

**状態**: ✅ 実装済み（TODO-2）

---

（LLM03〜LLM10まで同様の形式で記述）
```

#### 2.2 セキュリティチェックリスト（docs/security/SECURITY_CHECKLIST.md）

**構成**:
```markdown
# セキュリティチェックリスト

## 認証・認可
- [ ] ユーザー認証実装（現状は未実装、将来的に検討）
- [ ] APIキー管理（環境変数）

## データ保護
- [x] APIキーは.envファイルで管理
- [x] .gitignoreに.env追加済み
- [ ] データベース暗号化（TODO-8で検討）
- [ ] ログの機密情報マスキング（TODO-7）

## 入力検証
- [x] ファイルサイズ制限（MAX_UPLOAD_SIZE_MB）
- [x] ファイル形式検証（Excel/CSV）
- [x] 入力テキスト検証（Guardrails）
- [x] プロンプトインジェクション対策

## 出力検証
- [x] PII検出・マスキング
- [x] 有害言語検出
- [x] スキーマ検証

## ネットワークセキュリティ
- [x] CORS設定済み
- [x] 本番環境HTTPS強制
- [ ] レート制限実装（TODO-9）

## API セキュリティ
- [x] OpenAI APIキー保護
- [ ] APIコスト上限設定（TODO-9）
- [ ] タイムアウト設定（TODO-5）

## 依存関係管理
- [x] requirements.txtでバージョン固定
- [ ] 脆弱性スキャン（TODO-3で検討）

## ログ・監視
- [ ] 構造化ログ実装（TODO-7）
- [ ] セキュリティイベント監視（TODO-7）

## インシデント対応
- [ ] エラーハンドリング強化（TODO-5）
- [ ] フォールバック処理（TODO-5）
```

#### 2.3 脆弱性スキャン結果（docs/security/VULNERABILITY_SCAN.md）

**内容**:
- `pip-audit`を使った依存関係の脆弱性スキャン
- 発見された脆弱性と対応状況
- 定期スキャンの推奨

### 3. 実装内容

#### 3.1 ディレクトリ構成
```
output3/docs/
└── security/
    ├── OWASP_LLM_RISK_REGISTER.md  (日本語版)
    ├── OWASP_LLM_RISK_REGISTER_EN.md  (英語版)
    ├── SECURITY_CHECKLIST.md  (日本語版)
    ├── SECURITY_CHECKLIST_EN.md  (英語版)
    └── VULNERABILITY_SCAN.md
```

#### 3.2 脆弱性スキャン実施

**手順**:
```bash
# pip-auditインストール
pip install pip-audit

# スキャン実行
cd backend
pip-audit --desc --format json > ../docs/security/vulnerability_scan.json

# 人間が読める形式で出力
pip-audit --desc > ../docs/security/VULNERABILITY_SCAN.md
```

### 4. 技術スタック

- **Markdown**: ドキュメント記述
- **pip-audit**: 依存関係の脆弱性スキャン
- **OWASP LLM Top 10**: セキュリティ評価基準

### 5. 影響範囲

**新規作成ファイル**
- `docs/security/OWASP_LLM_RISK_REGISTER.md`
- `docs/security/OWASP_LLM_RISK_REGISTER_EN.md`
- `docs/security/SECURITY_CHECKLIST.md`
- `docs/security/SECURITY_CHECKLIST_EN.md`
- `docs/security/VULNERABILITY_SCAN.md`

**変更ファイル**
- なし（ドキュメントのみ）

### 6. リスクと対策

#### リスク1: リスク評価の不正確さ
- **対策**: OWASP公式ドキュメント参照、専門家レビュー

#### リスク2: 対策の漏れ
- **対策**: TODO-1〜TODO-9全体での実装状況を相互参照

#### リスク3: ドキュメントの陳腐化
- **対策**: 各TODO完了時にリスク登録票を更新

### 7. スケジュール

**Day 6**:
- OWASP LLM Top 10分析
- リスク登録票作成（ja/en）
- セキュリティチェックリスト作成（ja/en）
- 脆弱性スキャン実施
- ドキュメントレビュー

---

## 🔧 実施内容（実績）

### Day 6: 2025-10-20

#### 実施作業
- [x] pip-auditインストールと脆弱性スキャン実施
- [x] システム関連脆弱性の抽出と分析
- [x] 脆弱性のあるパッケージのアップデート
  - fastapi: 0.104.1 → 0.109.1
  - python-multipart: 0.0.6 → 0.0.18
  - starlette: 0.27.0 → 0.35.1（依存関係で自動アップデート）
- [x] テスト実行による動作確認（全152テストPASS）
- [x] OWASP LLM Top 10リスク登録票作成（日本語・英語）
- [x] セキュリティチェックリスト作成（日本語・英語）
- [x] 脆弱性スキャン結果ドキュメント作成
- [x] Slack進捗報告

#### 作成ファイル
- `docs/security/OWASP_LLM_RISK_REGISTER.md` - OWASP LLM Top 10リスク登録票（日本語）
- `docs/security/OWASP_LLM_RISK_REGISTER_EN.md` - OWASP LLM Top 10リスク登録票（英語）
- `docs/security/SECURITY_CHECKLIST.md` - セキュリティチェックリスト（日本語）
- `docs/security/SECURITY_CHECKLIST_EN.md` - セキュリティチェックリスト（英語）
- `docs/security/VULNERABILITY_SCAN.md` - 脆弱性スキャン結果

#### 変更ファイル
- `backend/requirements.txt` - パッケージバージョン更新
  - fastapi==0.109.1
  - python-multipart==0.0.18

#### 脆弱性スキャン結果
- **検出された全脆弱性数**: 36件（21パッケージ）
- **システムに関連する脆弱性数**: 3件（3パッケージ）
- **対応完了**: 3件すべて対応完了

**対応した脆弱性**:
1. fastapi 0.104.1 → 0.109.1（PYSEC-2024-38: ReDoS）
2. python-multipart 0.0.6 → 0.0.18（GHSA-2jv5-9r88-3w3p: ReDoS、GHSA-59g5-xgcq-4qw3: DoS）
3. starlette 0.27.0 → 0.35.1（GHSA-f96h-pmfr-66vw: DoS、GHSA-2c2j-9gv5-cj73: ブロッキング）

#### テスト結果
- **全テスト数**: 152テスト
- **成功**: 152テスト（100%）
- **カバレッジ**: 70%
- **実行時間**: 9.28秒

#### 課題・気づき
- yt-dlpなど、システムで使用していないパッケージの脆弱性も大量に検出されたため、requirements.txtに基づいて関連脆弱性のみを抽出する必要があった
- python-multipart 0.0.18を指定したが、最初は0.0.9がインストールされたため、--force-reinstallで再インストールが必要だった
- 依存関係の警告（app、generalmaster-backendプロジェクト）が出たが、このプロジェクトには影響なし

---

## 📊 実績

### 達成した成果
1. **OWASP LLM Top 10リスク評価の完全実施**
   - 10個のリスクをシステムに照らして評価
   - 該当リスク6件、非該当リスク4件を明確化
   - 各リスクの対策状況と今後の実装予定を文書化

2. **セキュリティドキュメント整備**
   - 4つのセキュリティドキュメントを日本語・英語で作成（計5ファイル）
   - 運用向けチェックリストの整備
   - 定期的なセキュリティレビューの仕組み構築

3. **脆弱性対応の完了**
   - システムで使用する全パッケージの脆弱性を解決
   - 全152テストが引き続きPASS
   - システムの安定性を維持

### 発見されたセキュリティ課題
1. **サプライチェーンリスク**
   - 依存パッケージに複数の脆弱性が存在（今回対応完了）
   - 定期的な脆弱性スキャンの必要性を確認

2. **残存リスク**
   - LLM04（モデルDoS）: レート制限未実装 → TODO-9で対応予定
   - LLM09（過度な依存）: リトライロジック未実装 → TODO-5で対応予定
   - ログの機密情報マスキング未実装 → TODO-7で対応予定
   - データベース暗号化未実装 → TODO-8で検討予定

3. **継続的な対策の必要性**
   - 高度なプロンプトインジェクション技術への監視
   - 新しい攻撃手法への対応
   - OpenAI APIの障害時対応

### 学び
1. **pip-auditの活用**
   - 定期的な脆弱性スキャンが重要
   - システムに関連するパッケージのみを抽出して対応することでノイズを削減
   - 月次スキャンのスケジュールを設定

2. **OWASP LLM Top 10の重要性**
   - LLMシステム特有のリスクを体系的に理解
   - 従来のWebアプリケーションセキュリティとは異なる観点が必要
   - プロンプトインジェクション、出力検証など、LLM特有の対策が重要

3. **ドキュメントの重要性**
   - セキュリティ対策は実装だけでなく、ドキュメント化も重要
   - 運用担当者向けのチェックリストで継続的なセキュリティ維持
   - 多言語対応により国際的な展開にも対応

---

## ✅ 完了チェックリスト
- [x] OWASP LLM Top 10リスク登録票完成（ja/en）
- [x] セキュリティチェックリスト完成（ja/en）
- [x] 脆弱性スキャン実施・記録
- [x] すべてのリスクの対策状況を明記
- [x] 未対応リスクのTODO参照を明記
- [x] ドキュメントレビュー完了（セルフレビュー）
- [x] テスト実行確認（全152テストPASS）
- [x] 多言語対応確認（ja/en）

## 📚 参考資料
- todo.md (259-332行目): TODO-3詳細
- `/home/ec2-user/hirashimallc/02_pj-ReadyTensor/output/doc/34_autonomy-meets-attack-securing-agentic-ai-from-real-world-exploits-aaidc-week9-lesson3.md`
- OWASP LLM Top 10: https://owasp.org/www-project-top-10-for-large-language-model-applications/

---

**作成日**: 2025-10-18
**最終更新**: 2025-10-20
**担当**: Claude Code
**ステータス**: 完了
