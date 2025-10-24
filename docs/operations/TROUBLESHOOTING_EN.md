# Troubleshooting Guide

## 📋 Table of Contents

1. [Top 10 Common Issues](#top-10-common-issues)
2. [Log Checking Methods](#log-checking-methods)
3. [Error Code Resolutions](#error-code-resolutions)
4. [Performance Issues](#performance-issues)
5. [OpenAI API Related Issues](#openai-api-related-issues)
6. [Database Issues](#database-issues)
7. [Network Issues](#network-issues)
8. [Multi-language Related Issues](#multi-language-related-issues)

---

## Top 10 Common Issues

### Issue 1: Server Won't Start

**Symptoms**:
```bash
$ systemctl status estimator
● estimator.service - Estimator Backend
   Active: failed (Result: exit-code)
```

**Causes and Solutions**:

#### Cause 1-1: Port 8100 Already in Use

**Check**:
```bash
lsof -i :8100
# Output: uvicorn [PID] your-username ...
```

**Solution**:
```bash
# Identify process
ps aux | grep uvicorn | grep 8100

# Stop process
kill <PID>

# Or stop all uvicorn processes
pkill -f "uvicorn.*8100"

# Restart service
sudo systemctl restart estimator
```

#### Cause 1-2: Environment Variable Parse Error

**Error Log**:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
DAILY_UNIT_COST
  Input should be a valid integer, unable to parse string as an integer
```

**Cause**: End-of-line comments in `.env` file

**Check**:
```bash
cat backend/.env | grep DAILY_UNIT_COST
# NG: DAILY_UNIT_COST=40000  # comment
```

**Solution**:
```bash
# Edit .env file
nano backend/.env

# Before (NG):
# DAILY_UNIT_COST=40000  # Deprecated

# After (OK):
# Note: DAILY_UNIT_COST is deprecated
DAILY_UNIT_COST=40000

# Restart service
sudo systemctl restart estimator
```

#### Cause 1-3: Conda Environment Not Found

**Error Log**:
```
CommandNotFoundError: Your shell has not been properly configured to use 'conda activate'.
```

**Solution**:
```bash
# Check conda environment
source /path/to/python/bin/activate
conda env list

# Create if doesn't exist
conda create -n 311 python=3.11
conda activate your-python-env
pip install -r backend/requirements.txt

# Restart service
sudo systemctl restart estimator
```

#### Cause 1-4: Missing Dependencies

**Solution**:
```bash
source /path/to/python/bin/activate
conda activate your-python-env
cd backend
pip install -r requirements.txt --upgrade

sudo systemctl restart estimator
```

---

### Issue 2: Estimation Generation Fails

**Symptoms**: "OpenAI API error" displayed

#### Cause 2-1: OpenAI API Outage

**Check**:
```bash
# Check OpenAI API status
curl -s https://status.openai.com/api/v2/status.json | jq '.status.description'
```

**Solution**:
- Wait for OpenAI recovery
- Monitor status page: https://status.openai.com/

#### Cause 2-2: Invalid API Key

**Check**:
```bash
cat backend/.env | grep OPENAI_API_KEY
# Check if key is empty or invalid
```

**Solution**:
```bash
# Get new API key from OpenAI dashboard
# https://platform.openai.com/api-keys

# Update .env file
nano backend/.env
# OPENAI_API_KEY=sk-proj-xxxxx

sudo systemctl restart estimator
```

#### Cause 2-3: API Usage Limit Reached

**Check**:
```bash
# Check OpenAI usage page
# https://platform.openai.com/usage
```

**Solution**:
- Review billing settings
- Increase usage limit
- Adjust rate limiting

#### Cause 2-4: CircuitBreaker in OPEN State

**Check**:
```bash
journalctl -u estimator -n 100 | grep "CircuitBreaker"
# Output: CircuitBreaker is OPEN
```

**Solution**:
```bash
# Wait 60 seconds for HALF_OPEN transition
sleep 60

# Or restart immediately
sudo systemctl restart estimator
```

---

### Issue 3: File Upload Fails

**Symptoms**: "File too large" error

**Check**:
```bash
ls -lh /path/to/upload/file.xlsx
# Check file size
```

**Solution**:

#### Solution 1: Reduce File Size

- Remove unnecessary rows/columns
- Compress to under 10MB

#### Solution 2: Change Configuration

```bash
# Edit .env file
nano backend/.env

# Change
MAX_UPLOAD_SIZE_MB=20

# Restart service
sudo systemctl restart estimator
```

---

### Issue 4: Basic Authentication Fails

**Symptoms**: 401 Unauthorized

**Check**:
```bash
# Check password file
sudo cat /etc/httpd/.htpasswd_estimator

# Check user exists
sudo cat /etc/httpd/.htpasswd_estimator | grep username
```

**Solution**:
```bash
# Reset password
sudo htpasswd /etc/httpd/.htpasswd_estimator username

# Reload Apache
sudo systemctl reload httpd
```

---

### Issue 5: SSL Certificate Error

**Symptoms**: Browser shows "Your connection is not private"

**Check**:
```bash
# Check certificate expiration
sudo certbot certificates

# Or
echo | openssl s_client -connect estimator.path-finder.jp:443 2>/dev/null | \
  openssl x509 -noout -dates
```

**Solution**:
```bash
# Renew certificate
sudo certbot renew

# Reload Apache
sudo systemctl reload httpd
```

---

### Issue 6: Database Lock Error

**Symptoms**: "database is locked" error

**Check**:
```bash
# Check long-running processes
ps aux | grep uvicorn
```

**Solution**:
```bash
# Restart service
sudo systemctl restart estimator

# Database integrity check
sqlite3 backend/app.db "PRAGMA integrity_check;"
```

---

### Issue 7: Out of Memory Error

**Symptoms**: Service suddenly stops, OOM Killer log

**Check**:
```bash
# Memory usage
free -h

# OOM Killer log
dmesg | grep -i "out of memory"
journalctl -k | grep -i "killed process"
```

**Solution**:
```bash
# Immediate action: Restart service
sudo systemctl restart estimator

# Long-term solution: Change instance type
# t3.small → t3.medium
```

---

### Issue 8: Timeout Error

**Symptoms**: "Request timeout", 504 Gateway Timeout

**Check**:
```bash
# Check timeout settings
grep -r "timeout" /etc/httpd/conf.d/estimator*.conf
grep -r "timeout" backend/.env
```

**Solution**:
```bash
# Change Apache configuration
sudo nano /etc/httpd/conf.d/estimator.path-finder.jp.conf

# Extend ProxyTimeout
ProxyTimeout 900

sudo systemctl reload httpd

# Extend Uvicorn timeout
# Edit systemd file
sudo nano /etc/systemd/system/estimator.service

# --timeout-keep-alive 120 → 180

sudo systemctl daemon-reload
sudo systemctl restart estimator
```

---

### Issue 9: Language Switch Not Reflected

**Symptoms**: Still Japanese even after changing to LANGUAGE=en

**Check**:
```bash
cat backend/.env | grep LANGUAGE
```

**Solution**:
```bash
# Check/change .env file
nano backend/.env
# LANGUAGE=en

# Restart service (required)
sudo systemctl restart estimator

# Clear browser cache
# Ctrl+Shift+R (hard reload)
```

---

### Issue 10: Excel Output Garbled Text

**Symptoms**: Downloaded Excel file has garbled characters

**Check**:
```bash
# Check locales files
ls -la backend/app/locales/

# Check translation file encoding
file backend/app/locales/ja.json
# Output: UTF-8 Unicode text
```

**Solution**:
```bash
# Reinstall openpyxl
source /path/to/python/bin/activate
conda activate your-python-env
pip install --upgrade openpyxl

sudo systemctl restart estimator
```

---

## Log Checking Methods

### Development Environment

```bash
# Output directly to console
cd backend
source /path/to/python/bin/activate
conda activate your-python-env
uvicorn app.main:app --reload --log-level debug
```

### Production Environment (systemd)

#### Real-time Logs

```bash
# estimator service log (real-time)
journalctl -u estimator -f

# Apache log (real-time)
sudo tail -f /var/log/httpd/access_log
sudo tail -f /var/log/httpd/error_log
```

#### Historical Logs

```bash
# Last 100 lines
journalctl -u estimator -n 100

# Date range
journalctl -u estimator --since "2025-10-21 00:00:00" --until "2025-10-21 23:59:59"

# Errors only
journalctl -u estimator -p err

# Search specific string
journalctl -u estimator | grep "OpenAI"
```

#### File Logs

```bash
# estimator log files
tail -f /var/log/estimator/backend.log
tail -f /var/log/estimator/backend-error.log

# Apache log files
sudo tail -f /var/log/httpd/access_log
sudo tail -f /var/log/httpd/error_log
```

---

## Error Code Resolutions

### HTTP Status Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad Request | Check request parameters, Guardrails check |
| 401 | Unauthorized | Check Basic auth, reset password |
| 403 | Forbidden | Check access permissions, file permissions |
| 404 | Not Found | Check URL path, routing |
| 413 | Payload Too Large | Reduce file size, change MAX_UPLOAD_SIZE_MB |
| 422 | Unprocessable Entity | Check request body, Pydantic validation |
| 500 | Internal Server Error | Check server logs, stack trace |
| 502 | Bad Gateway | Check backend service, Uvicorn startup |
| 503 | Service Unavailable | Check resource limits, concurrent executions |
| 504 | Gateway Timeout | Check timeout settings, optimize processing time |

### OpenAI API Errors

| Error | Cause | Solution |
|-------|-------|----------|
| AuthenticationError | Invalid API key | Reset API key |
| RateLimitError | Rate limit exceeded | Wait and retry, upgrade plan |
| APIConnectionError | Network error | Check connection, retry |
| Timeout | Timeout | Retry, extend timeout |
| APIError | API-side error | Check status page, wait |

---

## Performance Issues

### High CPU Usage

**Check**:
```bash
top -b -n 1 | head -20
ps aux --sort=-%cpu | head -10
```

**Solution**:
```bash
# Restart process
sudo systemctl restart estimator

# Consider scale-up
# t3.small → t3.medium
```

### High Memory Usage

**Check**:
```bash
free -h
ps aux --sort=-%mem | head -10
```

**Solution**:
```bash
# Suspected memory leak: restart
sudo systemctl restart estimator

# Clear cache
sync; echo 3 | sudo tee /proc/sys/vm/drop_caches
```

### Slow Response

**Check**:
```bash
# Measure response time
time curl -u user:pass https://estimator.path-finder.jp/api/v1/health
```

**Solution**:
```bash
# Optimize database queries
# Adjust parallel processing
# Utilize caching
```

---

## OpenAI API Related Issues

### API Call Failure

**Check**:
```bash
# OpenAI API status
curl -s https://status.openai.com/api/v2/status.json | jq .

# Network connection
ping api.openai.com
```

**Solution**:
```bash
# Retry logic auto-executes (max 3 times)
# CircuitBreaker automatic fallback

# Manual retry
sudo systemctl restart estimator
```

### API Usage Exceeded

**Check**:
```bash
# Check OpenAI dashboard
# https://platform.openai.com/usage
```

**Solution**:
- Review monthly budget
- Adjust rate limiting (implemented in Cost management and rate limiting)
- Optimize prompts

---

## Database Issues

### Database File Corruption

**Check**:
```bash
sqlite3 backend/app.db "PRAGMA integrity_check;"
# Expected: ok
```

**Solution**:
```bash
# Restore from backup
sudo systemctl stop estimator
cp /path/to/backups/estimator/<latest>/app.db backend/app.db
sudo systemctl start estimator
```

### Database Lock

**Check**:
```bash
# Check locking process
lsof backend/app.db
```

**Solution**:
```bash
sudo systemctl restart estimator
```

---

## Network Issues

### External Connection Unavailable

**Check**:
```bash
# OpenAI API connection test
curl -I https://api.openai.com

# DNS resolution test
nslookup api.openai.com
```

**Solution**:
```bash
# Check network configuration
ip addr show
route -n

# Check security group (EC2)
```

### SSL/TLS Certificate Issues

**Check**:
```bash
# Check certificate chain
openssl s_client -connect estimator.path-finder.jp:443 -showcerts
```

**Solution**:
```bash
# Renew certificate
sudo certbot renew
sudo systemctl reload httpd
```

---

## Multi-language Related Issues

### Missing Translation Key Error

**Symptoms**: KeyError: 'ui.some_key'

**Solution**:
```bash
# Add to both ja.json and en.json
nano backend/app/locales/ja.json
nano backend/app/locales/en.json

# Example addition
{
  "ui": {
    "some_key": "translated text"
  }
}

sudo systemctl restart estimator
```

### LLM Output Not in Expected Language

**Check**:
```bash
# Check if prompt contains language instruction
cat backend/app/prompts/question_prompts.py | grep language_instruction
```

**Solution**:
```python
# Add language instruction to prompt
language_instruction = t('prompts.language_instruction')
prompt = f"{base_prompt}\n\n{language_instruction}"
```

---

## Emergency Response Flowchart

```
Issue Occurs
   ↓
Check Service Status
   ├─ Stopped → systemctl restart estimator
   └─ Running → Next
       ↓
Check Logs
   ├─ OpenAI API Error → Check API status
   ├─ Database Error → Integrity check
   ├─ Memory Error → Restart
   └─ Other → Detailed investigation
       ↓
Implement Solution
   ↓
Verify Operation
   ├─ Normal → Complete
   └─ Abnormal → Escalate
```

---

## References

- [DEPLOYMENT.md](../deployment/DEPLOYMENT.md) - Deployment Guide
- [RUNBOOK.md](RUNBOOK.md) - Operations Runbook
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - Architecture Documentation

---

**Last Updated**: 2025-10-21
**Author**: Claude Code
**Version**: 1.0
