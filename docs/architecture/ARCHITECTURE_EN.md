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
2. **Scalability**: Support for future scaling
3. **Maintainability**: Easy to understand and modify structure
4. **Security**: Multi-layer defense for safety
5. **Resilience**: Auto-recovery from failures

### Key Technology Decisions

| Technology Selection | Reason |
|---------------------|--------|
| **FastAPI** | High performance, type safety, automatic API documentation |
| **SQLite** | Simple, file-based, no dependencies |
| **Uvicorn** | High-speed ASGI, async support |
| **Apache HTTPD** | Proven track record, SSL/TLS support, Basic authentication |
| **OpenAI API** | High accuracy AI, cost-effective (gpt-4o-mini) |
| **systemd** | Standard process management, automatic restart |

---

## System Architecture

### Overall Architecture Diagram

```mermaid
graph TB
    subgraph "Internet"
        User[User<br/>Web Browser]
    end

    subgraph "EC2 Instance"
        subgraph "Apache HTTPD Layer"
            Apache[Apache HTTPD 2.4.62<br/>Port 443/80<br/>- SSL/TLS Termination<br/>- Basic Authentication<br/>- Reverse Proxy]
        end

        subgraph "Application Layer"
            SystemD[systemd<br/>estimator.service<br/>- Auto-restart<br/>- Log management]

            Uvicorn[Uvicorn ASGI Server<br/>127.0.0.1:8100<br/>- Async processing<br/>- Timeout: 120s]

            FastAPI[FastAPI Application<br/>Python 3.11<br/>- REST API<br/>- Multi-language ja/en]
        end

        subgraph "Service Layer"
            TaskSvc[TaskService<br/>Task Management]
            QuestionSvc[QuestionService<br/>Question Generation]
            EstimateSvc[EstimatorService<br/>Estimation Calculation]
            ChatSvc[ChatService<br/>Adjustment Proposal]
            SafetySvc[SafetyService<br/>Safety Validation]
            InputSvc[InputService<br/>File Processing]
            ExportSvc[ExportService<br/>Excel Output]
        end

        subgraph "Data Layer"
            SQLite[(SQLite Database<br/>app.db<br/>- tasks<br/>- deliverables<br/>- qa_pairs<br/>- estimates<br/>- messages)]
        end
    end

    subgraph "External Services"
        OpenAI[OpenAI API<br/>OpenAI<br/>- Question generation<br/>- Estimate generation<br/>- Chat adjustment]
    end

    User -->|HTTPS| Apache
    Apache -->|HTTP| SystemD
    SystemD -->|Process| Uvicorn
    Uvicorn -->|ASGI| FastAPI

    FastAPI --> TaskSvc
    FastAPI --> QuestionSvc
    FastAPI --> EstimateSvc
    FastAPI --> ChatSvc
    FastAPI --> SafetySvc
    FastAPI --> InputSvc
    FastAPI --> ExportSvc

    TaskSvc --> SQLite
    QuestionSvc --> SQLite
    QuestionSvc --> OpenAI
    EstimateSvc --> SQLite
    EstimateSvc --> OpenAI
    ChatSvc --> SQLite
    ChatSvc --> OpenAI
    InputSvc --> SQLite
    ExportSvc --> SQLite
```

### Layer Details

#### 1. Frontend Layer

**Components**:
- Vanilla JavaScript
- Chart.js (graph rendering)
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

