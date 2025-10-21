# AI見積りシステム 監視計画

**最終更新**: 2025-10-22
**バージョン**: 1.0
**対象システム**: AI見積りシステム (Estimator Backend)

---

## 📋 目次

1. [概要](#概要)
2. [監視対象指標](#監視対象指標)
3. [SLI/SLO/SLA](#slislosla)
4. [警戒閾値とアラート](#警戒閾値とアラート)
5. [ログ確認方法](#ログ確認方法)
6. [トラブルシューティング](#トラブルシューティング)
7. [将来の拡張](#将来の拡張)

---

## 概要

### 監視の目的

AI見積りシステムの運用状況を可視化し、以下を実現する：

- **早期障害検知**: エラー発生を即座に検知し、ユーザー影響を最小化
- **性能劣化の検知**: API応答時間の悪化を早期に発見
- **リソース使用量の追跡**: OpenAI APIトークン消費量を監視しコスト管理
- **運用品質の向上**: メトリクスに基づいた継続的改善

### 監視アーキテクチャ

```
┌─────────────────┐
│  FastAPI App    │
│  (Estimator)    │
└────────┬────────┘
         │
         ├─→ 構造化ログ (JSON)
         │   - リクエストID
         │   - レベル (INFO/WARNING/ERROR)
         │   - タイムスタンプ
         │   - カスタムフィールド
         │
         ├─→ メトリクス収集
         │   - API呼び出し統計
         │   - OpenAI使用量
         │   - エラー発生状況
         │
         └─→ ヘルスチェック
             - /health (基本)
             - /api/v1/health (詳細)
             - /api/v1/metrics (統計)
```

---

## 監視対象指標

### 1. API応答性能

| 指標 | 説明 | 取得方法 |
|------|------|----------|
| **平均応答時間** | 全APIエンドポイントの平均応答時間（秒） | `GET /api/v1/metrics` → `avg_response_time` |
| **P95応答時間** | 95パーセンタイル応答時間（秒） | `GET /api/v1/metrics` → `p95_response_time` |
| **総API呼び出し数** | 累積API呼び出し回数 | `GET /api/v1/metrics` → `total_api_calls` |

**監視ポイント**:
- 平均応答時間が3秒を超えたら注意
- P95応答時間が10秒を超えたら警告

### 2. API成功率

| 指標 | 説明 | 取得方法 |
|------|------|----------|
| **成功率** | HTTP 2xx レスポンスの割合（%） | `GET /api/v1/metrics` → `success_rate` |
| **エラー率** | エラー発生の割合（%） | `GET /api/v1/metrics` → `error_rate` |
| **総エラー数** | 累積エラー発生回数 | `GET /api/v1/metrics` → `total_errors` |

**監視ポイント**:
- 成功率が95%を下回ったら警告
- エラー率が5%を超えたら警告

### 3. OpenAI API使用状況

| 指標 | 説明 | 取得方法 |
|------|------|----------|
| **OpenAI呼び出し数** | OpenAI API総呼び出し回数 | `GET /api/v1/metrics` → `total_openai_calls` |
| **OpenAI成功率** | OpenAI API成功率（%） | `GET /api/v1/metrics` → `openai_success_rate` |
| **トークン消費量** | 累積トークン消費数 | `GET /api/v1/metrics` → `total_tokens_used` |
| **操作別統計** | estimate/question/chat別の統計 | `GET /api/v1/metrics` → `openai_operations` |

**監視ポイント**:
- OpenAI成功率が90%を下回ったら警告
- トークン消費量の異常な増加を監視（コスト管理）

### 4. システム健全性

| 指標 | 説明 | 取得方法 |
|------|------|----------|
| **ヘルスステータス** | healthy / degraded / unhealthy | `GET /api/v1/health` → `status` |

**判定基準**:
- `healthy`: すべての指標が正常範囲内
- `degraded`: OpenAI成功率 < 90%
- `unhealthy`: エラー率 > 5%

---

## SLI/SLO/SLA

### Service Level Indicator (SLI)

システムの実際のパフォーマンス指標：

| SLI | 定義 | 測定方法 |
|-----|------|----------|
| **可用性** | サービスが正常に応答する割合 | `success_rate` (HTTP 2xx / 総リクエスト) |
| **レイテンシ** | API応答時間のP95 | `p95_response_time` |
| **正確性** | OpenAI API成功率 | `openai_success_rate` |

### Service Level Objective (SLO)

目標とするサービスレベル：

| SLO | 目標値 | 測定期間 |
|-----|--------|----------|
| **可用性** | 99%以上 | 月次 |
| **レイテンシ** | P95 < 5秒 | 日次 |
| **正確性** | OpenAI成功率 95%以上 | 週次 |

### Service Level Agreement (SLA)

ユーザーに約束するサービスレベル：

| SLA | 保証値 | ペナルティ |
|-----|--------|-----------|
| **月間稼働率** | 95%以上 | 契約条件による |

---

## 警戒閾値とアラート

### アラートレベル

| レベル | 説明 | 対応時間 |
|--------|------|----------|
| **🟢 正常** | すべての指標が正常範囲内 | - |
| **🟡 注意** | 指標が注意範囲に入った | 24時間以内に確認 |
| **🟠 警告** | 指標が警告範囲に入った | 4時間以内に対応 |
| **🔴 重大** | サービス停止またはSLA違反 | 即座に対応 |

### 具体的な閾値

#### 1. API応答時間

| 指標 | 注意 | 警告 | 重大 |
|------|------|------|------|
| 平均応答時間 | > 3秒 | > 5秒 | > 10秒 |
| P95応答時間 | > 5秒 | > 10秒 | > 20秒 |

**対応アクション**:
- 注意: ログを確認し、遅延原因を調査
- 警告: OpenAI APIタイムアウト設定を確認、DB接続を確認
- 重大: サービス再起動、スケールアップを検討

#### 2. エラー率

| 指標 | 注意 | 警告 | 重大 |
|------|------|------|------|
| エラー率 | > 2% | > 5% | > 10% |
| 成功率 | < 98% | < 95% | < 90% |

**対応アクション**:
- 注意: エラーログを確認（`GET /api/v1/metrics/errors`）
- 警告: エラーの根本原因を特定し修正
- 重大: サービス停止を検討、ユーザー通知

#### 3. OpenAI API

| 指標 | 注意 | 警告 | 重大 |
|------|------|------|------|
| OpenAI成功率 | < 95% | < 90% | < 80% |
| トークン消費量 | +50%増加 | +100%増加 | +200%増加 |

**対応アクション**:
- 注意: OpenAI APIキーとレート制限を確認
- 警告: フォールバック処理の動作を確認
- 重大: OpenAIサポートに連絡、一時的にフォールバック処理に切り替え

---

## ログ確認方法

### 構造化ログの場所

```bash
# システムログ（systemd journal）
sudo journalctl -u estimator -n 100

# ファイルログ
sudo tail -f /var/log/estimator/backend.log
sudo tail -f /var/log/estimator/backend-error.log
```

### JSON形式ログの検索

#### 1. 特定のrequest_idでフィルタ

```bash
sudo grep "request_id.*abc-123-def" /var/log/estimator/backend-error.log | jq .
```

#### 2. エラーログのみ抽出

```bash
sudo grep '"level":"ERROR"' /var/log/estimator/backend-error.log | jq .
```

#### 3. 特定の時間帯のログ

```bash
sudo journalctl -u estimator --since "2025-10-22 00:00:00" --until "2025-10-22 23:59:59"
```

#### 4. OpenAI API呼び出しログ

```bash
sudo grep "OpenAI API call" /var/log/estimator/backend-error.log | jq .
```

### メトリクスAPI

#### メトリクスサマリー取得

```bash
curl -s http://127.0.0.1:8100/api/v1/metrics | jq .
```

**出力例**:
```json
{
  "total_api_calls": 150,
  "avg_response_time": 1.234,
  "p95_response_time": 3.456,
  "success_rate": 98.5,
  "total_openai_calls": 45,
  "openai_success_rate": 100.0,
  "total_tokens_used": 67800,
  "openai_operations": {
    "estimate": {"count": 30, "tokens": 50000},
    "question": {"count": 10, "tokens": 12000},
    "chat": {"count": 5, "tokens": 5800}
  },
  "total_errors": 2,
  "error_rate": 1.3
}
```

#### 最近のエラー取得

```bash
curl -s http://127.0.0.1:8100/api/v1/metrics/errors | jq .
```

#### ヘルスチェック

```bash
curl -s http://127.0.0.1:8100/api/v1/health | jq .
```

**出力例**:
```json
{
  "status": "healthy",
  "metrics": {
    "total_api_calls": 150,
    "avg_response_time": 1.234,
    ...
  }
}
```

---

## トラブルシューティング

### シナリオ1: API応答が遅い

**症状**: P95応答時間が10秒を超える

**診断手順**:

1. メトリクス確認
```bash
curl -s http://127.0.0.1:8100/api/v1/metrics | jq '.avg_response_time, .p95_response_time'
```

2. OpenAI API呼び出し時間確認
```bash
sudo grep "OpenAI API call successful" /var/log/estimator/backend-error.log | jq '.duration' | tail -20
```

3. リソース使用状況確認
```bash
top -bn1 | grep uvicorn
free -h
```

**対応**:
- OpenAI APIが遅い → タイムアウト設定を調整（`.env`の`OPENAI_TIMEOUT`）
- メモリ不足 → サーバースケールアップ
- 並列処理数不足 → `MAX_PARALLEL_ESTIMATES`を増やす

### シナリオ2: エラー率が上昇

**症状**: エラー率が5%を超える

**診断手順**:

1. エラー一覧取得
```bash
curl -s http://127.0.0.1:8100/api/v1/metrics/errors | jq .
```

2. エラーログ確認
```bash
sudo grep '"level":"ERROR"' /var/log/estimator/backend-error.log | tail -20 | jq .
```

3. エラーパターン分析
```bash
sudo grep '"level":"ERROR"' /var/log/estimator/backend-error.log | jq '.error' | sort | uniq -c
```

**対応**:
- OpenAI APIエラー → APIキー確認、レート制限確認
- データベースエラー → DB接続確認、ディスク容量確認
- 入力検証エラー → Guardrails設定確認

### シナリオ3: OpenAI成功率が低下

**症状**: OpenAI成功率が90%を下回る

**診断手順**:

1. OpenAI関連ログ確認
```bash
sudo grep "OpenAI API call failed" /var/log/estimator/backend-error.log | jq .
```

2. Circuit Breaker状態確認
```bash
sudo grep "Circuit breaker" /var/log/estimator/backend-error.log | tail -10 | jq .
```

3. リトライログ確認
```bash
sudo grep "Retrying" /var/log/estimator/backend-error.log | jq .
```

**対応**:
- レート制限 → OpenAIダッシュボードで確認、プラン変更検討
- タイムアウト → `OPENAI_TIMEOUT`を増やす
- APIキー無効 → 新しいAPIキーに更新

---

## 将来の拡張

現在の監視システムは基本的な機能を提供していますが、以下の拡張が可能です：

### 1. Prometheusメトリクスエクスポート

**目的**: メトリクスを時系列データベースに保存

**実装方法**:
```python
# prometheus_clientライブラリを使用
from prometheus_client import Counter, Histogram, Gauge

request_count = Counter('api_requests_total', 'Total API requests')
response_time = Histogram('api_response_time_seconds', 'API response time')
openai_tokens = Gauge('openai_tokens_used', 'OpenAI tokens used')
```

**メリット**:
- 長期的なトレンド分析
- 高度なクエリ機能
- 業界標準ツールとの統合

### 2. Grafanaダッシュボード

**目的**: メトリクスの可視化

**構成要素**:
- API応答時間グラフ（時系列）
- エラー率ゲージ
- OpenAIトークン消費量グラフ
- ヘルスステータス表示

### 3. アラート通知

**目的**: 異常検知時の自動通知

**通知先**:
- Slack
- Email
- PagerDuty

**実装例**:
```python
# Slack通知
if error_rate > 5:
    send_slack_alert(f"⚠️ Error rate exceeds threshold: {error_rate}%")
```

### 4. 分散トレーシング

**目的**: マイクロサービス間のリクエスト追跡

**ツール**:
- Jaeger
- Zipkin
- OpenTelemetry

### 5. ログ集約

**目的**: 複数サーバーのログを一元管理

**ツール**:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Loki + Grafana
- CloudWatch Logs (AWS)

---

## まとめ

このモニタリングシステムは以下を提供します：

✅ **構造化ログ**: JSON形式、リクエストIDトレース
✅ **メトリクス収集**: API統計、OpenAI使用量
✅ **ヘルスチェック**: 自動健全性判定
✅ **PII保護**: 個人情報マスキング
✅ **トラブルシューティング**: 詳細な診断手順

**運用開始後のアクション**:
1. メトリクスベースラインを1週間収集
2. 閾値を実データに基づいて調整
3. 定期的な監視レビュー（週次）
4. インシデント対応手順の整備

---

**問い合わせ先**: システム運用チーム
**ドキュメントバージョン**: 1.0
**最終更新日**: 2025-10-22
