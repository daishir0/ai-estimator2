# Emergency Shutdown Procedure

**Version**: 1.0
**Last Updated**: 2025-10-22
**Target**: AI Estimator System
**Purpose**: Emergency response procedures for OpenAI API cost overruns or unauthorized access detection

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Emergency Shutdown for Cost Overrun](#emergency-shutdown-for-cost-overrun)
3. [Response to Unauthorized Access](#response-to-unauthorized-access)
4. [Service Restart Procedure](#service-restart-procedure)
5. [Contact Information](#contact-information)
6. [Periodic Checks](#periodic-checks)

---

## Overview

This document establishes procedures for responding to the following emergency situations:

1. **OpenAI API Cost Overrun**: When monthly cost limit (default: $200/month) is exceeded
2. **Unauthorized Access / DoS Attack**: When access exceeding rate limits continues
3. **Other Anomalies**: When unexpected large volumes of API calls occur

---

## Emergency Shutdown for Cost Overrun

### ⚠️ Emergency Shutdown Triggers

Consider emergency shutdown in any of the following situations:

| Situation | Threshold | Response |
|-----------|-----------|----------|
| Monthly Cost Warning | $160 (80%) | Enhanced monitoring |
| Monthly Cost Exceeded | $200 (100%) | **Automatic shutdown** |
| Abnormal Growth Rate | >$10 in 1 hour | Immediate investigation & shutdown |

### 🛑 Step 1: Immediate System Shutdown

```bash
# SSH connection
ssh your-username@<server-IP>

# Stop service immediately
sudo systemctl stop estimator

# Verify shutdown
sudo systemctl status estimator
```

**Result**: Confirm `inactive (dead)` is displayed

---

### 📊 Step 2: Verify Cost Status

Check cost status via admin endpoint (if checking before service shutdown):

```bash
# Get cost status
curl http://localhost:8009/api/v1/admin/costs

# Example response
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

**Check Points**:
- `monthly_cost_usd`: Monthly cumulative cost
- `monthly_usage_percent`: Usage rate against limit
- `total_openai_calls`: Number of API calls

---

### 🔍 Step 3: Root Cause Investigation

#### Log Verification

```bash
# Check error logs (last 100 lines)
sudo journalctl -u estimator -n 100 --no-pager

# Extract cost-related logs
sudo journalctl -u estimator | grep -i "cost"

# Check logs for specific time period
sudo journalctl -u estimator --since "2025-10-22 10:00:00" --until "2025-10-22 11:00:00"
```

#### Identify Abnormal Patterns

**Anomalies to Check**:
1. **High Volume of API Calls**: Concentrated access to specific endpoints
2. **Abnormally Long Prompts**: Input token count 10x+ normal
3. **Retry Loops**: Same request occurring in large volumes in short time
4. **Unauthorized Access**: Abnormal access from specific IPs

---

### 🔧 Step 4: Configuration Adjustment

Adjust settings based on root cause:

#### 4.1 Reduce Cost Limits

```bash
# Edit .env file
cd /path/to/ai-estimator2/backend
nano .env

# Edit the following
DAILY_COST_LIMIT=5.0      # Default: 10.0
MONTHLY_COST_LIMIT=100.0  # Default: 200.0
```

#### 4.2 Strengthen Rate Limits

```bash
# Edit .env file
nano .env

# Edit the following
RATE_LIMIT_MAX_REQUESTS=50   # Default: 100
RATE_LIMIT_WINDOW_SECONDS=3600  # 1 hour (usually no change needed)
```

#### 4.3 Limit Parallel Execution

```bash
# Edit .env file
nano .env

# Add/edit the following
MAX_CONCURRENT_ESTIMATES=2  # Default: 5
```

---

### ✅ Step 5: Pre-Restart Checklist

- [ ] Root cause of cost overrun identified
- [ ] Configuration changes implemented (if needed)
- [ ] Actual usage verified on OpenAI dashboard
- [ ] Decision made: wait until next month or raise limit
- [ ] Enhanced monitoring in place (periodic check scripts, etc.)

---

## Response to Unauthorized Access

### 🚨 Detection Methods

#### Check Rate Limit Exceeded Logs

```bash
# Extract rate limit exceeded logs
sudo journalctl -u estimator | grep "Rate limit exceeded"

# Check rate limit exceeded for specific IP
sudo journalctl -u estimator | grep "Rate limit exceeded" | grep "192.168.1.100"
```

#### Check via Admin Endpoint

```bash
# Check rate limit status
curl http://localhost:8009/api/v1/admin/rate-limits

# Example response
{
  "max_requests": 100,
  "window_seconds": 3600,
  "active_clients": 25
}
```

---

### 🛡️ Response Procedure

#### 1. Reset Rate Limit for Specific IP

```bash
# Only execute for legitimate IPs
curl -X POST http://localhost:8009/api/v1/admin/reset-rate-limit/192.168.1.100
```

#### 2. Block via Firewall (for malicious access)

```bash
# Block specific IP
sudo iptables -A INPUT -s 192.168.1.100 -j DROP

# Save settings
sudo service iptables save

# Verify
sudo iptables -L -n
```

#### 3. Strengthen Rate Limits (system-wide)

Refer to "Step 4.2 Strengthen Rate Limits" above

---

## Service Restart Procedure

### 1. Apply Configuration Changes

```bash
# After editing config file, restart service
cd /path/to/ai-estimator2/backend
sudo systemctl restart estimator
```

### 2. Verify Restart

```bash
# Check service status
sudo systemctl status estimator

# Health check
curl http://localhost:8009/health

# Response: {"status":"healthy"}
```

### 3. Start Monitoring

```bash
# Real-time log monitoring
sudo journalctl -u estimator -f

# Periodic cost status check (separate terminal)
watch -n 300 'curl -s http://localhost:8009/api/v1/admin/costs | jq .'
```

**Monitoring Items**:
- Cost status check every 5 minutes
- Error log monitoring
- Rate limit exceeded monitoring

---

## Contact Information

### System Administrators

| Role | Contact | Availability |
|------|---------|--------------|
| Primary Admin | admin@example.com | 24/7 |
| Secondary Admin | backup@example.com | Weekdays 9-18 |
| Emergency Contact | +81-XX-XXXX-XXXX | 24/7 |

### External Services

| Service | Dashboard URL | Notes |
|---------|---------------|-------|
| OpenAI API | https://platform.openai.com/usage | API Key: `OPENAI_API_KEY` |
| AWS (Server) | https://console.aws.amazon.com/ec2/ | EC2 Instance Management |

---

## Periodic Checks

### Daily Checks (Recommended)

```bash
# Check cost status
curl http://localhost:8009/api/v1/admin/costs

# Check items:
# - daily_usage_percent < 80%
# - monthly_usage_percent < 90%
```

### Weekly Checks (Recommended)

```bash
# Check full metrics
curl http://localhost:8009/api/v1/admin/metrics

# Check items:
# - Error rate < 5%
# - OpenAI success rate > 95%
# - Rate limit exceeded incidents
```

### Monthly Checks (Required)

1. Verify actual billing amount on OpenAI dashboard
2. Verify consistency with system logs
3. Review cost limit settings

---

## Appendix: Automated Monitoring Scripts

### Cost Monitoring Script

```bash
#!/bin/bash
# /home/your-username/scripts/monitor_costs.sh

THRESHOLD=80
RESPONSE=$(curl -s http://localhost:8009/api/v1/admin/costs)
USAGE=$(echo $RESPONSE | jq -r '.cost.daily_usage_percent')

if (( $(echo "$USAGE > $THRESHOLD" | bc -l) )); then
    echo "WARNING: Daily cost usage at ${USAGE}%"
    # Add email or Slack notification
fi
```

### Example cron Configuration

```bash
# Add to crontab -e
# Monitor costs every hour
0 * * * * /home/your-username/scripts/monitor_costs.sh
```

---

**Created**: 2025-10-22
**Author**: Claude Code
**Version**: 1.0
**Approved by**: (Approver Name)

---

## Change History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-10-22 | 1.0 | Initial creation | Claude Code |