```mermaid
sequenceDiagram
    actor User as User
    participant UI as Web UI
    participant API as FastAPI
    participant Safety as SafetyService
    participant Input as InputService
    participant Task as TaskService
    participant Question as QuestionService
    participant Estimator as EstimatorService
    participant Export as ExportService
    participant DB as SQLite
    participant OpenAI as OpenAI API

    User->>UI: 1. Input deliverables<br/>(Excel/CSV/Web form)
    UI->>API: POST /api/v1/tasks

    API->>Safety: 2. Safety check
    Safety-->>API: OK

    API->>Input: 3. File processing
    Input->>Input: Parse Excel/CSV
    Input->>DB: 4. Create task
    DB-->>Input: task_id
    Input->>DB: 5. Save deliverables
    Input-->>API: task
    API-->>UI: TaskResponse

    UI->>API: 6. GET /tasks/{id}/questions
    API->>Question: Generate questions request
    Question->>DB: Get deliverables & requirements
    DB-->>Question: deliverables, requirements

    Question->>OpenAI: 7. Send LLM prompt<br/>(question generation)
    OpenAI-->>Question: 3 questions

    Question->>DB: 8. Save questions
    Question-->>API: questions
    API-->>UI: QuestionsResponse

    UI->>User: 9. Display questions
    User->>UI: 10. Input answers
    UI->>API: POST /tasks/{id}/answers

    API->>DB: 11. Save answers
    API->>Task: 12. Start estimation

    loop Each deliverable
        Task->>Estimator: Generate estimate
        Estimator->>OpenAI: Send LLM prompt<br/>(estimate generation)
        OpenAI-->>Estimator: Effort, cost, rationale
        Estimator->>DB: Save estimate
    end

    Task->>Estimator: 13. Calculate totals
    Estimator->>Estimator: Calculate subtotal, tax, total

    Task->>Export: 14. Generate Excel
    Export->>DB: Get data
    DB-->>Export: estimates, qa_pairs
    Export->>Export: Create Excel file
    Export-->>Task: file_path

    Task->>DB: 15. Save results
    Task-->>API: success
    API-->>UI: AnswersResponse

    UI->>API: 16. GET /tasks/{id}/result
    API->>DB: Get results
    DB-->>API: estimates, totals
    API-->>UI: ResultResponse
    UI->>User: 17. Display estimate
```

### Chat Adjustment Flow

```mermaid
sequenceDiagram
    actor User as User
    participant UI as Web UI
    participant API as FastAPI
    participant Safety as SafetyService
    participant Chat as ChatService
    participant DB as SQLite
    participant OpenAI as OpenAI API

    User->>UI: 1. Input adjustment request<br/>("reduce by $30,000")
    UI->>API: POST /tasks/{id}/chat

    API->>Safety: 2. Safety check
    Safety-->>API: OK

    API->>Chat: 3. Generate adjustment proposals
    Chat->>DB: Get current estimates
    DB-->>Chat: current_estimates

    Chat->>Chat: 4. Generate adjustment prompt<br/>(direction, amount)
    Chat->>OpenAI: 5. Send LLM prompt<br/>(adjustment proposals)
    OpenAI-->>Chat: 3 proposals

    Chat->>DB: 6. Save messages
    Chat-->>API: proposals
    API-->>UI: ChatResponse

    UI->>User: 7. Display proposal cards
    User->>UI: 8. Select proposal
    UI->>API: POST /tasks/{id}/apply

    API->>DB: 9. Update estimates
    API->>DB: 10. Regenerate Excel
    API-->>UI: success
    UI->>User: 11. Update complete
```

---

## Sequence Diagrams

### Task Creation Detailed Sequence

```mermaid
sequenceDiagram
    participant Client as Client
    participant API as API Layer
    participant Safety as SafetyService
    participant Input as InputService
    participant Task as TaskService
    participant DB as Database

    Client->>API: POST /api/v1/tasks<br/>(file OR deliverables_json)

    alt File upload
        API->>API: File size check<br/>(< 10MB)
        API->>API: File format check<br/>(.xlsx, .xls, .csv)
    end

    API->>Safety: validate_and_reject()<br/>(system_requirements)

    alt Guardrails check
        Safety->>Safety: Prompt injection detection
        Safety->>Safety: Inappropriate content detection
        alt If detected
            Safety-->>API: HTTPException(400)
            API-->>Client: Error Response
        end
    end

    alt File case
        API->>Input: load_excel_data(file_path)
        Input->>Input: Parse with openpyxl/pandas
        Input-->>API: deliverables_list
    else Web form case
        API->>API: JSON.parse(deliverables_json)
    end

    API->>Task: create_task(file_path, system_reqs)
    Task->>DB: INSERT INTO tasks
    DB-->>Task: task_id

    loop Each deliverable
        Task->>DB: INSERT INTO deliverables
    end

    Task-->>API: TaskResponse
    API-->>Client: 200 OK + TaskResponse
```

