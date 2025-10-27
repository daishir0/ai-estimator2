# 運用Runbook

## 📋 目次

1. [概要](#概要)
2. [日次運用](#日次運用)
3. [週次運用](#週次運用)
4. [月次運用](#月次運用)
5. [障害対応](#障害対応)
6. [メンテナンス手順](#メンテナンス手順)
7. [エスカレーション](#エスカレーション)
8. [連絡先](#連絡先)
9. [チェックリスト](#チェックリスト)

---

## 概要

### 目的

本Runbookは、AI見積りシステムの日常的な運用作業を標準化し、安定したサービス提供を実現することを目的としています。

### 対象読者

- システム運用担当者
- インフラ担当者
- オンコール担当者

### サービスレベル目標 (SLO)

- **稼働率**: 99.0% (月間ダウンタイム < 7.2時間)
- **レスポンスタイム**: P95 < 5秒
- **エラー率**: < 1%

### システム概要

```
Apache HTTPD (Port 443/80)
   ↓
systemd estimator.service (Port 8100)
   ↓
FastAPI + SQLite + OpenAI API
```

---

## 日次運用

### 朝の点検 (09:00)

#### 1. サービス稼働確認

```bash
# サービスステータス確認
systemctl status httpd estimator --no-pager

# 期待される出力: 両方とも "active (running)"
```

**判定基準**:
- ✅ 正常: `active (running)`
- ⚠️ 警告: `activating`（起動中）
- 🔴 異常: `failed`, `inactive`

**異常時の対応**:
1. [障害対応](#障害対応)セクションを参照
2. サービス再起動を試行
3. 改善しない場合はエスカレーション

#### 2. ヘルスチェック

```bash
# ローカルヘルスチェック
curl -s http://127.0.0.1:8100/health

# 期待される出力
{"status":"healthy"}

# 本番環境ヘルスチェック
curl -u username:password https://your-domain.com/api/v1/health
```

**判定基準**:
- ✅ 正常: `{"status":"healthy"}` + HTTPステータス200
- 🔴 異常: エラー応答、タイムアウト、接続拒否

**異常時の対応**:
1. サービスログ確認: `journalctl -u estimator -n 100`
2. Apache再起動: `sudo systemctl restart httpd`
3. estimator再起動: `sudo systemctl restart estimator`

#### 3. ディスク使用量確認

```bash
# ディスク使用量確認
df -h /

# ディスク使用量閾値
# - 警告: 80%以上
# - 危険: 90%以上
```

**警告時の対応**:
```bash
# ログファイルのクリーンアップ
sudo journalctl --vacuum-time=7d

# 古いアップロードファイルの削除（30日以前）
find /path/to/ai-estimator2/backend/uploads -type f -mtime +30 -delete

# 不要なバックアップ削除（60日以前）
find /path/to/backups/estimator -type d -mtime +60 -exec rm -rf {} +
```

#### 4. エラーログ確認

```bash
# estimatorエラーログ（直近24時間）
journalctl -u estimator --since "24 hours ago" -p err

# Apacheエラーログ（直近24時間）
sudo tail -1000 /var/log/httpd/error_log | grep -i error
```

**エラー分類**:
- **OpenAI API Error**: API状態確認、APIキー確認
- **Database Lock**: 同時実行数確認、長時間クエリ調査
- **Memory Error**: メモリ使用量確認、プロセス再起動
- **Timeout**: タイムアウト設定確認、ネットワーク確認

#### 5. リソース使用状況確認

```bash
# CPU・メモリ使用率
top -b -n 1 | head -20

# プロセス別リソース
ps aux | grep -E 'uvicorn|httpd' | grep -v grep

# メモリ閾値
# - 警告: 80%以上
# - 危険: 90%以上
```

**高負荷時の対応**:
1. プロセス再起動（メモリリーク疑い）
2. 不要なプロセス停止
3. スケールアップ検討

### 夕方の点検 (17:00)

#### 1. 本日のリクエスト数確認

```bash
# 本日のアクセス数（Apache）
sudo grep "$(date +%d/%b/%Y)" /var/log/httpd/access_log | wc -l

# 本日の見積り作成数（estimator）
journalctl -u estimator --since "today" | grep "タスク作成" | wc -l
```

#### 2. エラー率確認

```bash
# 本日のエラー数
journalctl -u estimator --since "today" -p err | wc -l

# エラー率 = エラー数 / リクエスト数 × 100
# 閾値: 1%以下
```

#### 3. レスポンスタイム確認

```bash
# 平均レスポンスタイム（Apache access_log解析）
sudo awk '{print $NF}' /var/log/httpd/access_log | \
  grep -E '^[0-9]+$' | \
  awk '{sum+=$1; count++} END {print sum/count/1000000 " seconds"}'
```

### 日次レポート作成

以下の情報をまとめてSlack/メールで報告:

```
【日次運用レポート】2025-10-21

■ サービス稼働状況
- httpd: 正常
- estimator: 正常
- ヘルスチェック: 正常

■ リソース使用状況
- ディスク使用率: 65%
- メモリ使用率: 70%
- CPU使用率: 30%

■ 本日の実績
- アクセス数: 120件
- 見積り作成数: 45件
- エラー数: 2件
- エラー率: 0.44%

■ 特記事項
- 特になし

■ 対応事項
- 特になし
```

---

## 週次運用

### 毎週月曜日 (10:00)

#### 1. バックアップ確認

```bash
# バックアップディレクトリ確認
ls -lht /path/to/backups/estimator/ | head -10

# 最新バックアップの中身確認
LATEST_BACKUP=$(ls -t /path/to/backups/estimator/ | head -1)
ls -lh /path/to/backups/estimator/$LATEST_BACKUP/
```

**確認項目**:
- ✅ app.db が存在
- ✅ .env が存在
- ✅ uploads/ ディレクトリが存在
- ✅ バックアップサイズが妥当（過去と比較）

**異常時の対応**:
1. 手動バックアップ実施
2. cronジョブ確認
3. バックアップスクリプト確認

#### 2. SSL証明書の有効期限確認

```bash
# SSL証明書の有効期限確認
sudo certbot certificates

# 期限が30日以内の場合は警告
# 期限が7日以内の場合は緊急対応
```

**更新手順**:
```bash
# 証明書更新（ドライラン）
sudo certbot renew --dry-run

# 実際の更新
sudo certbot renew

# Apache再読み込み
sudo systemctl reload httpd
```

#### 3. ログローテーション確認

```bash
# estimatorログファイルサイズ確認
ls -lh /var/log/estimator/

# 1ファイルが100MB超えている場合は手動ローテーション
sudo journalctl --rotate
sudo journalctl --vacuum-size=100M
```

#### 4. セキュリティアップデート確認

```bash
# Amazon Linuxセキュリティアップデート確認
sudo yum check-update --security

# アップデート適用（必要に応じて）
sudo yum update --security -y

# 再起動が必要な場合
# - メンテナンスウィンドウで実施
# - 事前にバックアップ取得
```

#### 5. データベース整合性チェック

```bash
# データベースファイル確認
ls -lh /path/to/ai-estimator2/backend/app.db

# SQLite整合性チェック
sqlite3 /path/to/ai-estimator2/backend/app.db "PRAGMA integrity_check;"

# 期待される出力: "ok"
```

**異常時の対応**:
1. データベースバックアップから復旧
2. 開発チームへエスカレーション

### 週次レポート作成

```
【週次運用レポート】2025-10-21 ~ 2025-10-27

■ 稼働状況
- 稼働率: 99.8%
- ダウンタイム: 0分
- インシデント数: 0件

■ パフォーマンス
- 平均レスポンスタイム: 1.2秒
- P95レスポンスタイム: 3.5秒
- エラー率: 0.3%

■ 利用状況
- 総アクセス数: 840件
- 総見積り作成数: 315件
- ユニークユーザー数: 12名

■ リソース使用状況
- 平均CPU使用率: 35%
- 平均メモリ使用率: 72%
- ディスク使用率: 68%

■ セキュリティ
- SSL証明書有効期限: 残り45日
- セキュリティアップデート: 適用済み

■ 特記事項
- 特になし

■ 改善提案
- 特になし
```

---

## 月次運用

### 毎月1日 (10:00)

#### 1. OpenAI API使用量・コスト確認

```bash
# OpenAI使用量確認（ダッシュボード）
# https://platform.openai.com/usage
```

**確認項目**:
- 月間トークン使用量
- 月間コスト
- 予算超過の有無

**予算超過時の対応**:
1. 使用量の詳細分析
2. レート制限の調整
3. プロンプト最適化検討

#### 2. 容量計画レビュー

```bash
# 月間データ増加量
DB_SIZE_START=$(du -h /path/to/backups/estimator/$(ls -t /path/to/backups/estimator/ | tail -1)/app.db | cut -f1)
DB_SIZE_END=$(du -h /path/to/ai-estimator2/backend/app.db | cut -f1)

echo "データベースサイズ変化: $DB_SIZE_START → $DB_SIZE_END"

# ディスク使用量トレンド
df -h / | tail -1
```

**容量拡張が必要な判断基準**:
- ディスク使用率が80%超え
- 月間増加率が20%超え
- 3ヶ月後に90%到達予測

#### 3. パフォーマンスレビュー

**データ収集**:
```bash
# 月間パフォーマンスサマリー
journalctl -u estimator --since "1 month ago" | \
  grep -E "EST.*done" | \
  awk '{print $(NF-1)}' | \
  awk -F's' '{sum+=$1; count++} END {print "平均処理時間:", sum/count, "秒"}'
```

**分析項目**:
- 平均レスポンスタイム
- P95/P99レスポンスタイム
- スローリクエストの調査

#### 4. セキュリティレビュー

```bash
# アクセスログ分析（不審なアクセス）
sudo grep "401" /var/log/httpd/access_log | tail -50

# 失敗したBasic認証の試行
sudo grep "authentication failure" /var/log/httpd/error_log | wc -l
```

**セキュリティチェック項目**:
- 不正アクセス試行の有無
- ブルートフォース攻撃の兆候
- 異常なトラフィックパターン

#### 5. バックアップのテスト復旧

```bash
# テスト用ディレクトリ作成
mkdir -p /tmp/estimator_restore_test

# 最新バックアップを復旧テスト
LATEST_BACKUP=$(ls -t /path/to/backups/estimator/ | head -1)
cp -r /path/to/backups/estimator/$LATEST_BACKUP/* /tmp/estimator_restore_test/

# データベース整合性確認
sqlite3 /tmp/estimator_restore_test/app.db "PRAGMA integrity_check;"

# クリーンアップ
rm -rf /tmp/estimator_restore_test
```

### 月次レポート作成

```
【月次運用レポート】2025年10月

■ サービス稼働状況
- 稼働率: 99.7%
- 総ダウンタイム: 13分
- インシデント数: 1件（軽微）

■ パフォーマンス指標
- 平均レスポンスタイム: 1.3秒
- P95レスポンスタイム: 3.8秒
- P99レスポンスタイム: 8.2秒
- エラー率: 0.4%

■ 利用状況
- 総アクセス数: 3,600件
- 総見積り作成数: 1,350件
- ユニークユーザー数: 45名
- 月間増加率: +15%

■ リソース使用状況
- 平均CPU使用率: 38%
- 最大CPU使用率: 85%
- 平均メモリ使用率: 75%
- ディスク使用率: 72% (+5%増)

■ コスト
- EC2: $15.00
- OpenAI API: $2.80
- 合計: $17.80

■ セキュリティ
- 不正アクセス試行: 3件（全てブロック済み）
- SSL証明書更新: 正常
- セキュリティアップデート: 全て適用済み

■ バックアップ
- 定期バックアップ: 正常
- バックアップ復旧テスト: 成功

■ インシデントサマリー
1. 2025-10-15 10:23: OpenAI APIタイムアウト（13分）
   - 原因: OpenAI側の一時的な障害
   - 対応: 自動復旧
   - 再発防止策: リトライロジック強化済み

■ 改善実施事項
- CircuitBreaker実装（Resilience implementation）
- レート制限強化（Cost management and rate limiting）

■ 次月の予定
- データベースパフォーマンス最適化
- 監視ダッシュボード構築検討
```

---

## 障害対応

### 障害レベル定義

| レベル | 影響範囲 | 対応時間 | エスカレーション |
|--------|---------|---------|----------------|
| **P1 (緊急)** | サービス全停止 | 即時 | 即座に上位者 |
| **P2 (重要)** | 一部機能停止 | 30分以内 | 30分後に上位者 |
| **P3 (通常)** | パフォーマンス劣化 | 2時間以内 | 2時間後に上位者 |
| **P4 (軽微)** | 一部エラー発生 | 24時間以内 | 不要 |

### 障害対応フロー

```
障害検知
   ↓
初動対応（5分以内）
 - 影響範囲確認
 - 障害レベル判定
 - 初期エスカレーション
   ↓
原因調査（15分以内）
 - ログ確認
 - リソース確認
 - 外部サービス確認
   ↓
復旧作業
 - 再起動
 - 設定変更
 - ロールバック
   ↓
動作確認
 - ヘルスチェック
 - 機能テスト
   ↓
事後対応
 - インシデントレポート作成
 - 再発防止策検討
```

### P1: サービス全停止

#### 症状
- ヘルスチェック失敗
- サービス応答なし
- 全ユーザー影響

#### 初動対応（5分以内）

```bash
# 1. サービスステータス確認
systemctl status httpd estimator

# 2. プロセス確認
ps aux | grep -E 'uvicorn|httpd'

# 3. ポート確認
lsof -i :443 -i :80 -i :8100

# 4. エラーログ確認
journalctl -u estimator -n 50
sudo tail -50 /var/log/httpd/error_log
```

#### 復旧手順

**ステップ1: サービス再起動**
```bash
# estimator再起動
sudo systemctl restart estimator

# Apache再起動
sudo systemctl restart httpd

# 30秒待機
sleep 30

# ヘルスチェック
curl -s http://127.0.0.1:8100/health
```

**ステップ2: それでも復旧しない場合**
```bash
# EC2インスタンス再起動
sudo reboot

# 再起動後（3分待機）
# サービス自動起動確認
systemctl status httpd estimator
```

**ステップ3: 完全復旧しない場合**
1. バックアップから復旧 → [バックアップ・復旧手順](../deployment/DEPLOYMENT.md#バックアップ復旧)
2. 開発チームへエスカレーション

### P2: 一部機能停止

#### 症状
- 見積り生成のみ失敗
- 特定エンドポイントでエラー
- 一部ユーザー影響

#### 復旧手順

**OpenAI API障害の場合**
```bash
# OpenAI API状態確認
curl -s https://status.openai.com/api/v2/status.json | jq '.status.description'

# OpenAI側の障害の場合は自動復旧を待つ
# 復旧後、estimator再起動
sudo systemctl restart estimator
```

**データベースロックの場合**
```bash
# 長時間実行中のプロセス確認
ps aux | grep uvicorn

# プロセス再起動
sudo systemctl restart estimator
```

### P3: パフォーマンス劣化

#### 症状
- レスポンス時間が5秒以上
- タイムアウト頻発
- ユーザー体験低下

#### 原因調査

```bash
# CPU使用率確認
top -b -n 1 | head -20

# メモリ使用率確認
free -h

# ディスクI/O確認
iostat -x 1 5

# プロセス別リソース
ps aux --sort=-%cpu | head -10
ps aux --sort=-%mem | head -10
```

#### 対処方法

**高CPU使用率の場合**
```bash
# プロセス再起動
sudo systemctl restart estimator

# それでも改善しない場合
# インスタンスタイプ変更を検討
```

**高メモリ使用率の場合**
```bash
# メモリリーク疑い
sudo systemctl restart estimator

# キャッシュクリア
sync; echo 3 | sudo tee /proc/sys/vm/drop_caches
```

### P4: 一部エラー発生

#### 症状
- エラー率が1%未満
- 特定条件でのみ発生
- サービス継続可能

#### 対応

```bash
# エラーログ収集
journalctl -u estimator --since "1 hour ago" -p err > /tmp/error_log.txt

# エラーパターン分析
cat /tmp/error_log.txt | grep -oP 'Error: \K.*' | sort | uniq -c | sort -rn

# 開発チームへ報告（24時間以内）
```

---

## メンテナンス手順

### 計画メンテナンス

#### 事前準備（メンテナンス1週間前）

1. **メンテナンス通知**
   - ユーザーへ通知（Slack/メール）
   - メンテナンス日時・予定時間・影響範囲を明記

2. **バックアップ取得**
   ```bash
   /home/your-username/scripts/backup_estimator.sh
   ```

3. **メンテナンス手順書作成**
   - 作業ステップの明確化
   - ロールバック手順の確認

#### メンテナンス実施

**ステップ1: サービス停止**
```bash
# メンテナンスページ表示（Apacheで実装）
# または503エラーページ表示

# estimator停止
sudo systemctl stop estimator

# ステータス確認
systemctl status estimator
```

**ステップ2: 作業実施**
```bash
# 例: コード更新
cd /path/to/ai-estimator2
git pull origin main

# 例: 依存関係更新
cd backend
source /path/to/python/bin/activate
conda activate your-python-env
pip install -r requirements.txt

# 例: データベースマイグレーション
# （必要に応じて）
```

**ステップ3: サービス起動**
```bash
# estimator起動
sudo systemctl start estimator

# 起動待機
sleep 10

# ステータス確認
systemctl status estimator
```

**ステップ4: 動作確認**
```bash
# ヘルスチェック
curl -s http://127.0.0.1:8100/health

# 機能テスト
# - タスク作成
# - 質問生成
# - 見積り生成
# - Excel出力
```

**ステップ5: メンテナンス完了通知**
- ユーザーへ完了通知
- 作業結果の報告

#### メンテナンス失敗時

```bash
# ロールバック実施
git checkout <previous-commit>
sudo systemctl restart estimator

# それでも復旧しない場合
# バックアップから復旧
```

### 緊急メンテナンス

#### セキュリティパッチ適用

```bash
# 1. バックアップ取得
/home/your-username/scripts/backup_estimator.sh

# 2. パッチ適用
sudo yum update --security -y

# 3. サービス再起動（必要な場合）
sudo systemctl restart estimator

# 4. 動作確認
curl -s http://127.0.0.1:8100/health
```

#### SSL証明書更新

```bash
# 1. 証明書更新
sudo certbot renew

# 2. Apache設定リロード
sudo systemctl reload httpd

# 3. SSL確認
echo | openssl s_client -connect your-domain.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

---

## エスカレーション

### エスカレーション基準

| 状況 | エスカレーション先 | タイミング |
|------|------------------|-----------|
| P1障害発生 | インフラ責任者 | 即座 |
| P1障害が30分以内に復旧しない | CTO/開発責任者 | 30分後 |
| P2障害が2時間以内に復旧しない | インフラ責任者 | 2時間後 |
| セキュリティインシデント | セキュリティ責任者 | 即座 |
| データ損失の可能性 | CTO/開発責任者 | 即座 |

### エスカレーション手順

1. **初期報告**（5分以内）
   - 障害発生時刻
   - 障害レベル
   - 影響範囲
   - 初期対応内容

2. **定期報告**（15分ごと）
   - 現在の状況
   - 調査結果
   - 復旧見込み

3. **復旧報告**
   - 復旧時刻
   - 根本原因
   - 再発防止策

### エスカレーション連絡テンプレート

```
【障害報告】AI見積りシステム

■ 障害レベル: P1（緊急）

■ 発生時刻: 2025-10-21 10:23

■ 現在の状況: サービス全停止中

■ 影響範囲: 全ユーザー

■ 原因: 調査中

■ 初期対応:
- estimatorサービス再起動実施 → 失敗
- Apacheサービス再起動実施 → 失敗
- 現在、ログ解析中

■ 次のアクション:
- EC2インスタンス再起動を実施予定（10:30）

■ 復旧見込み: 10:40

■ 報告者: 運用担当者A
```

---

## 連絡先

### 緊急連絡先

| 役割 | 名前 | 連絡先 | 対応時間 |
|------|------|--------|---------|
| インフラ責任者 | [名前] | [メール/電話] | 24/7 |
| 開発責任者 | [名前] | [メール/電話] | 平日9-18時 |
| CTO | [名前] | [メール/電話] | 24/7（P1のみ） |
| セキュリティ責任者 | [名前] | [メール/電話] | 24/7 |

### 外部サービス連絡先

| サービス | 問い合わせ先 | ステータスページ |
|---------|------------|----------------|
| OpenAI | https://help.openai.com/ | https://status.openai.com/ |
| AWS | AWS Support Console | https://status.aws.amazon.com/ |
| Let's Encrypt | https://letsencrypt.org/contact/ | https://letsencrypt.status.io/ |

---

## チェックリスト

### 日次チェックリスト

```
【日次運用チェックリスト】

日付: ___________
担当者: ___________

□ サービス稼働確認（httpd/estimator）
□ ヘルスチェック実行（ローカル/本番）
□ ディスク使用量確認（< 80%）
□ エラーログ確認（直近24時間）
□ リソース使用状況確認（CPU/メモリ）
□ 本日のリクエスト数確認
□ エラー率確認（< 1%）
□ 日次レポート作成・送信

特記事項:
___________________________
___________________________
___________________________
```

### 週次チェックリスト

```
【週次運用チェックリスト】

週: ___________
担当者: ___________

□ バックアップ確認（存在・サイズ）
□ SSL証明書有効期限確認（> 30日）
□ ログローテーション確認
□ セキュリティアップデート確認・適用
□ データベース整合性チェック
□ 週次レポート作成・送信

特記事項:
___________________________
___________________________
___________________________
```

### 月次チェックリスト

```
【月次運用チェックリスト】

月: ___________
担当者: ___________

□ OpenAI API使用量・コスト確認
□ 容量計画レビュー
□ パフォーマンスレビュー
□ セキュリティレビュー
□ バックアップのテスト復旧
□ 月次レポート作成・送信

特記事項:
___________________________
___________________________
___________________________
```

---

## 参考資料

- [DEPLOYMENT.md](../deployment/DEPLOYMENT.md) - デプロイメントガイド
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - トラブルシューティングガイド
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - アーキテクチャドキュメント

---

**最終更新**: 2025-10-21
**作成者**: Claude Code
**バージョン**: 1.0
