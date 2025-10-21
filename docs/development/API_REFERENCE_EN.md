# API Reference

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints List](#endpoints-list)
4. [Data Models](#data-models)
5. [Error Codes](#error-codes)
6. [Examples](#examples)

---

## Overview

### Base URL

```
https://estimator.path-finder.jp/api/v1
```

**Development Environment**:
```
http://localhost:8000/api/v1
```

### Protocol

- **HTTPS**: Required for production
- **HTTP**: Local development only

### Request Format

- **Content-Type**: `application/json` or `multipart/form-data` (file uploads)
- **Encoding**: UTF-8

### Response Format

- **Content-Type**: `application/json`
- **Encoding**: UTF-8
- **Date Format**: ISO 8601 (`YYYY-MM-DDTHH:MM:SS`)

---

## Authentication

### Basic Authentication

All endpoints are protected with Basic Authentication (production environment).

**Authorization Header**:
```http
Authorization: Basic <base64(username:password)>
```

**Example**:
```bash
curl -u username:password https://estimator.path-finder.jp/api/v1/tasks
```

### Development Environment

No authentication required for local development.

---

## Endpoints List

### Task Management

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tasks` | Create task |
| GET | `/tasks/{task_id}/questions` | Get questions |
| POST | `/tasks/{task_id}/answers` | Submit answers |
| GET | `/tasks/{task_id}/status` | Get status |
| GET | `/tasks/{task_id}/result` | Get result |
| GET | `/tasks/{task_id}/download` | Download Excel result |

### Chat Adjustment

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tasks/{task_id}/chat` | Chat adjustment |
| POST | `/tasks/{task_id}/apply` | Apply adjusted estimates |

### Sample Files

| Method | Path | Description |
|--------|------|-------------|
| GET | `/sample-input` | Download sample Excel |
| GET | `/sample-input-csv` | Download sample CSV |

### Multi-language Support

| Method | Path | Description |
|--------|------|-------------|
| GET | `/translations` | Get translation data |

---

## Endpoint Details

### 1. Create Task

Create a new estimation task.

**Endpoint**:
```http
POST /api/v1/tasks
```

**Request Format**: `multipart/form-data`

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file` | File | No | Excel/CSV file (deliverables list) |
| `deliverables_json` | String | No | Deliverables JSON from web form |
| `system_requirements` | String | No | System requirements (optional) |

**Note**: Either `file` or `deliverables_json` is required.

**Request Example (File Upload)**:
```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks \
  -u username:password \
  -F "file=@input.xlsx" \
  -F "system_requirements=Requirements defined, 3-month development period"
```

**Request Example (Web Form)**:
```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks \
  -u username:password \
  -F "deliverables_json=[{\"name\":\"Requirements Document\",\"description\":\"Define system requirements\"}]" \
  -F "system_requirements=Requirements defined"
```

**Response** (`TaskResponse`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2025-01-17T10:30:00",
  "updated_at": null,
  "error_message": null,
  "result_file_path": null
}
```

**Status Values**:
- `pending`: Created, awaiting questions
- `in_progress`: Processing
- `completed`: Completed
- `failed`: Error occurred

**Error Responses**:
- `400 Bad Request`: Invalid parameters or file format
- `413 Payload Too Large`: File size exceeds 10MB
- `500 Internal Server Error`: Server error

---

### 2. Get Questions

Generate questions for the task (AI-generated).

**Endpoint**:
```http
GET /api/v1/tasks/{task_id}/questions
```

**Path Parameters**:

| Name | Type | Description |
|------|------|-------------|
| `task_id` | String(UUID) | Task ID |

**Request Example**:
```bash
curl https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/questions \
  -u username:password
```

**Response** (String Array):
```json
[
  "What is the expected number of users and access frequency?",
  "Are there any development environment or infrastructure constraints?",
  "Is integration with existing systems required?",
  "Are there any security requirements (authentication, authorization, encryption)?",
  "Are there any deadline or budget constraints?"
]
```

**Error Responses**:
- `404 Not Found`: Task not found
- `500 Internal Server Error`: OpenAI API error, file read error

---

### 3. Submit Answers

Submit answers to questions and start estimation processing.

**Endpoint**:
```http
POST /api/v1/tasks/{task_id}/answers
```

**Path Parameters**:

| Name | Type | Description |
|------|------|-------------|
| `task_id` | String(UUID) | Task ID |

**Request Body** (JSON):
```json
[
  {
    "question": "What is the expected number of users and access frequency?",
    "answer": "Expected 1000 users, average 100 accesses per day."
  },
  {
    "question": "Are there any development environment or infrastructure constraints?",
    "answer": "Development on AWS using Docker."
  }
]
```

**Request Example**:
```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/answers \
  -u username:password \
  -H "Content-Type: application/json" \
  -d '[
    {"question":"Expected users?","answer":"1000 users, 100 accesses/day"},
    {"question":"Environment constraints?","answer":"AWS + Docker"}
  ]'
```

**Response**:
```json
{
  "message": "Task processing started",
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Processing Flow**:
1. Save answers to database
2. Generate estimates for each deliverable in background (parallel execution)
3. Generate Excel result file
4. Update task status to `completed`

**Error Responses**:
- `404 Not Found`: Task not found
- `500 Internal Server Error`: Estimation generation error, database error

---

### 4. Get Status

Get task processing status.

**Endpoint**:
```http
GET /api/v1/tasks/{task_id}/status
```

**Path Parameters**:

| Name | Type | Description |
|------|------|-------------|
| `task_id` | String(UUID) | Task ID |

**Request Example**:
```bash
curl https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/status \
  -u username:password
```

**Response** (`TaskStatusResponse`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2025-01-17T10:30:00",
  "updated_at": "2025-01-17T10:35:00",
  "error_message": null
}
```

**Status Values**:
- `pending`: Awaiting questions
- `in_progress`: Generating estimates
- `completed`: Completed (result available)
- `failed`: Error occurred

**Error Responses**:
- `404 Not Found`: Task not found

---

### 5. Get Result

Get estimation result (completed tasks only).

**Endpoint**:
```http
GET /api/v1/tasks/{task_id}/result
```

**Path Parameters**:

| Name | Type | Description |
|------|------|-------------|
| `task_id` | String(UUID) | Task ID |

**Request Example**:
```bash
curl https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/result \
  -u username:password
```

**Response** (`TaskResultResponse`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "estimates": [
    {
      "deliverable_name": "Requirements Document",
      "deliverable_description": "Define and document system requirements",
      "person_days": 5.0,
      "amount": 200000.0,
      "reasoning": "Requirements phase",
      "reasoning_breakdown": "Design: 2 days, Review: 1 day, Documentation: 2 days",
      "reasoning_notes": "Review existing requirements and add new ones"
    },
    {
      "deliverable_name": "Basic Design Document",
      "deliverable_description": "Design system architecture",
      "person_days": 8.0,
      "amount": 320000.0,
      "reasoning": "Basic design phase",
      "reasoning_breakdown": "Design: 4 days, Review: 2 days, Documentation: 2 days",
      "reasoning_notes": "Create architecture diagrams, ER diagrams, sequence diagrams"
    }
  ],
  "subtotal": 520000.0,
  "tax": 52000.0,
  "total": 572000.0,
  "error_message": null
}
```

**Error Responses**:
- `400 Bad Request`: Task not completed
- `404 Not Found`: Task not found

---

### 6. Download Excel Result

Download estimation result as Excel file.

**Endpoint**:
```http
GET /api/v1/tasks/{task_id}/download
```

**Path Parameters**:

| Name | Type | Description |
|------|------|-------------|
| `task_id` | String(UUID) | Task ID |

**Request Example**:
```bash
curl -O https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/download \
  -u username:password
```

**Response**:
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Filename: `estimate_result_YYYYMMDD_HHMMSS.xlsx`

**Excel File Structure**:

**Sheet 1: Estimates**
- Deliverables list (Name, Description, Person-days, Amount, Breakdown, Notes)
- Totals (Subtotal, Tax, Total)
- Q&A section

**Error Responses**:
- `404 Not Found`: Task or result file not found

---

### 7. Chat Adjustment

Interactively adjust estimates (AI proposal generation).

**Endpoint**:
```http
POST /api/v1/tasks/{task_id}/chat
```

**Path Parameters**:

| Name | Type | Description |
|------|------|-------------|
| `task_id` | String(UUID) | Task ID |

**Request Body** (`ChatRequest`):
```json
{
  "message": "Want to fit within $500,000 budget",
  "intent": "fit_budget",
  "params": {
    "target_budget": 500000
  },
  "estimates": [
    {
      "deliverable_name": "Requirements Document",
      "deliverable_description": "Define system requirements",
      "person_days": 5.0,
      "amount": 200000.0,
      "reasoning": "..."
    }
  ]
}
```

**Request Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message` | String | No | User message |
| `intent` | String | No | Adjustment intent (fit_budget, scope_reduce, unit_cost_change, risk_buffer) |
| `params` | Object | No | Intent-specific parameters |
| `estimates` | Array | No | Current estimates |

**Intent-specific Parameters**:

**fit_budget**: Fit to budget
```json
{"target_budget": 500000}
```

**scope_reduce**: Reduce scope
```json
{"keywords": ["API", "Admin panel"]}
```

**unit_cost_change**: Change unit cost
```json
{"new_daily_cost": 35000}
```

**risk_buffer**: Add risk buffer
```json
{"risk_percentage": 20}
```

**Request Example**:
```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/chat \
  -u username:password \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Want to fit within $500,000 budget",
    "intent": "fit_budget",
    "params": {"target_budget": 500000}
  }'
```

**Response** (`ChatResponse`):
```json
{
  "reply_md": "Generated 3 adjustment proposals to fit within $500,000 budget.",
  "suggestions": null,
  "proposals": [
    {
      "title": "Option 1: Focus on core features",
      "description": "Simplify admin panel, implement basic CRUD only",
      "delta": -72000,
      "estimated_total": 500000
    },
    {
      "title": "Option 2: Leverage external services",
      "description": "Delegate authentication to Auth0 or similar",
      "delta": -68000,
      "estimated_total": 504000
    },
    {
      "title": "Option 3: Phase splitting",
      "description": "Separate MVP (minimum features) as Phase 1",
      "delta": -100000,
      "estimated_total": 472000
    }
  ],
  "estimates": [
    {
      "deliverable_name": "Requirements Document",
      "deliverable_description": "Define system requirements (simplified version)",
      "person_days": 3.0,
      "amount": 120000.0,
      "reasoning": "Focus on core features"
    }
  ],
  "totals": {
    "subtotal": 454545.45,
    "tax": 45454.55,
    "total": 500000.0
  },
  "version": 1
}
```

**Error Responses**:
- `404 Not Found`: Task not found
- `500 Internal Server Error`: AI generation error

---

### 8. Apply Adjusted Estimates

Save adjusted estimates to database and regenerate Excel.

**Endpoint**:
```http
POST /api/v1/tasks/{task_id}/apply
```

**Path Parameters**:

| Name | Type | Description |
|------|------|-------------|
| `task_id` | String(UUID) | Task ID |

**Request Body**:
```json
{
  "estimates": [
    {
      "deliverable_name": "Requirements Document",
      "deliverable_description": "Define system requirements (simplified version)",
      "person_days": 3.0,
      "amount": 120000.0,
      "reasoning": "Focus on core features",
      "reasoning_breakdown": "Design: 1 day, Review: 0.5 days, Documentation: 1.5 days",
      "reasoning_notes": "MVP only"
    }
  ]
}
```

**Request Example**:
```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/apply \
  -u username:password \
  -H "Content-Type: application/json" \
  -d '{
    "estimates": [...]
  }'
```

**Response** (`TaskResultResponse`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "estimates": [...],
  "subtotal": 454545.45,
  "tax": 45454.55,
  "total": 500000.0,
  "error_message": null
}
```

**Error Responses**:
- `404 Not Found`: Task not found
- `500 Internal Server Error`: Database error, Excel generation error

---

### 9. Download Sample Excel

Download sample Excel input file (dynamically generated based on language setting).

**Endpoint**:
```http
GET /api/v1/sample-input
```

**Request Example**:
```bash
curl -O https://estimator.path-finder.jp/api/v1/sample-input \
  -u username:password
```

**Response**:
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Filename: `sample_input.xlsx`

**File Contents** (English setting):

| Deliverable Name | Description |
|-----------------|-------------|
| Requirements Document | Define and document system requirements |
| Basic Design Document | Design system architecture and key features |
| Detailed Design Document | Document detailed specifications for each feature |

---

### 10. Download Sample CSV

Download sample CSV input file (dynamically generated based on language setting).

**Endpoint**:
```http
GET /api/v1/sample-input-csv
```

**Request Example**:
```bash
curl -O https://estimator.path-finder.jp/api/v1/sample-input-csv \
  -u username:password
```

**Response**:
- Content-Type: `text/csv`
- Filename: `sample_input.csv`
- Encoding: UTF-8 with BOM (Excel compatible)

---

### 11. Get Translations

Get translation data for frontend.

**Endpoint**:
```http
GET /api/v1/translations
```

**Request Example**:
```bash
curl https://estimator.path-finder.jp/api/v1/translations \
  -u username:password
```

**Response**:
```json
{
  "language": "en",
  "translations": {
    "ui": {
      "app_title": "AI Estimator System",
      "button_create_task": "Create Task"
    },
    "prompts": {
      "language_instruction": "Please respond in English."
    },
    "excel": {
      "sheet_name": "Estimates",
      "column_deliverable_name": "Deliverable Name"
    }
  }
}
```

**Language Settings**:
- Based on server-side `LANGUAGE` environment variable (`ja` / `en`)
- Translation files: `backend/app/locales/ja.json`, `en.json`

---

## Data Models

### TaskResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String(UUID) | Yes | Task ID |
| `status` | String | Yes | Status (pending, in_progress, completed, failed) |
| `created_at` | DateTime | Yes | Creation timestamp (ISO 8601) |
| `updated_at` | DateTime | No | Update timestamp (ISO 8601) |
| `error_message` | String | No | Error message |
| `result_file_path` | String | No | Result file path |

### TaskStatusResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String(UUID) | Yes | Task ID |
| `status` | String | Yes | Status |
| `created_at` | DateTime | Yes | Creation timestamp |
| `updated_at` | DateTime | No | Update timestamp |
| `error_message` | String | No | Error message |

### TaskResultResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String(UUID) | Yes | Task ID |
| `status` | String | Yes | Status |
| `estimates` | Array[EstimateResponse] | Yes | Estimates list |
| `subtotal` | Float | Yes | Subtotal |
| `tax` | Float | Yes | Tax amount |
| `total` | Float | Yes | Total |
| `error_message` | String | No | Error message |

### EstimateResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `deliverable_name` | String | Yes | Deliverable name |
| `deliverable_description` | String | No | Deliverable description |
| `person_days` | Float | Yes | Estimated effort (person-days) |
| `amount` | Float | Yes | Amount |
| `reasoning` | String | No | Estimation rationale (legacy) |
| `reasoning_breakdown` | String | No | Effort breakdown |
| `reasoning_notes` | String | No | Rationale and notes |

### QAPairRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | String | Yes | Question |
| `answer` | String | Yes | Answer |

### ChatRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | String | No | User message |
| `intent` | String | No | Adjustment intent |
| `params` | Object | No | Intent-specific parameters |
| `estimates` | Array | No | Current estimates |

**intent values**:
- `fit_budget`: Fit to budget
- `scope_reduce`: Reduce scope
- `unit_cost_change`: Change unit cost
- `risk_buffer`: Add risk buffer

### ChatResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reply_md` | String | Yes | AI reply (Markdown) |
| `suggestions` | Array | No | Suggestions |
| `proposals` | Array | No | Proposal cards (2-step UX) |
| `estimates` | Array[ChatEstimateItem] | No | Adjusted estimates |
| `totals` | Object | No | Totals (subtotal, tax, total) |
| `version` | Integer | No | Version number |

---

## Error Codes

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | OK | Success |
| 400 | Bad Request | Check request parameters, Guardrails validation |
| 401 | Unauthorized | Check Basic Auth credentials |
| 404 | Not Found | Check task ID |
| 413 | Payload Too Large | Reduce file size to under 10MB |
| 422 | Unprocessable Entity | Request body validation error |
| 500 | Internal Server Error | Check server logs, OpenAI API status |
| 502 | Bad Gateway | Check backend service (Uvicorn) |
| 503 | Service Unavailable | Check resource limits, concurrent connections |
| 504 | Gateway Timeout | Check timeout settings, optimize processing |

### Error Response Format

```json
{
  "detail": "Detailed error message"
}
```

### Common Errors

#### 1. File Size Exceeded

**Response**:
```json
{
  "detail": "File size exceeds 10MB"
}
```

**Action**: Reduce file to under 10MB

#### 2. Invalid File Format

**Response**:
```json
{
  "detail": "Only Excel (.xlsx, .xls) or CSV (.csv) files are supported"
}
```

**Action**: Use Excel (.xlsx, .xls) or CSV (.csv) files

#### 3. Task Not Completed

**Response**:
```json
{
  "detail": "Task not completed (status: in_progress)"
}
```

**Action**: Check status with `/tasks/{task_id}/status` and wait for completion

#### 4. OpenAI API Error

**Response**:
```json
{
  "detail": "OpenAI API error: Rate limit exceeded"
}
```

**Action**:
- Check OpenAI rate limits
- Check API usage
- Retry logic automatically executes (max 3 attempts)

#### 5. Guardrails Validation Error

**Response**:
```json
{
  "detail": "Input validation failed: Potential prompt injection detected in system_requirements"
}
```

**Action**: Potential prompt injection attack detected; modify input content

---

## Rate Limiting

### Concurrent Connections

- Maximum concurrent requests: **5**
- Queue wait timeout: **30 seconds**

### OpenAI API Limits

- Retry logic: **Max 3 attempts** (exponential backoff: 1s, 2s, 4s)
- CircuitBreaker: Opens for 60 seconds after 5 consecutive failures

### Timeout Settings

- Apache ProxyTimeout: **600 seconds**
- Uvicorn keep-alive timeout: **120 seconds**

---

## Examples

### Scenario 1: Create Task from Excel → Get Result

#### Step 1: Create Task

```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks \
  -u username:password \
  -F "file=@input.xlsx" \
  -F "system_requirements=Requirements defined, 3-month development"
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  ...
}
```

#### Step 2: Get Questions

```bash
curl https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/questions \
  -u username:password
```

**Response**:
```json
[
  "What is the expected number of users and access frequency?",
  "Are there any development environment or infrastructure constraints?",
  ...
]
```

#### Step 3: Submit Answers

```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/answers \
  -u username:password \
  -H "Content-Type: application/json" \
  -d '[
    {"question":"Expected users?","answer":"1000 users, 100 accesses/day"},
    {"question":"Environment constraints?","answer":"AWS + Docker"}
  ]'
```

#### Step 4: Check Status (Polling)

```bash
curl https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/status \
  -u username:password
```

**Response (Processing)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  ...
}
```

**Response (Completed)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  ...
}
```

#### Step 5: Get Result

```bash
curl https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/result \
  -u username:password
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "estimates": [...],
  "subtotal": 520000.0,
  "tax": 52000.0,
  "total": 572000.0
}
```

#### Step 6: Download Excel

```bash
curl -O https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/download \
  -u username:password
```

---

### Scenario 2: Chat Adjustment to Fit Budget

#### Step 1: Chat Adjustment Request

```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/chat \
  -u username:password \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Want to fit within $500,000 budget",
    "intent": "fit_budget",
    "params": {"target_budget": 500000},
    "estimates": [...]
  }'
```

**Response**:
```json
{
  "reply_md": "Generated 3 adjustment proposals to fit within $500,000 budget.",
  "proposals": [
    {
      "title": "Option 1: Focus on core features",
      "description": "...",
      "delta": -72000,
      "estimated_total": 500000
    }
  ],
  "estimates": [...],
  "totals": {...}
}
```

#### Step 2: Apply Adjusted Estimates

```bash
curl -X POST https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/apply \
  -u username:password \
  -H "Content-Type: application/json" \
  -d '{
    "estimates": [...]
  }'
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "estimates": [...],
  "subtotal": 454545.45,
  "tax": 45454.55,
  "total": 500000.0
}
```

#### Step 3: Download Updated Excel

```bash
curl -O https://estimator.path-finder.jp/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/download \
  -u username:password
```

---

### Scenario 3: Create Task from Web Form

#### JavaScript Request Example

```javascript
const formData = new FormData();
formData.append('deliverables_json', JSON.stringify([
  {
    "name": "Requirements Document",
    "description": "Define system requirements"
  },
  {
    "name": "Basic Design Document",
    "description": "Design system architecture"
  }
]));
formData.append('system_requirements', 'Requirements defined, 3-month development');

const response = await fetch('https://estimator.path-finder.jp/api/v1/tasks', {
  method: 'POST',
  headers: {
    'Authorization': 'Basic ' + btoa('username:password')
  },
  body: formData
});

const task = await response.json();
console.log('Task ID:', task.id);
```

---

## Security

### Guardrails (Safety Validation)

All user inputs are validated by `SafetyService`.

**Validation Items**:
1. **Prompt Injection Detection**: Check suspicious patterns
2. **Inappropriate Content Detection**: Filter harmful content
3. **Length Limit Check**: Enforce maximum input length

**Validation Targets**:
- `system_requirements` (task creation)
- `answer` (answer submission, each answer)

**Validation Failure**:
- HTTP Status: `400 Bad Request`
- Error message includes detailed reason

### CORS

- Allowed origins: Configured `ALLOWED_ORIGINS` only
- Allowed methods: GET, POST
- Allowed headers: Content-Type, Authorization

### File Upload

- Maximum file size: **10MB**
- Allowed formats: Excel (.xlsx, .xls), CSV (.csv)
- Chunk processing: 1MB streaming

---

## Multi-language Support

### Language Settings

Configure language in server-side `.env` file:

```bash
LANGUAGE=ja  # or en
```

### Impact Scope

- AI-generated content (questions, estimate rationales, chat responses)
- Excel output (column names, labels, date format)
- Sample files (Excel/CSV)
- Error messages (partial)

### Get Translation Data

Use `/api/v1/translations` endpoint to get frontend translation data.

---

## References

- [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [DEVELOPER_GUIDE_EN.md](DEVELOPER_GUIDE_EN.md) - Developer Guide
- [ARCHITECTURE_EN.md](../architecture/ARCHITECTURE_EN.md) - Architecture Documentation

---

**Last Updated**: 2025-10-21
**Author**: Claude Code
**Version**: 1.0
