# Developer Guide

## 📋 Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Directory Structure](#directory-structure)
3. [Coding Standards](#coding-standards)
4. [Testing Procedures](#testing-procedures)
5. [Debugging Methods](#debugging-methods)
6. [Adding New Features](#adding-new-features)
7. [Multi-language Support](#multi-language-support)
8. [Common Issues and Solutions](#common-issues-and-solutions)

---

## Development Environment Setup

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Programming language |
| conda | latest | Python environment management |
| Git | 2.x+ | Version control |
| VSCode | latest | Editor (recommended) |
| SQLite | 3.x+ | Database |

### Setup Procedure

#### 1. Clone Repository

```bash
git clone https://github.com/daishir0/ai-estimator2.git
cd ai-estimator2/backend
```

#### 2. Create Python Virtual Environment

```bash
# Create conda environment
source /path/to/python/bin/activate
conda create -n your-python-env python=3.11
conda activate your-python-env
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

```bash
# Create .env file
cp .env.sample .env

# Edit
nano .env
```

**.env file contents**:
```bash
# OpenAI API Key (required)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx

# Database
DATABASE_URL=sqlite:///./app.db

# Language (ja or en)
LANGUAGE=ja

# Other settings...
```

#### 5. Initialize Database

```bash
# Auto-created on first startup
# To manually initialize:
rm app.db
uvicorn app.main:app --reload
```

#### 6. Start Server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### 7. Access in Browser

- UI: http://localhost:8000/ui
- API Docs: http://localhost:8000/docs

### VSCode Recommended Settings

**.vscode/settings.json**:
```json
{
  "python.defaultInterpreterPath": "/path/to/python/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"]
}
```

---

## Directory Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI application
│   │
│   ├── api/                       # API endpoints
│   │   └── v1/
│   │       └── tasks.py           # Task-related API
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── task.py
│   │   ├── deliverable.py
│   │   ├── qa_pair.py
│   │   ├── estimate.py
│   │   └── message.py
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── task.py
│   │   ├── estimate.py
│   │   ├── qa_pair.py
│   │   └── chat.py
│   │
│   ├── services/                  # Business logic
│   │   ├── task_service.py       # Task management
│   │   ├── question_service.py   # Question generation
│   │   ├── estimator_service.py  # Estimation calculation
│   │   ├── chat_service.py       # Chat adjustment
│   │   ├── safety_service.py     # Safety validation
│   │   ├── input_service.py      # File input
│   │   └── export_service.py     # Excel output
│   │
│   ├── core/                      # Common functions
│   │   ├── config.py             # Configuration management
│   │   └── i18n.py               # Multi-language support
│   │
│   ├── db/                        # Database
│   │   └── database.py           # DB connection
│   │
│   ├── prompts/                   # LLM prompts
│   │   ├── question_prompts.py
│   │   ├── estimate_prompts.py
│   │   └── chat_prompts.py
│   │
│   ├── middleware/                # Middleware
│   │   ├── circuit_breaker.py
│   │   ├── loop_detector.py
│   │   └── resource_limiter.py
│   │
│   ├── utils/                     # Utilities
│   │   └── retry.py
│   │
│   ├── locales/                   # Translation files
│   │   ├── ja.json
│   │   └── en.json
│   │
│   └── static/                    # Static files
│       ├── index.html
│       ├── styles.css
│       └── script.js
│
├── tests/                         # Test code
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
└── app.db                        # SQLite database
```

---

## Coding Standards

### Python Code Style

**Basic Policy**: PEP 8 compliant

#### Formatter

```bash
# Use Black (auto-format)
pip install black
black app/

# Use flake8 (Lint)
pip install flake8
flake8 app/
```

#### Type Hints

**Required**: Add type hints to all functions

```python
# Good
def get_task(task_id: str) -> Task:
    return db.query(Task).filter(Task.id == task_id).first()

# Bad
def get_task(task_id):
    return db.query(Task).filter(Task.id == task_id).first()
```

#### Docstrings

**Style**: Google Style

```python
def estimate_deliverable(deliverable: Deliverable, qa_pairs: List[QAPair]) -> Estimate:
    """Generate estimate for a single deliverable.

    Args:
        deliverable: Deliverable object to estimate
        qa_pairs: List of question-answer pairs for context

    Returns:
        Estimate object with calculated effort and cost

    Raises:
        OpenAIError: If API call fails
        ValidationError: If deliverable data is invalid
    """
    # Implementation...
```

### Naming Conventions

| Target | Convention | Example |
|--------|-----------|---------|
| Class | PascalCase | `EstimatorService` |
| Function/Variable | snake_case | `get_estimate`, `task_id` |
| Constant | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private | _prefix | `_internal_method` |

### Import Order

```python
# 1. Standard library
import os
import sys
from typing import List, Optional

# 2. Third-party libraries
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 3. Local modules
from app.models.task import Task
from app.services.task_service import TaskService
```

### Comments

**Write in English**: All comments and docstrings should be in English

```python
# Good
def calculate_total(estimates: List[Estimate]) -> float:
    """Calculate total cost from estimates."""
    # Sum all estimated costs
    subtotal = sum(e.estimated_cost for e in estimates)
    # Add tax (10% for Japan, 0% for English)
    tax = subtotal * (TAX_RATE / 100)
    return subtotal + tax

# Bad
def calculate_total(estimates: List[Estimate]) -> float:
    """見積りの合計を計算"""
    # 全見積りの合計
    subtotal = sum(e.estimated_cost for e in estimates)
    # 消費税を追加
    tax = subtotal * (TAX_RATE / 100)
    return subtotal + tax
```

---

## Testing Procedures

### Run All Tests

```bash
pytest tests/ -v --cov=app --cov-report=html
```

### Unit Tests Only

```bash
pytest tests/unit/ -v
```

### Integration Tests Only

```bash
pytest tests/integration/ -v
```

### E2E Tests Only

```bash
pytest tests/e2e/ -v
```

### Specific Test File

```bash
pytest tests/unit/test_task_service.py -v
```

### View Coverage Report

```bash
# Generate HTML report
pytest tests/ --cov=app --cov-report=html

# Open in browser
open htmlcov/index.html
```

### Test Execution Options

| Option | Description |
|--------|-------------|
| `-v` | Verbose output |
| `-s` | Show print statements |
| `-x` | Stop at first failure |
| `-k <pattern>` | Run tests matching pattern |
| `--lf` | Run last failed tests only |

---

## Debugging Methods

### Log Level Settings

```bash
# Start with DEBUG level
uvicorn app.main:app --reload --log-level debug
```

### Breakpoints

```python
# Use pdb
import pdb; pdb.set_trace()

# Or Python 3.7+
breakpoint()
```

### VSCode Debug Configuration

**.vscode/launch.json**:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "127.0.0.1",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def some_function():
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
```

---

## Adding New Features

### Step 1: Feature Design

1. **Requirements Definition**
   - Clarify feature purpose and scope
   - Create use cases

2. **API Design**
   - Design endpoints
   - Define request/response schemas

3. **Data Model Design**
   - Design required tables and columns
   - Define relationships

### Step 2: Implementation

#### 2-1. Create/Update Model

**For new table**:

```python
# app/models/new_model.py
from sqlalchemy import Column, String, Text
from app.db.database import Base

class NewModel(Base):
    __tablename__ = "new_models"

    id = Column(String(36), primary_key=True)
    name = Column(String(200))
    description = Column(Text)
```

#### 2-2. Create Schema

```python
# app/schemas/new_schema.py
from pydantic import BaseModel

class NewModelCreate(BaseModel):
    name: str
    description: str

class NewModelResponse(BaseModel):
    id: str
    name: str
    description: str

    class Config:
        from_attributes = True
```

#### 2-3. Implement Service Layer

```python
# app/services/new_service.py
from sqlalchemy.orm import Session
from app.models.new_model import NewModel

class NewService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> NewModel:
        """Create new model instance."""
        model = NewModel(**data)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model
```

#### 2-4. Add API Endpoint

```python
# app/api/v1/new_endpoint.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.new_service import NewService
from app.schemas.new_schema import NewModelCreate, NewModelResponse

router = APIRouter()

@router.post("/new-models", response_model=NewModelResponse)
def create_new_model(
    data: NewModelCreate,
    db: Session = Depends(get_db)
):
    """Create new model."""
    service = NewService(db)
    model = service.create(data.dict())
    return model
```

#### 2-5. Register Router

```python
# app/main.py
from app.api.v1 import new_endpoint

app.include_router(
    new_endpoint.router,
    prefix="/api/v1",
    tags=["new_models"]
)
```

### Step 3: Test Implementation

```python
# tests/unit/test_new_service.py
import pytest
from app.services.new_service import NewService

def test_create_new_model(db_session):
    """Test creating new model."""
    service = NewService(db_session)
    data = {"name": "Test", "description": "Test desc"}
    model = service.create(data)

    assert model.id is not None
    assert model.name == "Test"
    assert model.description == "Test desc"
```

### Step 4: Multi-language Support

**Add translations to ja.json / en.json**:

```json
{
  "ui": {
    "new_feature_title": "New Feature Title"
  },
  "messages": {
    "new_feature_created": "New feature has been created"
  }
}
```

**Use in code**:

```python
from app.core.i18n import t

title = t('ui.new_feature_title')
message = t('messages.new_feature_created')
```

### Step 5: Update Documentation

- Add new endpoint to API_REFERENCE.md
- Update feature list in README.md
- Record changes in CHANGELOG.md

---

## Multi-language Support

For details, see [CLAUDE.md](../../CLAUDE.md#multi-language-support).

### Quick Procedure

#### 1. Add to Translation Files

**backend/app/locales/ja.json**:
```json
{
  "ui": {
    "new_button": "新しいボタン"
  }
}
```

**backend/app/locales/en.json**:
```json
{
  "ui": {
    "new_button": "New Button"
  }
}
```

#### 2. Get Translation in Code

```python
from app.core.i18n import t

button_text = t('ui.new_button')
```

#### 3. Test Both Languages

```bash
# Japanese
nano backend/.env
# LANGUAGE=ja
sudo systemctl restart estimator

# English
nano backend/.env
# LANGUAGE=en
sudo systemctl restart estimator
```

---

## Common Issues and Solutions

### Q1: ImportError: cannot import name 'xxx'

**Cause**: Circular import

**Solution**:
- Check `__init__.py`
- Use lazy import (import inside function)

### Q2: SQLAlchemy relationship error

**Cause**: Relationship definition error

**Solution**:
```python
# Reference from ModelA to ModelB
class ModelA(Base):
    model_b_id = Column(String(36), ForeignKey("model_bs.id"))
    model_b = relationship("ModelB", back_populates="model_as")

class ModelB(Base):
    model_as = relationship("ModelA", back_populates="model_b")
```

### Q3: Pydantic validation error

**Cause**: Schema and model mismatch

**Solution**:
```python
class MySchema(BaseModel):
    class Config:
        from_attributes = True  # Convert SQLAlchemy model to Pydantic
```

### Q4: Translation not reflected

**Cause**: Service not restarted

**Solution**:
```bash
sudo systemctl restart estimator
```

---

## References

- [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Official Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Official Documentation](https://docs.pydantic.dev/)
- [pytest Official Documentation](https://docs.pytest.org/)

---

**Last Updated**: 2025-10-21
**Author**: Claude Code
**Version**: 1.0