### Estimation Generation Detailed Sequence

```mermaid
sequenceDiagram
    participant API as API Layer
    participant Task as TaskService
    participant Question as QuestionService
    participant Estimator as EstimatorService
    participant Circuit as CircuitBreaker
    participant Retry as RetryLogic
    participant OpenAI as OpenAI API
    participant DB as Database

    API->>Task: process_task(task_id, answers)
    Task->>DB: UPDATE qa_pairs SET answer

    Task->>DB: SELECT deliverables
    DB-->>Task: deliverables_list

    loop Each deliverable (parallel execution)
        Task->>Estimator: estimate_deliverable()
        Estimator->>Circuit: check_state()

        alt CircuitBreaker CLOSED
            Circuit-->>Estimator: OK

            Estimator->>Retry: with_retry()
            loop Max 3 retries
                Retry->>OpenAI: create_completion()

                alt Success
                    OpenAI-->>Retry: response
                    Retry-->>Estimator: result
                else Timeout/Error
                    OpenAI-->>Retry: Error
                    Retry->>Retry: wait & retry
                end
            end

            alt All 3 failed
                Retry-->>Estimator: Error
                Estimator->>Circuit: record_failure()
                Circuit->>Circuit: increment_failure_count
            end

        else CircuitBreaker OPEN
            Circuit-->>Estimator: CircuitOpenError
            Estimator-->>Task: Fallback processing
        end

        Estimator->>DB: INSERT INTO estimates
    end

    Task->>Estimator: calculate_totals()
    Estimator-->>Task: subtotal, tax, total

    Task->>DB: UPDATE tasks SET status=completed
    Task-->>API: success
```

---

## Data Model

### ER Diagram

```mermaid
erDiagram
    tasks ||--o{ deliverables : "has many"
    tasks ||--o{ qa_pairs : "has many"
    tasks ||--o{ messages : "has many"
    deliverables ||--o{ estimates : "has many"

    tasks {
        string id PK "UUID"
        string excel_file_path "Uploaded file path"
        text system_requirements "System requirements"
        string status "pending/processing/completed/failed"
        text error_message "Error message"
        string result_file_path "Output Excel path"
        datetime created_at
        datetime updated_at
    }

    deliverables {
        string id PK "UUID"
        string task_id FK "Task ID"
        string name "Deliverable name"
        text description "Description"
        datetime created_at
    }

    qa_pairs {
        string id PK "UUID"
        string task_id FK "Task ID"
        text question "Question"
        text answer "Answer"
        datetime created_at
    }

    estimates {
        string id PK "UUID"
        string deliverable_id FK "Deliverable ID"
        float estimated_days "Estimated effort (person-days)"
        float estimated_cost "Estimated cost"
        json breakdown "Effort breakdown"
        text reasoning "Rationale & notes"
        datetime created_at
    }

    messages {
        string id PK "UUID"
        string task_id FK "Task ID"
        string role "user/assistant"
        text content "Message content"
        datetime created_at
    }
```

### Data Model Relationships

