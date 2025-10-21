# トラブルシューティングガイド

## 📋 目次

1. [よくある問題TOP10](#よくある問題top10)
2. [ログ確認方法](#ログ確認方法)
3. [エラーコード別対処法](#エラーコード別対処法)
4. [パフォーマンス問題](#パフォーマンス問題)
5. [OpenAI API関連問題](#openai-api関連問題)
6. [データベース問題](#データベース問題)
7. [ネットワーク問題](#ネットワーク問題)
8. [多言語関連問題](#多言語関連問題)

---

## よくある問題TOP10

### 問題1: サーバーが起動しない

**症状**:
```bash
$ systemctl status estimator
● estimator.service - Estimator Backend
   Active: failed (Result: exit-code)
```

**原因と対処法**:

#### 原因1-1: ポート8100が既に使用中

**確認**:
```bash
lsof -i :8100
# 出力: uvicorn 12345 ec2-user ...
```

**対処**:
```bash
# プロセス特定
ps aux | grep uvicorn | grep 8100

# プロセス停止
kill <PID>

# または全uvicornプロセス停止
pkill -f "uvicorn.*8100"

# サービス再起動
sudo systemctl restart estimator
```

#### 原因1-2: 環境変数パースエラー

**エラーログ**:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
DAILY_UNIT_COST
  Input should be a valid integer, unable to parse string as an integer
```

**原因**: `.env`ファイルに行末コメントがある

**確認**:
```bash
cat backend/.env | grep DAILY_UNIT_COST
# NG: DAILY_UNIT_COST=40000  # コメント
```

**対処**:
```bash
# .envファイルを編集
nano backend/.env

# 修正前（NG）:
# DAILY_UNIT_COST=40000  # Deprecated

# 修正後（OK）:
# Note: DAILY_UNIT_COST is deprecated
DAILY_UNIT_COST=40000

# サービス再起動
sudo systemctl restart estimator
```

#### 原因1-3: conda環境が見つからない

**エラーログ**:
```
CommandNotFoundError: Your shell has not been properly configured to use 'conda activate'.
```

**対処**:
```bash
# conda環境確認
source /home/ec2-user/anaconda3/bin/activate
conda env list

# 環境が無い場合は作成
conda create -n 311 python=3.11
conda activate 311
pip install -r backend/requirements.txt

# サービス再起動
sudo systemctl restart estimator
```

#### 原因1-4: 依存関係の欠落

**対処**:
```bash
source /home/ec2-user/anaconda3/bin/activate
conda activate 311
cd backend
pip install -r requirements.txt --upgrade

sudo systemctl restart estimator
```

---

### 問題2: 見積り生成が失敗する

**症状**: 「OpenAI API error」が表示される

#### 原因2-1: OpenAI API障害

**確認**:
```bash
# OpenAI API状態確認
curl -s https://status.openai.com/api/v2/status.json | jq '.status.description'
```

**対処**:
- OpenAI側の復旧を待つ
- ステータスページ監視: https://status.openai.com/

#### 原因2-2: APIキーが無効

**確認**:
```bash
cat backend/.env | grep OPENAI_API_KEY
# キーが空または無効でないか確認
```

**対処**:
```bash
# OpenAIダッシュボードで新しいAPIキー取得
# https://platform.openai.com/api-keys

# .envファイル更新
nano backend/.env
# OPENAI_API_KEY=sk-proj-xxxxx

sudo systemctl restart estimator
```

#### 原因2-3: API利用上限に達した

**確認**:
```bash
# OpenAI使用量ページで確認
# https://platform.openai.com/usage
```

**対処**:
- 請求設定の見直し
- 利用上限の引き上げ
- レート制限の調整

#### 原因2-4: CircuitBreakerがOPEN状態

**確認**:
```bash
journalctl -u estimator -n 100 | grep "CircuitBreaker"
# 出力: CircuitBreaker is OPEN
```

**対処**:
```bash
# 60秒待機してHALF_OPENに移行
sleep 60

# または即座に再起動
sudo systemctl restart estimator
```

---

### 問題3: ファイルアップロードが失敗する

**症状**: 「File too large」エラー

**確認**:
```bash
ls -lh /path/to/upload/file.xlsx
# ファイルサイズ確認
```

**対処**:

#### 対処法1: ファイルサイズ削減

- 不要な行・列を削除
- 10MB以下に圧縮

#### 対処法2: 設定変更

```bash
# .envファイル編集
nano backend/.env

# 変更
MAX_UPLOAD_SIZE_MB=20

# サービス再起動
sudo systemctl restart estimator
```

---

### 問題4: Basic認証が通らない

**症状**: 401 Unauthorized

**確認**:
```bash
# パスワードファイル確認
sudo cat /etc/httpd/.htpasswd_estimator

# ユーザー存在確認
sudo cat /etc/httpd/.htpasswd_estimator | grep username
```

**対処**:
```bash
# パスワード再設定
sudo htpasswd /etc/httpd/.htpasswd_estimator username

# Apache再起動
sudo systemctl reload httpd
```

---

### 問題5: SSL証明書エラー

**症状**: ブラウザで「この接続ではプライバシーが保護されません」

**確認**:
```bash
# 証明書の有効期限確認
sudo certbot certificates

# または
echo | openssl s_client -connect estimator.path-finder.jp:443 2>/dev/null | \
  openssl x509 -noout -dates
```

**対処**:
```bash
# 証明書更新
sudo certbot renew

# Apache再読み込み
sudo systemctl reload httpd
```

---

### 問題6: データベースロックエラー

**症状**: 「database is locked」エラー

**確認**:
```bash
# 長時間実行中のプロセス確認
ps aux | grep uvicorn
```

**対処**:
```bash
# サービス再起動
sudo systemctl restart estimator

# データベース整合性チェック
sqlite3 backend/app.db "PRAGMA integrity_check;"
```

---

### 問題7: メモリ不足エラー

**症状**: サービスが突然停止、OOM Killerログ

**確認**:
```bash
# メモリ使用状況
free -h

# OOM Killerログ
dmesg | grep -i "out of memory"
journalctl -k | grep -i "killed process"
```

**対処**:
```bash
# 即時対応: サービス再起動
sudo systemctl restart estimator

# 長期対応: インスタンスタイプ変更
# t3.small → t3.medium
```

---

### 問題8: タイムアウトエラー

**症状**: 「Request timeout」、504 Gateway Timeout

**確認**:
```bash
# タイムアウト設定確認
grep -r "timeout" /etc/httpd/conf.d/estimator*.conf
grep -r "timeout" backend/.env
```

**対処**:
```bash
# Apache設定変更
sudo nano /etc/httpd/conf.d/estimator.path-finder.jp.conf

# ProxyTimeout を延長
ProxyTimeout 900

sudo systemctl reload httpd

# Uvicornタイムアウト延長
# systemdファイル編集
sudo nano /etc/systemd/system/estimator.service

# --timeout-keep-alive 120 → 180

sudo systemctl daemon-reload
sudo systemctl restart estimator
```

---

### 問題9: 多言語切り替えが反映されない

**症状**: LANGUAGE=enに変更しても日本語のまま

**確認**:
```bash
cat backend/.env | grep LANGUAGE
```

**対処**:
```bash
# .envファイル確認・変更
nano backend/.env
# LANGUAGE=en

# サービス再起動（必須）
sudo systemctl restart estimator

# ブラウザキャッシュクリア
# Ctrl+Shift+R (ハードリロード)
```

---

### 問題10: Excel出力が文字化けする

**症状**: ダウンロードしたExcelファイルが文字化け

**確認**:
```bash
# localesファイル確認
ls -la backend/app/locales/

# 翻訳ファイルのエンコーディング確認
file backend/app/locales/ja.json
# 出力: UTF-8 Unicode text
```

**対処**:
```bash
# openpyxl再インストール
source /home/ec2-user/anaconda3/bin/activate
conda activate 311
pip install --upgrade openpyxl

sudo systemctl restart estimator
```

---

## ログ確認方法

### 開発環境

```bash
# コンソールに直接出力
cd backend
source /home/ec2-user/anaconda3/bin/activate
conda activate 311
uvicorn app.main:app --reload --log-level debug
```

### 本番環境（systemd）

#### リアルタイムログ

```bash
# estimatorサービスログ（リアルタイム）
journalctl -u estimator -f

# Apacheログ（リアルタイム）
sudo tail -f /var/log/httpd/access_log
sudo tail -f /var/log/httpd/error_log
```

#### 過去ログ

```bash
# 直近100行
journalctl -u estimator -n 100

# 日付指定
journalctl -u estimator --since "2025-10-21 00:00:00" --until "2025-10-21 23:59:59"

# エラーのみ
journalctl -u estimator -p err

# 特定文字列検索
journalctl -u estimator | grep "OpenAI"
```

#### ファイルログ

```bash
# estimatorログファイル
tail -f /var/log/estimator/backend.log
tail -f /var/log/estimator/backend-error.log

# Apacheログファイル
sudo tail -f /var/log/httpd/access_log
sudo tail -f /var/log/httpd/error_log
```

---

## エラーコード別対処法

### HTTPステータスコード

| コード | 意味 | 対処法 |
|-------|------|--------|
| 400 | Bad Request | リクエストパラメータ確認、Guardrailsチェック |
| 401 | Unauthorized | Basic認証確認、パスワード再設定 |
| 403 | Forbidden | アクセス権限確認、ファイルパーミッション確認 |
| 404 | Not Found | URLパス確認、ルーティング確認 |
| 413 | Payload Too Large | ファイルサイズ削減、MAX_UPLOAD_SIZE_MB変更 |
| 422 | Unprocessable Entity | リクエストボディ確認、Pydanticバリデーション |
| 500 | Internal Server Error | サーバーログ確認、スタックトレース確認 |
| 502 | Bad Gateway | バックエンドサービス確認、Uvicorn起動確認 |
| 503 | Service Unavailable | リソース制限確認、同時実行数確認 |
| 504 | Gateway Timeout | タイムアウト設定確認、処理時間最適化 |

### OpenAI APIエラー

| エラー | 原因 | 対処法 |
|-------|------|--------|
| AuthenticationError | APIキー無効 | APIキー再設定 |
| RateLimitError | レート制限超過 | 待機後リトライ、プラン変更 |
| APIConnectionError | ネットワークエラー | 接続確認、リトライ |
| Timeout | タイムアウト | リトライ、タイムアウト延長 |
| APIError | API側エラー | ステータスページ確認、待機 |

---

## パフォーマンス問題

### 高CPU使用率

**確認**:
```bash
top -b -n 1 | head -20
ps aux --sort=-%cpu | head -10
```

**対処**:
```bash
# プロセス再起動
sudo systemctl restart estimator

# スケールアップ検討
# t3.small → t3.medium
```

### 高メモリ使用率

**確認**:
```bash
free -h
ps aux --sort=-%mem | head -10
```

**対処**:
```bash
# メモリリーク疑い: 再起動
sudo systemctl restart estimator

# キャッシュクリア
sync; echo 3 | sudo tee /proc/sys/vm/drop_caches
```

### 低速なレスポンス

**確認**:
```bash
# レスポンスタイム測定
time curl -u user:pass https://estimator.path-finder.jp/api/v1/health
```

**対処**:
```bash
# データベースクエリ最適化
# 並列処理の調整
# キャッシュ活用
```

---

## OpenAI API関連問題

### API呼び出し失敗

**確認**:
```bash
# OpenAI API状態
curl -s https://status.openai.com/api/v2/status.json | jq .

# ネットワーク接続
ping api.openai.com
```

**対処**:
```bash
# リトライロジックが自動実行（最大3回）
# CircuitBreakerによる自動フォールバック

# 手動リトライ
sudo systemctl restart estimator
```

### API使用量超過

**確認**:
```bash
# OpenAIダッシュボードで確認
# https://platform.openai.com/usage
```

**対処**:
- 月次予算の見直し
- レート制限の調整（TODO-9で実装済み）
- プロンプト最適化

---

## データベース問題

### データベースファイル破損

**確認**:
```bash
sqlite3 backend/app.db "PRAGMA integrity_check;"
# 期待: ok
```

**対処**:
```bash
# バックアップから復元
sudo systemctl stop estimator
cp /home/ec2-user/backups/estimator/<latest>/app.db backend/app.db
sudo systemctl start estimator
```

### データベースロック

**確認**:
```bash
# ロックしているプロセス確認
lsof backend/app.db
```

**対処**:
```bash
sudo systemctl restart estimator
```

---

## ネットワーク問題

### 外部接続不可

**確認**:
```bash
# OpenAI API接続テスト
curl -I https://api.openai.com

# DNS解決テスト
nslookup api.openai.com
```

**対処**:
```bash
# ネットワーク設定確認
ip addr show
route -n

# セキュリティグループ確認（EC2）
```

### SSL/TLS証明書問題

**確認**:
```bash
# 証明書チェーン確認
openssl s_client -connect estimator.path-finder.jp:443 -showcerts
```

**対処**:
```bash
# 証明書更新
sudo certbot renew
sudo systemctl reload httpd
```

---

## 多言語関連問題

### 翻訳キー不足エラー

**症状**: KeyError: 'ui.some_key'

**対処**:
```bash
# ja.jsonとen.json両方に追加
nano backend/app/locales/ja.json
nano backend/app/locales/en.json

# 追加例
{
  "ui": {
    "some_key": "翻訳文"
  }
}

sudo systemctl restart estimator
```

### LLM出力が期待言語でない

**確認**:
```bash
# プロンプトに言語指示が含まれているか確認
cat backend/app/prompts/question_prompts.py | grep language_instruction
```

**対処**:
```python
# プロンプトに言語指示を追加
language_instruction = t('prompts.language_instruction')
prompt = f"{base_prompt}\n\n{language_instruction}"
```

---

## 緊急対応フローチャート

```
問題発生
   ↓
サービス稼働確認
   ├─ 停止 → systemctl restart estimator
   └─ 稼働中 → 次へ
       ↓
ログ確認
   ├─ OpenAI APIエラー → API状態確認
   ├─ データベースエラー → 整合性チェック
   ├─ メモリエラー → 再起動
   └─ その他 → 詳細調査
       ↓
対処実施
   ↓
動作確認
   ├─ 正常 → 完了
   └─ 異常 → エスカレーション
```

---

## 参考資料

- [DEPLOYMENT.md](../deployment/DEPLOYMENT.md) - デプロイメントガイド
- [RUNBOOK.md](RUNBOOK.md) - 運用Runbook
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - アーキテクチャドキュメント

---

**最終更新**: 2025-10-21
**作成者**: Claude Code
**バージョン**: 1.0
