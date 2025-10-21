# Deployment Guide

## 📋 Table of Contents

1. [Infrastructure Architecture](#infrastructure-architecture)
2. [System Requirements](#system-requirements)
3. [Environment Variables](#environment-variables)
4. [Secret Management](#secret-management)
5. [Start/Stop Procedures](#startstop-procedures)
6. [Deployment Procedures](#deployment-procedures)
7. [Rollback Procedures](#rollback-procedures)
8. [Scaling Strategy](#scaling-strategy)
9. [Backup & Recovery](#backup--recovery)
10. [Monitoring](#monitoring)
11. [Cost Management](#cost-management)
12. [Troubleshooting](#troubleshooting)

---

## Infrastructure Architecture

### System Architecture Diagram

```
Internet (HTTPS/HTTP)
    │
    ↓ Port 443/80
┌───────────────────────────┐
│  Apache HTTPD 2.4.62      │
│  - SSL/TLS Termination    │
│  - Basic Authentication   │
│  - Reverse Proxy          │
│  - ProxyTimeout: 600s     │
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
│  - Timeout: 120s          │
│  - Workers: 1             │
└───────────────────────────┘
    │
    ↓
┌───────────────────────────┐
│ FastAPI Application       │
│  - Python 3.11            │
│  - conda env: 311         │
│  - Multi-language (ja/en) │
└───────────────────────────┘
    │
    ├─→ SQLite Database
    │    - File: backend/app.db
    │    - Schema: estimator
    │
    └─→ OpenAI API
         - Model: gpt-4o-mini
         - API Key: Environment Variable
```

### Component Details

#### 1. Apache HTTPD (Reverse Proxy)

**Responsibilities**:
- SSL/TLS termination (Let's Encrypt certificate)
- Access control via Basic Authentication
- Reverse proxy (routing to backend)
- HTTP→HTTPS redirect

**Configuration File**: `/etc/httpd/conf.d/estimator.path-finder.jp.conf`

**Key Configuration**:
```apache
<VirtualHost *:443>
    ServerName estimator.path-finder.jp
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/path-finder.jp/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/path-finder.jp/privkey.pem

    ProxyTimeout 600

    # Basic Authentication
    <Location />
      AuthType Basic
      AuthName "Restricted"
      AuthUserFile /etc/httpd/.htpasswd_estimator
      Require valid-user
    </Location>

    # Proxy Configuration
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

**Ports**: 443 (HTTPS), 80 (HTTP)

**Process Management**: systemd (`httpd.service`)

#### 2. systemd Service (estimator.service)

**Responsibilities**:
- Start/stop/restart Uvicorn process
- Automatic restart on failure
- Log management

**Configuration File**: `/etc/systemd/system/estimator.service`

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

**Key Parameters**:
- `User/Group`: ec2-user
- `Restart`: on-failure (restart only on failure)
- `RestartSec`: 5 seconds wait before restart
- `EnvironmentFile`: Load environment variables from .env file

#### 3. Uvicorn (ASGI Server)

**Responsibilities**:
- ASGI server for FastAPI application
- Asynchronous request processing
- Proxy header support

**Startup Command**:
```bash
uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8100 \
  --proxy-headers \
  --timeout-keep-alive 120
```

**Key Parameters**:
- `--host 127.0.0.1`: Listen on localhost only (security)
- `--port 8100`: Port 8100
- `--proxy-headers`: Respect X-Forwarded-For headers
- `--timeout-keep-alive 120`: Keep-Alive timeout 120 seconds

#### 4. FastAPI Application

**Responsibilities**:
- Provide RESTful API endpoints
- Execute business logic
- Database operations
- OpenAI API integration

**Python Environment**:
- Python 3.11 (conda environment: 311)
- Framework: FastAPI
- ORM: SQLAlchemy 2.0
- Database: SQLite3

**Directory Structure**:
```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── api/v1/tasks.py      # API endpoints
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── core/                # Configuration & utilities
│   ├── db/                  # Database connection
│   ├── prompts/             # LLM prompts
│   ├── middleware/          # Middleware
│   └── locales/             # Multi-language files (ja.json/en.json)
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── app.db                   # SQLite database
```

#### 5. Database (SQLite)

**File**: `backend/app.db`

**Table Structure**:
- `tasks`: Estimation tasks
- `deliverables`: Deliverables
- `qa_pairs`: Questions and answers
- `estimates`: Estimation results
- `messages`: Chat messages

**Backup**:
- Manual backup: `cp app.db app.db.backup`
- Scheduled backup: Recommended via cron

#### 6. External API (OpenAI)

**Endpoint**: `https://api.openai.com/v1/chat/completions`

**Model**: `gpt-4o-mini`

**Use Cases**:
- Question generation
- Estimate generation
- Chat adjustments

**Authentication**: API Key (environment variable `OPENAI_API_KEY`)

---

## System Requirements

### Hardware Requirements

**Minimum Requirements**:
- CPU: 2 vCPU
- Memory: 2 GB RAM
- Storage: 10 GB (OS + Application + Logs)

**Recommended Requirements**:
- CPU: 4 vCPU
- Memory: 4 GB RAM
- Storage: 20 GB SSD

**Production Environment (EC2)**:
- Instance Type: t3.small or higher
- OS: Amazon Linux 2023
- Architecture: x86_64

### Software Requirements

**Operating System**:
- Amazon Linux 2023
- Or CentOS 7+, Ubuntu 20.04+

**Required Software**:
- Apache HTTPD 2.4+ (mod_ssl, mod_proxy, mod_proxy_http)
- Python 3.11+
- Anaconda/Miniconda (conda environment manager)
- SQLite 3.x
- systemd

**SSL Certificate**:
- Let's Encrypt (certbot)

**External Services**:
- OpenAI API account
- Internet connection (OpenAI API communication)

---

## Environment Variables

### .env File

**File Path**: `backend/.env`

**Configuration Items**:

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

### Environment Variable Details

| Variable Name | Description | Default Value | Required |
|--------------|-------------|---------------|----------|
| `DATABASE_URL` | SQLite database URL | `sqlite:///./app.db` | ✓ |
| `DB_SCHEMA` | Database schema name | `estimator` | ✓ |
| `OPENAI_API_KEY` | OpenAI API key | - | ✓ |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o-mini` | ✓ |
| `DAILY_UNIT_COST` | Daily unit cost (deprecated) | `40000` | - |
| `DAILY_UNIT_COST_JPY` | Daily unit cost (JPY) | `40000` | ✓ |
| `DAILY_UNIT_COST_USD` | Daily unit cost (USD) | `500` | ✓ |
| `TAX_RATE_JA` | Tax rate (Japan) | `10` | ✓ |
| `TAX_RATE_EN` | Tax rate (English) | `0` | ✓ |
| `UPLOAD_DIR` | File upload directory | `uploads` | ✓ |
| `MAX_UPLOAD_SIZE_MB` | Max upload size (MB) | `10` | ✓ |
| `LANGUAGE` | System language (ja/en) | `ja` | ✓ |
| `HOST` | Uvicorn bind host | `127.0.0.1` | ✓ |
| `PORT` | Uvicorn port | `8100` | ✓ |
| `CORS_ORIGINS` | CORS allowed origins | `https://estimator.path-finder.jp` | ✓ |

### Environment Variable Caveats

**⚠️ Important**:
- **Do NOT use inline comments (`#`) in `.env` file**
- Pydantic cannot parse integer values with inline comments

**NG Example**:
```bash
DAILY_UNIT_COST=40000  # Deprecated: Use language-specific settings below
```

**OK Example**:
```bash
# Note: DAILY_UNIT_COST is deprecated - use language-specific settings below
DAILY_UNIT_COST=40000
```

---

## Secret Management

### OpenAI API Key

**Storage Location**: `backend/.env` (File permissions: 600)

**Security Measures**:
1. Add `.env` file to `.gitignore` (prevent commit)
2. Restrict file permissions:
   ```bash
   chmod 600 backend/.env
   chown ec2-user:ec2-user backend/.env
   ```
3. Regular key rotation
4. Usage monitoring (OpenAI dashboard)

### Basic Authentication Password

**Storage Location**: `/etc/httpd/.htpasswd_estimator`

**Password Change**:
```bash
sudo htpasswd /etc/httpd/.htpasswd_estimator <username>
```

**File Permissions**:
```bash
sudo chmod 644 /etc/httpd/.htpasswd_estimator
sudo chown root:root /etc/httpd/.htpasswd_estimator
```

### SSL/TLS Certificate

**Certificate Paths**:
- Full chain: `/etc/letsencrypt/live/path-finder.jp/fullchain.pem`
- Private key: `/etc/letsencrypt/live/path-finder.jp/privkey.pem`

**Auto-renewal** (certbot):
```bash
# Test certificate renewal
sudo certbot renew --dry-run

# Auto-renewal (cron)
0 0,12 * * * certbot renew --quiet --post-hook "systemctl reload httpd"
```

---

## Start/Stop Procedures

### 1. Apache Start/Stop

```bash
# Start
sudo systemctl start httpd

# Stop
sudo systemctl stop httpd

# Restart
sudo systemctl restart httpd

# Reload config (zero downtime)
sudo systemctl reload httpd

# Status check
sudo systemctl status httpd

# Enable auto-start
sudo systemctl enable httpd
```

### 2. estimator.service Start/Stop

```bash
# Start
sudo systemctl start estimator

# Stop
sudo systemctl stop estimator

# Restart
sudo systemctl restart estimator

# Status check
systemctl status estimator

# Real-time logs
journalctl -u estimator -f

# Last 100 lines
journalctl -u estimator -n 100

# Enable auto-start
sudo systemctl enable estimator
```

### 3. Health Check

```bash
# Local health check
curl -s http://127.0.0.1:8100/health

# Expected output
{"status":"healthy"}

# Production health check (Basic Auth required)
curl -u username:password https://estimator.path-finder.jp/api/v1/health
```

### 4. Complete Startup Sequence

```bash
# 1. Start Apache
sudo systemctl start httpd

# 2. Start estimator service
sudo systemctl start estimator

# 3. Verify
systemctl status httpd estimator
curl -s http://127.0.0.1:8100/health
```

### 5. Complete Shutdown Sequence

```bash
# 1. Stop estimator service
sudo systemctl stop estimator

# 2. Stop Apache (caution: affects other apps)
sudo systemctl stop httpd
```

---

## Deployment Procedures

### Initial Deployment

#### 1. Clone Repository

```bash
cd /home/ec2-user/hirashimallc
git clone <repository-url> 09_pj-見積り作成システム
cd 09_pj-見積り作成システム/output3/backend
```

#### 2. Python Environment Setup

```bash
# Create conda environment
source /home/ec2-user/anaconda3/bin/activate
conda create -n 311 python=3.11
conda activate 311

# Install dependencies
pip install -r requirements.txt
```

#### 3. Environment Variables Configuration

```bash
# Create .env file
cp .env.sample .env
nano .env

# Set required items
# - OPENAI_API_KEY
# - DATABASE_URL
# - CORS_ORIGINS
```

#### 4. Database Initialization

```bash
# Auto-created on first startup
# Or manually run migrations
# (alembic not currently used)
```

#### 5. Create Log Directory

```bash
sudo mkdir -p /var/log/estimator
sudo chown ec2-user:ec2-user /var/log/estimator
```

#### 6. Register systemd Service

```bash
# Place service file
sudo cp /path/to/estimator.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable estimator

# Start service
sudo systemctl start estimator
```

#### 7. Apache Configuration

```bash
# Place configuration file
sudo cp /path/to/estimator.path-finder.jp.conf /etc/httpd/conf.d/

# Test configuration
sudo apachectl configtest

# Restart Apache
sudo systemctl restart httpd
```

#### 8. Basic Authentication Setup

```bash
# Create user
sudo htpasswd -c /etc/httpd/.htpasswd_estimator <username>

# Set permissions
sudo chmod 644 /etc/httpd/.htpasswd_estimator
```

#### 9. SSL Certificate Setup

```bash
# Obtain certificate (first time only)
sudo certbot certonly --webroot -w /var/www/html -d estimator.path-finder.jp

# Auto-renewal setup
sudo crontab -e
# Add the following
0 0,12 * * * certbot renew --quiet --post-hook "systemctl reload httpd"
```

#### 10. Verification

```bash
# Local check
curl -s http://127.0.0.1:8100/health

# Production check
curl -u username:password https://estimator.path-finder.jp/api/v1/health
```

### Update Deployment

#### 1. Update Code

```bash
cd /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3

# Git pull
git pull origin main

# Or manually update files
```

#### 2. Update Dependencies (if needed)

```bash
cd backend
source /home/ec2-user/anaconda3/bin/activate
conda activate 311
pip install -r requirements.txt
```

#### 3. Update Environment Variables (if needed)

```bash
nano .env
# Save changes
```

#### 4. Database Migration (if needed)

```bash
# Currently alembic not used
# Future migrations will be performed here
```

#### 5. Restart Service

```bash
# Restart estimator service
sudo systemctl restart estimator

# Check status
systemctl status estimator

# Check logs
journalctl -u estimator -n 50
```

#### 6. Verification

```bash
# Health check
curl -s http://127.0.0.1:8100/health

# API test
curl -u username:password https://estimator.path-finder.jp/api/v1/translations
```

---

## Rollback Procedures

### Code Rollback

#### Using Git

```bash
cd /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3

# View commit history
git log --oneline -10

# Rollback to specific commit
git checkout <commit-hash>

# Or return to branch
git checkout main
git pull

# Restart service
sudo systemctl restart estimator
```

#### Using Manual Backup

```bash
# Restore from backup
cp -r /path/to/backup/backend/* /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/

# Restart service
sudo systemctl restart estimator
```

### Database Rollback

```bash
# Restore from backup
cp /path/to/backup/app.db.backup /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/app.db

# Restart service
sudo systemctl restart estimator
```

### Environment Variables Rollback

```bash
# Restore from backup
cp /path/to/backup/.env.backup /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/.env

# Restart service
sudo systemctl restart estimator
```

### Apache Configuration Rollback

```bash
# Restore from backup
sudo cp /etc/httpd/conf.d/estimator.path-finder.jp.conf.backup /etc/httpd/conf.d/estimator.path-finder.jp.conf

# Test configuration
sudo apachectl configtest

# Restart Apache
sudo systemctl restart httpd
```

---

## Scaling Strategy

### Vertical Scaling (Scale Up)

**EC2 Instance Type Change**:

```bash
# 1. Stop services
sudo systemctl stop estimator
sudo systemctl stop httpd

# 2. Change instance type via EC2 console
#    t3.small → t3.medium → t3.large

# 3. After instance restart, start services
sudo systemctl start httpd
sudo systemctl start estimator
```

**Recommended Instance Types**:
- Small scale (~100 requests/day): t3.small (2 vCPU, 2 GB)
- Medium scale (~500 requests/day): t3.medium (2 vCPU, 4 GB)
- Large scale (~1000 requests/day): t3.large (2 vCPU, 8 GB)

### Horizontal Scaling (Scale Out)

**Multiple Uvicorn Workers**:

```bash
# Modify systemd service file
sudo nano /etc/systemd/system/estimator.service

# Change ExecStart to:
ExecStart=/bin/bash -lc "source /home/ec2-user/anaconda3/bin/activate && conda activate 311 && exec uvicorn app.main:app --host 127.0.0.1 --port 8100 --workers 4 --proxy-headers --timeout-keep-alive 120"

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart estimator
```

**Note**:
- SQLite may have concurrency issues with multiple workers
- Migration to PostgreSQL/MySQL recommended

### Load Balancing (Future)

**Example Configuration**:
```
Internet
   ↓
AWS ELB/ALB
   ↓
┌────────────┬────────────┬────────────┐
│ Instance 1 │ Instance 2 │ Instance 3 │
└────────────┴────────────┴────────────┘
   ↓
Shared RDS (PostgreSQL)
```

---

## Backup & Recovery

### Backup Targets

1. **Database**: `backend/app.db`
2. **Environment Variables**: `backend/.env`
3. **Uploaded Files**: `backend/uploads/`
4. **Apache Configuration**: `/etc/httpd/conf.d/estimator.path-finder.jp.conf`
5. **systemd Configuration**: `/etc/systemd/system/estimator.service`

### Manual Backup

```bash
#!/bin/bash
# Backup script

BACKUP_DIR="/home/ec2-user/backups/estimator"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR/$TIMESTAMP

# Database
cp /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/app.db \
   $BACKUP_DIR/$TIMESTAMP/app.db

# Environment variables
cp /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/.env \
   $BACKUP_DIR/$TIMESTAMP/.env

# Uploaded files
cp -r /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/uploads \
   $BACKUP_DIR/$TIMESTAMP/

# Apache configuration
sudo cp /etc/httpd/conf.d/estimator.path-finder.jp.conf \
   $BACKUP_DIR/$TIMESTAMP/estimator.path-finder.jp.conf

# systemd configuration
sudo cp /etc/systemd/system/estimator.service \
   $BACKUP_DIR/$TIMESTAMP/estimator.service

echo "Backup completed: $BACKUP_DIR/$TIMESTAMP"
```

### Automated Backup (cron)

```bash
# Edit crontab
crontab -e

# Daily backup at 3 AM
0 3 * * * /home/ec2-user/scripts/backup_estimator.sh
```

### Recovery Procedure

```bash
# 1. Stop service
sudo systemctl stop estimator

# 2. Restore database
cp /home/ec2-user/backups/estimator/<timestamp>/app.db \
   /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/app.db

# 3. Restore environment variables
cp /home/ec2-user/backups/estimator/<timestamp>/.env \
   /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/.env

# 4. Restore uploaded files
cp -r /home/ec2-user/backups/estimator/<timestamp>/uploads/* \
   /home/ec2-user/hirashimallc/09_pj-見積り作成システム/output3/backend/uploads/

# 5. Start service
sudo systemctl start estimator

# 6. Verify
curl -s http://127.0.0.1:8100/health
```

---

## Monitoring

### Log Checking

#### 1. estimator Service Logs

```bash
# Real-time logs
journalctl -u estimator -f

# Last 100 lines
journalctl -u estimator -n 100

# Errors only
journalctl -u estimator -p err

# Date filter
journalctl -u estimator --since "2025-10-21 00:00:00"

# File logs
tail -f /var/log/estimator/backend.log
tail -f /var/log/estimator/backend-error.log
```

#### 2. Apache Logs

```bash
# Access log
sudo tail -f /var/log/httpd/access_log

# Error log
sudo tail -f /var/log/httpd/error_log

# estimator-specific logs (if configured)
sudo tail -f /var/log/httpd/estimator_access.log
sudo tail -f /var/log/httpd/estimator_error.log
```

### Health Check

```bash
# Local health check
curl -s http://127.0.0.1:8100/health

# Production health check
curl -u username:password https://estimator.path-finder.jp/api/v1/health

# Status code only
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8100/health
```

### Process Monitoring

```bash
# Process check
ps aux | grep uvicorn
ps aux | grep httpd

# Port check
lsof -i :8100
lsof -i :443
lsof -i :80

# Resource usage
top -u ec2-user
htop -u ec2-user
```

### Metrics Collection (Recommended)

**CloudWatch Metrics**:
- CPUUtilization
- MemoryUtilization
- DiskReadBytes/DiskWriteBytes
- NetworkIn/NetworkOut

**Custom Metrics**:
- Request count (CustomMetric)
- Response time (CustomMetric)
- Error rate (CustomMetric)

---

## Cost Management

### OpenAI API Cost

**Pricing** (gpt-4o-mini):
- Input: $0.15 / 1M tokens
- Output: $0.6 / 1M tokens

**Cost Estimation**:
- Per estimate: ~5,000 tokens (2,000 input + 3,000 output)
- Cost: ~$0.0021/estimate
- 1,000 estimates: ~$2.1

**Cost Reduction**:
1. Optimize prompts (remove unnecessary info)
2. Cache reuse (reuse same questions)
3. Implement rate limiting (TODO-9 completed)
4. Usage monitoring and alerts

### AWS Infrastructure Cost

**EC2**:
- t3.small: $0.0208/hour × 24 hours × 30 days = ~$15/month

**Data Transfer**:
- Free up to 1TB/month (typically within limits)

**SSL Certificate**:
- Let's Encrypt: Free

**Total Estimation**:
- ~$17/month (EC2 + OpenAI API)

---

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

**Symptom**: `systemctl status estimator` shows `failed` state

**Causes and Solutions**:

**Cause 1: Port 8100 Already in Use**
```bash
# Check port usage
lsof -i :8100

# Stop process
kill <PID>

# Restart service
sudo systemctl restart estimator
```

**Cause 2: Environment Variable Parse Error**
```bash
# Check error log
sudo tail -50 /var/log/estimator/backend-error.log

# Check .env file (remove inline comments)
nano backend/.env

# Restart service
sudo systemctl restart estimator
```

**Cause 3: conda Environment Not Found**
```bash
# Check conda environment
source /home/ec2-user/anaconda3/bin/activate
conda env list

# Create if missing
conda create -n 311 python=3.11
conda activate 311
pip install -r requirements.txt

# Restart service
sudo systemctl restart estimator
```

#### 2. Estimate Generation Fails

**Symptom**: "OpenAI API error" displayed

**Solution**:
```bash
# Check OpenAI API status
curl https://status.openai.com/

# Check API key
cat backend/.env | grep OPENAI_API_KEY

# Check logs
journalctl -u estimator -n 100 | grep -i openai
```

#### 3. Basic Authentication Fails

**Symptom**: 401 Unauthorized

**Solution**:
```bash
# Check password file
sudo cat /etc/httpd/.htpasswd_estimator

# Reset password
sudo htpasswd /etc/httpd/.htpasswd_estimator <username>

# Reload Apache
sudo systemctl reload httpd
```

For detailed troubleshooting, see [TROUBLESHOOTING_EN.md](../operations/TROUBLESHOOTING_EN.md).

---

## References

- [TROUBLESHOOTING_EN.md](../operations/TROUBLESHOOTING_EN.md) - Troubleshooting Guide
- [RUNBOOK_EN.md](../operations/RUNBOOK_EN.md) - Operations Runbook
- [ARCHITECTURE_EN.md](../architecture/ARCHITECTURE_EN.md) - Architecture Documentation
- [DEVELOPER_GUIDE_EN.md](../development/DEVELOPER_GUIDE_EN.md) - Developer Guide

---

**Last Updated**: 2025-10-21
**Author**: Claude Code
**Version**: 1.0