```mermaid
classDiagram
    class Task {
        +String id
        +String excel_file_path
        +Text system_requirements
        +TaskStatus status
        +Text error_message
        +String result_file_path
        +DateTime created_at
        +DateTime updated_at
        +List~Deliverable~ deliverables
        +List~QAPair~ qa_pairs
        +List~Message~ messages
    }

    class Deliverable {
        +String id
        +String task_id
        +String name
        +Text description
        +DateTime created_at
        +Task task
        +List~Estimate~ estimates
    }

    class QAPair {
        +String id
        +String task_id
        +Text question
        +Text answer
        +DateTime created_at
        +Task task
    }

    class Estimate {
        +String id
        +String deliverable_id
        +Float estimated_days
        +Float estimated_cost
        +JSON breakdown
        +Text reasoning
        +DateTime created_at
        +Deliverable deliverable
    }

    class Message {
        +String id
        +String task_id
        +String role
        +Text content
        +DateTime created_at
        +Task task
    }

    class TaskStatus {
        <<enumeration>>
        PENDING
        PROCESSING
        COMPLETED
        FAILED
    }

    Task "1" --> "*" Deliverable
    Task "1" --> "*" QAPair
    Task "1" --> "*" Message
    Deliverable "1" --> "*" Estimate
    Task --> TaskStatus
```

---

## Directory Structure

```
output3/backend/
├── app/
│   ├── main.py                    # FastAPI application
│   │
│   ├── api/                       # API endpoints
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── tasks.py           # Task-related API
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── task.py               # Task model
│   │   ├── deliverable.py        # Deliverable model
│   │   ├── qa_pair.py            # QAPair model
│   │   ├── estimate.py           # Estimate model
│   │   └── message.py            # Message model
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── task.py               # Task-related schemas
│   │   ├── estimate.py           # Estimate-related schemas
│   │   ├── qa_pair.py            # QA-related schemas
│   │   └── chat.py               # Chat-related schemas
│   │
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── task_service.py       # Task management service
│   │   ├── question_service.py   # Question generation service
│   │   ├── estimator_service.py  # Estimation calculation service
│   │   ├── chat_service.py       # Chat adjustment service
│   │   ├── safety_service.py     # Safety validation service
│   │   ├── input_service.py      # File input service
│   │   └── export_service.py     # Excel output service
│   │
│   ├── core/                      # Common functions & config
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration management
│   │   └── i18n.py               # Multi-language support
│   │
│   ├── db/                        # Database
│   │   ├── __init__.py
│   │   └── database.py           # DB connection & session management
│   │
│   ├── prompts/                   # LLM prompts
│   │   ├── __init__.py
│   │   ├── question_prompts.py   # Question generation prompts
│   │   ├── estimate_prompts.py   # Estimation generation prompts
│   │   └── chat_prompts.py       # Chat adjustment prompts
│   │
│   ├── middleware/                # Middleware
│   │   ├── __init__.py
│   │   ├── circuit_breaker.py    # Circuit breaker
│   │   ├── loop_detector.py      # Loop detection
│   │   └── resource_limiter.py   # Resource limiting
│   │
│   ├── utils/                     # Utilities
│   │   ├── __init__.py
│   │   └── retry.py              # Retry logic
│   │
│   ├── locales/                   # Multi-language translation files
│   │   ├── ja.json               # Japanese translations
│   │   └── en.json               # English translations
│   │
│   └── static/                    # Static files
│       ├── index.html            # Main UI
│       ├── styles.css            # Stylesheet
│       └── script.js             # Client-side JS
│
├── tests/                         # Test code
│   ├── __init__.py
│   ├── conftest.py               # pytest fixtures
│   ├── unit/                     # Unit tests
│   │   ├── test_task_service.py
│   │   ├── test_estimator_service.py
│   │   └── test_safety_service.py
│   ├── integration/              # Integration tests
│   │   ├── test_api_tasks.py
│   │   └── test_database.py
│   └── e2e/                      # E2E tests
│       └── test_full_workflow.py
│
├── .env                          # Environment variables
├── .env.sample                   # Environment variables sample
├── requirements.txt              # Python dependencies
├── pytest.ini                    # pytest configuration
└── app.db                        # SQLite database
```

---

## Security Architecture

### Multi-layer Defense

