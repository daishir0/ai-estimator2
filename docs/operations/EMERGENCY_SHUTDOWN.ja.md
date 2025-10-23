# 緊急停止手順書

**バージョン**: 1.0
**最終更新**: 2025-10-22
**対象**: AI見積りシステム
**目的**: OpenAI APIコスト超過時または不正アクセス検出時の緊急対応手順

---

## 📋 目次

1. [概要](#概要)
2. [コスト超過時の緊急停止手順](#コスト超過時の緊急停止手順)
3. [不正アクセス検出時の対応](#不正アクセス検出時の対応)
4. [サービス再開手順](#サービス再開手順)
5. [連絡先](#連絡先)
6. [定期確認事項](#定期確認事項)

---

## 概要

本文書は、以下の緊急事態に対応するための手順を定めます：

1. **OpenAI APIコスト超過**: 月次コスト上限（デフォルト: $200/月）を超過した場合
2. **不正アクセス・DoS攻撃**: レート制限を超過するアクセスが継続する場合
3. **その他の異常動作**: 予期しない大量のAPI呼び出しが発生した場合

---

## コスト超過時の緊急停止手順

### ⚠️ 緊急停止トリガー

以下のいずれかの状況で緊急停止を検討：

| 状況 | 閾値 | 対応 |
|------|------|------|
| 月次コスト警告 | $160（80%） | 監視強化 |
| 月次コスト超過 | $200（100%） | **自動停止** |
| 異常な増加率 | 1時間で$10以上 | 即座に調査・停止検討 |

### 🛑 ステップ1: システム即座停止

```bash
# SSH接続
ssh your-username@<サーバーIP>

# サービス即座停止
sudo systemctl stop estimator

# 停止確認
sudo systemctl status estimator
```

**結果**: `inactive (dead)` と表示されることを確認

---

### 📊 ステップ2: コスト状況確認

管理者エンドポイントでコスト状況を確認（サービス停止前に確認する場合）：

```bash
# コスト状況取得
curl http://localhost:8009/api/v1/admin/costs

# レスポンス例
{
  "cost": {
    "daily_cost_usd": 8.5234,
    "monthly_cost_usd": 215.4567,
    "daily_limit_usd": 10.0,
    "monthly_limit_usd": 200.0,
    "daily_usage_percent": 85.23,
    "monthly_usage_percent": 107.73
  },
  "metrics": {
    "total_openai_calls": 1250,
    "total_tokens_used": 2500000
  }
}
```

**確認ポイント**:
- `monthly_cost_usd`: 月次累計コスト
- `monthly_usage_percent`: 上限に対する使用率
- `total_openai_calls`: API呼び出し回数

---

### 🔍 ステップ3: 原因調査

#### ログ確認

```bash
# エラーログ確認（最新100行）
sudo journalctl -u estimator -n 100 --no-pager

# コスト関連ログ抽出
sudo journalctl -u estimator | grep -i "cost"

# 特定時刻のログ確認
sudo journalctl -u estimator --since "2025-10-22 10:00:00" --until "2025-10-22 11:00:00"
```

#### 異常パターンの特定

**確認すべき異常**:
1. **大量のAPI呼び出し**: 特定のエンドポイントに集中したアクセス
2. **異常に長いプロンプト**: 入力トークン数が通常の10倍以上
3. **リトライループ**: 同じリクエストが短時間に大量発生
4. **不正アクセス**: 特定IPからの異常なアクセス

---

### 🔧 ステップ4: 設定調整

原因に応じて設定を調整：

#### 4.1 コスト上限引き下げ

```bash
# .envファイル編集
cd /path/to/ai-estimator2/backend
nano .env

# 以下を編集
DAILY_COST_LIMIT=5.0      # デフォルト: 10.0
MONTHLY_COST_LIMIT=100.0  # デフォルト: 200.0
```

#### 4.2 レート制限強化

```bash
# .envファイル編集
nano .env

# 以下を編集
RATE_LIMIT_MAX_REQUESTS=50   # デフォルト: 100
RATE_LIMIT_WINDOW_SECONDS=3600  # 1時間（変更不要の場合が多い）
```

#### 4.3 並列実行数制限

```bash
# .envファイル編集
nano .env

# 以下を追加/編集
MAX_CONCURRENT_ESTIMATES=2  # デフォルト: 5
```

---

### ✅ ステップ5: 再開前チェックリスト

- [ ] コスト超過の原因を特定
- [ ] 設定変更を実施（必要な場合）
- [ ] OpenAIダッシュボードで実際の使用量を確認
- [ ] 翌月の開始まで待機するか、上限を引き上げるか決定
- [ ] 監視体制を強化（定期確認スクリプト設定等）

---

## 不正アクセス検出時の対応

### 🚨 検出方法

#### レート制限超過ログの確認

```bash
# レート制限超過のログを抽出
sudo journalctl -u estimator | grep "Rate limit exceeded"

# 特定IPのレート制限超過確認
sudo journalctl -u estimator | grep "Rate limit exceeded" | grep "192.168.1.100"
```

#### 管理者エンドポイントでの確認

```bash
# レート制限状況確認
curl http://localhost:8009/api/v1/admin/rate-limits

# レスポンス例
{
  "max_requests": 100,
  "window_seconds": 3600,
  "active_clients": 25
}
```

---

### 🛡️ 対応手順

#### 1. 特定IPのレート制限リセット

```bash
# 正常なIPの場合のみ実施
curl -X POST http://localhost:8009/api/v1/admin/reset-rate-limit/192.168.1.100
```

#### 2. ファイアウォールでのブロック（悪意あるアクセスの場合）

```bash
# 特定IPをブロック
sudo iptables -A INPUT -s 192.168.1.100 -j DROP

# 設定保存
sudo service iptables save

# 確認
sudo iptables -L -n
```

#### 3. レート制限強化（システム全体）

前述の「ステップ4.2 レート制限強化」を参照

---

## サービス再開手順

### 1. 設定変更の反映

```bash
# 設定ファイル編集後、サービス再起動
cd /path/to/ai-estimator2/backend
sudo systemctl restart estimator
```

### 2. 再開確認

```bash
# サービス状態確認
sudo systemctl status estimator

# ヘルスチェック
curl http://localhost:8009/health

# レスポンス: {"status":"healthy"}
```

### 3. 監視開始

```bash
# リアルタイムログ監視
sudo journalctl -u estimator -f

# コスト状況定期確認（別ターミナル）
watch -n 300 'curl -s http://localhost:8009/api/v1/admin/costs | jq .'
```

**監視項目**:
- 5分ごとにコスト状況確認
- エラーログの監視
- レート制限超過の監視

---

## 連絡先

### システム管理者

| 役割 | 連絡先 | 対応時間 |
|------|--------|---------|
| プライマリ管理者 | admin@example.com | 24/7 |
| セカンダリ管理者 | backup@example.com | 平日9-18時 |
| 緊急連絡先 | +81-XX-XXXX-XXXX | 24/7 |

### 外部サービス

| サービス | ダッシュボードURL | 備考 |
|---------|------------------|------|
| OpenAI API | https://platform.openai.com/usage | APIキー: `OPENAI_API_KEY` |
| AWS (サーバー) | https://console.aws.amazon.com/ec2/ | EC2インスタンス管理 |

---

## 定期確認事項

### 日次確認（推奨）

```bash
# コスト状況確認
curl http://localhost:8009/api/v1/admin/costs

# 確認項目：
# - daily_usage_percent < 80%
# - monthly_usage_percent < 90%
```

### 週次確認（推奨）

```bash
# メトリクス全体確認
curl http://localhost:8009/api/v1/admin/metrics

# 確認項目：
# - エラー率 < 5%
# - OpenAI成功率 > 95%
# - レート制限超過の有無
```

### 月次確認（必須）

1. OpenAIダッシュボードで実際の請求額を確認
2. システムログとの整合性確認
3. コスト上限設定の見直し

---

## 付録: 自動監視スクリプト

### コスト監視スクリプト

```bash
#!/bin/bash
# /home/your-username/scripts/monitor_costs.sh

THRESHOLD=80
RESPONSE=$(curl -s http://localhost:8009/api/v1/admin/costs)
USAGE=$(echo $RESPONSE | jq -r '.cost.daily_usage_percent')

if (( $(echo "$USAGE > $THRESHOLD" | bc -l) )); then
    echo "WARNING: Daily cost usage at ${USAGE}%"
    # メール通知やSlack通知を追加
fi
```

### cron設定例

```bash
# crontab -e で以下を追加
# 1時間ごとにコスト監視
0 * * * * /home/your-username/scripts/monitor_costs.sh
```

---

**作成日**: 2025-10-22
**作成者**: Claude Code
**バージョン**: 1.0
**承認者**: (承認者名)

---

## 変更履歴

| 日付 | バージョン | 変更内容 | 変更者 |
|------|-----------|---------|--------|
| 2025-10-22 | 1.0 | 初版作成 | Claude Code |
