# デプロイメントガイド

## 📋 目次

1. [インフラ構成](#インフラ構成)
2. [システム要件](#システム要件)
3. [環境変数](#環境変数)
4. [秘密管理](#秘密管理)
5. [起動・停止手順](#起動停止手順)
6. [デプロイ手順](#デプロイ手順)
7. [ロールバック手順](#ロールバック手順)
8. [スケーリング戦略](#スケーリング戦略)
9. [バックアップ・復旧](#バックアップ復旧)
10. [モニタリング](#モニタリング)
11. [コスト管理](#コスト管理)
12. [トラブルシューティング](#トラブルシューティング)

---

## インフラ構成

### システムアーキテクチャ図

```
Internet (HTTPS/HTTP)
    │
    ↓ Port 443/80
┌───────────────────────────┐
│  Apache HTTPD 2.4.62      │
│  - SSL/TLS終端            │
│  - Basic認証              │
│  - リバースプロキシ        │
│  - ProxyTimeout: 600秒    │
└───────────────────────────┘
    │
    ↓ HTTP Port 8100 (localhost)
┌───────────────────────────┐
│ systemd estimator.service │
│  - User: ec2-user         │
│  - Restart: on-failure    │
│  - Logs: /var/log/        │
└───────────────────────────┘
    │
    ↓
┌───────────────────────────┐
│ Uvicorn (ASGI Server)     │
│  - Host: 127.0.0.1        │
│  - Port: 8100             │
│  - Timeout: 120秒         │
│  - Workers: 1             │
└───────────────────────────┘
    │
    ↓
┌───────────────────────────┐
│ FastAPI Application       │
│  - Python 3.11            │
│  - conda環境: 311         │
│  - 多言語対応 (ja/en)     │
└───────────────────────────┘
    │
    ├─→ SQLite Database
    │    - File: backend/app.db
    │    - Schema: estimator
    │
    └─→ OpenAI API
         - Model: gpt-4o-mini
         - API Key: 環境変数
```

### コンポーネント詳細

#### 1. Apache HTTPD (リバースプロキシ)

**役割**:
- SSL/TLS終端 (Let's Encrypt証明書)
- Basic認証によるアクセス制御
- リバースプロキシ（バックエンドへのルーティング）
- HTTP→HTTPSリダイレクト

**設定ファイル**: `/etc/httpd/conf.d/estimator.path-finder.jp.conf`

**主要設定**:
```apache
<VirtualHost *:443>
    ServerName estimator.path-finder.jp
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/path-finder.jp/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/path-finder.jp/privkey.pem

    ProxyTimeout 600

    # Basic認証
    <Location />
      AuthType Basic
      AuthName "Restricted"
      AuthUserFile /etc/httpd/.htpasswd_estimator
      Require valid-user
    </Location>

    # プロキシ設定
    ProxyPass        "/api/"     "http://127.0.0.1:8100/api/"     timeout=600
    ProxyPassReverse "/api/"     "http://127.0.0.1:8100/api/"
    ProxyPass        "/static/"  "http://127.0.0.1:8100/static/"  timeout=600
    ProxyPassReverse "/static/"  "http://127.0.0.1:8100/static/"
    ProxyPass        "/"         "http://127.0.0.1:8100/ui/"      timeout=600
    ProxyPassReverse "/"         "http://127.0.0.1:8100/ui/"
</VirtualHost>

<VirtualHost *:80>
    ServerName estimator.path-finder.jp
    RewriteEngine On
    RewriteCond %{HTTPS} !=on
    RewriteRule ^/?(.*) https://%{SERVER_NAME}/ [R=301,L]
</VirtualHost>
```

**ポート**: 443 (HTTPS), 80 (HTTP)

**プロセス管理**: systemd (`httpd.service`)

#### 2. systemd Service (estimator.service)

**役割**:
- Uvicornプロセスの起動・停止・再起動
- 自動再起動（障害時）
- ログ管理

**設定ファイル**: `/etc/systemd/system/estimator.service`

```ini
[Unit]
Description=Estimator Backend (FastAPI with Uvicorn)
After=network.target

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend
EnvironmentFile=/home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/.env
ExecStart=/bin/bash -lc "source /home/ec2-user/anaconda3/bin/activate && conda activate 311 && exec uvicorn app.main:app --host 127.0.0.1 --port 8100 --proxy-headers --timeout-keep-alive 120"
Restart=on-failure
RestartSec=5
StandardOutput=append:/var/log/estimator/backend.log
StandardError=append:/var/log/estimator/backend-error.log

[Install]
WantedBy=multi-user.target
```

**主要パラメータ**:
- `User/Group`: ec2-user
- `Restart`: on-failure (失敗時のみ再起動)
- `RestartSec`: 5秒待機後に再起動
- `EnvironmentFile`: .envファイルから環境変数を読み込み

#### 3. Uvicorn (ASGI Server)

**役割**:
- FastAPIアプリケーションのASGIサーバー
- 非同期リクエスト処理
- プロキシヘッダー対応

**起動コマンド**:
```bash
uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8100 \
  --proxy-headers \
  --timeout-keep-alive 120
```

**主要パラメータ**:
- `--host 127.0.0.1`: localhostのみでリスニング（セキュリティ）
- `--port 8100`: ポート8100
- `--proxy-headers`: X-Forwarded-Forヘッダーを尊重
- `--timeout-keep-alive 120`: Keep-Aliveタイムアウト120秒

#### 4. FastAPI Application

**役割**:
- RESTful APIエンドポイント提供
- ビジネスロジック実行
- データベース操作
- OpenAI API連携

**Python環境**:
- Python 3.11 (conda環境: 311)
- フレームワーク: FastAPI
- ORM: SQLAlchemy 2.0
- データベース: SQLite3

**ディレクトリ構造**:
```
backend/
├── app/
│   ├── main.py              # FastAPIアプリケーション
│   ├── api/v1/tasks.py      # APIエンドポイント
│   ├── models/              # SQLAlchemyモデル
│   ├── schemas/             # Pydanticスキーマ
│   ├── services/            # ビジネスロジック
│   ├── core/                # 設定・共通機能
│   ├── db/                  # データベース接続
│   ├── prompts/             # LLMプロンプト
│   ├── middleware/          # ミドルウェア
│   └── locales/             # 多言語翻訳ファイル (ja.json/en.json)
├── .env                     # 環境変数
├── requirements.txt         # Python依存関係
└── app.db                   # SQLiteデータベース
```

#### 5. データベース (SQLite)

**ファイル**: `backend/app.db`

**テーブル構造**:
- `tasks`: 見積りタスク
- `deliverables`: 成果物
- `qa_pairs`: 質問と回答
- `estimates`: 見積り結果
- `messages`: チャットメッセージ

**バックアップ**:
- 手動バックアップ: `cp app.db app.db.backup`
- 定期バックアップ: cronで自動実行推奨

#### 6. 外部API (OpenAI)

**エンドポイント**: `https://api.openai.com/v1/chat/completions`

**使用モデル**: `gpt-4o-mini`

**用途**:
- 質問生成
- 見積り生成
- チャット調整

**認証**: APIキー (環境変数 `OPENAI_API_KEY`)

---

## システム要件

### ハードウェア要件

**最小要件**:
- CPU: 2 vCPU
- メモリ: 2 GB RAM
- ストレージ: 10 GB (OS + アプリ + ログ)

**推奨要件**:
- CPU: 4 vCPU
- メモリ: 4 GB RAM
- ストレージ: 20 GB SSD

**本番環境 (EC2)**:
- インスタンスタイプ: t3.small以上
- OS: Amazon Linux 2023
- アーキテクチャ: x86_64

### ソフトウェア要件

**OS**:
- Amazon Linux 2023
- または CentOS 7+, Ubuntu 20.04+

**必須ソフトウェア**:
- Apache HTTPD 2.4+ (mod_ssl, mod_proxy, mod_proxy_http)
- Python 3.11+
- Anaconda/Miniconda (conda環境管理)
- SQLite 3.x
- systemd

**SSL証明書**:
- Let's Encrypt (certbot)

**外部サービス**:
- OpenAI API アカウント
- インターネット接続 (OpenAI API通信)

---

## 環境変数

### .envファイル

**ファイルパス**: `backend/.env`

**設定項目**:

```bash
# Database
DATABASE_URL=sqlite:///./app.db
DB_SCHEMA=estimator

# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini

# Config
# Note: DAILY_UNIT_COST is deprecated - use language-specific settings below
DAILY_UNIT_COST=40000
DAILY_UNIT_COST_JPY=40000
DAILY_UNIT_COST_USD=500
TAX_RATE_JA=10
TAX_RATE_EN=0
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=10

# Language Setting (ja or en)
LANGUAGE=ja

# Server
HOST=127.0.0.1
PORT=8100
CORS_ORIGINS=https://estimator.path-finder.jp
```

### 環境変数詳細

| 変数名 | 説明 | デフォルト値 | 必須 |
|--------|------|-------------|------|
| `DATABASE_URL` | SQLiteデータベースのURL | `sqlite:///./app.db` | ✓ |
| `DB_SCHEMA` | データベーススキーマ名 | `estimator` | ✓ |
| `OPENAI_API_KEY` | OpenAI APIキー | - | ✓ |
| `OPENAI_MODEL` | 使用するOpenAIモデル | `gpt-4o-mini` | ✓ |
| `DAILY_UNIT_COST` | 1人日単価（非推奨） | `40000` | - |
| `DAILY_UNIT_COST_JPY` | 1人日単価（日本円） | `40000` | ✓ |
| `DAILY_UNIT_COST_USD` | 1人日単価（米ドル） | `500` | ✓ |
| `TAX_RATE_JA` | 消費税率（日本） | `10` | ✓ |
| `TAX_RATE_EN` | 消費税率（英語圏） | `0` | ✓ |
| `UPLOAD_DIR` | ファイルアップロードディレクトリ | `uploads` | ✓ |
| `MAX_UPLOAD_SIZE_MB` | 最大アップロードサイズ (MB) | `10` | ✓ |
| `LANGUAGE` | システム言語 (ja/en) | `ja` | ✓ |
| `HOST` | Uvicornバインドホスト | `127.0.0.1` | ✓ |
| `PORT` | Uvicornポート | `8100` | ✓ |
| `CORS_ORIGINS` | CORS許可オリジン | `https://estimator.path-finder.jp` | ✓ |

### 環境変数の注意事項

**⚠️ 重要**:
- `.env`ファイルに**行末コメント（`#`）を付けない**こと
- Pydanticが整数値をパースできずエラーになります

**NG例**:
```bash
DAILY_UNIT_COST=40000  # Deprecated: Use language-specific settings below
```

**OK例**:
```bash
# Note: DAILY_UNIT_COST is deprecated - use language-specific settings below
DAILY_UNIT_COST=40000
```

---

## 秘密管理

### OpenAI APIキー

**保存場所**: `backend/.env` (ファイルパーミッション: 600)

**セキュリティ対策**:
1. `.env`ファイルを`.gitignore`に追加（コミット禁止）
2. ファイルパーミッション制限:
   ```bash
   chmod 600 backend/.env
   chown ec2-user:ec2-user backend/.env
   ```
3. 定期的なキーローテーション
4. 使用量監視（OpenAIダッシュボード）

### Basic認証パスワード

**保存場所**: `/etc/httpd/.htpasswd_estimator`

**パスワード変更**:
```bash
sudo htpasswd /etc/httpd/.htpasswd_estimator <username>
```

**ファイルパーミッション**:
```bash
sudo chmod 644 /etc/httpd/.htpasswd_estimator
sudo chown root:root /etc/httpd/.htpasswd_estimator
```

### SSL/TLS証明書

**証明書パス**:
- フルチェーン: `/etc/letsencrypt/live/path-finder.jp/fullchain.pem`
- 秘密鍵: `/etc/letsencrypt/live/path-finder.jp/privkey.pem`

**自動更新** (certbot):
```bash
# 証明書更新テスト
sudo certbot renew --dry-run

# 自動更新 (cron)
0 0,12 * * * certbot renew --quiet --post-hook "systemctl reload httpd"
```

---

## 起動・停止手順

### 1. Apacheの起動・停止

```bash
# 起動
sudo systemctl start httpd

# 停止
sudo systemctl stop httpd

# 再起動
sudo systemctl restart httpd

# 設定リロード（ダウンタイムなし）
sudo systemctl reload httpd

# ステータス確認
sudo systemctl status httpd

# 自動起動設定
sudo systemctl enable httpd
```

### 2. estimator.serviceの起動・停止

```bash
# 起動
sudo systemctl start estimator

# 停止
sudo systemctl stop estimator

# 再起動
sudo systemctl restart estimator

# ステータス確認
systemctl status estimator

# ログ確認（リアルタイム）
journalctl -u estimator -f

# ログ確認（直近100行）
journalctl -u estimator -n 100

# 自動起動設定
sudo systemctl enable estimator
```

### 3. ヘルスチェック

```bash
# ローカルからヘルスチェック
curl -s http://127.0.0.1:8100/health

# 期待される出力
{"status":"healthy"}

# 本番環境ヘルスチェック（Basic認証が必要）
curl -u username:password https://estimator.path-finder.jp/api/v1/health
```

### 4. 完全な起動順序

```bash
# 1. Apache起動
sudo systemctl start httpd

# 2. estimatorサービス起動
sudo systemctl start estimator

# 3. 動作確認
systemctl status httpd estimator
curl -s http://127.0.0.1:8100/health
```

### 5. 完全な停止順序

```bash
# 1. estimatorサービス停止
sudo systemctl stop estimator

# 2. Apache停止（他のアプリも影響を受ける場合は注意）
sudo systemctl stop httpd
```

---

## デプロイ手順

### 初回デプロイ

#### 1. リポジトリクローン

```bash
cd /home/ec2-user/hirashimallc
git clone <repository-url> 09_pj-見積り作成システム
cd 09_pj-見積り作成システム/output3/backend
```

#### 2. Python環境セットアップ

```bash
# conda環境作成
source /home/ec2-user/anaconda3/bin/activate
conda create -n 311 python=3.11
conda activate 311

# 依存関係インストール
pip install -r requirements.txt
```

#### 3. 環境変数設定

```bash
# .envファイル作成
cp .env.sample .env
nano .env

# 必須項目を設定
# - OPENAI_API_KEY
# - DATABASE_URL
# - CORS_ORIGINS
```

#### 4. データベース初期化

```bash
# 初回起動時に自動作成される
# または手動でマイグレーション実行
# （現在はalembicは未使用）
```

#### 5. ログディレクトリ作成

```bash
sudo mkdir -p /var/log/estimator
sudo chown ec2-user:ec2-user /var/log/estimator
```

#### 6. systemdサービス登録

```bash
# サービスファイル配置
sudo cp /path/to/estimator.service /etc/systemd/system/

# systemdリロード
sudo systemctl daemon-reload

# サービス有効化
sudo systemctl enable estimator

# サービス起動
sudo systemctl start estimator
```

#### 7. Apache設定

```bash
# 設定ファイル配置
sudo cp /path/to/estimator.path-finder.jp.conf /etc/httpd/conf.d/

# 設定テスト
sudo apachectl configtest

# Apache再起動
sudo systemctl restart httpd
```

#### 8. Basic認証設定

```bash
# ユーザー作成
sudo htpasswd -c /etc/httpd/.htpasswd_estimator <username>

# パーミッション設定
sudo chmod 644 /etc/httpd/.htpasswd_estimator
```

#### 9. SSL証明書設定

```bash
# certbotで証明書取得（初回のみ）
sudo certbot certonly --webroot -w /var/www/html -d estimator.path-finder.jp

# 自動更新設定
sudo crontab -e
# 以下を追加
0 0,12 * * * certbot renew --quiet --post-hook "systemctl reload httpd"
```

#### 10. 動作確認

```bash
# ローカル確認
curl -s http://127.0.0.1:8100/health

# 本番確認
curl -u username:password https://estimator.path-finder.jp/api/v1/health
```

### 更新デプロイ

#### 1. コード更新

```bash
cd /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3

# Gitプル
git pull origin main

# または手動でファイル更新
```

#### 2. 依存関係更新（必要な場合）

```bash
cd backend
source /home/ec2-user/anaconda3/bin/activate
conda activate 311
pip install -r requirements.txt
```

#### 3. 環境変数更新（必要な場合）

```bash
nano .env
# 変更を保存
```

#### 4. データベースマイグレーション（必要な場合）

```bash
# 現在はalembic未使用
# 将来的にマイグレーションが必要な場合はこちらで実施
```

#### 5. サービス再起動

```bash
# estimatorサービス再起動
sudo systemctl restart estimator

# ステータス確認
systemctl status estimator

# ログ確認
journalctl -u estimator -n 50
```

#### 6. 動作確認

```bash
# ヘルスチェック
curl -s http://127.0.0.1:8100/health

# APIテスト
curl -u username:password https://estimator.path-finder.jp/api/v1/translations
```

---

## ロールバック手順

### コードロールバック

#### Git使用の場合

```bash
cd /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3

# コミット履歴確認
git log --oneline -10

# 特定のコミットにロールバック
git checkout <commit-hash>

# またはブランチに戻る
git checkout main
git pull

# サービス再起動
sudo systemctl restart estimator
```

#### 手動バックアップの場合

```bash
# バックアップから復元
cp -r /path/to/backup/backend/* /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/

# サービス再起動
sudo systemctl restart estimator
```

### データベースロールバック

```bash
# バックアップから復元
cp /path/to/backup/app.db.backup /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/app.db

# サービス再起動
sudo systemctl restart estimator
```

### 環境変数ロールバック

```bash
# バックアップから復元
cp /path/to/backup/.env.backup /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/.env

# サービス再起動
sudo systemctl restart estimator
```

### Apache設定ロールバック

```bash
# バックアップから復元
sudo cp /etc/httpd/conf.d/estimator.path-finder.jp.conf.backup /etc/httpd/conf.d/estimator.path-finder.jp.conf

# 設定テスト
sudo apachectl configtest

# Apache再起動
sudo systemctl restart httpd
```

---

## スケーリング戦略

### 垂直スケーリング（スケールアップ）

**EC2インスタンスタイプ変更**:

```bash
# 1. サービス停止
sudo systemctl stop estimator
sudo systemctl stop httpd

# 2. EC2コンソールでインスタンスタイプ変更
#    t3.small → t3.medium → t3.large

# 3. インスタンス再起動後、サービス起動
sudo systemctl start httpd
sudo systemctl start estimator
```

**推奨インスタンスタイプ**:
- 小規模 (〜100リクエスト/日): t3.small (2 vCPU, 2 GB)
- 中規模 (〜500リクエスト/日): t3.medium (2 vCPU, 4 GB)
- 大規模 (〜1000リクエスト/日): t3.large (2 vCPU, 8 GB)

### 水平スケーリング（スケールアウト）

**複数Uvicornワーカー**:

```bash
# systemdサービスファイル変更
sudo nano /etc/systemd/system/estimator.service

# ExecStartを以下に変更
ExecStart=/bin/bash -lc "source /home/ec2-user/anaconda3/bin/activate && conda activate 311 && exec uvicorn app.main:app --host 127.0.0.1 --port 8100 --workers 4 --proxy-headers --timeout-keep-alive 120"

# リロード・再起動
sudo systemctl daemon-reload
sudo systemctl restart estimator
```

**注意**:
- SQLiteは複数ワーカーで競合する可能性あり
- PostgreSQL/MySQLへの移行を推奨

### ロードバランシング（将来的）

**構成例**:
```
Internet
   ↓
AWS ELB/ALB
   ↓
┌────────────┬────────────┬────────────┐
│ Instance 1 │ Instance 2 │ Instance 3 │
└────────────┴────────────┴────────────┘
   ↓
共有RDS (PostgreSQL)
```

---

## バックアップ・復旧

### バックアップ対象

1. **データベース**: `backend/app.db`
2. **環境変数**: `backend/.env`
3. **アップロードファイル**: `backend/uploads/`
4. **Apache設定**: `/etc/httpd/conf.d/estimator.path-finder.jp.conf`
5. **systemd設定**: `/etc/systemd/system/estimator.service`

### 手動バックアップ

```bash
#!/bin/bash
# バックアップスクリプト

BACKUP_DIR="/home/ec2-user/backups/estimator"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR/$TIMESTAMP

# データベース
cp /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/app.db \
   $BACKUP_DIR/$TIMESTAMP/app.db

# 環境変数
cp /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/.env \
   $BACKUP_DIR/$TIMESTAMP/.env

# アップロードファイル
cp -r /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/uploads \
   $BACKUP_DIR/$TIMESTAMP/

# Apache設定
sudo cp /etc/httpd/conf.d/estimator.path-finder.jp.conf \
   $BACKUP_DIR/$TIMESTAMP/estimator.path-finder.jp.conf

# systemd設定
sudo cp /etc/systemd/system/estimator.service \
   $BACKUP_DIR/$TIMESTAMP/estimator.service

echo "Backup completed: $BACKUP_DIR/$TIMESTAMP"
```

### 自動バックアップ (cron)

```bash
# crontab編集
crontab -e

# 毎日午前3時にバックアップ
0 3 * * * /home/ec2-user/scripts/backup_estimator.sh
```

### 復旧手順

```bash
# 1. サービス停止
sudo systemctl stop estimator

# 2. データベース復元
cp /home/ec2-user/backups/estimator/<timestamp>/app.db \
   /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/app.db

# 3. 環境変数復元
cp /home/ec2-user/backups/estimator/<timestamp>/.env \
   /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/.env

# 4. アップロードファイル復元
cp -r /home/ec2-user/backups/estimator/<timestamp>/uploads/* \
   /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/uploads/

# 5. サービス起動
sudo systemctl start estimator

# 6. 動作確認
curl -s http://127.0.0.1:8100/health
```

---

## モニタリング

### ログ確認

#### 1. estimatorサービスログ

```bash
# リアルタイムログ
journalctl -u estimator -f

# 直近100行
journalctl -u estimator -n 100

# エラーのみ
journalctl -u estimator -p err

# 日付指定
journalctl -u estimator --since "2025-10-21 00:00:00"

# ファイルログ
tail -f /var/log/estimator/backend.log
tail -f /var/log/estimator/backend-error.log
```

#### 2. Apacheログ

```bash
# アクセスログ
sudo tail -f /var/log/httpd/access_log

# エラーログ
sudo tail -f /var/log/httpd/error_log

# estimator専用ログ（設定されている場合）
sudo tail -f /var/log/httpd/estimator_access.log
sudo tail -f /var/log/httpd/estimator_error.log
```

### ヘルスチェック

```bash
# ローカルヘルスチェック
curl -s http://127.0.0.1:8100/health

# 本番ヘルスチェック
curl -u username:password https://estimator.path-finder.jp/api/v1/health

# ステータスコードのみ確認
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8100/health
```

### プロセス監視

```bash
# プロセス確認
ps aux | grep uvicorn
ps aux | grep httpd

# ポート確認
lsof -i :8100
lsof -i :443
lsof -i :80

# リソース使用状況
top -u ec2-user
htop -u ec2-user
```

### メトリクス収集（推奨）

**CloudWatch Metrics**:
- CPUUtilization
- MemoryUtilization
- DiskReadBytes/DiskWriteBytes
- NetworkIn/NetworkOut

**カスタムメトリクス**:
- リクエスト数 (CustomMetric)
- レスポンスタイム (CustomMetric)
- エラー率 (CustomMetric)

---

## コスト管理

### OpenAI API コスト

**料金体系** (gpt-4o-mini):
- Input: $0.15 / 1M tokens
- Output: $0.6 / 1M tokens

**コスト見積り**:
- 1見積りあたり: 約5,000トークン（入力2,000 + 出力3,000）
- コスト: 約$0.0021/見積り
- 1,000見積り: 約$2.1

**コスト削減策**:
1. プロンプト最適化（不要な情報削除）
2. キャッシュ活用（同じ質問の再利用）
3. レート制限実装（TODO-9で実施済み）
4. 使用量監視とアラート

### AWS インフラコスト

**EC2**:
- t3.small: $0.0208/時間 × 24時間 × 30日 = 約$15/月

**データ転送**:
- 月間1TBまで無料（通常範囲内）

**SSL証明書**:
- Let's Encrypt: 無料

**合計見積り**:
- 月額約$17（EC2 + OpenAI API）

---

## トラブルシューティング

### よくある問題

#### 1. サービスが起動しない

**症状**: `systemctl status estimator`で`failed`状態

**原因と対処**:

**原因1: ポート8100が既に使用中**
```bash
# ポート使用状況確認
lsof -i :8100

# プロセス停止
kill <PID>

# サービス再起動
sudo systemctl restart estimator
```

**原因2: 環境変数パースエラー**
```bash
# エラーログ確認
sudo tail -50 /var/log/estimator/backend-error.log

# .envファイル確認（行末コメント削除）
nano backend/.env

# サービス再起動
sudo systemctl restart estimator
```

**原因3: conda環境が見つからない**
```bash
# conda環境確認
source /home/ec2-user/anaconda3/bin/activate
conda env list

# 環境が無い場合は作成
conda create -n 311 python=3.11
conda activate 311
pip install -r requirements.txt

# サービス再起動
sudo systemctl restart estimator
```

#### 2. 見積り生成が失敗する

**症状**: 「OpenAI API error」が表示される

**対処**:
```bash
# OpenAI API状態確認
curl https://status.openai.com/

# APIキー確認
cat backend/.env | grep OPENAI_API_KEY

# ログ確認
journalctl -u estimator -n 100 | grep -i openai
```

#### 3. Basic認証が通らない

**症状**: 401 Unauthorized

**対処**:
```bash
# パスワードファイル確認
sudo cat /etc/httpd/.htpasswd_estimator

# パスワード再設定
sudo htpasswd /etc/httpd/.htpasswd_estimator <username>

# Apache再起動
sudo systemctl reload httpd
```

詳細なトラブルシューティングは[TROUBLESHOOTING.md](../operations/TROUBLESHOOTING.md)を参照してください。

---

## 参考資料

- [TROUBLESHOOTING.md](../operations/TROUBLESHOOTING.md) - トラブルシューティングガイド
- [RUNBOOK.md](../operations/RUNBOOK.md) - 運用Runbook
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - アーキテクチャドキュメント
- [DEVELOPER_GUIDE.md](../development/DEVELOPER_GUIDE.md) - 開発者ガイド

---

**最終更新**: 2025-10-21
**作成者**: Claude Code
**バージョン**: 1.0