```mermaid
graph TB
    subgraph "Layer 1: Network"
        SSL[SSL/TLS Encryption<br/>Let's Encrypt]
        BasicAuth[Basic Authentication<br/>.htpasswd]
    end

    subgraph "Layer 2: Application"
        CORS[CORS Restriction<br/>Allowed origins only]
        FileSizeLimit[File Size Limit<br/>10MB]
        ResourceLimit[Resource Limit<br/>Concurrent request count]
    end

    subgraph "Layer 3: Business Logic"
        Safety[SafetyService<br/>Guardrails]
        InputValidation[Input Validation<br/>Pydantic]
        SQLInjection[SQL Injection Prevention<br/>SQLAlchemy ORM]
    end

    subgraph "Layer 4: Data"
        EnvVars[Environment Variable Isolation<br/>.env]
        FilePermission[File Permissions<br/>600]
        DBIsolation[Database Isolation<br/>Per user]
    end

    SSL --> CORS
    BasicAuth --> FileSizeLimit
    CORS --> Safety
    FileSizeLimit --> InputValidation
    ResourceLimit --> SQLInjection
    Safety --> EnvVars
    InputValidation --> FilePermission
    SQLInjection --> DBIsolation
```

### Guardrails Implementation

```mermaid
graph LR
    Input[User Input] --> Safety[SafetyService]

    Safety --> PI[Prompt Injection Detection]
    Safety --> IC[Inappropriate Content Detection]
    Safety --> LL[Length Limit Check]

    PI --> |Detected| Reject[HTTPException 400]
    IC --> |Detected| Reject
    LL --> |Exceeded| Reject

    PI --> |Safe| Process[Continue Processing]
    IC --> |Safe| Process
    LL --> |Safe| Process

    Process --> LLM[LLM API Call]
```

**Implementation**:
- `app/services/safety_service.py`
- `app/api/v1/tasks.py` (create_task, chat)

---

## Resilience Architecture

### CircuitBreaker Pattern

```mermaid
stateDiagram-v2
    [*] --> CLOSED: Initial state

    CLOSED --> OPEN: 5 consecutive failures
    OPEN --> HALF_OPEN: 60 seconds elapsed
    HALF_OPEN --> CLOSED: Success
    HALF_OPEN --> OPEN: Failure

    CLOSED: CircuitBreaker CLOSED<br/>Normal operation<br/>- Requests pass through<br/>- Count failures

    OPEN: CircuitBreaker OPEN<br/>Immediate failure<br/>- Block requests<br/>- Execute fallback

    HALF_OPEN: CircuitBreaker HALF_OPEN<br/>Test operation<br/>- Only 1 request allowed<br/>- CLOSED on success, OPEN on failure
```

**Configuration**:
- Failure threshold: 5 times
- Timeout: 60 seconds
- Half-open retry count: 1 time

**Implementation**: `app/middleware/circuit_breaker.py`

### Retry Logic

```mermaid
graph TB
    Start[Start API Call] --> Try1[1st Attempt]

    Try1 --> |Success| Success[Success]
    Try1 --> |Failure| Wait1[Wait 1 second]

    Wait1 --> Try2[2nd Attempt]
    Try2 --> |Success| Success
    Try2 --> |Failure| Wait2[Wait 2 seconds<br/>Exponential Backoff]

    Wait2 --> Try3[3rd Attempt]
    Try3 --> |Success| Success
    Try3 --> |Failure| Failure[Failure<br/>Record to CircuitBreaker]

    Success --> [*]
    Failure --> [*]
```

**Configuration**:
- Maximum retry count: 3 times
- Backoff strategy: Exponential (1s, 2s, 4s)
- Retry-eligible errors: Timeout, RateLimitError, APIConnectionError

**Implementation**: `app/utils/retry.py`

### Loop Detector

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant LoopDetector
    participant Cache

    Client->>API: Request (prompt_hash)
    API->>LoopDetector: check_loop(task_id, prompt_hash)

    LoopDetector->>Cache: get(task_id)
    Cache-->>LoopDetector: history[]

    alt Same prompt_hash 3+ times
        LoopDetector-->>API: LoopDetectedError
        API-->>Client: 400 Bad Request<br/>"Loop detected"
    else Normal
        LoopDetector->>Cache: append(prompt_hash)
        LoopDetector-->>API: OK
        API->>API: Continue processing
    end
