# AI Estimation System Monitoring Plan

**Last Updated**: 2025-10-22
**Version**: 1.0
**Target System**: AI Estimation System (Estimator Backend)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Monitored Metrics](#monitored-metrics)
3. [SLI/SLO/SLA](#slislosla)
4. [Alert Thresholds](#alert-thresholds)
5. [Log Investigation](#log-investigation)
6. [Troubleshooting](#troubleshooting)
7. [Future Enhancements](#future-enhancements)

---

## Overview

### Monitoring Objectives

Visualize the operational status of the AI Estimation System to achieve:

- **Early Failure Detection**: Instantly detect errors and minimize user impact
- **Performance Degradation Detection**: Identify API response time deterioration early
- **Resource Usage Tracking**: Monitor OpenAI API token consumption for cost management
- **Operational Quality Improvement**: Continuous improvement based on metrics

### Monitoring Architecture

```
┌─────────────────┐
│  FastAPI App    │
│  (Estimator)    │
└────────┬────────┘
         │
         ├─→ Structured Logs (JSON)
         │   - Request ID
         │   - Level (INFO/WARNING/ERROR)
         │   - Timestamp
         │   - Custom Fields
         │
         ├─→ Metrics Collection
         │   - API Call Statistics
         │   - OpenAI Usage
         │   - Error Tracking
         │
         └─→ Health Checks
             - /health (basic)
             - /api/v1/health (detailed)
             - /api/v1/metrics (statistics)
```

---

## Monitored Metrics

### 1. API Response Performance

| Metric | Description | Retrieval Method |
|--------|-------------|------------------|
| **Average Response Time** | Average response time for all API endpoints (seconds) | `GET /api/v1/metrics` → `avg_response_time` |
| **P95 Response Time** | 95th percentile response time (seconds) | `GET /api/v1/metrics` → `p95_response_time` |
| **Total API Calls** | Cumulative API call count | `GET /api/v1/metrics` → `total_api_calls` |

**Monitoring Points**:
- Caution if average response time exceeds 3 seconds
- Warning if P95 response time exceeds 10 seconds

### 2. API Success Rate

| Metric | Description | Retrieval Method |
|--------|-------------|------------------|
| **Success Rate** | Percentage of HTTP 2xx responses (%) | `GET /api/v1/metrics` → `success_rate` |
| **Error Rate** | Percentage of error occurrences (%) | `GET /api/v1/metrics` → `error_rate` |
| **Total Errors** | Cumulative error count | `GET /api/v1/metrics` → `total_errors` |

**Monitoring Points**:
- Warning if success rate falls below 95%
- Warning if error rate exceeds 5%

### 3. OpenAI API Usage

| Metric | Description | Retrieval Method |
|--------|-------------|------------------|
| **OpenAI Call Count** | Total OpenAI API calls | `GET /api/v1/metrics` → `total_openai_calls` |
| **OpenAI Success Rate** | OpenAI API success rate (%) | `GET /api/v1/metrics` → `openai_success_rate` |
| **Token Consumption** | Cumulative token usage | `GET /api/v1/metrics` → `total_tokens_used` |
| **Operation Statistics** | Statistics by estimate/question/chat | `GET /api/v1/metrics` → `openai_operations` |

**Monitoring Points**:
- Warning if OpenAI success rate falls below 90%
- Monitor abnormal increases in token consumption (cost management)

### 4. System Health

| Metric | Description | Retrieval Method |
|--------|-------------|------------------|
| **Health Status** | healthy / degraded / unhealthy | `GET /api/v1/health` → `status` |

**Determination Criteria**:
- `healthy`: All metrics within normal range
- `degraded`: OpenAI success rate < 90%
- `unhealthy`: Error rate > 5%

---

## SLI/SLO/SLA

### Service Level Indicator (SLI)

Actual system performance metrics:

| SLI | Definition | Measurement Method |
|-----|------------|-------------------|
| **Availability** | Percentage of successful service responses | `success_rate` (HTTP 2xx / Total Requests) |
| **Latency** | P95 API response time | `p95_response_time` |
| **Accuracy** | OpenAI API success rate | `openai_success_rate` |

### Service Level Objective (SLO)

Target service levels:

| SLO | Target | Measurement Period |
|-----|--------|-------------------|
| **Availability** | ≥ 99% | Monthly |
| **Latency** | P95 < 5 seconds | Daily |
| **Accuracy** | OpenAI success rate ≥ 95% | Weekly |

### Service Level Agreement (SLA)

Service levels promised to users:

| SLA | Guaranteed Value | Penalty |
|-----|-----------------|---------|
| **Monthly Uptime** | ≥ 95% | Per contract terms |

---

## Alert Thresholds

### Alert Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| **🟢 Normal** | All metrics within normal range | - |
| **🟡 Caution** | Metrics entered caution range | Review within 24 hours |
| **🟠 Warning** | Metrics entered warning range | Respond within 4 hours |
| **🔴 Critical** | Service outage or SLA violation | Immediate response |

### Specific Thresholds

#### 1. API Response Time

| Metric | Caution | Warning | Critical |
|--------|---------|---------|----------|
| Average Response Time | > 3s | > 5s | > 10s |
| P95 Response Time | > 5s | > 10s | > 20s |

**Action Items**:
- Caution: Check logs and investigate delay causes
- Warning: Verify OpenAI API timeout settings, check DB connections
- Critical: Restart service, consider scaling up

#### 2. Error Rate

| Metric | Caution | Warning | Critical |
|--------|---------|---------|----------|
| Error Rate | > 2% | > 5% | > 10% |
| Success Rate | < 98% | < 95% | < 90% |

**Action Items**:
- Caution: Check error logs (`GET /api/v1/metrics/errors`)
- Warning: Identify and fix root cause of errors
- Critical: Consider service shutdown, notify users

#### 3. OpenAI API

| Metric | Caution | Warning | Critical |
|--------|---------|---------|----------|
| OpenAI Success Rate | < 95% | < 90% | < 80% |
| Token Consumption | +50% increase | +100% increase | +200% increase |

**Action Items**:
- Caution: Check OpenAI API key and rate limits
- Warning: Verify fallback processing operation
- Critical: Contact OpenAI support, temporarily switch to fallback

---

## Log Investigation

### Structured Log Locations

```bash
# System logs (systemd journal)
sudo journalctl -u estimator -n 100

# File logs
sudo tail -f /var/log/estimator/backend.log
sudo tail -f /var/log/estimator/backend-error.log
```

### Searching JSON Logs

#### 1. Filter by Specific request_id

```bash
sudo grep "request_id.*abc-123-def" /var/log/estimator/backend-error.log | jq .
```

#### 2. Extract Error Logs Only

```bash
sudo grep '"level":"ERROR"' /var/log/estimator/backend-error.log | jq .
```

#### 3. Logs for Specific Time Period

```bash
sudo journalctl -u estimator --since "2025-10-22 00:00:00" --until "2025-10-22 23:59:59"
```

#### 4. OpenAI API Call Logs

```bash
sudo grep "OpenAI API call" /var/log/estimator/backend-error.log | jq .
```

### Metrics API

#### Get Metrics Summary

```bash
curl -s http://127.0.0.1:8100/api/v1/metrics | jq .
```

**Example Output**:
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

#### Get Recent Errors

```bash
curl -s http://127.0.0.1:8100/api/v1/metrics/errors | jq .
```

#### Health Check

```bash
curl -s http://127.0.0.1:8100/api/v1/health | jq .
```

**Example Output**:
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

## Troubleshooting

### Scenario 1: Slow API Response

**Symptom**: P95 response time exceeds 10 seconds

**Diagnostic Steps**:

1. Check metrics
```bash
curl -s http://127.0.0.1:8100/api/v1/metrics | jq '.avg_response_time, .p95_response_time'
```

2. Check OpenAI API call duration
```bash
sudo grep "OpenAI API call successful" /var/log/estimator/backend-error.log | jq '.duration' | tail -20
```

3. Check resource usage
```bash
top -bn1 | grep uvicorn
free -h
```

**Actions**:
- Slow OpenAI API → Adjust timeout settings (`.env` `OPENAI_TIMEOUT`)
- Insufficient memory → Scale up server
- Insufficient parallelism → Increase `MAX_PARALLEL_ESTIMATES`

### Scenario 2: Rising Error Rate

**Symptom**: Error rate exceeds 5%

**Diagnostic Steps**:

1. Get error list
```bash
curl -s http://127.0.0.1:8100/api/v1/metrics/errors | jq .
```

2. Check error logs
```bash
sudo grep '"level":"ERROR"' /var/log/estimator/backend-error.log | tail -20 | jq .
```

3. Analyze error patterns
```bash
sudo grep '"level":"ERROR"' /var/log/estimator/backend-error.log | jq '.error' | sort | uniq -c
```

**Actions**:
- OpenAI API errors → Check API key, verify rate limits
- Database errors → Check DB connection, verify disk space
- Input validation errors → Check Guardrails configuration

### Scenario 3: Low OpenAI Success Rate

**Symptom**: OpenAI success rate falls below 90%

**Diagnostic Steps**:

1. Check OpenAI-related logs
```bash
sudo grep "OpenAI API call failed" /var/log/estimator/backend-error.log | jq .
```

2. Check Circuit Breaker status
```bash
sudo grep "Circuit breaker" /var/log/estimator/backend-error.log | tail -10 | jq .
```

3. Check retry logs
```bash
sudo grep "Retrying" /var/log/estimator/backend-error.log | jq .
```

**Actions**:
- Rate limiting → Check OpenAI dashboard, consider plan change
- Timeout → Increase `OPENAI_TIMEOUT`
- Invalid API key → Update to new API key

---

## Future Enhancements

The current monitoring system provides basic functionality, but the following enhancements are possible:

### 1. Prometheus Metrics Export

**Purpose**: Store metrics in time-series database

**Implementation**:
```python
# Use prometheus_client library
from prometheus_client import Counter, Histogram, Gauge

request_count = Counter('api_requests_total', 'Total API requests')
response_time = Histogram('api_response_time_seconds', 'API response time')
openai_tokens = Gauge('openai_tokens_used', 'OpenAI tokens used')
```

**Benefits**:
- Long-term trend analysis
- Advanced query capabilities
- Integration with industry-standard tools

### 2. Grafana Dashboard

**Purpose**: Metrics visualization

**Components**:
- API response time graph (time-series)
- Error rate gauge
- OpenAI token consumption graph
- Health status display

### 3. Alert Notifications

**Purpose**: Automatic notifications on anomaly detection

**Notification Targets**:
- Slack
- Email
- PagerDuty

**Implementation Example**:
```python
# Slack notification
if error_rate > 5:
    send_slack_alert(f"⚠️ Error rate exceeds threshold: {error_rate}%")
```

### 4. Distributed Tracing

**Purpose**: Request tracking across microservices

**Tools**:
- Jaeger
- Zipkin
- OpenTelemetry

### 5. Log Aggregation

**Purpose**: Centralized management of logs from multiple servers

**Tools**:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Loki + Grafana
- CloudWatch Logs (AWS)

---

## Summary

This monitoring system provides:

✅ **Structured Logging**: JSON format, request ID tracing
✅ **Metrics Collection**: API statistics, OpenAI usage
✅ **Health Checks**: Automatic health determination
✅ **PII Protection**: Personal information masking
✅ **Troubleshooting**: Detailed diagnostic procedures

**Post-Deployment Actions**:
1. Collect metrics baseline for 1 week
2. Adjust thresholds based on actual data
3. Regular monitoring reviews (weekly)
4. Establish incident response procedures

---

**Contact**: System Operations Team
**Document Version**: 1.0
**Last Updated**: 2025-10-22
