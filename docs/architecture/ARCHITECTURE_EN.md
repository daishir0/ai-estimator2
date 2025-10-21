# Architecture Documentation

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Data Flow](#data-flow)
4. [Sequence Diagrams](#sequence-diagrams)
5. [Data Model](#data-model)
6. [Directory Structure](#directory-structure)
7. [Security Architecture](#security-architecture)
8. [Resilience Architecture](#resilience-architecture)
9. [Multi-language Architecture](#multi-language-architecture)
10. [Performance Optimization](#performance-optimization)

---

## Overview

### Architecture Design Principles

1. **Simplicity**: Minimal necessary components
2. **Scalability**: Future scaling support
3. **Maintainability**: Easy to understand and modify
4. **Security**: Multi-layer defense
5. **Resilience**: Auto-recovery from failures

### Key Technology Decisions

| Technology | Reason |
|-----------|--------|
| **FastAPI** | High performance, type safety, auto API documentation |
| **SQLite** | Simple, file-based, no dependencies |
| **Uvicorn** | Fast ASGI, async support |
| **Apache HTTPD** | Proven reliability, SSL/TLS, Basic Auth |
| **OpenAI API** | High accuracy AI, cost-effective (gpt-4o-mini) |
| **systemd** | Standard process management, auto-restart |

---

## System Architecture

### Overall Architecture Diagram

(See Japanese version ARCHITECTURE.md for detailed Mermaid diagrams)

### Layer Details

#### 1. Frontend Layer

**Components**:
- Vanilla JavaScript
- Chart.js (chart rendering)
- HTML5/CSS3

**Responsibilities**:
- User interface display
- User input collection
- API calls
- Result visualization

#### 2. Proxy Layer (Apache HTTPD)

**Responsibilities**:
- SSL/TLS termination
- Basic authentication
- Reverse proxy
- HTTP→HTTPS redirect

**Configuration**:
```apache
ProxyPass /api/ http://127.0.0.1:8100/api/ timeout=600
ProxyPass /static/ http://127.0.0.1:8100/static/ timeout=600
ProxyPass / http://127.0.0.1:8100/ui/ timeout=600
```

#### 3. Application Layer (FastAPI)

**Responsibilities**:
- REST API endpoint provision
- Request validation
- Business logic execution
- Response generation

**Main Endpoints**:
- `POST /api/v1/tasks` - Create task
- `GET /api/v1/tasks/{id}/questions` - Get questions
- `POST /api/v1/tasks/{id}/answers` - Submit answers
- `GET /api/v1/tasks/{id}/result` - Get results
- `POST /api/v1/tasks/{id}/chat` - Adjustment request

#### 4. Service Layer

**TaskService**:
- Task lifecycle management
- Overall estimation process control

**QuestionService**:
- AI question generation
- OpenAI API integration

**EstimatorService**:
- Estimation calculation logic
- Effort and cost calculation

**ChatService**:
- Adjustment proposal generation
- AI dialogue control

**SafetyService**:
- Prompt injection detection
- Inappropriate content filtering

**InputService**:
- Excel/CSV parsing
- Data extraction and validation

**ExportService**:
- Excel file generation
- Format styling

#### 5. Data Layer (SQLite)

**Responsibilities**:
- Data persistence
- Transaction management
- Query execution

---

## Data Flow

### Task Creation to Estimation Generation Flow

(See Japanese version ARCHITECTURE.md for detailed Mermaid sequence diagrams)

**Flow Summary**:
1. User inputs deliverables (Excel/CSV/Web form)
2. Safety check (SafetyService)
3. File processing (InputService)
4. Task creation in database
5. AI question generation (QuestionService + OpenAI API)
6. User answers questions
7. Estimate generation for each deliverable (parallel execution)
8. Total calculation (subtotal, tax, total)
9. Excel file generation (ExportService)
10. Result display to user

### Chat Adjustment Flow

**Flow Summary**:
1. User inputs adjustment request ("reduce by $3,000")
2. Safety check
3. AI proposal generation (ChatService + OpenAI API)
4. Display 3 proposal cards
5. User selects and applies proposal
6. Update estimates
7. Regenerate Excel file

---

## Sequence Diagrams

(See Japanese version ARCHITECTURE.md for detailed Mermaid sequence diagrams)

### Task Creation Detailed Sequence

**Key Steps**:
- File upload or web form submission
- Safety validation (Guardrails)
- File parsing (Excel/CSV)
- Database insertion (tasks, deliverables)
- Response generation

### Estimation Generation Detailed Sequence

**Key Steps**:
- Answer submission
- Parallel processing for each deliverable
- CircuitBreaker state check
- Retry logic (max 3 attempts)
- OpenAI API calls
- Database insertion (estimates)
- Total calculation
- Excel generation

---

## Data Model

### ER Diagram

(See Japanese version ARCHITECTURE.md for detailed Mermaid ER diagram)

**Tables**:
- **tasks**: Task information
- **deliverables**: Deliverable items
- **qa_pairs**: Questions and answers
- **estimates**: Estimation results
- **messages**: Chat messages

### Relationships

- tasks 1:N deliverables
- tasks 1:N qa_pairs
- tasks 1:N messages
- deliverables 1:N estimates

---

## Directory Structure

```
output3/backend/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── api/v1/tasks.py           # API endpoints
│   ├── models/                    # SQLAlchemy models
│   ├── schemas/                   # Pydantic schemas
│   ├── services/                  # Business logic
│   ├── core/                      # Common functions & config
│   ├── db/                        # Database connection
│   ├── prompts/                   # LLM prompts
│   ├── middleware/                # Middleware
│   ├── utils/                     # Utilities
│   ├── locales/                   # Translation files (ja.json/en.json)
│   └── static/                    # Static files (HTML/CSS/JS)
├── tests/                         # Test code
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── e2e/                       # E2E tests
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
└── app.db                        # SQLite database
```

---

## Security Architecture

### Multi-layer Defense

**Layer 1: Network**
- SSL/TLS encryption (Let's Encrypt)
- Basic authentication (.htpasswd)

**Layer 2: Application**
- CORS restriction (allowed origins only)
- File size limit (10MB)
- Resource limit (concurrent requests)

**Layer 3: Business Logic**
- SafetyService (Guardrails)
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)

**Layer 4: Data**
- Environment variable isolation (.env)
- File permissions (600)
- Database isolation

### Guardrails Implementation

**Detection Mechanisms**:
1. **Prompt Injection Detection**
   - Suspicious pattern matching
   - Command injection prevention

2. **Inappropriate Content Detection**
   - Harmful content filtering
   - Policy violation detection

3. **Length Limit Check**
   - Maximum input length enforcement

**Implementation**: `app/services/safety_service.py`

---

## Resilience Architecture

### CircuitBreaker Pattern

**States**:
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Failure state, requests blocked, fallback executed
- **HALF_OPEN**: Testing state, limited requests allowed

**Configuration**:
- Failure threshold: 5 consecutive failures
- Timeout: 60 seconds
- Half-open retry count: 1

**Implementation**: `app/middleware/circuit_breaker.py`

### Retry Logic

**Strategy**:
- Maximum retry count: 3
- Backoff strategy: Exponential (1s, 2s, 4s)
- Retry-eligible errors: Timeout, RateLimitError, APIConnectionError

**Flow**:
1. 1st attempt
2. If failed, wait 1 second, 2nd attempt
3. If failed, wait 2 seconds, 3rd attempt
4. If failed, record to CircuitBreaker

**Implementation**: `app/utils/retry.py`

### Loop Detector

**Purpose**: Prevent infinite loops in AI conversations

**Detection**:
- Track prompt hash history
- Threshold: Same prompt 3 times
- Cache TTL: 1 hour

**Implementation**: `app/middleware/loop_detector.py`

### Resource Limiter

**Configuration**:
- Maximum concurrent requests: 5
- Timeout: 30 seconds
- Queue-based waiting

**Implementation**: `app/middleware/resource_limiter.py`

---

## Multi-language Architecture

### Translation System

**Components**:
- Environment variable: `LANGUAGE=ja/en`
- Translation files: `locales/ja.json`, `locales/en.json`
- Translation engine: `app/core/i18n.py`

**Translation Function**:
```python
from app.core.i18n import t

# UI text
title = t('ui.app_title')

# LLM prompt
language_instruction = t('prompts.language_instruction')

# Excel column name
column_name = t('excel.column_deliverable_name')
```

**Translation File Structure**:
```json
{
  "ui": { "app_title": "..." },
  "prompts": { "language_instruction": "..." },
  "excel": { "column_deliverable_name": "..." },
  "messages": { "error_message": "..." }
}
```

---

## Performance Optimization

### Parallel Processing

**Mechanism**:
- `ThreadPoolExecutor` for parallel execution
- Maximum workers: 10
- Concurrent LLM API calls for each deliverable

**Benefits**:
- Reduced total processing time
- Better resource utilization

**Implementation**: `app/services/task_service.py`

### Caching

**Cache Targets**:
- Question generation results (per task ID)
- Adjustment proposals (task ID + request hash)

**TTL**: 1 hour

**Benefits**:
- Reduced API calls
- Faster response time
- Cost savings

---

## References

- [DEPLOYMENT_EN.md](../deployment/DEPLOYMENT_EN.md) - Deployment Guide
- [DEVELOPER_GUIDE_EN.md](../development/DEVELOPER_GUIDE_EN.md) - Developer Guide
- [API_REFERENCE_EN.md](../development/API_REFERENCE_EN.md) - API Reference
- [SECURITY_CHECKLIST_EN.md](../security/SECURITY_CHECKLIST_EN.md) - Security Checklist

---

**Last Updated**: 2025-10-21
**Author**: Claude Code
**Version**: 1.0