```

**Configuration**:
- Loop detection threshold: 3 times
- Cache retention time: 1 hour

**Implementation**: `app/middleware/loop_detector.py`

### Resource Limiter

```mermaid
graph TB
    Request[Receive Request] --> Check[Check concurrent execution count]

    Check --> |< MAX_CONCURRENT| Acquire[Acquire semaphore]
    Check --> |>= MAX_CONCURRENT| Wait[Wait in queue<br/>Max 30 seconds]

    Wait --> |Timeout| Reject[503 Service Unavailable]
    Wait --> |Available| Acquire

    Acquire --> Process[Execute processing]
    Process --> Release[Release semaphore]
    Release --> Response[Return response]

    Reject --> [*]
    Response --> [*]
```

**Configuration**:
- Maximum concurrent executions: 5
- Timeout: 30 seconds

**Implementation**: `app/middleware/resource_limiter.py`

---

## Multi-language Architecture

### Translation System

```mermaid
graph TB
    subgraph "Environment Variables"
        ENV[.env<br/>LANGUAGE=ja/en]
    end

    subgraph "Translation Files"
        JA[locales/ja.json<br/>Japanese translations]
        EN[locales/en.json<br/>English translations]
    end

    subgraph "Application"
        I18N[i18n.py<br/>Translation engine]
        Services[Services<br/>Business logic]
        Prompts[Prompts<br/>LLM prompts]
        API[API Endpoints]
    end

    subgraph "Output"
        UI[UI Text]
        Excel[Excel Output]
        LLMOutput[LLM Generated Content]
    end

    ENV --> I18N
    JA --> I18N
    EN --> I18N

    I18N --> Services
    I18N --> Prompts
    I18N --> API

    Services --> UI
    Prompts --> LLMOutput
    API --> Excel
```

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

```mermaid
graph TB
    Start[Start Estimation] --> Split[Split Deliverables]

    Split --> P1[Deliverable 1<br/>LLM API Call]
    Split --> P2[Deliverable 2<br/>LLM API Call]
    Split --> P3[Deliverable 3<br/>LLM API Call]
    Split --> PN[Deliverable N<br/>LLM API Call]

    P1 --> |ThreadPoolExecutor| Join[Merge Results]
    P2 --> |ThreadPoolExecutor| Join
    P3 --> |ThreadPoolExecutor| Join
    PN --> |ThreadPoolExecutor| Join

    Join --> Calculate[Calculate Totals]
    Calculate --> Excel[Generate Excel]
    Excel --> End[Complete]
```

**Implementation**: `app/services/task_service.py`
- Parallel execution with `ThreadPoolExecutor`
- Maximum workers: 10

### Caching

```mermaid
graph LR
    Request[Request] --> CheckCache{Check Cache}

    CheckCache --> |HIT| CacheReturn[Return from Cache]
    CheckCache --> |MISS| Process[Execute Processing]

    Process --> LLM[LLM API Call]
    LLM --> SaveCache[Save to Cache]
    SaveCache --> Return[Return Result]

    CacheReturn --> [*]
    Return --> [*]
```

**Cache Targets**:
- Question generation results (per task ID)
- Adjustment proposals (task ID + request hash)

**TTL**: 1 hour

---

## References

- [DEPLOYMENT.md](../deployment/DEPLOYMENT.md) - Deployment Guide
- [DEVELOPER_GUIDE.md](../development/DEVELOPER_GUIDE.md) - Developer Guide
- [API_REFERENCE.md](../development/API_REFERENCE.md) - API Reference
- [SECURITY_CHECKLIST.md](../security/SECURITY_CHECKLIST.md) - Security Checklist

---

**Last Updated**: 2025-10-21
**Author**: Claude Code
**Version**: 1.0
