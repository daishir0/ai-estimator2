# Operations Runbook

## 📋 Table of Contents

1. [Overview](#overview)
2. [Daily Operations](#daily-operations)
3. [Weekly Operations](#weekly-operations)
4. [Monthly Operations](#monthly-operations)
5. [Incident Response](#incident-response)
6. [Maintenance Procedures](#maintenance-procedures)
7. [Escalation](#escalation)
8. [Contact Information](#contact-information)
9. [Checklists](#checklists)

---

## Overview

### Purpose

This Runbook standardizes daily operational tasks for the AI Estimator System to ensure stable service delivery.

### Target Audience

- System Operations Team
- Infrastructure Team
- On-call Engineers

### Service Level Objectives (SLO)

- **Uptime**: 99.0% (Monthly downtime < 7.2 hours)
- **Response Time**: P95 < 5 seconds
- **Error Rate**: < 1%

### System Overview

```
Apache HTTPD (Port 443/80)
   ↓
systemd estimator.service (Port 8100)
   ↓
FastAPI + SQLite + OpenAI API
```

---

## Daily Operations

### Morning Check (09:00)

#### 1. Service Status Check

```bash
# Check service status
systemctl status httpd estimator --no-pager

# Expected output: Both "active (running)"
```

**Criteria**:
- ✅ Normal: `active (running)`
- ⚠️ Warning: `activating` (starting)
- 🔴 Critical: `failed`, `inactive`

**Action on Failure**:
1. Refer to [Incident Response](#incident-response) section
2. Attempt service restart
3. Escalate if not resolved

#### 2. Health Check

```bash
# Local health check
curl -s http://127.0.0.1:8100/health

# Expected output
{"status":"healthy"}

# Production health check
curl -u username:password https://your-domain.com/api/v1/health
```

**Criteria**:
- ✅ Normal: `{"status":"healthy"}` + HTTP 200
- 🔴 Critical: Error response, timeout, connection refused

**Action on Failure**:
1. Check service logs: `journalctl -u estimator -n 100`
2. Restart Apache: `sudo systemctl restart httpd`
3. Restart estimator: `sudo systemctl restart estimator`

#### 3. Disk Usage Check

```bash
# Check disk usage
df -h /

# Thresholds:
# - Warning: 80%+
# - Critical: 90%+
```

**Action on Warning**:
```bash
# Clean up log files
sudo journalctl --vacuum-time=7d

# Delete old uploads (30+ days)
find /path/to/ai-estimator2/backend/uploads -type f -mtime +30 -delete

# Delete old backups (60+ days)
find /path/to/backups/estimator -type d -mtime +60 -exec rm -rf {} +
```

#### 4. Error Log Review

```bash
# estimator errors (last 24 hours)
journalctl -u estimator --since "24 hours ago" -p err

# Apache errors (last 24 hours)
sudo tail -1000 /var/log/httpd/error_log | grep -i error
```

**Error Classification**:
- **OpenAI API Error**: Check API status, verify API key
- **Database Lock**: Check concurrency, investigate long queries
- **Memory Error**: Check memory usage, restart process
- **Timeout**: Check timeout settings, verify network

#### 5. Resource Usage Check

```bash
# CPU & Memory usage
top -b -n 1 | head -20

# Process-specific resources
ps aux | grep -E 'uvicorn|httpd' | grep -v grep

# Memory thresholds:
# - Warning: 80%+
# - Critical: 90%+
```

**Action on High Load**:
1. Restart process (suspected memory leak)
2. Stop unnecessary processes
3. Consider scaling up

### Evening Check (17:00)

#### 1. Today's Request Count

```bash
# Today's access count (Apache)
sudo grep "$(date +%d/%b/%Y)" /var/log/httpd/access_log | wc -l

# Today's estimate count (estimator)
journalctl -u estimator --since "today" | grep "Task created" | wc -l
```

#### 2. Error Rate Check

```bash
# Today's error count
journalctl -u estimator --since "today" -p err | wc -l

# Error rate = Error count / Request count × 100
# Threshold: < 1%
```

#### 3. Response Time Check

```bash
# Average response time (Apache access_log analysis)
sudo awk '{print $NF}' /var/log/httpd/access_log | \
  grep -E '^[0-9]+$' | \
  awk '{sum+=$1; count++} END {print sum/count/1000000 " seconds"}'
```

### Daily Report

Report the following via Slack/Email:

```
【Daily Operations Report】2025-10-21

■ Service Status
- httpd: Normal
- estimator: Normal
- Health check: Normal

■ Resource Usage
- Disk usage: 65%
- Memory usage: 70%
- CPU usage: 30%

■ Today's Metrics
- Access count: 120
- Estimate count: 45
- Error count: 2
- Error rate: 0.44%

■ Notes
- None

■ Actions Taken
- None
```

---

## Weekly Operations

### Every Monday (10:00)

#### 1. Backup Verification

```bash
# Check backup directory
ls -lht /path/to/backups/estimator/ | head -10

# Check latest backup contents
LATEST_BACKUP=$(ls -t /path/to/backups/estimator/ | head -1)
ls -lh /path/to/backups/estimator/$LATEST_BACKUP/
```

**Verification Items**:
- ✅ app.db exists
- ✅ .env exists
- ✅ uploads/ directory exists
- ✅ Backup size is reasonable (compare with history)

**Action on Failure**:
1. Perform manual backup
2. Check cron job
3. Check backup script

#### 2. SSL Certificate Expiry Check

```bash
# Check SSL certificate expiry
sudo certbot certificates

# Warning if < 30 days
# Critical if < 7 days
```

**Renewal Procedure**:
```bash
# Test certificate renewal
sudo certbot renew --dry-run

# Actual renewal
sudo certbot renew

# Reload Apache
sudo systemctl reload httpd
```

#### 3. Log Rotation Check

```bash
# Check estimator log file sizes
ls -lh /var/log/estimator/

# Manual rotation if any file > 100MB
sudo journalctl --rotate
sudo journalctl --vacuum-size=100M
```

#### 4. Security Update Check

```bash
# Check Amazon Linux security updates
sudo yum check-update --security

# Apply updates (if needed)
sudo yum update --security -y

# Reboot if required
# - During maintenance window
# - After backup
```

#### 5. Database Integrity Check

```bash
# Check database file
ls -lh /path/to/ai-estimator2/backend/app.db

# SQLite integrity check
sqlite3 /path/to/ai-estimator2/backend/app.db "PRAGMA integrity_check;"

# Expected output: "ok"
```

**Action on Failure**:
1. Restore from database backup
2. Escalate to development team

### Weekly Report

```
【Weekly Operations Report】2025-10-21 ~ 2025-10-27

■ Uptime
- Availability: 99.8%
- Downtime: 0 minutes
- Incidents: 0

■ Performance
- Average response time: 1.2s
- P95 response time: 3.5s
- Error rate: 0.3%

■ Usage
- Total access count: 840
- Total estimate count: 315
- Unique users: 12

■ Resource Usage
- Average CPU usage: 35%
- Average memory usage: 72%
- Disk usage: 68%

■ Security
- SSL certificate expiry: 45 days remaining
- Security updates: All applied

■ Notes
- None

■ Improvement Suggestions
- None
```

---

## Monthly Operations

### 1st of Every Month (10:00)

#### 1. OpenAI API Usage & Cost Review

```bash
# Check OpenAI usage (Dashboard)
# https://platform.openai.com/usage
```

**Review Items**:
- Monthly token usage
- Monthly cost
- Budget overrun

**Action on Budget Overrun**:
1. Detailed usage analysis
2. Adjust rate limits
3. Consider prompt optimization

#### 2. Capacity Planning Review

```bash
# Monthly data growth
DB_SIZE_START=$(du -h /path/to/backups/estimator/$(ls -t /path/to/backups/estimator/ | tail -1)/app.db | cut -f1)
DB_SIZE_END=$(du -h /path/to/ai-estimator2/backend/app.db | cut -f1)

echo "Database size change: $DB_SIZE_START → $DB_SIZE_END"

# Disk usage trend
df -h / | tail -1
```

**Criteria for Capacity Expansion**:
- Disk usage > 80%
- Monthly growth rate > 20%
- Predicted to reach 90% in 3 months

#### 3. Performance Review

**Data Collection**:
```bash
# Monthly performance summary
journalctl -u estimator --since "1 month ago" | \
  grep -E "EST.*done" | \
  awk '{print $(NF-1)}' | \
  awk -F's' '{sum+=$1; count++} END {print "Average processing time:", sum/count, "seconds"}'
```

**Analysis Items**:
- Average response time
- P95/P99 response time
- Slow request investigation

#### 4. Security Review

```bash
# Access log analysis (suspicious access)
sudo grep "401" /var/log/httpd/access_log | tail -50

# Failed Basic authentication attempts
sudo grep "authentication failure" /var/log/httpd/error_log | wc -l
```

**Security Checklist**:
- Unauthorized access attempts
- Signs of brute force attacks
- Abnormal traffic patterns

#### 5. Backup Test Recovery

```bash
# Create test directory
mkdir -p /tmp/estimator_restore_test

# Test restore from latest backup
LATEST_BACKUP=$(ls -t /path/to/backups/estimator/ | head -1)
cp -r /path/to/backups/estimator/$LATEST_BACKUP/* /tmp/estimator_restore_test/

# Verify database integrity
sqlite3 /tmp/estimator_restore_test/app.db "PRAGMA integrity_check;"

# Cleanup
rm -rf /tmp/estimator_restore_test
```

### Monthly Report

```
【Monthly Operations Report】October 2025

■ Service Uptime
- Availability: 99.7%
- Total downtime: 13 minutes
- Incidents: 1 (minor)

■ Performance Metrics
- Average response time: 1.3s
- P95 response time: 3.8s
- P99 response time: 8.2s
- Error rate: 0.4%

■ Usage Statistics
- Total access count: 3,600
- Total estimate count: 1,350
- Unique users: 45
- Monthly growth: +15%

■ Resource Usage
- Average CPU usage: 38%
- Peak CPU usage: 85%
- Average memory usage: 75%
- Disk usage: 72% (+5% increase)

■ Cost
- EC2: $15.00
- OpenAI API: $2.80
- Total: $17.80

■ Security
- Unauthorized access attempts: 3 (all blocked)
- SSL certificate renewal: Normal
- Security updates: All applied

■ Backup
- Scheduled backups: Normal
- Backup recovery test: Successful

■ Incident Summary
1. 2025-10-15 10:23: OpenAI API timeout (13 minutes)
   - Cause: Temporary OpenAI outage
   - Resolution: Auto-recovery
   - Prevention: Retry logic strengthened

■ Improvements Implemented
- CircuitBreaker implementation
- Rate limiting enhancement

■ Next Month Plans
- Database performance optimization
- Monitoring dashboard construction
```

---

## Incident Response

### Incident Level Definition

| Level | Impact | Response Time | Escalation |
|-------|--------|---------------|------------|
| **P1 (Critical)** | Complete service outage | Immediate | Immediately to senior |
| **P2 (Major)** | Partial service outage | Within 30 min | After 30 min to senior |
| **P3 (Normal)** | Performance degradation | Within 2 hours | After 2 hours to senior |
| **P4 (Minor)** | Some errors occurring | Within 24 hours | Not required |

### Incident Response Flow

```
Incident Detection
   ↓
Initial Response (Within 5 min)
 - Confirm impact scope
 - Determine incident level
 - Initial escalation
   ↓
Root Cause Analysis (Within 15 min)
 - Check logs
 - Check resources
 - Check external services
   ↓
Recovery Actions
 - Restart
 - Configuration change
 - Rollback
   ↓
Verification
 - Health check
 - Functional testing
   ↓
Post-incident
 - Create incident report
 - Plan prevention measures
```

### P1: Complete Service Outage

#### Symptoms
- Health check failed
- Service not responding
- All users affected

#### Initial Response (Within 5 min)

```bash
# 1. Check service status
systemctl status httpd estimator

# 2. Check processes
ps aux | grep -E 'uvicorn|httpd'

# 3. Check ports
lsof -i :443 -i :80 -i :8100

# 4. Check error logs
journalctl -u estimator -n 50
sudo tail -50 /var/log/httpd/error_log
```

#### Recovery Procedure

**Step 1: Service Restart**
```bash
# Restart estimator
sudo systemctl restart estimator

# Restart Apache
sudo systemctl restart httpd

# Wait 30 seconds
sleep 30

# Health check
curl -s http://127.0.0.1:8100/health
```

**Step 2: If Still Not Recovered**
```bash
# Reboot EC2 instance
sudo reboot

# After reboot (wait 3 minutes)
# Check auto-start
systemctl status httpd estimator
```

**Step 3: If Complete Recovery Fails**
1. Restore from backup → [Backup & Recovery](../deployment/DEPLOYMENT_EN.md#backup--recovery)
2. Escalate to development team

### P2: Partial Service Outage

#### Symptoms
- Only estimate generation fails
- Specific endpoints return errors
- Some users affected

#### Recovery Procedure

**If OpenAI API Issue**
```bash
# Check OpenAI API status
curl -s https://status.openai.com/api/v2/status.json | jq '.status.description'

# If OpenAI outage, wait for auto-recovery
# After recovery, restart estimator
sudo systemctl restart estimator
```

**If Database Lock**
```bash
# Check long-running processes
ps aux | grep uvicorn

# Restart process
sudo systemctl restart estimator
```

### P3: Performance Degradation

#### Symptoms
- Response time > 5 seconds
- Frequent timeouts
- Poor user experience

#### Investigation

```bash
# Check CPU usage
top -b -n 1 | head -20

# Check memory usage
free -h

# Check disk I/O
iostat -x 1 5

# Process-specific resources
ps aux --sort=-%cpu | head -10
ps aux --sort=-%mem | head -10
```

#### Actions

**If High CPU Usage**
```bash
# Restart process
sudo systemctl restart estimator

# If still not improved
# Consider instance type change
```

**If High Memory Usage**
```bash
# Suspected memory leak
sudo systemctl restart estimator

# Clear cache
sync; echo 3 | sudo tee /proc/sys/vm/drop_caches
```

### P4: Minor Errors

#### Symptoms
- Error rate < 1%
- Occurs only under specific conditions
- Service continues

#### Actions

```bash
# Collect error logs
journalctl -u estimator --since "1 hour ago" -p err > /tmp/error_log.txt

# Analyze error patterns
cat /tmp/error_log.txt | grep -oP 'Error: \K.*' | sort | uniq -c | sort -rn

# Report to development team (within 24 hours)
```

---

## Maintenance Procedures

### Planned Maintenance

#### Preparation (1 Week Before)

1. **Maintenance Notification**
   - Notify users (Slack/Email)
   - Specify date/time, duration, impact

2. **Take Backup**
   ```bash
   /home/your-username/scripts/backup_estimator.sh
   ```

3. **Create Maintenance Procedure**
   - Clarify work steps
   - Confirm rollback procedure

#### Maintenance Execution

**Step 1: Stop Service**
```bash
# Display maintenance page (implement in Apache)
# Or display 503 error page

# Stop estimator
sudo systemctl stop estimator

# Check status
systemctl status estimator
```

**Step 2: Perform Work**
```bash
# Example: Code update
cd /path/to/ai-estimator2
git pull origin main

# Example: Dependency update
cd backend
source /path/to/python/bin/activate
conda activate your-python-env
pip install -r requirements.txt

# Example: Database migration
# (if needed)
```

**Step 3: Start Service**
```bash
# Start estimator
sudo systemctl start estimator

# Wait for startup
sleep 10

# Check status
systemctl status estimator
```

**Step 4: Verification**
```bash
# Health check
curl -s http://127.0.0.1:8100/health

# Functional testing
# - Task creation
# - Question generation
# - Estimate generation
# - Excel output
```

**Step 5: Maintenance Completion Notification**
- Notify users of completion
- Report work results

#### On Maintenance Failure

```bash
# Perform rollback
git checkout <previous-commit>
sudo systemctl restart estimator

# If still not recovered
# Restore from backup
```

### Emergency Maintenance

#### Security Patch Application

```bash
# 1. Take backup
/home/your-username/scripts/backup_estimator.sh

# 2. Apply patch
sudo yum update --security -y

# 3. Restart service (if needed)
sudo systemctl restart estimator

# 4. Verification
curl -s http://127.0.0.1:8100/health
```

#### SSL Certificate Renewal

```bash
# 1. Renew certificate
sudo certbot renew

# 2. Reload Apache config
sudo systemctl reload httpd

# 3. Verify SSL
echo | openssl s_client -connect your-domain.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

---

## Escalation

### Escalation Criteria

| Situation | Escalate To | Timing |
|-----------|-------------|--------|
| P1 incident occurs | Infrastructure Manager | Immediately |
| P1 not recovered within 30 min | CTO/Dev Manager | After 30 min |
| P2 not recovered within 2 hours | Infrastructure Manager | After 2 hours |
| Security incident | Security Manager | Immediately |
| Data loss possibility | CTO/Dev Manager | Immediately |

### Escalation Procedure

1. **Initial Report** (Within 5 min)
   - Incident occurrence time
   - Incident level
   - Impact scope
   - Initial response actions

2. **Regular Updates** (Every 15 min)
   - Current status
   - Investigation results
   - Recovery estimate

3. **Recovery Report**
   - Recovery time
   - Root cause
   - Prevention measures

### Escalation Communication Template

```
【Incident Report】AI Estimator System

■ Incident Level: P1 (Critical)

■ Occurrence Time: 2025-10-21 10:23

■ Current Status: Complete service outage

■ Impact Scope: All users

■ Cause: Under investigation

■ Initial Response:
- Restarted estimator service → Failed
- Restarted Apache service → Failed
- Currently analyzing logs

■ Next Actions:
- EC2 instance reboot scheduled (10:30)

■ Estimated Recovery: 10:40

■ Reporter: Operations Team A
```

---

## Contact Information

### Emergency Contacts

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| Infrastructure Manager | [Name] | [Email/Phone] | 24/7 |
| Development Manager | [Name] | [Email/Phone] | Weekdays 9-18 |
| CTO | [Name] | [Email/Phone] | 24/7 (P1 only) |
| Security Manager | [Name] | [Email/Phone] | 24/7 |

### External Service Contacts

| Service | Contact | Status Page |
|---------|---------|-------------|
| OpenAI | https://help.openai.com/ | https://status.openai.com/ |
| AWS | AWS Support Console | https://status.aws.amazon.com/ |
| Let's Encrypt | https://letsencrypt.org/contact/ | https://letsencrypt.status.io/ |

---

## Checklists

### Daily Checklist

```
【Daily Operations Checklist】

Date: ___________
Operator: ___________

□ Service status check (httpd/estimator)
□ Health check execution (local/production)
□ Disk usage check (< 80%)
□ Error log review (last 24 hours)
□ Resource usage check (CPU/Memory)
□ Today's request count check
□ Error rate check (< 1%)
□ Daily report creation/submission

Notes:
___________________________
___________________________
___________________________
```

### Weekly Checklist

```
【Weekly Operations Checklist】

Week: ___________
Operator: ___________

□ Backup verification (existence/size)
□ SSL certificate expiry check (> 30 days)
□ Log rotation check
□ Security update check/application
□ Database integrity check
□ Weekly report creation/submission

Notes:
___________________________
___________________________
___________________________
```

### Monthly Checklist

```
【Monthly Operations Checklist】

Month: ___________
Operator: ___________

□ OpenAI API usage/cost review
□ Capacity planning review
□ Performance review
□ Security review
□ Backup test recovery
□ Monthly report creation/submission

Notes:
___________________________
___________________________
___________________________
```

---

## References

- [DEPLOYMENT_EN.md](../deployment/DEPLOYMENT_EN.md) - Deployment Guide
- [TROUBLESHOOTING_EN.md](TROUBLESHOOTING_EN.md) - Troubleshooting Guide
- [ARCHITECTURE_EN.md](../architecture/ARCHITECTURE_EN.md) - Architecture Documentation

---

**Last Updated**: 2025-10-21
**Author**: Claude Code
**Version**: 1.0
